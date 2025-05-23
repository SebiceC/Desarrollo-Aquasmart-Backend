from django_filters import rest_framework as filters
from auditlog.models import LogEntry

class LogEntryFilter(filters.FilterSet):
    ACTION_CHOICES = (
        ('0', 'CREATE'),
        ('1', 'UPDATE'),
        ('2', 'DELETE'),
        ('3', 'ACCESS'),
        ('CREATE', 'CREATE'),
        ('UPDATE', 'UPDATE'),
        ('DELETE', 'DELETE'),
        ('ACCESS', 'ACCESS'),
    )

    action = filters.CharFilter(method='filter_action')
    start_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
    actor = filters.CharFilter(field_name="actor__document")
    content_type = filters.CharFilter(field_name="content_type__model")

    class Meta:
        model = LogEntry
        fields = ["action", "content_type", "actor"]

    def filter_action(self, queryset, name, value):
        if not value:
            return queryset

        action_map = {
            '0': 0, 'CREATE': 0, 'create': 0,
            '1': 1, 'UPDATE': 1, 'update': 1,
            '2': 2, 'DELETE': 2, 'delete': 2,
            '3': 3, 'ACCESS': 3, 'access': 3,
        }

        action_value = action_map.get(str(value))
        if action_value is not None:
            return queryset.filter(action=action_value)
        return queryset