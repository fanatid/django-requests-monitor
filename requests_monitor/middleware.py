import imp
import thread

from debug_toolbar.middleware import DebugToolbarMiddleware

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
        content_length = len(response.content)
        ret = super(RequestMonitorMiddleware, self).process_response(request,
            response)
        ident = thread.get_ident()
        toolbar = self.__class__.toolbars.get(ident)
        if toolbar is not None \
          and not request.get_full_path().startswith('/%s' % requests_monitor.urls._PREFIX):
            self.__class__.debug_toolbars[ident] = toolbar
            call_process_response = content_length != len(response.content)
            panels = []
            for panel in toolbar.panels:
                if call_process_response:
                    panel.process_response(request, response)
                panels.append({
                    'title':        unicode(panel.title()),
                    'nav_title':    unicode(panel.nav_title()),
                    'nav_subtitle': unicode(panel.nav_subtitle()),
                    'content':      panel.content(),
                })
            Storage.add(request=request, response=response, panels=panels)
            del self.__class__.debug_toolbars[ident]
            del self.__class__.toolbars[ident]
        return ret
