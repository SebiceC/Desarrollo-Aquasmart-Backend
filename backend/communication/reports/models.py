from django.db import models
from communication.models import BaseRequestReport
from plots_lots.models import Plot
from communication.utils import generate_unique_id

class TypeReport(models.TextChoices):
    WATER_SUPPLY_FAILURE = 'Fallo en el Suministro del Agua', 'Fallo en el Suministro del Agua'
    APPLICATION_FAILURE = 'Fallo en el Aplicativo', 'Fallo en el Aplicativo'

class FailureReport(BaseRequestReport):
    """Modelo para almacenar reportes de fallos"""
    id = models.IntegerField(primary_key=True, verbose_name="ID", help_text="Identificador único del reporte de fallo")
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Predio", help_text="Predio al que se le realiza el reporte")
    failure_type = models.CharField(max_length=50, choices=TypeReport.choices, verbose_name="Tipo de reporte", help_text="Tipo de reporte (suministro de agua o aplicativo)")

    class Meta:
        verbose_name = "Reporte de Fallo"
        verbose_name_plural = "Reportes de Fallo"

    def __str__(self):
        return f"Reporte de {self.failure_type} hecha por {self.created_by.get_full_name()} dirigido al {self.plot} - {self.status}"

    def _validate_plot_is_activate(self):
        ''' Valida que el predio en cuya solicitud está presente, esté habilitado '''
        if self.plot and self.plot.is_activate != True:
            raise ValueError("No se puede realizar un reporte de un predio inhabilitado.")

    def _validate_pending_report_plot_lot(self):
        '''Valida que el predio y el lote no tengan reportes pendientes, excepto si el predio tiene pendiente pero el lote no'''
        plot_pending = FailureReport.objects.filter(plot=self.plot).exclude(status='Finalizado').exclude(pk=self.pk)
        lot_pending = FailureReport.objects.filter(lot=self.lot).exclude(status='Finalizado').exclude(pk=self.pk)

        if plot_pending.exists() and not lot_pending.exists():
            return

        if lot_pending.exists() or plot_pending.exists():
            raise ValueError("No se puede crear el reporte porque ya existe uno pendiente para el predio o el lote seleccionado.")

    def _validate_owner(self):
        """Valida que el usuario creador sea dueño del predio o del lote."""
        if self.failure_type == TypeReport.WATER_SUPPLY_FAILURE:
            if self.lot and self.created_by != self.lot.plot.owner:
                raise ValueError("Solo el dueño del predio puede crear un reporte para este lote.")
            if self.plot and self.created_by != self.plot.owner:
                raise ValueError("Solo el dueño del predio puede crear un reporte para este predio.")

    def _assign_plot_from_lot(self):
        ''' Asigna el predio automáticamente desde el lote '''
        if self.lot and hasattr(self.lot, 'plot'):
            self.plot = self.lot.plot

    def clean(self):
        super().clean()
        if self.failure_type == TypeReport.WATER_SUPPLY_FAILURE:
            self._validate_plot_is_activate()
            self._validate_pending_report_plot_lot()
            self._validate_owner()

    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_status = self.status if not is_new else None

        if not self.id:
            self.id = generate_unique_id(FailureReport, "20")

        self.type = 'Reporte'
        self._assign_plot_from_lot()

        super().save(*args, **kwargs)
        
        # Notificaciones
        if is_new:
            from communication.notifications import send_failure_report_created_notification
            send_failure_report_created_notification(self)
        elif old_status != self.status:
            from communication.notifications import send_failure_report_status_notification
            send_failure_report_status_notification(self)