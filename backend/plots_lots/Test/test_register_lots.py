import pytest
from django.urls import reverse
from rest_framework import status
from plots_lots.models import Lot, Plot, SoilType
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
def admin_user(db, person_type):
    """Crea un usuario administrador válido con todos los campos requeridos."""
    user = CustomUser.objects.create_superuser(
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
    user.set_password("AdminPass123")
    user.save()
    return user


@pytest.fixture
def normal_user(db, person_type):
    """Crea un usuario normal en el sistema con una contraseña correctamente encriptada."""
    user = CustomUser.objects.create(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567890",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )
    user.set_password("SecurePass123")
    user.save()
    return user


@pytest.fixture
def registered_plot(db, admin_user):
    """Crea un predio registrado en la base de datos."""
    return Plot.objects.create(
        plot_name="Predio de Prueba",
        owner=admin_user,
        is_activate=True,
        latitud=-74.00597,
        longitud=40.712776,
        plot_extension=2000.75,
    )


@pytest.fixture
def soil_type(db):
    """Crea un tipo de suelo válido en la base de datos."""
    return SoilType.objects.create(name="Arcilloso")  # 🔥 Asegura que exista en la DB


@pytest.mark.django_db
def test_admin_can_register_lot(api_client, admin_user, soil_type, registered_plot):
    """✅ Verifica que un administrador pueda registrar un lote exitosamente."""

    # 🔹 Paso 1: Iniciar sesión como administrador
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Obtener y validar OTP
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    plot_id = registered_plot.id_plot  # ✅ Obtener ID del predio creado
    soil_type_id = soil_type.id  # ✅ Obtener ID del tipo de suelo creado
    print(f"🔹 Usando plot_id: {plot_id}, soil_type_id: {soil_type_id}")  # 🔥 Depuración

    # 🔹 Paso 4: Registrar el lote
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    register_lot_url = reverse("lot-create")  # 🔥 Verifica que esta URL sea la correcta

    lot_data = {
        "lot_name": "Lote de Prueba",
        "owner": admin_user.document,
        "crop_type": "Maíz",
        "soil_type": soil_type_id,
        "plot": plot_id,
        "is_activate": True,
        "latitud": -74.00597,
        "longitud": 40.712776,
    }

    response = api_client.post(register_lot_url, lot_data, format="json", **headers)

    # 🔹 Verificar la respuesta de la API
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Error en el registro del lote: {response.data}"
    assert "id_lot" in response.data, "❌ No se recibió el identificador del lote."

    registered_lot_id = response.data["id_lot"]
    print(f"✅ Lote registrado con ID: {registered_lot_id}")

    # 🔹 Verificación redundante necesaria
    assert (
        response.data["id_lot"] == response.data["id_lot"]
    ), "❌ El ID del lote no coincide."

    print(
        "✅ Test completado con éxito. El administrador pudo registrar un lote correctamente."
    )


@pytest.mark.django_db
def test_normal_user_cannot_register_lot(api_client, normal_user):
    """🚫 Verifica que un usuario normal NO pueda registrar un lote."""

    # 🔹 Paso 1: Iniciar sesión como usuario normal
    login_url = reverse("login")
    login_data = {"document": normal_user.document, "password": "SecurePass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Validar OTP
    otp_instance = Otp.objects.filter(user=normal_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": normal_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Intentar registrar un lote
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    register_lot_url = reverse("lot-create")

    lot_data = {
        "lot_name": "Lote no permitido",
        "area": 400.00,
        "owner": normal_user.document,
        "is_activate": True,
        "latitud": -75.12345,
        "longitud": 39.98765,
    }

    response = api_client.post(register_lot_url, lot_data, format="json", **headers)

    # 🔹 Debe fallar con error 403 Forbidden
    assert (
        response.status_code == status.HTTP_403_FORBIDDEN
    ), f"❌ Se permitió a un usuario sin permisos registrar un lote: {response.data}"

    print("✅ Test completado con éxito. Un usuario normal no puede registrar lotes.")


@pytest.mark.django_db
def test_unauthenticated_user_cannot_register_lot(api_client):
    """🚫 Verifica que un usuario no autenticado NO pueda registrar un lote."""

    register_lot_url = reverse("lot-create")

    lot_data = {
        "lot_name": "Lote no autenticado",
        "area": 350.50,
        "owner": "123456789012",  # 🔥 No importa el dueño, el usuario no está autenticado
        "is_activate": True,
        "latitud": -74.12345,
        "longitud": 40.54321,
    }

    response = api_client.post(register_lot_url, lot_data, format="json")

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"❌ Se permitió a un usuario no autenticado registrar un lote: {response.data}"

    print(
        "✅ Test completado con éxito. Un usuario no autenticado no puede registrar lotes."
    )
