import imp
import thread

from debug_toolbar.middleware import DebugToolbarMiddleware

import requests_monitor.urls
from requests_monitor.storage import Storage
from requests_monitor.filters import get_filters


class RequestMonitorMiddleware(DebugToolbarMiddleware):
    toolbars = {}
    filters  = {}

    def __init__(self):
        super(RequestMonitorMiddleware, self).__init__()

    def process_request(self, request):
        ret = super(RequestMonitorMiddleware, self).process_request(request)
        ident = thread.get_ident()
        toolbar = self.__class__.debug_toolbars.get(ident)
        if toolbar is not None:
            self.__class__.filters[ident] = get_filters()
            if all(f.process_request(request) for f in self.__class__.filters[ident]):
                self.__class__.toolbars[ident] = toolbar
            else:
                del self.__class__.debug_toolbars[ident]
        urlconf = imp.new_module('urlconf')
        urlconf.urlpatterns = requests_monitor.urls.urlpatterns + \
            request.urlconf.urlpatterns
        request.urlconf = urlconf
        return ret

    def process_response(self, request, response):
        content_length = len(response.content)
        ret = super(RequestMonitorMiddleware, self).process_response(request,
            response)
        ident = thread.get_ident()
        toolbar = self.__class__.toolbars.get(ident)
        if toolbar is not None:
            if all(f.process_response(request, response) for f in self.__class__.filters[ident]):
                self.__class__.debug_toolbars[ident] = toolbar
                if content_length == len(response.content):
                    for panel in toolbar.panels:
                        panel.process_response(request, response)
                Storage.add(request=request, response=response, toolbar=toolbar)
                del self.__class__.debug_toolbars[ident]
            del self.__class__.toolbars[ident]
            del self.__class__.filters[ident]
        return ret
