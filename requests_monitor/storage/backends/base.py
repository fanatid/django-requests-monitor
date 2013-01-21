import sys
import json
import hashlib
import time
import random
import string

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseServerError
from django.views import debug as debug_views
from django.utils import timezone


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

    def add(self, request, response, panels=None):
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

    def _make_data(self, request, response, panels=None):
        data = {
            'date':   timezone.now(),
            'expiry': time.time() + self.timeout,
            'method': request.method,
            'status': response.status_code,
            'path':   request.get_full_path(),
            'panels': panels,
        }
        if isinstance(response, HttpResponseServerError):
            reporter = debug_views.ExceptionReporter(request, *sys.exc_info())
            data['response_content'] = reporter.get_traceback_html()
        key = self._make_key('%(date)s:%(path)s' % data)
        data['key'] = key
        return (key, data)
