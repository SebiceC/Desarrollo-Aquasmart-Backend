import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, LoginRestriction, Otp, PersonType
from django.utils import timezone
from datetime import timedelta


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea un tipo de persona para usar en los tests."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def admin_user(db, person_type):
    """Crea un usuario administrador para realizar acciones de habilitación/deshabilitación."""
    return CustomUser.objects.create_superuser(
        document="admin123456",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        password="AdminPass123@",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def registered_user(db, person_type):
    """Crea un usuario registrado para pruebas de inhabilitación."""
    return CustomUser.objects.create_user(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="9876543210",
        password="UserPass123@",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def unregistered_user(db, person_type):
    """Crea un usuario no registrado para pruebas de validación."""
    return CustomUser.objects.create_user(
        document="987654321098",
        first_name="Jane",
        last_name="Smith",
        email="janesmith@example.com",
        phone="5555555555",
        password="UnregisteredPass123@",
        person_type=person_type,
        is_active=False,
        is_registered=False,
    )


class TestUserValidationAndStatusManagement:
    """
    Pruebas integrales para validación y gestión de estado de usuarios.
    Cubre los aspectos del Requerimiento 18.
    """

    @pytest.mark.django_db
    def test_disable_active_user(self, api_client, admin_user, registered_user):
        """
        Prueba la inhabilitación de un usuario activo por un administrador.

        Pasos:
        1. Iniciar sesión como administrador
        2. Validar OTP
        3. Intentar deshabilitar un usuario activo
        4. Verificar que el usuario queda inhabilitado
        """
        # 1. Login del administrador
        login_url = reverse("login")
        login_data = {"document": admin_user.document, "password": "AdminPass123@"}
        login_response = api_client.post(login_url, login_data)
        assert (
            login_response.status_code == status.HTTP_200_OK
        ), "Fallo en el inicio de sesión del administrador"

        # Obtener y validar OTP
        otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
        otp_validation_url = reverse("validate-otp")
        otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
        otp_response = api_client.post(otp_validation_url, otp_data)
        assert (
            otp_response.status_code == status.HTTP_200_OK
        ), "Fallo en la validación del OTP"

        # Deshabilitar usuario
        disable_user_url = reverse(
            "Inative-user", kwargs={"document": registered_user.document}
        )
        response = api_client.patch(
            disable_user_url, HTTP_AUTHORIZATION=f"Token {otp_response.data['token']}"
        )

        # Verificaciones
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Error al deshabilitar usuario: {response.data}"
        registered_user.refresh_from_db()
        assert (
            registered_user.is_active is False
        ), "El usuario no fue deshabilitado correctamente"
        assert (
            "desactivado correctamente" in response.data["status"]
        ), "Mensaje de desactivación incorrecto"

    @pytest.mark.django_db
    def test_activate_inactive_user(self, api_client, admin_user, registered_user):
        """
        Prueba la activación de un usuario inactivo por un administrador.

        Pasos:
        1. Deshabilitar usuario
        2. Iniciar sesión como administrador
        3. Validar OTP
        4. Intentar habilitar el usuario
        5. Verificar que el usuario queda habilitado
        """
        # Deshabilitar usuario primero
        registered_user.is_active = False
        registered_user.save()

        # 1. Login del administrador
        login_url = reverse("login")
        login_data = {"document": admin_user.document, "password": "AdminPass123@"}
        login_response = api_client.post(login_url, login_data)
        assert (
            login_response.status_code == status.HTTP_200_OK
        ), "Fallo en el inicio de sesión del administrador"

        # Obtener y validar OTP
        otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
        otp_validation_url = reverse("validate-otp")
        otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
        otp_response = api_client.post(otp_validation_url, otp_data)
        assert (
            otp_response.status_code == status.HTTP_200_OK
        ), "Fallo en la validación del OTP"

        # Habilitar usuario
        activate_user_url = reverse(
            "Activate-user", kwargs={"document": registered_user.document}
        )
        response = api_client.patch(
            activate_user_url, HTTP_AUTHORIZATION=f"Token {otp_response.data['token']}"
        )

        # Verificaciones
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Error al activar usuario: {response.data}"
        registered_user.refresh_from_db()
        assert (
            registered_user.is_active is True
        ), "El usuario no fue activado correctamente"
        assert (
            "a sido activado con exito" in response.data["status"]
        ), "Mensaje de activación incorrecto"

    @pytest.mark.django_db
    def test_login_attempt_with_disabled_user(self, api_client, registered_user):
        """
        Prueba que un usuario inhabilitado no pueda iniciar sesión.

        Pasos:
        1. Deshabilitar usuario
        2. Intentar iniciar sesión
        3. Verificar que el inicio de sesión es rechazado
        """
        # Deshabilitar usuario
        registered_user.is_active = False
        registered_user.save()

        # Intentar login
        login_url = reverse("login")
        login_data = {"document": registered_user.document, "password": "UserPass123@"}
        response = api_client.post(login_url, login_data)

        # Verificaciones
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "No se rechazó el inicio de sesión para usuario inhabilitado"
        assert (
            "inactiva" in response.data["error"]["detail"]
        ), "Mensaje de error incorrecto para usuario inhabilitado"

    @pytest.mark.django_db
    def test_login_attempt_with_unregistered_user(self, api_client, unregistered_user):
        """
        Prueba que un usuario no registrado no pueda iniciar sesión.

        Pasos:
        1. Intentar iniciar sesión con usuario no registrado
        2. Verificar que el inicio de sesión es rechazado
        """
        login_url = reverse("login")
        login_data = {
            "document": unregistered_user.document,
            "password": "UnregisteredPass123@",
        }
        response = api_client.post(login_url, login_data)

        # Verificaciones
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), "No se rechazó el inicio de sesión para usuario no registrado"
        assert "Usuario en espera de validar su pre-registro" in str(
            response.data["error"]["detail"]
        ), "Mensaje de error incorrecto para usuario no registrado"

    @pytest.mark.django_db
    def test_multiple_failed_login_attempts(self, api_client, registered_user):
        """
        Prueba el bloqueo de usuario después de múltiples intentos fallidos.

        Pasos:
        1. Realizar múltiples intentos de login con contraseña incorrecta
        2. Verificar que el usuario es bloqueado
        3. Verificar que no puede iniciar sesión
        """
        login_url = reverse("login")

        # Intentos fallidos
        for _ in range(5):
            response = api_client.post(
                login_url,
                {"document": registered_user.document, "password": "WrongPassword123"},
            )

        # Verificar bloqueo
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), "No se bloqueó al usuario después de intentos fallidos"
        assert "Usuario bloqueado por 30 minutos" in str(
            response.data["error"]["detail"][0]
        ), "Mensaje de bloqueo incorrecto"

    @pytest.mark.django_db
    def test_unauthorized_user_cannot_change_user_status(
        self, api_client, registered_user
    ):
        """
        Prueba que un usuario sin permisos no pueda cambiar el estado de otro usuario.

        Pasos:
        1. Crear un usuario sin permisos de administración
        2. Iniciar sesión del usuario sin permisos
        3. Intentar deshabilitar/habilitar otro usuario
        4. Verificar que la acción es rechazada
        """
        # Crear usuario con un documento de máximo 12 caracteres
        unauthorized_user = CustomUser.objects.create_user(
            document="unauthorized",
            first_name="Unauthorized",
            last_name="User",
            email="unauthorized@example.com",
            phone="1111111111",
            password="UnauthorizedPass123@",
            is_active=True,
            is_registered=True,
            person_type=registered_user.person_type,  # Agregar tipo de persona
        )

        # Login del usuario sin permisos
        login_url = reverse("login")
        login_data = {
            "document": unauthorized_user.document,
            "password": "UnauthorizedPass123@",
        }
        login_response = api_client.post(login_url, login_data)

        # Imprimir detalles de la respuesta si el login falla
        if login_response.status_code != status.HTTP_200_OK:
            print("Login Response Data:", login_response.data)
            print("Login Response Status:", login_response.status_code)

        # Verificar que el login fue exitoso
        assert (
            login_response.status_code == status.HTTP_200_OK
        ), "Fallo en el inicio de sesión del usuario sin permisos"

        # Obtener y validar OTP
        otp_instance = Otp.objects.filter(user=unauthorized_user, is_login=True).first()
        assert otp_instance is not None, "No se generó OTP para el usuario"

        otp_validation_url = reverse("validate-otp")
        otp_data = {"document": unauthorized_user.document, "otp": otp_instance.otp}
        otp_response = api_client.post(otp_validation_url, otp_data)

        # Imprimir detalles si la validación de OTP falla
        if otp_response.status_code != status.HTTP_200_OK:
            print("OTP Validation Response Data:", otp_response.data)
            print("OTP Validation Response Status:", otp_response.status_code)

        assert (
            otp_response.status_code == status.HTTP_200_OK
        ), "Fallo en la validación del OTP"

        # Intentar deshabilitar usuario
        disable_user_url = reverse(
            "Inative-user", kwargs={"document": registered_user.document}
        )
        response = api_client.patch(
            disable_user_url, HTTP_AUTHORIZATION=f"Token {otp_response.data['token']}"
        )

        # Verificaciones
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Se permitió cambiar el estado de usuario sin permisos"
