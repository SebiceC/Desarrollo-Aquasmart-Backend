from django.db import models
from plots_lots.models import Plot,Lot
import random
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

class DeviceType(models.Model):
    device_id = models.CharField(max_length=2, primary_key=True, editable=False)
    name = models.CharField(max_length=50, blank=False, null=False)

    def save(self, *args, **kwargs):
        if not self.device_id:
            last_device = DeviceType.objects.order_by('-device_id').first()
            if last_device:
                new_id = int(last_device.device_id) + 1  # Incrementa el último ID
                self.device_id = f"{new_id:02d}"  # Formatea con dos dígitos
            else:
                self.device_id = "01"  # Primer ID

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.device_id})"
    
    class Meta:
        verbose_name = "Tipo de dispositivo IoT"
        verbose_name_plural = "Tipos de dispositivos IoT"

# Constantes para tipos de válvulas
VALVE_48_ID = '6' # ID para válvula de 48"
VALVE_4_ID = '7' # ID para válvula de 4"

class IoTDevice(models.Model):
    iot_id = models.CharField(max_length=7, primary_key=True, editable=False)  # Formato XX-YYYY
    id_plot = models.ForeignKey(
        Plot, 
        on_delete=models.SET_NULL,  # Si el plot se elimina, el campo queda en NULL
        null=True,                  # Permite valores NULL en la base de datos
        blank=True,                 # Permite que los formularios no requieran este campo
        related_name="iot_devices"
    )
    id_lot = models.ForeignKey(
        Lot, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="iot_devices"
    )
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=100, verbose_name="Nombre del Dispositivo")
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, verbose_name="Tipo de Dispositivo")
    is_active = models.BooleanField(default=True, help_text="Indica si el dispositivo está habilitado", db_index=True, verbose_name="Estado del Dispositivo")
    characteristics = models.CharField(max_length=300, blank=True, null=False, default="Sin características", verbose_name="Características del Dispositivo")
    actual_flow = models.FloatField(
        verbose_name="Caudal actual (L/s)",
        help_text="Caudal actual en litros por segundo (L/s)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(180)]
    )

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Si se asigna un lote pero no el predio
        if self.id_lot and not self.id_plot:
            raise ValidationError({
                "id_plot": "El lote fue asignado sin su predio correspondiente."
            })
        
        # Si `id_lot` está presente, validar que pertenece al `id_plot`
        if self.id_lot and self.id_plot and self.id_lot.plot != self.id_plot:
            raise ValidationError({
                "id_lot": "El lote no pertenece al predio especificado."
            })

        # Validar que el dispositivo sea una válvula
        if self.device_type_id in [VALVE_48_ID, VALVE_4_ID]:
            # Validaciones específicas para válvula de 48"
            if self.device_type_id == VALVE_48_ID:
                # Verificar que no exista otra válvula de 48"
                existing_valve_48 = IoTDevice.objects.filter(device_type_id=VALVE_48_ID).exclude(iot_id=self.iot_id).exists()
                if existing_valve_48:
                    raise ValidationError(
                    "Ya existe una válvula de 48\" en el distrito."
                )

                # La válvula de 48" no debe asignarse a ningún predio ni lote
                if self.id_plot or self.id_lot:
                    raise ValidationError(
                        "La válvula de 48\" no puede asignarse a predios ni lotes."
                    )

            # Validaciones específicas para válvula de 4"
            elif self.device_type_id == VALVE_4_ID:
                # Validar que se asigne a un predio o a un lote
                if not self.id_plot and not self.id_lot:
                    raise ValidationError(
                        "Una válvula de 4\" debe asignarse a un predio o a un lote."
                    )
                
                # Validar que no haya más de una válvula de 4" por predio
                if self.id_plot and not self.id_lot:
                    queryset = IoTDevice.objects.filter(
                    device_type_id=VALVE_4_ID,
                    id_plot=self.id_plot,
                    id_lot__isnull=True
                )
                    if self.iot_id:  # Si es una actualización, excluir el dispositivo actual
                        queryset = queryset.exclude(iot_id=self.iot_id)
                    if queryset.exists(): # Evaluar si ya existe una válvula de 4" asignada al predio
                            raise ValidationError(
                                "Ya existe una válvula asignada a este predio."
                            )
                
                # Validar que no haya más de una válvula de 4" por lote
                if self.id_lot:
                    queryset = IoTDevice.objects.filter(
                    device_type_id=VALVE_4_ID,
                    id_lot=self.id_lot
                )
                    if self.iot_id:  # Si es una actualización, excluir el dispositivo actual
                        queryset = queryset.exclude(iot_id=self.iot_id)
                    if queryset.exists(): # Evaluar si ya existe una válvula de 4" asignada al lote
                            raise ValidationError(
                                "Ya existe una válvula asignada a este lote."
                            )
        else:
            # Para dispositivos que no son válvulas, actual_flow debe ser None
            if self.actual_flow is not None:
                raise ValidationError({
                    "actual_flow": "El caudal actual solo aplica para válvulas."
                })

    class Meta:
        verbose_name = "Dispositivo IoT"
        verbose_name_plural = "Dispositivos IoT"

    def save(self, *args, **kwargs):
        if not self.iot_id:
            random_suffix = f"{random.randint(0, 9999):04d}"  # Números aleatorios de 4 dígitos
            self.iot_id = f"{self.device_type.device_id}-{random_suffix}"  # XX-YYYY
        
        if self.id_plot and self.id_plot.owner:
            self.owner_name = self.id_plot.owner.get_full_name()
        elif not self.owner_name:
            self.owner_name = "Sin dueño"  # ✅ Valor predeterminado si está vacío    
        
        self.full_clean()  # Ejecutar todas las validaciones
        super().save(*args, **kwargs)

    def __str__(self):
        base_str = f"{self.name} ({self.device_type.name})"
        if self.device_type_id in [VALVE_48_ID, VALVE_4_ID]:
            return f"{base_str} - {self.actual_flow} L/s"
        return base_str
