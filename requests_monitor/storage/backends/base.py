import json
import hashlib
import time
import random
import string

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder


class StorageJSONEncode(DjangoJSONEncoder):
    pass


class Storage(object):
    _KEY_PREFIX      = 'request:'
    _client_instance = None
    _info_fields = (
        'key',
        'date',
        'method',
        'status',
        'path',
    )

    def add(self, request, response, toolbar=None):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def get_keys(self, clean_db=True):
        raise NotImplementedError

    def get_info(self, keys):
        raise NotImplementedError

    def _timeout(self):
        return settings.REQUESTS_MONITOR_CONFIG['TIMEOUT']
    timeout = property(_timeout)

    def _dump(self, data):
        return json.dumps(data, cls=StorageJSONEncode)

    def _load(self, data):
        return json.loads(data)

    def _make_key(self, data):
        symbols = string.ascii_letters
        salt = [random.choice(symbols) for _ in range(random.randrange(40, 50))]
        return hashlib.md5(''.join(salt) + data).hexdigest()

    def _make_data(self, request, response, toolbar=None):
        data = {
            'expiry': time.time() + self.timeout,
            'key':    self._make_key('%s:%s' % (time.time(), request.get_full_path())),
        }
        for processor in settings.REQUESTS_MONITOR_CONFIG['DATA_PROCESSORS']:
            data.update(processor(self, request, response, toolbar))
        return (data['key'], data)
