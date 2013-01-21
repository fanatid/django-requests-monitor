import re

from django.conf import settings


class StorageParseError(Exception):
    pass

def _get_storage(url):
    if url.startswith('redis://'):
        try:
            host, port = re.search('^redis://(.+):(\d{1,5})$', url).groups()
        except AttributeError:
            raise StorageParseError('Cann\'t parse string: %s'%url)
        else:
            from requests_monitor.storage.backends.redisdb import RedisStorage
            return RedisStorage(host, port)
    raise StorageParseError('Cann\'t parse string: %s'%url)

Storage = _get_storage(settings.REQUESTS_MONITOR_CONFIG['STORAGE'])
