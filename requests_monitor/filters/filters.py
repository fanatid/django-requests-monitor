from requests_monitor.filters.base import BaseFilter

__all__ = ['DisallowUrlFilter', 'AjaxOnlyFilter']


class DisallowUrlFilter(BaseFilter):
    def __init__(self, regex):
        self.regex = regex

    def process_request(self, request):
        return self.regex.match(request.get_full_path()) is None


class AjaxOnlyFilter(BaseFilter):
    def process_request(self, request):
        return request.is_ajax()
