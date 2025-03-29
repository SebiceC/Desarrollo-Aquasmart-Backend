import pytest
from django.urls import reverse
from rest_framework import status
from iot.models import IoTDevice, DeviceType
from plots_lots.models import SoilType, Plot, Lot
from users.models import CustomUser, Otp, PersonType
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea un tipo de persona válido en la base de datos."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def soil_type(db):
    """Crea un tipo de suelo válido en la base de datos."""
    return SoilType.objects.create(name="Arcilloso")


@pytest.fixture
def admin_user(db, person_type):
    """Crea un usuario administrador válido."""
    user = CustomUser.objects.create_superuser(
        document="123456789012",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        password="AdminPass123@",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )
    user.set_password("AdminPass123@")
    user.save()
    return user


@pytest.fixture
def normal_user(db, person_type):
    """Crea un usuario normal."""
    user = CustomUser.objects.create(
        document="123456789013",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567891",
        password="SecurePass123@",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )
    user.set_password("SecurePass123@")
    user.save()
    return user


@pytest.fixture
def device_type(db):
    """Crea un tipo de dispositivo IoT."""
    return DeviceType.objects.create(name="Sensor de humedad")


@pytest.fixture
def admin_plots(db, admin_user):
    """Crea predios registrados para el administrador."""
    return [
        Plot.objects.create(
            plot_name="Predio Admin 1",
            owner=admin_user,
            is_activate=True,
            latitud=-74.00597,
            longitud=40.712776,
            plot_extension=2000.75,
        ),
        Plot.objects.create(
            plot_name="Predio Admin 2",
            owner=admin_user,
            is_activate=True,
            latitud=-74.00600,
            longitud=40.713000,
            plot_extension=1500.50,
        ),
    ]


@pytest.fixture
def user_plots(db, normal_user):
    """Crea predios registrados para un usuario normal."""
    return [
        Plot.objects.create(
            plot_name="Predio Usuario 1",
            owner=normal_user,
            is_activate=True,
            latitud=-74.01000,
            longitud=40.715000,
            plot_extension=2000.75,
        ),
        Plot.objects.create(
            plot_name="Predio Usuario 2",
            owner=normal_user,
            is_activate=True,
            latitud=-74.01200,
            longitud=40.716500,
            plot_extension=1500.50,
        ),
    ]


@pytest.fixture
def admin_devices(db, admin_plots, device_type):
    """Crea dispositivos IoT asignados al administrador (vinculados a sus predios)."""
    return [
        IoTDevice.objects.create(
            name="Sensor 1",
            device_type=device_type,
            id_plot=admin_plots[0],
            is_active=True,
            characteristics="Mide humedad cada 5 minutos",
        ),
        IoTDevice.objects.create(
            name="Sensor 2",
            device_type=device_type,
            id_plot=admin_plots[1],
            is_active=True,
            characteristics="Mide temperatura y humedad",
        ),
    ]


@pytest.fixture
def user_devices(db, user_plots, device_type):
    """Crea dispositivos IoT asignados al usuario normal (vinculados a sus predios)."""
    return [
        IoTDevice.objects.create(
            name="Sensor 3",
            device_type=device_type,
            id_plot=user_plots[0],
            is_active=True,
            characteristics="Mide humedad cada 5 minutos",
        ),
        IoTDevice.objects.create(
            name="Sensor 4",
            device_type=device_type,
            id_plot=user_plots[1],
            is_active=True,
            characteristics="Mide temperatura y humedad",
        ),
    ]


@pytest.mark.django_db
def test_admin_can_update_iot_device(api_client, admin_user, admin_devices):
    """✅ Verifica que un administrador pueda actualizar un dispositivo IoT."""

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

    # 🔹 Obtener el token
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    # 🔹 Intentar actualizar el dispositivo
    iot_device = admin_devices[0]
    update_url = reverse("update_iot_device", kwargs={"iot_id": iot_device.iot_id})

    update_data = {
        "name": "Sensor de Temperatura",
        "is_active": False,
        "characteristics": "Actualizado por el admin",
    }

    response = api_client.patch(update_url, update_data, format="json", **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al actualizar el dispositivo: {response.data}"

    # 🔹 Verificar actualización en la base de datos
    iot_device.refresh_from_db()
    assert iot_device.name == "Sensor de Temperatura"
    assert not iot_device.is_active
    assert iot_device.characteristics == "Actualizado por el admin"

    print("✅ Test completado: El administrador pudo actualizar un dispositivo IoT.")


@pytest.mark.django_db
def test_normal_user_cannot_update_other_users_iot_device(
    api_client, normal_user, admin_devices
):
    """🚫 Un usuario normal NO puede actualizar dispositivos de otros usuarios."""

    # 🔹 Paso 1: Iniciar sesión como usuario normal
    login_url = reverse("login")
    login_data = {"document": normal_user.document, "password": "SecurePass123@"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Validar OTP
    otp_instance = Otp.objects.filter(user=normal_user, is_login=True).first()
    assert otp_instance, "❌ No se generó OTP para el usuario."

    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": normal_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Obtener el token y definir headers
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    # 🔹 Paso 4: Intentar actualizar un dispositivo de otro usuario
    iot_device = admin_devices[0]
    update_url = reverse(
        "update_iot_device", kwargs={"iot_id": iot_device.iot_id}
    )  # 🔥 Verifica la URL correcta

    update_data = {"name": "Intento de cambio"}

    response = api_client.patch(update_url, update_data, format="json", **headers)

    print(f"🔹 Respuesta de la API: {response.data}")  # 🔥 Depuración

    assert (
        response.status_code == status.HTTP_403_FORBIDDEN
    ), f"❌ Un usuario normal pudo modificar un dispositivo de otro usuario. Respuesta: {response.data}"

    print(
        "✅ Test completado: Un usuario normal NO puede actualizar dispositivos ajenos."
    )
