from django.db import models
from communication.models import BaseFlowRequest

class WaterSupplyFailureReport(BaseFlowRequest):
    """Modelo para almacenar reportes de fallos en el suministro de agua."""
    observations = models.CharField(
        max_length=200,
        verbose_name="Observaciones",
        help_text="Detalle del fallo reportado (hasta 200 caracteres)"
    )

    class Meta(BaseFlowRequest.Meta):
        verbose_name = "Reporte de fallo de suministro de agua"
        verbose_name_plural = "Reportes de fallos de suministro de agua"

    def __str__(self):
        return f"Reporte de {self.user.get_full_name()} - {self.lot} ({self.status})"
