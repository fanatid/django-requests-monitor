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
}
config.update(getattr(settings, 'REQUESTS_MONITOR_CONFIG', {}))
settings.REQUESTS_MONITOR_CONFIG = config
