import pytest
from django.urls import reverse
from rest_framework import status
from plots_lots.models import Plot
from iot.models import IoTDevice, DeviceType
from users.models import CustomUser, Otp, PersonType
from rest_framework.test import APIClient

# 🔹 FIXTURES


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea un tipo de persona válido en la base de datos."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def admin_user(db, person_type):
    """Crea un usuario administrador."""
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
def device_type(db):
    """Crea un tipo de dispositivo IoT."""
    return DeviceType.objects.create(name="Sensor de humedad")


@pytest.fixture
def admin_devices(db, admin_plots, device_type):
    """Crea dispositivos IoT asignados al administrador."""
    return [
        IoTDevice.objects.create(
            name="Sensor 1",
            device_type=device_type,
            id_plot=admin_plots[0],  # ✅ CORRECCIÓN: Ahora usamos una lista de predios
            is_active=True,
            characteristics="Mide humedad cada 5 minutos",
        ),
        IoTDevice.objects.create(
            name="Sensor 2",
            device_type=device_type,
            id_plot=admin_plots[1],  # ✅ CORRECCIÓN: Asignar a otro predio
            is_active=True,
            characteristics="Mide temperatura y humedad",
        ),
    ]


@pytest.fixture
def user_devices(db, user_plots, device_type):
    """Crea dispositivos IoT asignados al usuario normal."""
    return [
        IoTDevice.objects.create(
            name="Sensor 3",
            device_type=device_type,
            id_plot=user_plots[0],  # ✅ CORRECCIÓN: Usar id_plot en lugar de owner
            is_active=True,
            characteristics="Mide humedad cada 5 minutos",
        ),
        IoTDevice.objects.create(
            name="Sensor 4",
            device_type=device_type,
            id_plot=user_plots[1],  # ✅ CORRECCIÓN: Usar id_plot en lugar de owner
            is_active=True,
            characteristics="Mide temperatura y humedad",
        ),
    ]


# 🔹 TEST CASES


@pytest.mark.django_db
def test_admin_can_view_all_iot_devices(
    api_client, admin_user, admin_devices, user_devices
):
    """✅ Un administrador puede ver todos los dispositivos IoT registrados."""

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

    # 🔹 Consultar los dispositivos IoT
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_devices_url = reverse("list_iot_devices")
    response = api_client.get(list_devices_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de dispositivos: {response.data}"

    # 🔹 Verificar que se devuelvan todos los dispositivos
    total_devices_db = IoTDevice.objects.count()
    total_devices_api = len(response.data)

    assert (
        total_devices_api == total_devices_db
    ), f"❌ Se esperaban {total_devices_db} dispositivos, pero la API devolvió {total_devices_api}."

    print("✅ Test completado: El administrador puede ver todos los dispositivos IoT.")


@pytest.mark.django_db
def test_normal_user_can_only_view_own_devices(
    api_client, normal_user, user_devices, admin_devices
):
    """✅ Un usuario normal solo puede ver sus propios dispositivos IoT."""

    # 🔹 Iniciar sesión como usuario normal
    login_url = reverse("login")
    login_data = {"document": normal_user.document, "password": "SecurePass123@"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Validar OTP
    otp_instance = Otp.objects.filter(user=normal_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": normal_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Consultar los dispositivos IoT
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_devices_url = reverse("list_iot_devices")
    response = api_client.get(list_devices_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de dispositivos: {response.data}"

    # 🔹 Filtrar los dispositivos que pertenecen a los predios del usuario
    user_devices_db = IoTDevice.objects.filter(
        id_plot__owner=normal_user
    )  # ✅ CORRECCIÓN: Usar id_plot__owner
    api_devices = [
        device
        for device in response.data
        if device["id_plot"]
        in list(
            Plot.objects.filter(owner=normal_user).values_list("id_plot", flat=True)
        )
    ]

    print(
        "🔹 Dispositivos en la BD con dueño:",
        list(IoTDevice.objects.values("iot_id", "id_plot__owner")),
    )
    print("🔹 Respuesta de la API:", response.data)

    assert (
        len(api_devices) == user_devices_db.count()
    ), f"❌ El usuario debería ver {user_devices_db.count()} dispositivos, pero la API devolvió {len(api_devices)}."

    print(
        "✅ Test completado: El usuario normal solo puede ver sus propios dispositivos."
    )


@pytest.mark.django_db
def test_unauthenticated_user_cannot_view_devices(api_client):
    """🚫 Un usuario no autenticado no puede ver la lista de dispositivos IoT."""

    list_devices_url = reverse("list_iot_devices")
    response = api_client.get(list_devices_url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"❌ Un usuario no autenticado pudo acceder a la lista de dispositivos: {response.data}"

    print(
        "✅ Test completado: Un usuario no autenticado NO puede ver los dispositivos IoT."
    )
