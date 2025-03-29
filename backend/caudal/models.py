from django.db import models
from iot.models import IoTDevice
from plots_lots.models import Plot, Lot
from django.core.exceptions import ValidationError
from django.db.models import Sum
from auditlog.registry import auditlog
from django.utils import timezone
from datetime import timedelta


class FlowMeasurement(models.Model):
    device = models.ForeignKey(
        IoTDevice, on_delete=models.CASCADE, related_name="flow_measurements"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    flow_rate = models.FloatField(
        help_text="Caudal medido en metros cúbicos por segundo (m³/s)"
    )

    class Meta:
        verbose_name = "Medición de Caudal"
        verbose_name_plural = "Mediciones de Caudal"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.device.name} - {self.flow_rate} m³/s - {self.timestamp}"


class FlowMeasurementPredio(models.Model):
    plot = models.ForeignKey(
        Plot,
        on_delete=models.CASCADE,
        related_name="flow_measurements_predio",
        verbose_name="Predio",
    )
    device = models.ForeignKey(
        IoTDevice,
        on_delete=models.SET_NULL,
        related_name="flow_measurements_predio",
        verbose_name="Dispositivo IoT",
        null=True,
        blank=True,
    )
    flow_rate = models.FloatField(verbose_name="Caudal (m³/s)")
    timestamp = models.DateTimeField(verbose_name="Fecha y Hora")

    class Meta:
        verbose_name = "Medición de Caudal de Predio"
        verbose_name_plural = "Mediciones de Caudal de Predios"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Caudal Predio {self.plot.plot_name}: {self.flow_rate} m³/s ({self.timestamp})"

    def save(self, *args, **kwargs):
        """Validación antes de guardar"""
        if (
            self.device
            and not IoTDevice.objects.filter(iot_id=self.device.iot_id).exists()
        ):
            raise ValidationError(
                f"El dispositivo {self.device.iot_id} no existe en la base de datos."
            )

        super().save(*args, **kwargs)


class FlowMeasurementLote(models.Model):
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        related_name="flow_measurements_lote",
        verbose_name="Lote",
    )
    device = models.ForeignKey(
        IoTDevice,
        on_delete=models.SET_NULL,
        related_name="flow_measurements_lote",
        verbose_name="Dispositivo IoT",
        null=True,
        blank=True,
    )
    flow_rate = models.FloatField(verbose_name="Caudal (m³/s)")
    timestamp = models.DateTimeField(verbose_name="Fecha y Hora")

    class Meta:
        verbose_name = "Medición de Caudal de Lote"
        verbose_name_plural = "Mediciones de Caudal de Lotes"
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"Caudal Lote {self.lot.id_lot}: {self.flow_rate} m³/s ({self.timestamp})"
        )

    def verificar_inconsistencia(self):
        """Valida y guarda inconsistencias si hay diferencias significativas, sin validar tiempo."""
        predio = self.lot.plot
        ultima_medicion_predio = (
            FlowMeasurementPredio.objects.filter(plot=predio)
            .order_by("-timestamp")
            .first()
        )

        # 🆕 Si no hay medición previa del predio, crear una nueva
        if not ultima_medicion_predio:
            print(
                f"📌 Creando primera medición de predio para {predio.plot_name} con {self.flow_rate} m³/s"
            )
            ultima_medicion_predio = FlowMeasurementPredio.objects.create(
                plot=predio,
                flow_rate=self.flow_rate,  # Se toma el caudal del lote como base
                timestamp=timezone.now(),
                device=self.device,  # Asignamos el mismo dispositivo que midió el lote
            )
            return  # No validamos inconsistencia porque es la referencia inicial

        # 🔍 Calcular el flujo total de los lotes
        total_flow_lotes = (
            FlowMeasurementLote.objects.filter(
                lot__plot=predio, timestamp__gte=ultima_medicion_predio.timestamp
            ).aggregate(Sum("flow_rate"))["flow_rate__sum"]
            or 0
        )

        max_allowed_flow = ultima_medicion_predio.flow_rate * 1.05  # 5% de margen
        diferencia = total_flow_lotes - ultima_medicion_predio.flow_rate

        if total_flow_lotes > max_allowed_flow:
            # 📌 Guardar inconsistencia sin validar tiempo
            print(
                f"✅ Guardando inconsistencia: Predio {predio.plot_name}, Diferencia: {diferencia}"
            )
            FlowInconsistency.objects.create(
                plot=predio,
                recorded_flow=ultima_medicion_predio.flow_rate,
                total_lots_flow=total_flow_lotes,
                difference=diferencia,
            )

    def save(self, *args, **kwargs):
        """Guarda la medición del lote y verifica inconsistencias después de guardar."""
        if (
            self.device
            and not IoTDevice.objects.filter(iot_id=self.device.iot_id).exists()
        ):
            raise ValidationError(
                f"El dispositivo {self.device.iot_id} no existe en la base de datos."
            )

        super().save(*args, **kwargs)  # Guarda el objeto en la base de datos

        # Verifica inconsistencias después del guardado
        self.verificar_inconsistencia()


class FlowInconsistency(models.Model):
    plot = models.ForeignKey(
        Plot,
        on_delete=models.CASCADE,
        related_name="flow_inconsistencies",
        verbose_name="Predio",
    )
    recorded_flow = models.FloatField(
        verbose_name="Caudal registrado en el predio (m³/s)"
    )
    total_lots_flow = models.FloatField(
        verbose_name="Suma de caudales de los lotes (m³/s)"
    )
    difference = models.FloatField(verbose_name="Diferencia de caudales (m³/s)")
    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de detección"
    )

    class Meta:
        verbose_name = "Inconsistencia de caudal"
        verbose_name_plural = "Inconsistencias de caudal"
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inconsistencia en {self.plot.plot_name}: Diferencia de {self.difference:.3f} m³/s"


auditlog.register(FlowInconsistency)
auditlog.register(FlowMeasurementLote)
auditlog.register(FlowMeasurementPredio)
auditlog.register(FlowMeasurement)
