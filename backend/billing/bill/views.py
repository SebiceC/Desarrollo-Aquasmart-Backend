from rest_framework import generics
from .models import Bill
from .serializers import BillSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwnerOrAdmin  # Asegúrate de importar tu permiso
from caudal.models import WaterConsumptionRecord
class BillListView(generics.ListAPIView):
    """Vista para obtener todas las facturas o solo las de un usuario."""
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Devuelve solo las facturas del usuario si es un usuario normal, o todas las facturas si es un admin."""
        user = self.request.user
        if user.is_staff:
            return Bill.objects.all()  # Administradores pueden ver todas las facturas
        return Bill.objects.filter(client=user)  # Usuarios solo pueden ver sus propias facturas

class BillDetailView(generics.RetrieveAPIView):
    """Vista para obtener el detalle de una factura específica."""
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]  # Asegúrate de que esté el permiso

    def get_object(self):
        """Devuelve la factura asociada al pk, verificando el permiso del usuario."""
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)  # Verifica permisos
        return obj
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Bill
from plots_lots.models import Lot
from billing.models import Company
import hmac
import hashlib
import time
from datetime import datetime, timedelta
@csrf_exempt
@require_POST
def generate_monthly_bills(request):
    """Endpoint para generar facturas mensuales mediante una solicitud HTTP"""
    # Verificación de seguridad con token secreto
    provided_token = request.headers.get('X-Api-Token')
    
    if not settings.BILLING_SECRET_TOKEN or not provided_token:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # Comparación segura de tokens
    if not hmac.compare_digest(settings.BILLING_SECRET_TOKEN, provided_token):
        return JsonResponse({'error': 'Invalid token'}, status=403)
    
    # Obtener la empresa que emite las facturas
    company = Company.objects.first()
    
    if not company:
        return JsonResponse({'error': 'No company found'}, status=404)
    
    # Obtener lotes activos
    active_lots = Lot.objects.filter(is_activate=True)
    
    bills_created = 0
    errors = []
    
    # Fecha actual
    today = datetime.now().date()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    for lot in active_lots:
        try:
            client = lot.plot.owner
            
            # Verificar si ya existe una factura para este lote en el mes actual
            existing_bill = Bill.objects.filter(
                lot=lot,
                creation_date__gte=first_day,
                creation_date__lte=last_day
            ).exists()
            
            if existing_bill:
                continue
                
            # Verificar si el cliente está inactivo
            is_client_inactive = not getattr(client, 'is_active', True)
            
            if is_client_inactive:
                # Buscar la última factura para este cliente
                last_client_bill = Bill.objects.filter(
                    client=client
                ).order_by('-creation_date').first()
                
                if last_client_bill and getattr(last_client_bill, 'client_inactive', False):
                    # Ya se le facturó una vez estando inactivo, no crear nueva factura
                    continue
            last_consumption = WaterConsumptionRecord.objects.filter(
                lot=lot,
                billed=False,
                end_date__lt=today  # Solo consumos con periodos ya cerrados
        ).order_by('-end_date').first()
        
            if last_consumption:
                volumetric_quantity = last_consumption.period_consumption
            else:
                volumetric_quantity = getattr(lot, 'estimated_consumption', 2)    
            
            # Crear factura
            bill = Bill(
                company=company,
                client=client,
                lot=lot,
                fixed_rate_quantity=1,
                volumetric_rate_quantity=volumetric_quantity
            )
            
            # Si el cliente está inactivo, marcar
            if is_client_inactive and hasattr(Bill, 'client_inactive'):
                bill.client_inactive = True
            last_consumption.billed = True    
            bill.save()
            last_consumption.save()
            bills_created += 1
            
        except Exception as e:
            errors.append(f"Error al procesar lote {lot.id_lot}: {str(e)}")
    
    return JsonResponse({
        'status': 'success',
        'bills_created': bills_created,
        'date': today.strftime('%Y-%m-%d'),
        'errors': errors
    })    