import json
import hashlib
import copy

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.handlers.wsgi import WSGIRequest

import requests_monitor


class StorageJSONEncode(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, WSGIRequest):
            data = copy.copy(o.environ)
            data.update({
                'wsgi.errors':       '',
                'wsgi.file_wrapper': '',
                'wsgi.input':        '',
            })
            return data
        else:
            return super(StorageJSONEncode, self).default(o)


class Storage(object):
    def add(self, data):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def get_keys(self):
        raise NotImplementedError

    def get_info(self, keys, chunk_size):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def make_key(self, data):
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()

    def _timeout(self):
        return getattr(settings, 'RM_STORAGE_TIMEOUT',
            requests_monitor.RM_STORAGE_TIMEOUT)
    timeout = property(_timeout)

    def dump(self, data):
        return json.dumps(data, cls=StorageJSONEncode)

    def load(self, data):
        return json.loads(data)
