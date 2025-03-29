import pytest
from django.urls import reverse
from rest_framework import status
from iot.models import IoTDevice, DeviceType
from users.models import CustomUser, Otp
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Crea un usuario administrador válido."""
    user = CustomUser.objects.create_superuser(
        document="123456789012",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        password="AdminPass123@",
        is_active=True,
        is_registered=True,
    )
    user.set_password("AdminPass123@")
    user.save()
    return user


@pytest.fixture
def device_type(db):
    """Crea un tipo de dispositivo válido en la base de datos."""
    return DeviceType.objects.create(name="Sensor de temperatura")


@pytest.mark.django_db
def test_admin_can_register_iot_device(api_client, admin_user, device_type):
    """✅ Verifica que un administrador pueda registrar un dispositivo IoT exitosamente."""

    # 🔹 Iniciar sesión como administrador
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123@"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Validar OTP
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Registrar el dispositivo IoT
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    register_iot_url = reverse("registrar-dispositivo-iot")

    iot_data = {
        "name": "Sensor Exterior",
        "device_type": device_type.device_id,  # 🔹 ID del tipo de dispositivo
        "is_active": True,
    }

    response = api_client.post(register_iot_url, iot_data, format="json", **headers)

    # 🔹 Verificar la respuesta de la API
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Error en el registro del dispositivo IoT: {response.data}"
    assert (
        "iot_id" in response.data
    ), "❌ No se recibió el identificador del dispositivo IoT."

    # 🔹 Confirmar que el dispositivo fue guardado en la base de datos
    iot_id = response.data["iot_id"]
    assert IoTDevice.objects.filter(
        iot_id=iot_id
    ).exists(), "❌ El dispositivo IoT no fue guardado en la base de datos."

    print(f"✅ Test completado con éxito. Dispositivo IoT registrado con ID: {iot_id}")
