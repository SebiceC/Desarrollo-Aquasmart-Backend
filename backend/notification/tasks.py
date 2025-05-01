from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import EmailNotification, Notification
import logging

logger = logging.getLogger(__name__)

# Configuración segura con valores por defecto
email_timeout = settings.NOTIFICATION_CONFIG.get('DELIVERY_TIMEOUTS', {}).get('EMAIL', 30)

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    soft_time_limit=email_timeout,
    time_limit=email_timeout + 5
)
def send_email_notification_task(self, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        template_config = settings.NOTIFICATION_CONFIG['TEMPLATES']['EMAIL'].get(
            notification.notification_type,
            {}
        )
        
        email_notification, _ = EmailNotification.objects.get_or_create(
            notification=notification,
            defaults={
                'subject': template_config.get(
                    'subject',
                    f"[AquaSmart] {notification.get_notification_type_display()}"
                ).format(
                    report_id=notification.metadata.get('report_id', '')
                ),
            }
        )
        
        html_message = render_to_string(
            template_config.get('path', 'emails/default.html'),
            {
                'notification': notification,
                'object': notification.content_object,
                'metadata': notification.metadata,
                'settings': settings.NOTIFICATION_CONFIG
            }
        )
        
        send_mail(
            subject=email_notification.subject,
            message=notification.metadata.get('message', ''),
            html_message=html_message,
            from_email=settings.NOTIFICATION_CONFIG['RECIPIENTS']['DEFAULT_FROM'],
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        
        email_notification.status = EmailNotification.Status.SENT
        email_notification.sent_at = timezone.now()
        email_notification.save()
        
    except Exception as e:
        logger.error(f"Error enviando notificación {notification_id}: {str(e)}")
        if 'email_notification' not in locals():
            email_notification = EmailNotification.objects.get(notification_id=notification_id)
        email_notification.status = EmailNotification.Status.FAILED
        email_notification.metadata['error'] = str(e)
        email_notification.save()
        raise self.retry(exc=e)