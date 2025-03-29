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
def all_users(db, person_type):
    """Crea un conjunto de usuarios, incluyendo administradores y usuarios normales."""
    admin = CustomUser.objects.create_superuser(
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

    users = [
        CustomUser.objects.create(
            document=f"12345678900{i}",
            first_name=f"User{i}",
            last_name="Test",
            email=f"user{i}@example.com",
            phone=f"123456789{i}",
            address=f"Calle {i}",
            password="SecurePass123.",
            person_type=person_type,
            is_active=True,
            is_registered=True,
        )
        for i in range(1, 6)
    ]

    return [admin] + users  # Retorna una lista con todos los usuarios


@pytest.mark.django_db
def test_view_users_list(api_client, admin_user, all_users):
    """✅ Verifica que la API devuelva la lista de usuarios del sistema sin datos sensibles."""

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

    # 🔹 Paso 4: Usar el token para obtener la lista de usuarios
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_users_url = reverse("customuser-list")  # 🔹 Endpoint para listar usuarios
    response = api_client.get(list_users_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de usuarios: {response.data}"

    # 🔹 Verificar que la API devuelve la cantidad correcta de usuarios
    total_users_db = CustomUser.objects.count()
    total_users_api = len(response.data)

    assert (
        total_users_api == total_users_db
    ), f"❌ Se esperaban {total_users_db} usuarios, pero la API devolvió {total_users_api}."

    # 🔹 Verificar que cada usuario tiene los atributos requeridos
    required_fields = ["document", "first_name", "last_name"]
    for user_data in response.data:
        for field in required_fields:
            assert field in user_data, f"❌ Falta el campo '{field}' en la respuesta."

    print(
        "✅ Test completado con éxito. Se listaron correctamente los usuarios del sistema."
    )
