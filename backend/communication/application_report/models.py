from django.db import models
from users.models import CustomUser

class ApplicationFailureReport(models.Model):
    """Modelo para almacenar reportes de fallos en el aplicativo."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Solicitante")
    observations = models.CharField(max_length=200, verbose_name="Observaciones", help_text="Detalle del fallo reportado (hasta 200 caracteres)")
    status = models.CharField(max_length=10, choices=[('pendiente', 'Pendiente'), ('resuelto', 'Resuelto')], default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha solicitud")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha revisión")

    class Meta:
        verbose_name = "Reporte de fallo en el aplicativo"
        verbose_name_plural = "Reportes de fallos en el aplicativo"

    def __str__(self):
        return f"Reporte de {self.user.get_full_name()} - {self.status}"  