from django.conf import settings

from requests_monitor.filters.filters import *


def get_filters():
    return [cls(*args, **kwargs)
        for cls, args, kwargs in settings.REQUESTS_MONITOR_CONFIG['FILTERS']]
