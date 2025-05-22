from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from plots_lots.models import Lot


class ClimateRecord(models.Model):
    ''' Modelo que guarda los datos climáticos de la API '''
    datetime = models.DateTimeField()
    tempmax = models.FloatField()
    tempmin = models.FloatField()
    precip = models.FloatField()
    precipprob = models.FloatField()
    precipcover = models.FloatField()
    windgust  = models.FloatField()
    windspeed = models.FloatField()
    pressure = models.FloatField()
    cloudcover = models.FloatField()
    solarradiation = models.FloatField()
    sunrise = models.TimeField()
    sunset = models.TimeField()
    luminiscencia = models.FloatField()
    final_date = models.DateTimeField()

    class Meta:
        verbose_name = "Registro climático"
        verbose_name_plural = "Registros climáticos"

    def __str__(self):
        return f"Registro de clima desde {self.datetime} hasta {self.final_date}"

    def save(self, *args,**kwargs):
        if self.luminiscencia is None:
            # Cálculo de luminiscencia
            base_date= self.datetime.date()
            sunrise = datetime.combine(base_date, self.sunrise)
            sunset = datetime.combine(base_date, self.sunset)
            diference = sunset - sunrise
            luminiscencia_hours = round(diference.total_seconds() / 3600, 2)
            self.luminiscencia = luminiscencia_hours

        # Calcular la fecha final automáticamente (final_date)
        if self.final_date is None:
            self.final_date = self.datetime + timedelta(days=7)
        super().save(*args, **kwargs)


class ConsuptionPredictionLot(models.Model):
    ''' Modelo que almacena la predicción de consumo de un lote '''
    class PeriodTime(models.TextChoices):
        ONE = "1", ("1")
        THREE = "3", ("3")
        SIX = "6", ("6")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario solicitante", help_text="Usuario que solicita la predicción" )
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, verbose_name="Lote", help_text="Lote al que se le realiza la predicción")
    period_time = models.CharField(max_length=1, choices=PeriodTime, verbose_name="Periodo mensual de predicción", help_text="Periodo de tiempo (meses) a predecir")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación de la prediccion", help_text="Fecha de creacion de la predicción")
    date_prediction = models.DateField(null=True, verbose_name="Meses de predicción", help_text="Meses de predicción")
    consumption_prediction = models.FloatField(verbose_name="Consumo predecido", help_text="Consumo predecido")
    code_prediction = models.CharField(max_length=20, verbose_name="Código para las predicciones", help_text="Código de las predicciones")
    final_date = models.DateTimeField()

    class Meta:
        verbose_name = "Predicción de consumo de lote"
        verbose_name_plural = "Predicción de consumo de lotes"

    def __str__(self):
        return f"{self.code_prediction} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args,**kwargs):
        if self.final_date is None:
            now = timezone.now()
            self.final_date = now + timedelta(days=7)
        super().save(*args, **kwargs)