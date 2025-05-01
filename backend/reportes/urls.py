from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (  
    ReporteViewSet,
    AsignacionViewSet,
    InformeMantenimientoViewSet
)

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')
router.register(r'asignaciones', AsignacionViewSet, basename='asignacion')
router.register(r'informes', InformeMantenimientoViewSet, basename='informe')

urlpatterns = [
    # Endpoints personalizados
    path('reportes/<int:pk>/assign', AsignacionViewSet.as_view({'post': 'assign_technician'}), name='assign-technician'),
    path('informes/crear', InformeMantenimientoViewSet.as_view({'post': 'crear_informe'}), name='crear-informe'),
    path('informes/<int:pk>/admin-vaidate', InformeMantenimientoViewSet.as_view({'post': 'complete_report'}), name='complete-report'),
    path('informes/<int:pk>/update-status-complete', InformeMantenimientoViewSet.as_view({'post': 'update_status_to_complete'}), name='update-status-complete'),
    path('reportes/pending', ReporteViewSet.as_view({'get': 'pending_reports'}), name='pending-reports'),
] + router.urls