from django.conf import settings
from django.conf.urls import patterns, include, url

import requests_monitor


_PREFIX = getattr(settings, 'RM_URL', requests_monitor.RM_URL)
if _PREFIX.startswith('/'):
    _PREFIX = _PREFIX[1:]
if _PREFIX.endswith('/'):
    _PREFIX = _PREFIX[:-1]


urlpatterns_without_prefix = patterns('requests_monitor.views',
    url(r'^$', 					'index'),
    url(r'^r/(?P<key>\w{32})$', 'request')
)

urlpatterns = patterns('',
    url(r'^%s/' % _PREFIX, include(urlpatterns_without_prefix)),
)