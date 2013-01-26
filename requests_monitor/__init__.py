import os
import multiprocessing
import functools
import re

from django.conf import settings
from django.core import management
from django.core.management.commands import runserver

import requests_monitor.urls
from requests_monitor.filters import DisallowUrlFilter
from requests_monitor.utils.importlib import import_attr


try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('django-requests-monitor').version
except Exception, e:
    VERSION = 'unknown'


config = {
    'STORAGE':         'builtin://127.0.0.1:10627',
    'RUN_STORAGE_WITH_RUNSERVER': True,
    'TIMEOUT':         300,
    'PREFIX':          '/requests/',
    'FILTERS':         (),
    'DATA_PROCESSORS': (),
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
    'requests_monitor.context_processors.response_500_error',
] + list(config['DATA_PROCESSORS'])
config['DATA_PROCESSORS'] = [import_attr(path)
    for path in config['DATA_PROCESSORS']]

settings.REQUESTS_MONITOR_CONFIG = config

if settings.REQUESTS_MONITOR_CONFIG['RUN_STORAGE_WITH_RUNSERVER'] \
 and settings.REQUESTS_MONITOR_CONFIG['STORAGE'].startswith('builtin://'):
    runserver_run = runserver.Command.run
    def run(self, *args, **options):
        if os.environ.get("RUN_MAIN") is None:
            multiprocessing.Process(target=management.call_command,
                args=('runstorage',)).start()
        return runserver_run(self, *args, **options)
    runserver.Command.run = functools.update_wrapper(
        wrapper=run, wrapped=runserver_run)
