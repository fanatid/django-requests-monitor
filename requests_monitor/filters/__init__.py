from django.conf import settings
from django.core import exceptions
from django.utils.importlib import import_module

from requests_monitor.filters.filters import *


def _get_filter(path, args, kwargs):
    try:
        module, classname = path.rsplit('.', 1)
    except ValueError:
        raise exceptions.ImproperlyConfigured('%s isn\'t a filter module' % path)
    try:
        mod = import_module(module)
    except ImportError, e:
        raise exceptions.ImproperlyConfigured('Error importing filter %s: "%s"' % (module, e))
    try:
        cls = getattr(mod, classname)
    except AttributeError:
        raise exceptions.ImproperlyConfigured('Filter module "%s" does not define a "%s" class' % (module, classname))
    return cls(*args, **kwargs)

def get_filters():
    return [_get_filter(path, args, kwargs)
        for path, args, kwargs in settings.REQUESTS_MONITOR_CONFIG['FILTERS']]
