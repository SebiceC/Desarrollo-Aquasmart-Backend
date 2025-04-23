from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.utils import timezone
from .bill.models import Bill

@receiver([post_save, post_init], sender=Bill)
def set_bill_expired(sender, instance, **kwargs):
    # Solo si la factura no está pagada ni vencida y ya pasó la fecha de vencimiento
    if (
        instance.status not in ['pagada', 'vencida']
        and instance.due_payment_date
        and timezone.now().date() > instance.due_payment_date
        and not instance.payment_date
    ):
        instance.status = 'vencida'
        # Solo guardar si es post_save (para evitar guardar al cargar desde BD)
        if kwargs.get('signal') == post_save:
            instance.save(update_fields=['status'])