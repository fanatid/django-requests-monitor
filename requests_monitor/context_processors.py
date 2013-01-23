import sys

from django.http import HttpResponseServerError
from django.views import debug as debug_views
from django.utils import timezone


def info(storage, request, response, toolbar):
    return {
        'date':   timezone.now(),
        'method': request.method,
        'status': response.status_code,
        'path':   request.get_full_path(),
    }

def panels(storage, request, response, toolbar):
    return {'panels': [{
        'title':        unicode(panel.title()),
        'nav_title':    unicode(panel.nav_title()),
        'nav_subtitle': unicode(panel.nav_subtitle()),
        'content':      panel.content(),
    } for panel in toolbar.panels]}

def response_500_error(storage, request, response, toolbar):
    data = {}
    if isinstance(response, HttpResponseServerError):
        reporter = debug_views.ExceptionReporter(request, *sys.exc_info())
        data['response_content'] = reporter.get_traceback_html()
    return data
