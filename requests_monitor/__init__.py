try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('django-requests-monitor').version
except Exception, e:
    VERSION = 'unknown'


RM_STORAGE         = 'memcached://127.0.0.1:11211'
RM_STORAGE_TIMEOUT = 300
RM_URL             = '/requests/'
