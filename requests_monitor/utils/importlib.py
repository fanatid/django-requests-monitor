from django.core import exceptions
from django.utils.importlib import import_module


def import_attr(path):
    try:
        module, classname = path.rsplit('.', 1)
    except ValueError:
        raise exceptions.ImproperlyConfigured('%s isn\'t a module' % path)
    try:
        mod = import_module(module)
    except ImportError, e:
        raise exceptions.ImproperlyConfigured('Error importing %s: "%s"' % (module, e))
    try:
        cls = getattr(mod, classname)
    except AttributeError:
        raise exceptions.ImproperlyConfigured('Module "%s" does not define a "%s" attribute' % (module, classname))
    return cls
