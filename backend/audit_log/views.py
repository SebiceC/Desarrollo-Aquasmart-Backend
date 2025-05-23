from auditlog.models import LogEntry
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import LogEntryFilter
from .serializers import LogEntrySerializer


class LogEntryListView(generics.ListAPIView):
    serializer_class = LogEntrySerializer
    permission_classes = [IsAuthenticated]
    filterset_class = LogEntryFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['actor__username', 'object_repr', 'changes']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']

    def get_queryset(self):
        return LogEntry.objects.select_related('actor', 'content_type')