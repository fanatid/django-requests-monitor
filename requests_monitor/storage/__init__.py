import re

from django.conf import settings


class StorageParseError(Exception):
    pass

addrport = re.compile(r"^(.+):(\d{1,5})$")

def _get_storage(url):
    try:
        if url.startswith('redis://'):
            host, port = addrport.search(url[8:]).groups()
            from requests_monitor.storage.backends.redisdb import RedisStorage
            return RedisStorage(host, port)
        elif url.startswith('builtin://'):
            host, port = addrport.search(url[10:]).groups()
            from requests_monitor.storage.backends.builtin import BuiltinStorage
            return BuiltinStorage(host, port)
    except AttributeError:
        raise StorageParseError('Cann\'t parse string: %s' % url)
    raise StorageParseError('Cann\'t parse string: %s'%url)

Storage = _get_storage(settings.REQUESTS_MONITOR_CONFIG['STORAGE'])
