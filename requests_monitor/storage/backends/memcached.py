import re
import telnetlib

import memcache

from requests_monitor.storage.backends.base import Storage


class MemcachedKeys(object):
    """
    Based on https://github.com/dlrust/python-memcached-stats
    """
    _slab_regex = re.compile(ur'STAT items:(.*):number')
    _key_regex  = re.compile(ur'ITEM (.*) \[.*; .*\]')

    def __init__(self, host, port):
        self._client = telnetlib.Telnet(host, port)

    def __del__(self):
        self._client.close()

    def command(self, cmd):
        self._client.write('%s\n'%cmd)
        return self._client.read_until('END')

    def slab_ids(self):
        return self._slab_regex.findall(self.command('stats items'))

    def keys(self, limit=1000):
        cmd = 'stats cachedump %%(id)s %(limit)s' % {'limit': limit}
        return [key for id in self.slab_ids()
            for key in self._key_regex.findall(self.command(cmd % {'id': id}))]


class MemcachedStorage(Storage):
    _memcached_client = None

    def __init__(self, host='127.0.0.1', port='11211'):
        self._host = host
        self._port = port

    def _get_memcached_client(self):
        if self._memcached_client is None:
            self._memcached_client = memcache.Client([
                '%(host)s:%(port)s' % {'host': self._host, 'port': self._port}])
        return self._memcached_client
    _client = property(_get_memcached_client)

    def add(self, data):
        timeout = self.timeout
        if 'date' in data and 'expiry' in data:
            timeout = (data['expiry']-data['date']).seconds
        data = self.dump(data)
        key = self.make_key(data)
        self._client.set(key, data, timeout)
        return key

    def get(self, key):
        value = self._client.get(key)
        if value is not None:
            value = self.load(value)
        return value

    def get_keys(self):
        return MemcachedKeys(self._host, self._port).keys()

    def get_info(self, keys, chunk_size=10):
        info = []
        for i in xrange(0, len(keys), chunk_size):
            for key, value in self._client.get_multi(keys[i:i+chunk_size]).items():
                value = self.load(value)
                value.pop('panels')
                value.pop('request')
                value['key'] = key
                info.append(value)
        return info

    def delete(self, key):
        self._client.delete(key)
