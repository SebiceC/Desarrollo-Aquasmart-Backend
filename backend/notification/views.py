from rest_framework import viewsets
from rest_framework.response import Response
from notification.models import Notification
from notification.serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def unread_count(self, request, *args, **kwargs):
        count = self.queryset.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})

    def mark_as_read(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})