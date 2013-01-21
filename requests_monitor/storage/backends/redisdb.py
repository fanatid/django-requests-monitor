import datetime, time

import redis

from requests_monitor.storage.backends.base import Storage


class RedisStorage(Storage):
    def __init__(self, host, port):
        self._host = host
        self._port = int(port)

    def _get_client(self):
        if self._client_instance is None:
            self._client_instance = redis.StrictRedis(
                host=self._host, port=self._port)
        return self._client_instance
    _client = property(_get_client)

    def _clean_db(self):
        expiry_keys = []
        for key in self.get_keys(clean_db=False):
            key = self._KEY_PREFIX + key
            if self._client.type(key) != 'hash':
                continue
            expiry = float(self._client.hmget(key, ['expiry'])[0])
            if expiry - time.time() < 0:
                expiry_keys.append(key)
        if expiry_keys:
            self._client.delete(*expiry_keys)

    def add(self, request, response, panels=None):
        key, data = self._make_data(request, response, panels)
        for datakey, value in data.items():
            data[datakey] = self._dump(value)
        self._client.hmset(self._KEY_PREFIX + key, data)
        self._clean_db()
        return key

    def get(self, key):
        fields = self._client.hkeys(self._KEY_PREFIX + key)
        return dict(zip(fields,
            map(self._load, self._client.hmget(self._KEY_PREFIX + key, fields))))

    def get_keys(self, clean_db=True):
        if clean_db:
            self._clean_db()
        prefix_length = len(self._KEY_PREFIX)
        for key in self._client.keys(pattern=self._KEY_PREFIX + '*'):
            yield key[prefix_length:]

    def get_info(self, keys):
        for key in keys:
            data = self._client.hmget(self._KEY_PREFIX + key, self._info_fields)
            yield dict(zip(self._info_fields, map(self._load, data)))
