from django.urls import path
from rest_framework.routers import DefaultRouter
from notification.views import NotificationViewSet

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('unread/', NotificationViewSet.as_view({'get': 'unread_count'})), 
    path('mark-as-read/<int:pk>/', NotificationViewSet.as_view({'post': 'mark_as_read'})),
] + router.urls