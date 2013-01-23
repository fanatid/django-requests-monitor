import re

from django.conf import settings

import requests_monitor.urls
from requests_monitor.filters import DisallowUrlFilter
from requests_monitor.utils.importlib import import_attr


try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('django-requests-monitor').version
except Exception, e:
    VERSION = 'unknown'


config = {
    'STORAGE':         'redis://127.0.0.1:6379',
    'TIMEOUT':         300,
    'PREFIX':          '/requests/',
    'FILTERS':         (),
    'DATA_PROCESSORS': (
        'requests_monitor.context_processors.response_500_error',
    ),
}
config.update(getattr(settings, 'REQUESTS_MONITOR_CONFIG', {}))

filters = [
    (DisallowUrlFilter, (re.compile('^/%s' % requests_monitor.urls._PREFIX),), {})
]
for row in config['FILTERS']:
    args, kwargs = (), {}
    if isinstance(row, (tuple, list)):
        row = list(row)
        if len(row) == 2:
            if isinstance(row[1], dict):
                row.insert(1, ())
            else:
                row.insert(2, {})
        row, args, kwargs = row
    filters.append((import_attr(row), args, kwargs))
config['FILTERS'] = filters

config['DATA_PROCESSORS'] = [
    'requests_monitor.context_processors.info',
    'requests_monitor.context_processors.panels',
] + list(config['DATA_PROCESSORS'])
config['DATA_PROCESSORS'] = [import_attr(path)
    for path in config['DATA_PROCESSORS']]

settings.REQUESTS_MONITOR_CONFIG = config
