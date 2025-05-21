from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from auditlog.models import LogEntry
from .serializers import LogEntrySerializer

class LogEntryListView(generics.ListAPIView):
    serializer_class = LogEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['actor__username', 'object_repr', 'changes']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']

    def get_queryset(self):
        queryset = LogEntry.objects.select_related('actor', 'content_type')

        # Obtener parámetros de la URL
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        action = self.request.query_params.get('action')
        content_type = self.request.query_params.get('content_type')
        actor = self.request.query_params.get('actor')

        # Aplicar filtros si los parámetros existen
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__gte=end_date)
        if action:
            queryset = queryset.filter(action=action)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        if actor:
            queryset = queryset.filter(actor_id=actor)

        return queryset