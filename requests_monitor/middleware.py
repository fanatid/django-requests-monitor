import imp
import thread
import datetime

from django.http import HttpResponseRedirect
from django.utils import timezone

from debug_toolbar.middleware import _HTML_TYPES, DebugToolbarMiddleware

import requests_monitor.urls
from requests_monitor.storage import Storage


class RequestMonitorMiddleware(DebugToolbarMiddleware):
    toolbars = {}

    def __init__(self):
        super(RequestMonitorMiddleware, self).__init__()

    def process_request(self, request):
        ret = super(RequestMonitorMiddleware, self).process_request(request)
        ident = thread.get_ident()
        toolbar = self.__class__.debug_toolbars.get(ident)
        if toolbar is not None:
            try:
                path = request.get_full_path()
                if path.startswith('/%s' % requests_monitor.urls._PREFIX):
                    raise Exception()
            except:
                del self.__class__.debug_toolbars[ident]
            else:
                self.__class__.toolbars[ident] = toolbar
            urlconf = imp.new_module('urlconf')
            urlconf.urlpatterns = requests_monitor.urls.urlpatterns + \
                request.urlconf.urlpatterns
            request.urlconf = urlconf
        return ret

    def process_response(self, request, response):
        ret = super(RequestMonitorMiddleware, self).process_response(request,
            response)
        ident = thread.get_ident()
        toolbar = self.__class__.toolbars.get(ident)
        if toolbar is not None:
            self.__class__.debug_toolbars[ident] = toolbar
            date = timezone.now()
            data = {
                'date':    date,
                'expiry':  date + datetime.timedelta(seconds=Storage.timeout),
                'method':  request.method,
                'status':  response.status_code,
                'path':    request.get_full_path(),
                'request': request,
                'panels':  [],
            }
            call_process_response = False
            if isinstance(response, HttpResponseRedirect):
                if not toolbar.config['INTERCEPT_REDIRECTS']:
                    call_process_response = True
            if not ('gzip' not in response.get('Content-Encoding', '') and \
                response.get('Content-Type', '').split(';')[0] in _HTML_TYPES):
                call_process_response = True
            for panel in toolbar.panels:
                if call_process_response:
                    panel.process_response(request, response)
                data['panels'].append({
                    'title':        unicode(panel.title()),
                    'nav_title':    unicode(panel.nav_title()),
                    'nav_subtitle': unicode(panel.nav_subtitle()),
                    'content':      panel.content(),
                })
            Storage.add(data)
            del self.__class__.debug_toolbars[ident]
            del self.__class__.toolbars[ident]
        return ret
