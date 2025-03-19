import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, Otp, PersonType


@pytest.fixture
def api_client():
    """Cliente API para realizar las solicitudes de prueba."""
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
def registered_users(db, person_type):
    """Crea varios usuarios registrados en la base de datos."""
    return [
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



@pytest.mark.django_db
def test_list_registered_users(api_client, admin_user, registered_users):
    """✅ Verifica que la API liste correctamente los usuarios registrados con autenticación real."""

    # 🔹 Paso 1: Intentar iniciar sesión (genera OTP aunque falle el envío de correo)
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    # 🔹 Si la API falla por el envío de correo, verificamos si el OTP fue creado
    if login_response.status_code == 400 and "send_email" in str(login_response.data):
        otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
        assert otp_instance, "❌ No se generó un OTP en la base de datos a pesar del error en envío de correo."

    # 🔹 Validar OTP para obtener token
    otp_validation_url = reverse("validate-otp")
    otp_response = api_client.post(otp_validation_url, {"document": admin_user.document, "otp": otp_instance.otp})

    assert otp_response.status_code == status.HTTP_200_OK, f"Error en validación de OTP: {otp_response.data}"
    token = otp_response.data.get("token")
    assert token, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Solicitar lista de usuarios con el token de autenticación
    list_users_url = reverse("customuser-list")
    response = api_client.get(list_users_url, HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == status.HTTP_200_OK, f"Error en la lista de usuarios: {response.data}"
    assert len(response.data) == len(registered_users), "❌ No se retornaron todos los usuarios registrados."





@pytest.mark.django_db
def test_admin_login(api_client, admin_user):
    """✅ Verifica que el login de administrador devuelve un token."""

    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    
    login_response = api_client.post(login_url, login_data)

    print("🔹 LOGIN RESPONSE:", login_response.data)  # Depuración

    assert login_response.status_code == status.HTTP_200_OK, f"Error en login: {login_response.data}"
    assert "token" in login_response.data, "❌ No se recibió un token tras iniciar sesión."


