import re

from django.conf import settings

import requests_monitor


class StorageParseError(Exception):
    pass

def _get_storage(url):
    if url.startswith('memcached://'):
        try:
            host, port = re.search('^memcached://(.+):(\d{1,5})$', url).groups()
        except AttributeError:
            raise StorageParseError('Cann\'t parse string: %s'%url)
        else:
            from requests_monitor.storage.backends.memcached import MemcachedStorage
            return MemcachedStorage(host, port)

Storage = _get_storage(getattr(settings, 'RM_STORAGE',
	requests_monitor.RM_STORAGE))
