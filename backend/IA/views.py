from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from datetime import datetime
from django.utils import timezone
from .models import ClimateRecord,Lot
from .serializers import ClimateRecordSerializer
from .utils import api_climate_request, predecir_n_meses,formatear_predicciones, generate_code_prediction
import time
import pandas as pd
from rest_framework import generics
from .models import ConsuptionPredictionLot
from .serializers import ConsuptionPredictionLotSerializer
from rest_framework.permissions import IsAuthenticated
import joblib
from django.conf import settings
import os
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError,PermissionDenied,NotFound
from dateutil.relativedelta import relativedelta

class ClimateRecordViewSet(viewsets.ModelViewSet):
    queryset = ClimateRecord.objects.all()
    serializer_class = ClimateRecordSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def fetch_climate_data(self, request):
        location = request.data.get('location', "4.60971%2C-74.08175")
        date = request.data.get('date', timezone.now().strftime("%Y-%m-%d"))
        today = timezone.now()

        # Obtener el último registro
        latest_record = ClimateRecord.objects.order_by('-datetime').first()

        if latest_record:
            if latest_record.final_date >= today:
                # Ya hay un registro válido, devolverlo sin hacer petición externa
                serializer = ClimateRecordSerializer(latest_record)
                return Response({
                    "message": "Ya existe un registro con datos válidos.",
                    "record": serializer.data
                }, status=status.HTTP_200_OK)

        # Continuar con la solicitud externa si no hay registro válido
        climate_data = api_climate_request(location, date)

        if not climate_data:
            return Response(
                {"error": "No se pudieron obtener datos de la API de clima"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        days = climate_data.get("days", [])
        if not days:
            return Response(
                {"error": "No se encontraron datos para la fecha especificada"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        saved_records = []
        for day_data in days:
            try:
                datetime_str = day_data.get('datetime')
                datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d")

                sunrise_time = datetime.strptime(day_data.get('sunrise'), "%H:%M:%S").time()
                sunset_time = datetime.strptime(day_data.get('sunset'), "%H:%M:%S").time()

                climate_record = ClimateRecord(
                    datetime=datetime_obj,
                    tempmax=day_data.get('tempmax'),
                    tempmin=day_data.get('tempmin'),
                    precip=day_data.get('precip'),
                    precipprob=day_data.get('precipprob'),
                    precipcover=day_data.get('precipcover'),
                    windgust=day_data.get('windgust'),
                    windspeed=day_data.get('windspeed'),
                    pressure=day_data.get('pressure'),
                    cloudcover=day_data.get('cloudcover'),
                    solarradiation=day_data.get('solarradiation'),
                    sunrise=sunrise_time,
                    sunset=sunset_time,
                    # final_date y luminiscencia deben ser calculados en el modelo
                )

                climate_record.save()
                serializer = ClimateRecordSerializer(climate_record)
                saved_records.append(serializer.data)

            except Exception as e:
                return Response(
                    {"error": f"Error al procesar los datos del clima: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {"message": "Datos climáticos obtenidos y guardados con éxito", "records": saved_records}, 
            status=status.HTTP_201_CREATED
        )

@api_view(['GET'])
def get_latest_climate_data(request):
    """
    Endpoint para obtener el registro climático más reciente.
    """
    try:
        latest_record = ClimateRecord.objects.order_by('-datetime').first()
        
        if latest_record:
            serializer = ClimateRecordSerializer(latest_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "No hay registros climáticos disponibles"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {"error": f"Error al obtener los datos del clima: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ConsuptionPredictionLotListCreateView(generics.ListCreateAPIView):
    serializer_class = ConsuptionPredictionLotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
       id_lot = self.request.query_params.get('lot')
       user = self.request.user

       if user.has_perm("AquaSmart.ver_predicciones_lotes"):
        return ConsuptionPredictionLot.objects.all().order_by('-created_at')

       elif user.has_perm("AquaSmart.ver_prediccion_consumo_mi_lote"):
            if id_lot:
                try:
                    lot_instan = Lot.objects.get(pk=id_lot)
                except Lot.DoesNotExist:
                    raise NotFound(f"No se encontró el lote con ID: {id_lot}")

                if lot_instan.plot.owner == user:
                    return ConsuptionPredictionLot.objects.filter(lot=id_lot).order_by('-created_at')
                else:
                    raise PermissionDenied("No tienes permiso para ver este lote.")
            else:
                # Si no se pasa `id_lot`, obtener todos los lotes del usuario
                return ConsuptionPredictionLot.objects.filter(
                    lot__plot__owner=user
                ).order_by('-created_at')

       raise PermissionDenied("No tienes permiso para ver las predicciones.")

    def perform_create(self, serializer):
        user = self.request.user
        lot = serializer.validated_data['lot']
              
        lot_id= lot.id_lot  
        if user.has_perm("AquaSmart.generar_predicciones_lotes"):
            pass  # Admin: puede generar predicciones para cualquier lote

        elif user.has_perm("AquaSmart.generar_prediccion_consumo_mi_lote"):
            if lot.plot.owner != user:
                raise PermissionDenied("No puedes generar una predicción para un lote que no pertenece a tu lote.")
        else:
            raise PermissionDenied("No tienes permiso para generar predicciones.")   
        
        period_time = int(serializer.validated_data['period_time'])
        # ⚠️ Validación previa: ya existe una predicción activa
        pred_existente = ConsuptionPredictionLot.objects.filter(
            lot=lot,
            period_time=period_time,
            final_date__gte=timezone.now()
        ).first()

        if pred_existente:
            text_mes =""
            if period_time == 1:
                text_mes = "Mes"
            else:
                 text_mes = "Meses"   
            raise ValidationError({
                "detail": f"Ya existe una predicción activa para este lote con ese periodo de {period_time} {text_mes }.",                
            })
        datos = ClimateRecord.objects.order_by('id').last()
        fecha_actual = datos.datetime
        mes = str(fecha_actual.month)
        año = str(fecha_actual.year)      
        
        datos_usuario = {
        'Año': año,
        'Mes_numero': mes,
        'Consumo Neiva (m3-mes)': 10.00,
        'Temperatura Minima(°C)':datos.tempmin,
        'Temperatura Maxima(°C)':datos.tempmax,
        'Precipitacion(mm)': datos.precip,
        'Probabilidad de Precipitacion(%)':datos.precipprob,
        'Cubrimiento de Precipitacion(%)': datos.precipcover,
        'Presión del nivel del Mar (mbar)': datos.pressure,
        'Nubosidad (%)': datos.cloudcover,
        'Radiación Solar (W/m2)': datos.solarradiation,
        'Velocidad del Viento (km/h)': datos.windspeed,
        'Luminiscencia': datos.luminiscencia
        }
        columnas_scaler = [
        'Consumo Neiva (m3-mes)', 'Temperatura Minima(°C)', 'Temperatura Maxima(°C)',
        'Precipitacion(mm)', 'Probabilidad de Precipitacion(%)',
        'Cubrimiento de Precipitacion(%)', 'Presión del nivel del Mar (mbar)',
        'Nubosidad (%)', 'Radiación Solar (W/m2)', 'Velocidad del Viento (km/h)',
        'Luminiscencia'
        ]
        scaler_x_path = os.path.join(settings.BASE_DIR, 'ia', 'Scaler', 'scaler_X_transformer.pkl')
        scaler_X = joblib.load(scaler_x_path)
        # Convertir y escalar solo columnas compatibles con el scaler
        df_usuario = pd.DataFrame([datos_usuario])[columnas_scaler]
        datos_usuario_scaled = scaler_X.transform(df_usuario)

        # Obtener datos para la predicción
        datos_actuales = datos_usuario_scaled[0]
        
        historico = None
        timesteps = 3
        # Ejecutar la predicción
        predicciones = predecir_n_meses(datos_actuales, historico, period_time, columnas_scaler, timesteps)
       
        predicciones_formateadas = formatear_predicciones(predicciones, fecha_inicio=timezone.now())

        # Crear un código único para agrupar las predicciones
        code_prediction = generate_code_prediction(ConsuptionPredictionLot,lot_id,period_time)
        final_date = timezone.now() + timedelta(days=7)
        
        for i, pred in enumerate(predicciones_formateadas):            
            date_prediction = final_date.date() + relativedelta(months=i+1)    
            ConsuptionPredictionLot.objects.create(
                user=user,                
                lot=lot,                
                period_time=period_time,
                created_at=timezone.now(),
                 date_prediction =date_prediction,
                consumption_prediction=pred['valor'],
                code_prediction=code_prediction,
                final_date=final_date
            )