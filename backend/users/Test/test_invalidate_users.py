import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, Otp, PersonType


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea y guarda un tipo de persona válido en la base de datos."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def admin_user(db, person_type):
    """Crea un usuario administrador de prueba."""
    return CustomUser.objects.create_superuser(
        document="admin",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        password="AdminPass123",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def normal_user(db, person_type):
    """Crea un usuario normal en el sistema."""
    return CustomUser.objects.create(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567890",
        password="SecurePass123",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )


@pytest.mark.django_db
def test_disable_user(api_client, admin_user, normal_user):
    """✅ Verifica que un administrador pueda inhabilitar un usuario del sistema."""

    # 🔹 Paso 1: Iniciar sesión (recibe OTP pero no token aún)
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"
    assert (
        "message" in login_response.data
    ), "❌ No se recibió un mensaje de confirmación de envío de OTP."

    # 🔹 Paso 2: Verificar que el OTP ha sido generado en la base de datos
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    assert otp_instance, "❌ No se generó un OTP en la base de datos."

    # 🔹 Paso 3: Validar OTP para obtener el token
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 4: Usar el token para deshabilitar un usuario
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    disable_user_url = reverse(
        "Inative-user", kwargs={"document": normal_user.document}
    )  # 🔹 Endpoint para inhabilitar usuario
    response = api_client.patch(disable_user_url, {}, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al inhabilitar usuario: {response.data}"

    # 🔹 Paso 5: Verificar que el usuario ha sido inhabilitado en la base de datos
    normal_user.refresh_from_db()
    assert (
        normal_user.is_active is False
    ), "❌ El usuario sigue activo después de la inhabilitación."

    print(
        "✅ Test completado con éxito. El administrador pudo inhabilitar un usuario correctamente."
    )
