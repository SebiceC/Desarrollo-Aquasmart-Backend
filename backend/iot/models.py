from django.db import models
from plots_lots.models import Plot,Lot
import random
from django.core.exceptions import ValidationError

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

# Constantes para tipos de válvulas
VALVE_48_ID = '3' # ID para válvula de 48"
VALVE_4_ID = '14' # ID para válvula de 4"

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
        blank=True
    )


    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validaciones para válvulas
        if self.device_type_id in [VALVE_48_ID, VALVE_4_ID]:
            # Validar que actual_flow esté presente para válvulas
            if self.actual_flow is None:
                raise ValidationError({
                    "actual_flow": "El caudal actual es requerido para válvulas."
                })

            if self.device_type_id == VALVE_48_ID:
                # La válvula de 48" no debe asignarse a ningún predio ni lote
                if self.id_plot or self.id_lot:
                    raise ValidationError(
                        "La válvula de 48\" no puede asignarse a predios ni lotes."
                    )

            elif self.device_type_id == VALVE_4_ID:
                # Validar que se asigne a un predio O a un lote, pero no a ambos
                if self.id_plot and self.id_lot:
                    raise ValidationError(
                        "Una válvula de 4\" debe asignarse a un predio o a un lote, no a ambos."
                    )
                if not self.id_plot and not self.id_lot:
                    raise ValidationError(
                        "Una válvula de 4\" debe asignarse a un predio o a un lote."
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
        constraints = [
            models.UniqueConstraint(
                fields=['device_type'],
                condition=models.Q(device_type_id=VALVE_48_ID),
                name='unique_valve_48'
            ),
            # Solo una válvula de 4" por predio (cuando no tiene lote)
            models.UniqueConstraint(
                fields=['device_type', 'id_plot'],
                condition=models.Q(
                    device_type_id=VALVE_4_ID,
                    id_lot__isnull=True
                ),
                name='unique_valve_4_plot'
            ),
            # Solo una válvula de 4" por lote
            models.UniqueConstraint(
                fields=['device_type', 'id_lot'],
                condition=models.Q(
                    device_type_id=VALVE_4_ID,
                    id_plot__isnull=True
                ),
                name='unique_valve_4_lot'
            )
        ]

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
        
# # Modelo para los tipos de válvulas
# class ValveType(models.Model):
#     BOCATOMA = 'BT'
#     PREDIO = 'PR'
#     LOTE = 'LT'
#     VALVE_TYPES = [
#         (BOCATOMA, 'Bocatoma'),
#         (PREDIO, 'Predio'),
#         (LOTE, 'Lote'),
#     ]
#     type_code = models.CharField(max_length=2, choices=VALVE_TYPES, primary_key=True, verbose_name="Tipo de Válvula")
#     diameter = models.IntegerField(verbose_name="Diámetro")  # en pulgadas
#     description = models.CharField(max_length=100, verbose_name="Descripción")

#     def clean(self):
#         # Llamar a la validación del padre
#         super().clean()
        
#         if self.type_code == self.BOCATOMA:
#             if self.diameter != 48:
#                 raise ValidationError({
#                     'diameter': 'Los tipos de válvula Bocatoma deben tener un diámetro de 48 pulgadas.'
#                 })
#         elif self.type_code in [self.PREDIO, self.LOTE]:
#             if self.diameter != 4:
#                 raise ValidationError({
#                     'diameter': 'Los tipos de válvula Predio y Lote deben tener un diámetro de 4 pulgadas.'
#                 })

#     class Meta:
#         verbose_name = "Tipo de válvula"
#         verbose_name_plural = "Tipos de válvulas"
#         ordering = ['type_code']

# # Modelo para válvulas
# class Valve(models.Model):
#     id_valve = models.CharField(max_length=10, primary_key=True, editable=False, verbose_name="ID de válvula")
#     valve_type = models.ForeignKey(
#         ValveType,
#         on_delete=models.PROTECT,  # Protegemos contra eliminación accidental
#         related_name="valves",
#         verbose_name="Tipo de válvula"
#     )
#     actual_flow = models.FloatField(
#         verbose_name="Caudal actual (L/s)",
#         help_text="Caudal actual en litros por segundo (L/s)"
#     )
#     is_active = models.BooleanField(default=True, verbose_name="¿Está activa?")
#     plot = models.ForeignKey(
#         Plot,
#         null=True,
#         blank=True,
#         on_delete=models.CASCADE,
#         related_name="valves",
#         verbose_name="Predio"
#     )
#     lot = models.ForeignKey(
#         Lot,
#         null=True,
#         blank=True,
#         on_delete=models.CASCADE,
#         related_name="valves",
#         verbose_name="Lote"
#     )
    
#     class Meta:
#         constraints = [
#             # Solo puede haber una válvula de bocatoma
#             models.UniqueConstraint(
#                 fields=['valve_type'],
#                 condition=models.Q(valve_type='BT'),
#                 name='unique_bocatoma_valve'
#             ),
#             # Solo una válvula por predio
#             models.UniqueConstraint(
#                 fields=['plot', 'valve_type'],
#                 condition=models.Q(valve_type='PR'),
#                 name='unique_plot_valve'
#             )
#         ]
#         verbose_name = "Válvula"
#         verbose_name_plural = "Válvulas"
#         ordering = ['id_valve']

#     def save(self, *args, **kwargs):
#         # Generar ID automático si es nuevo
#         if not self.id_valve:
#             last_valve = Valve.objects.order_by('-id_valve').first()
#             if last_valve:
#                 last_number = int(last_valve.id_valve[2:])  # Extrae el número después de 'VL'
#                 new_number = last_number + 1
#                 self.id_valve = f"VL{new_number:04d}"  # Formato: VL0001, VL0002, etc.
#             else:
#                 self.id_valve = "VL0001"  # Primera válvula
        
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"Válvula {self.id_valve} - {self.actual_flow} L/s"