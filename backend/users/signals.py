from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    """
    Señal que registra el historial de inicio de sesión de los usuarios usando auditlog.

    Esta función se ejecuta automáticamente cada vez que un usuario inicia sesión
    en el sistema. Crea un registro en auditlog con la información del usuario autenticado.

    Parámetros:
    - sender: El modelo que envía la señal (normalmente `User`).
    - request: Objeto HTTPRequest de Django con la información de la petición.
    - user: Usuario que ha iniciado sesión.
    - kwargs: Argumentos adicionales de la señal.
    """
    LogEntry.objects.create(
        content_type=ContentType.objects.get_for_model(user),
        object_pk=str(user.pk),
        actor=user,
        action=0,  # 0 = CREATE - Creando un nuevo registro de inicio de sesión
        changes={
            "ip_address": request.META.get("REMOTE_ADDR", ""),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "timestamp": now().isoformat(),
            "event": "login",
        },
    )
    print(f"User {user.document} logged in successfully!")
