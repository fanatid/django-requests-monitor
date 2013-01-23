import re

from django.conf import settings


try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('django-requests-monitor').version
except Exception, e:
    VERSION = 'unknown'


config = {
    'STORAGE': 'redis://127.0.0.1:6379',
    'TIMEOUT': 300,
    'PREFIX':  '/requests/',
    'FILTERS': (),
}
config.update(getattr(settings, 'REQUESTS_MONITOR_CONFIG', {}))

import requests_monitor.urls
filters = [
    ('requests_monitor.filters.DisallowUrlFilter', (re.compile('^/%s' % requests_monitor.urls._PREFIX), ), {}),
]
for name in config['FILTERS']:
    args, kwargs = (), {}
    if isinstance(name, (tuple, list)):
        name = list(name)
        if len(name) == 2:
            if isinstance(name[1], dict):
                name.insert(1, ())
            else:
                name.insert(2, {})
        name, args, kwargs = name
    filters.append((name, args, kwargs))
config['FILTERS'] = filters

settings.REQUESTS_MONITOR_CONFIG = config
