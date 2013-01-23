import json

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from requests_monitor.storage import Storage


def index(request):
    if request.is_ajax():
        keys  = set(request.REQUEST.getlist('keys[]'))
        ekeys = set(Storage.get_keys())
        data  = {
            'new':    list(Storage.get_info(list(ekeys-keys)[:50])),
            'delete': list(keys-ekeys),
        }
        return HttpResponse(json.dumps(data), 'application/json')
    request.META['CSRF_COOKIE_USED'] = True
    return render_to_response('requests_monitor/base.html', {},
        RequestContext(request))


def request(request, key):
    data = Storage.get(str(key))
    if data is None:
        raise Http404
    data['response_content'] = 'response_content' in data
    return HttpResponse(json.dumps(data), 'application/json')


def response_content(request, key):
    data = Storage.get(str(key))
    if data is None or 'response_content' not in data:
        raise Http404
    return HttpResponse(data['response_content'])
