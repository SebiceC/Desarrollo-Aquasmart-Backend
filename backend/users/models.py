from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.timezone import now, timedelta
from datetime import datetime, date
import secrets
import string
from auditlog.registry import auditlog
from auditlog.models import LogEntry


class UserManager(BaseUserManager):
    """
    Administrador de usuarios personalizado para la gestión de usuarios y superusuarios.
    """

    def create_user(
        self,
        document,
        first_name,
        last_name,
        email,
        phone,
        password=None,
        **extra_fields,
    ):
        """
        Crea y guarda un usuario con el documento, nombre, apellido, correo y teléfono proporcionados.

        Args:
            document (str): Número de documento del usuario.
            first_name (str): Nombre del usuario.
            last_name (str): Apellido del usuario.
            email (str): Correo electrónico único del usuario.
            phone (str): Número de teléfono del usuario.
            password (str, optional): Contraseña del usuario. Si no se proporciona, el usuario no podrá iniciar sesión.
            **extra_fields: Campos adicionales opcionales.

        Returns:
            CustomUser: Usuario creado.
        """
        if not document:
            raise ValueError("El documento es obligatorio")
        if not email:
            raise ValueError("El correo electrónico es obligatorio")
        if not phone:
            raise ValueError("El número de teléfono es obligatorio")

        email = self.normalize_email(email)
        user = self.model(
            document=document,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        document,
        first_name,
        last_name,
        email,
        phone,
        password=None,
        **extra_fields,
    ):
        """
        Crea y guarda un superusuario con privilegios administrativos.

        Args:
            document (str): Documento del superusuario.
            first_name (str): Nombre del superusuario.
            last_name (str): Apellido del superusuario.
            email (str): Correo electrónico único del superusuario.
            phone (str): Número de teléfono del superusuario.
            password (str, optional): Contraseña del superusuario.
            **extra_fields: Campos adicionales.

        Returns:
            CustomUser: Superusuario creado.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_registered", True)

        return self.create_user(
            document, first_name, last_name, email, phone, password, **extra_fields
        )


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado con autenticación basada en el documento.
    """

    document = models.CharField(
        max_length=12, primary_key=True, db_index=True, verbose_name="Documento"
    )
    first_name = models.CharField(max_length=50, db_index=True, verbose_name="Nombre")
    last_name = models.CharField(max_length=50, db_index=True, verbose_name="Apellido")
    email = models.EmailField(
        unique=True, db_index=True, verbose_name="Correo Electrónico"
    )
    document_type = models.ForeignKey(
        "DocumentType",
        on_delete=models.CASCADE,
        related_name="users_with_document_type",
        null=True,
        db_index=True,
        verbose_name="Tipo de Documento",
    )
    person_type = models.ForeignKey(
        "PersonType",
        on_delete=models.CASCADE,
        related_name="users_with_person_type",
        null=True,
        db_index=True,
        verbose_name="Tipo de Persona",
    )
    phone = models.CharField(max_length=10, db_index=True, verbose_name="Teléfono")
    address = models.CharField(max_length=200, db_index=True, verbose_name="Dirección")
    is_registered = models.BooleanField(
        default=False,
        help_text="Indica si el usuario completó el pre-registro",
        db_index=True,
        verbose_name="Registrado",
    )
    drive_folder_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID Carpeta Google Drive"
    )

    username = None

    USERNAME_FIELD = "document"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone", "address", "email"]

    objects = UserManager()

    class Meta:
        permissions = [
            ("can_toggle_is_active", "Puede cambiar el estado de is_active"),
            ("can_toggle_is_registered", "Puede cambiar el estado de is_registered"),
            ("can_toggle_is_staff", "Puede cambiar el estado de is_staff"),
        ]

    def __str__(self):
        return f"{self.document} - {self.first_name} {self.last_name}"


class Otp(models.Model):
    """
    Modelo para gestionar códigos OTP para autenticación y recuperación de cuentas.
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        to_field="document",
        related_name="otp",
        verbose_name="Usuario",
    )
    otp = models.CharField(max_length=6, unique=True, verbose_name="Código OTP")
    creation_time = models.DateTimeField(default=now, verbose_name="Fecha de Creación")
    is_validated = models.BooleanField(default=False, verbose_name="Validado")
    is_login = models.BooleanField(default=False, verbose_name="Para Inicio de Sesión")

    def generate_otp(self):
        """
        Genera un código OTP de 6 dígitos y lo almacena en la base de datos.

        Returns:
            str: Código OTP generado.
        """
        caracteres = string.digits
        self.otp = "".join(secrets.choice(caracteres) for _ in range(6))
        self.creation_time = datetime.now()
        self.is_validated = False
        self.save()
        return self.otp

    def validate_life_otp(self):
        """
        Valida si el OTP sigue siendo válido dentro de los 15 minutos de creación.

        Returns:
            bool: True si el OTP es válido, False si ha expirado.
        """
        return (now() - self.creation_time) <= timedelta(minutes=5)

    def __str__(self):
        return f"OTP {self.otp} para {self.user.first_name}"

    class Meta:
        verbose_name = "Código OTP"
        verbose_name_plural = "Códigos OTP"


class DocumentType(models.Model):
    """
    Modelo para los tipos de documentos de identificación.
    """

    documentTypeId = models.AutoField(
        primary_key=True, verbose_name="ID de Tipo de Documento"
    )
    typeName = models.CharField(
        max_length=50, verbose_name="Nombre del Tipo de Documento"
    )

    def __str__(self):
        return f"{self.documentTypeId} - {self.typeName}"


class PersonType(models.Model):
    """
    Modelo para definir tipos de personas (ej. Natural, Jurídica).
    """

    personTypeId = models.AutoField(
        primary_key=True, verbose_name="ID de Tipo de Persona"
    )
    typeName = models.CharField(
        max_length=20, verbose_name="Nombre del Tipo de Persona"
    )

    def __str__(self):
        return f"{self.personTypeId} - {self.typeName}"


class LoginRestriction(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        to_field="document",
        related_name="login_restriction",
        verbose_name="user",
    )
    attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    last_attempt_time = models.DateTimeField(null=True, blank=True)

    def register_attempt(self):
        """Registra un intento fallido de inicio de sesión"""
        if self.is_blocked():
            return "El usuario está bloqueado hasta {}".format(self.blocked_until)

        self.attempts += 1
        self.last_attempt_time = now()

        if self.attempts == 4:
            message = "Último intento antes de ser bloqueado."
        elif self.attempts >= 5:
            self.block_user()
            message = "Usuario bloqueado por 30 minutos."
        else:
            message = "Credenciales inválidas."

        self.save()
        return message

    def block_user(self):
        """Bloquea al usuario por 30 minutos"""
        self.blocked_until = now() + timedelta(minutes=1)
        self.attempts = 0  # Reiniciar intentos
        self.save()

    def is_blocked(self):
        """Verifica si el usuario está bloqueado"""
        if self.blocked_until and now() < self.blocked_until:
            return True
        if self.blocked_until and now() >= self.blocked_until:
            self.blocked_until = None
            self.attempts = 0
            self.save()
        return False


class UserUpdateLog(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="update_log"
    )
    update_count = models.IntegerField(default=0)
    last_update_date = models.DateTimeField(auto_now=True)
    first_update_date = models.DateTimeField(
        null=True, blank=True
    )  # Nuevo campo para la primera actualización

    def can_update(self, updating_user):
        """
        Verifica si el usuario que está realizando la actualización tiene permisos.

        - Si el usuario que realiza la actualización es staff, no hay restricciones.
        - Si es un usuario normal, se aplican las reglas de límite semanal.
        """

        # Si el usuario que está actualizando (updating_user) es staff, permitir sin restricciones
        if updating_user.is_staff:
            return (
                True,
                "Datos actualizados con éxito. No tienes restricciones de actualización.",
            )

        today = now()

        # Si es la primera actualización, inicializa la fecha de la primera actualización
        if self.first_update_date is None:
            self.first_update_date = today
            self.save()

        # Calcula el final de la semana personalizada (7 días después de la primera actualización)
        # end_of_week = self.first_update_date + timedelta(days=6)
        end_of_week = self.first_update_date + timedelta(seconds=10)

        # Si la fecha actual está fuera de la semana personalizada, reinicia el contador
        if today > end_of_week:
            self.update_count = 0
            self.first_update_date = today  # Reinicia la semana personalizada
            self.save()

        # Verifica si el usuario ha excedido el límite de actualizaciones
        if self.update_count >= 3:
            return (
                False,
                "Has alcanzado el límite de 3 actualizaciones esta semana. Podrás actualizar nuevamente la próxima semana.",
            )
        elif self.update_count == 2:
            return (
                True,
                "Datos actualizados con éxito. Te queda 0 cambio más esta semana.",
            )
        elif self.update_count == 1:
            return (
                True,
                "Datos actualizados con éxito. Te queda 1 cambio más esta semana.",
            )
        else:
            return True, "Datos actualizados con éxito."

    def increment_update_count(self):
        """Incrementa el contador de actualizaciones y actualiza la fecha."""
        self.update_count += 1
        self.last_update_date = now()
        self.save()

    def __str__(self):
        return f"Update profil {self.user} - Updates: {self.update_count}"


# Registrar modelos para auditoría
auditlog.register(
    CustomUser
)  # El registro de campos excluidos se maneja de otra manera
auditlog.register(DocumentType)
auditlog.register(PersonType)
auditlog.register(LoginRestriction)
auditlog.register(UserUpdateLog)
