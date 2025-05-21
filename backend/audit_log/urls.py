from django.urls import path
from .views import LogEntryListView

urlpatterns = [
    path('logs', LogEntryListView.as_view(), name='audit-logs'),
]