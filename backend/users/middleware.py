from django.utils.timezone import now
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

class LoginTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
