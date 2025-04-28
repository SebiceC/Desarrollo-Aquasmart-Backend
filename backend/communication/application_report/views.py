from rest_framework import generics
from .models import ApplicationFailureReport
from .serializers import ApplicationFailureReportSerializer
from rest_framework.permissions import IsAuthenticated


class ApplicationFailureReportCreateView(generics.CreateAPIView):
    """Vista para crear reportes de fallos en el aplicativo."""
    queryset = ApplicationFailureReport.objects.all()
    serializer_class = ApplicationFailureReportSerializer
    permission_classes = [IsAuthenticated]  