from rest_framework import viewsets
from .models import Reporte, Asignacion, InformeMantenimiento
from .serializers import ReporteSerializer, AsignacionSerializer, InformeMantenimientoSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework import status
from django.utils import timezone
class ReporteViewSet(viewsets.ModelViewSet):
    
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer

    def pending_reports(self, request, *args, **kwargs):
        queryset = self.queryset.filter(estado='PENDIENTE')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all()
    serializer_class = AsignacionSerializer

    def assign_technician(self, request, *args, **kwargs):
        # Tu lógica de asignación aquí
        return Response({'status': 'technician assigned'})

class InformeMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = InformeMantenimiento.objects.all()
    serializer_class = InformeMantenimientoSerializer
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def crear_informe(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete_report(self, request, pk=None):
        try:
            informe = self.get_object()

            # Verificar si el usuario es administrador
            if not request.user.is_staff:
                return Response({'detail': 'Solo un administrador puede aprobar el informe.'}, status=status.HTTP_403_FORBIDDEN)

            # Validar que el informe no esté ya aprobado
            if informe.aprobado:
                return Response({'detail': 'El informe ya está aprobado.'}, status=status.HTTP_400_BAD_REQUEST)

            # Actualizar el estado de aprobado
            informe.aprobado = True
            informe.save()

            return Response({'detail': 'Informe aprobado exitosamente.'}, status=status.HTTP_200_OK)
        except InformeMantenimiento.DoesNotExist:
            return Response({'detail': 'Informe no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status_to_complete(self, request, pk=None):
        try:
            informe = self.get_object()

            # Verificar si el estado actual es 'PENDIENTE'
            if informe.estado != 'PENDIENTE':
                return Response({'detail': 'El informe ya no está en estado PENDIENTE.'}, status=status.HTTP_400_BAD_REQUEST)

            # Comprobar si ya existe algo en la base de datos
            if not informe.descripcion_solucion or not informe.image_base64:
                # Validar que los campos requeridos estén presentes en la solicitud
                descripcion_solucion = request.data.get('descripcion_solucion')
                image_base64 = request.data.get('image_base64')

                if not descripcion_solucion:
                    return Response({'descripcion_solucion': 'Debe proporcionar una descripción de la solución.'}, status=status.HTTP_400_BAD_REQUEST)

                if not image_base64:
                    return Response({'image_base64': 'Debe proporcionar una imagen en formato base64.'}, status=status.HTTP_400_BAD_REQUEST)

                # Actualizar los campos con los datos proporcionados
                informe.descripcion_solucion = descripcion_solucion
                informe.image_base64 = image_base64

            # Actualizar el estado y la fecha de finalización
            informe.estado = 'COMPLETADO'
            informe.fecha_fin = timezone.now()
            informe.save()

            return Response({'detail': 'El informe ha sido actualizado a COMPLETADO exitosamente.'}, status=status.HTTP_200_OK)
        except InformeMantenimiento.DoesNotExist:
            return Response({'detail': 'Informe no encontrado.'}, status=status.HTTP_404_NOT_FOUND)   