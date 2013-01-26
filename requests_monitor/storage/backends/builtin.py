import socket
import time
import json

from requests_monitor.storage.backends.base import Storage


class BuiltinStorageClient(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def _read_sock(self, sock):
        response = ''
        while '\r\n' not in response:
            response += sock.recv(4096)
        length, response = response.split('\r\n', 1)
        try:
            length = int(length)
        except ValueError:
            return None
        while len(response) < length:
            response += sock.recv(4096)
        if len(response) > length:
            return None
        try:
            return json.loads(response)
        except ValueError:
            return None

    def execute_command(self, *command):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.250)
        sock.connect((self._host, self._port))
        command = json.dumps(command)
        sock.send('%d\r\n%s' % (len(command), command))
        response = self._read_sock(sock)
        sock.close()
        return response

    def hget(self, key, field):
        return self.execute_command('HGET', key, field)

    def hkeys(self, key):
        return self.execute_command('HKEYS', key)

    def hmget(self, key, *fields):
        return self.execute_command('HMGET', key, *fields)

    def hmset(self, key, data):
        return self.execute_command('HMSET', key, *sum(data.items(), ()))

    def hset(self, key, field, value):
        return self.execute_command('HSET', key, field, value)

    def keys(self):
        return self.execute_command('KEYS')

    def type(self, key):
        return self.execute_command('TYPE', key)

    def delete(self, *keys):
        return self.execute_command('DEL', *keys)


class BuiltinStorage(Storage):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def _get_client(self):
        if self._client_instance is None:
            self._client_instance = BuiltinStorageClient(
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
