from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import EnviosContador
from caudal.models import WaterConsumptionRecord
from .serializers import ConsumoSerializer
from datetime import timedelta
from django.utils.timezone import now

@api_view(['POST'])
@permission_classes([AllowAny])
def recibir_consumo(request):
    serializer = ConsumoSerializer(data=request.data)
    if serializer.is_valid():
        consumo_obj = serializer.save()
        dispositivo = consumo_obj.device
        lote = dispositivo.id_lot

        # Obtener o crear el contador para este dispositivo
        contador_obj, created = EnviosContador.objects.get_or_create(
            device=dispositivo,
            lote=lote,
            defaults={'contador': 0}
        )

        # Incrementar el contador y guardar
        contador_obj.contador += 1
        contador_obj.save()

        if contador_obj.contador >= 28:
            ultimo_registro = WaterConsumptionRecord.objects.filter(
                lot=lote, device=dispositivo
            ).order_by('-end_date').first()

            fecha_fin = now()
            if ultimo_registro:
                previous_reading = ultimo_registro.current_reading
                start_date = ultimo_registro.end_date + timedelta(seconds=1)
            else:
                previous_reading = 0
                start_date = fecha_fin - timedelta(days=28)

            current_reading = consumo_obj.contador_unidades / 1000.0  # Ajusta escala

            WaterConsumptionRecord.objects.create(
                lot=lote,
                device=dispositivo,
                previous_reading=previous_reading,
                current_reading=current_reading,
                start_date=start_date,
                end_date=fecha_fin,
                monthly_consumption=current_reading - previous_reading,
                period_consumption=current_reading - previous_reading,
                accumulated_consumption=current_reading,
                billed=False,
            )

            # Reiniciar contador para próximo ciclo
            contador_obj.contador = 0
            contador_obj.save()

            return Response({"mensaje": "Registro mensual creado correctamente"}, status=status.HTTP_201_CREATED)

        return Response({"mensaje": "Consumo parcial registrado"}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
