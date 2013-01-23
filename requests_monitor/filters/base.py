
class BaseFilter(object):

    def process_request(self, request):
        return True

    def process_response(self, request, response):
        return True
