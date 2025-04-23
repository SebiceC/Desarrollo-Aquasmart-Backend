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
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': now().isoformat(),
            'event': 'login'
        }
    )
    print(f"User {user.document} logged in successfully!")
    
def create_default_person_types(sender, **kwargs):
    from .models import PersonType
    from django.db import transaction

    try:
        default_types = {
            1: "Natural",
            2: "Jurídica",           
        }

        with transaction.atomic():
            for person_id, name in default_types.items():
                PersonType.objects.update_or_create(
                    personTypeId=person_id,
                    defaults={"typeName": name}
                )

    except Exception as e:
        print(f"Error creando tipos de documento: {e}")
        
def create_default_document_types(sender, **kwargs):
    from .models import DocumentType
    from django.db import transaction

    try:
        default_types = {
            1: "Cédula de Ciudadanía (CC)",
            2: "Número de Identificación Tributaria (NIT)",
            3: "Cédula de Extranjería (CE)",
            4: "Permiso Especial de Permanencia (PEP)",
            5: "Documento de Identificación Extranjero (DIE)"        
        }

        with transaction.atomic():
            for doc_id, name in default_types.items():
                DocumentType.objects.update_or_create(
                    documentTypeId=doc_id,
                    defaults={"typeName": name}
                )

    except Exception as e:
        print(f"Error creando tipos de documento: {e}")        