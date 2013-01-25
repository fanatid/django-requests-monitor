import socket
import time

from requests_monitor.storage.backends.base import Storage


class BuiltinClient(object):
    def __init__(self, host, port):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._buf = ''

    def __del__(self):
        self._socket.close()

    def _recv(self):
        while self._buf.find('\r\n') == -1:
            self._buf += self._socket.recv(512)

    def _get_row(self):
        pos = self._buf.find('\r\n')
        if pos == -1:
            self._recv()
            pos = self._buf.find('\r\n')
        row, self._buf = self._buf.split('\r\n', 1)
        return row

    def _get_reply(self, size):
        if size == -1:
            return None
        buf = self._get_row() + '\r\n'
        while len(buf) < size+2:
            buf += self._get_row() + '\r\n'
        return buf[:-2]

    def _get_multi_reply(self, size):
        bulk = []
        while size > 0:
            row = self._get_row()
            if row.startswith('$') and row[1:].isdigit():
                bulk.append(self._get_reply(int(row[1:])))
            else:
                bulk.append(None)
            size -= 1
        return bulk

    def execute_command(self, *args):
        data = '*%d\r\n' % len(args)
        for arg in args:
            data += '$%d\r\n%s\r\n' % (len(arg), arg)
        self._socket.send(data)
        row = self._get_row()
        if row.startswith(':') or row.startswith('-'):
            return (not row.startswith('-'), row[1:])
        elif row.startswith('$') and (row[1:].isdigit() or row == '$-1'):
            return (True, self._get_reply(int(row[1:])))
        elif row.startswith('*') and row[1:].isdigit():
            return (True, self._get_multi_reply(int(row[1:])))
        else:
            return (False, None)

    def hget(self, key, field):
        ret = self.execute_command('HGET', key, field)
        return ret[1] if ret[0] else None

    def hkeys(self, key):
        ret = self.execute_command('HKEYS', key)
        return ret[1] if ret[0] else []

    def hmget(self, key, *fields):
        ret = self.execute_command('HMGET', key, *fields)
        return ret[1] if ret[0] else []

    def hmset(self, key, data):
        ret = self.execute_command('HMSET', key, *sum(data.items(), ()))
        return int(ret[1]) if ret[0] and ret[1].isdigit() else 0

    def hset(self, key, field, value):
        ret = self.execute_command('HSET', key, field, value)
        return int(ret[1]) if ret[0] and ret[1].isdigit() else 0

    def keys(self):
        ret = self.execute_command('KEYS')
        return ret[1] if ret[0] else []

    def type(self, key):
        ret = self.execute_command('TYPE', key)
        return ret[1] if ret[0] else None

    def delete(self, *keys):
        ret = self.execute_command('DEL', *keys)
        return int(ret[1]) if ret[0] and ret[1].isdigit() else 0


class BuiltinStorage(Storage):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def _get_client(self):
        if self._client_instance is None:
            self._client_instance = BuiltinClient(
                host=self._host, port=int(self._port))
        return self._client_instance
    _client = property(_get_client)

    def _clean_db(self):
        expiry_keys = []
        for key in self.get_keys(clean_db=False):
            key = self._KEY_PREFIX + key
            if self._client.type(key) != 'hash':
                continue
            expiry = self._client.hget(key, 'expiry')
            if expiry is None:
                continue
            expiry = float(expiry)
            if expiry - time.time() < 0:
                expiry_keys.append(key)
        if expiry_keys:
            self._client.delete(*expiry_keys)

    def add(self, request, response, toolbar=None):
        key, data = self._make_data(request, response, toolbar)
        for datakey, value in data.items():
            data[datakey] = self._dump(value)
        self._client.hmset(self._KEY_PREFIX + key, data)
        self._clean_db()
        return key

    def get(self, key):
        fields = self._client.hkeys(self._KEY_PREFIX + key)
        return dict(zip(fields,
            map(self._load, self._client.hmget(self._KEY_PREFIX + key, *fields))))

    def get_keys(self, clean_db=True):
        if clean_db:
            self._clean_db()
        prefix_length = len(self._KEY_PREFIX)
        for key in self._client.keys():
            yield key[prefix_length:]

    def get_info(self, keys):
        for key in keys:
            data = self._client.hmget(self._KEY_PREFIX + key, *self._info_fields)
            yield dict(zip(self._info_fields, map(self._load, data)))
