import time

import redis

from requests_monitor.storage.backends.base import Storage


class RedisStorage(Storage):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def _get_client(self):
        if self._client_instance is None:
            self._client_instance = redis.StrictRedis(
                host=self._host, port=int(self._port))
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
            map(self._load, self._client.hmget(self._KEY_PREFIX + key, fields))))

    def get_keys(self, settings=None, clean_db=True):
        if clean_db:
            self._clean_db()
        prefix_length = len(self._KEY_PREFIX)
        keys = [key[prefix_length:] for key in self._client.keys(pattern=self._KEY_PREFIX + '*')]
        if settings is not None:
            fields = (
                'unix_time',
                'ajax',
                'method',
                'status',
            )
            result = []
            for key in keys:
                info = dict(zip(fields, map(self._load, self._client.hmget(self._KEY_PREFIX + key, *fields))))
                if settings.get('ajax_only', False) and info['ajax'] == False:
                    continue
                if settings.get('request_method', False) \
                  and info['method'] != settings['request_method']:
                    continue
                if settings.get('request_status_code', False) \
                  and settings['request_status_code'].isdigit() \
                  and info['status'] != int(settings['request_status_code']):
                    continue
                result.append((key, info['unix_time']))
            if settings.get('requests_count', False) and settings['requests_count'].isdigit():
                result = sorted(result, key=lambda x: x[1], reverse=True)[:int(settings['requests_count'])]
            keys = [x[0] for x in result]
        return keys

    def get_info(self, keys):
        for key in keys:
            data = self._client.hmget(self._KEY_PREFIX + key, self._info_fields)
            yield dict(zip(self._info_fields, map(self._load, data)))
