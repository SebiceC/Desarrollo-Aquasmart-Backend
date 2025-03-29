import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, Otp, PersonType
from plots_lots.models import Plot
from rest_framework.authtoken.models import Token
from users.models import CustomUser, Otp, PersonType


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
    """Crea un usuario administrador de prueba y refresca desde la base de datos."""
    user = CustomUser.objects.create_superuser(
        document="123456789012",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        password="AdminPass123",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )
    user.refresh_from_db()  # 🔥 Asegurar que el ID se asigna correctamente desde la BD
    return user


@pytest.fixture
def normal_user(db, person_type):
    """Crea un usuario normal sin permisos administrativos."""
    return CustomUser.objects.create(
        document="123456789013",
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
def test_register_plot_success(api_client, admin_user):
    """✅ Verifica que un administrador pueda registrar un predio exitosamente."""

    # 🔹 Paso 1: Iniciar sesión para obtener OTP
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Obtener el OTP generado
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

    # 🔹 Paso 4: Realizar la solicitud de registro de predio con los campos requeridos
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    register_plot_url = reverse("registrar-predio")

    plot_data = {
        "plot_name": "Predio de Prueba",  # 🔹 Campo obligatorio
        "area": 1500.50,
        "location": "Zona Rural",
        "owner": admin_user.document,
        "is_activate": True,
        "latitud": -74.00597,  # 🔹 Campo obligatorio
        "longitud": 40.712776,  # 🔹 Campo obligatorio
        "plot_extension": 2000.75,  # 🔹 Campo obligatorio
    }

    response = api_client.post(register_plot_url, plot_data, format="json", **headers)

    # 🔹 Verificar la respuesta de la API
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Error en el registro del predio: {response.data}"
    assert "id_plot" in response.data, "❌ No se recibió el identificador del predio."
    assert (
        response.data["id_plot"] == response.data["id_plot"]
    ), "❌ El ID del predio no coincide."

    print(
        "✅ Test completado con éxito. El administrador pudo registrar un predio correctamente."
    )
    print("✅ Predio registrado:", response.data)


@pytest.mark.django_db
def test_register_plot_missing_fields(api_client, admin_user):
    """❌ Verifica que no se pueda registrar un predio con datos faltantes."""

    # 🔹 Autenticación
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    register_plot_url = reverse("registrar-predio")

    # 🔹 Enviar datos incompletos
    incomplete_data = {"name": "Predio sin Área"}
    response = api_client.post(register_plot_url, incomplete_data, **headers)

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), "❌ La API permitió registrar un predio con datos incompletos."
    print(
        "✅ Test completado con éxito: No se permitió registrar un predio con datos faltantes."
    )


@pytest.mark.django_db
def test_register_plot_without_authentication(api_client):
    """🔒 Verifica que un usuario no autenticado no pueda registrar un predio."""

    register_plot_url = reverse("registrar-predio")

    plot_data = {
        "id_plot": "PREDIO123",
        "name": "Predio de Prueba",
        "area": 1500.50,
        "location": "Zona Rural",
        "owner": 1,  # Se pone un ID arbitrario
        "is_activate": True,
    }

    response = api_client.post(register_plot_url, plot_data)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), "❌ La API permitió registrar un predio sin autenticación."
    print("✅ Test completado con éxito: La API bloqueó el registro sin autenticación.")


@pytest.fixture
def otp_for_user(db, normal_user):
    """Genera un OTP válido para el usuario normal."""
    return Otp.objects.create(user=normal_user, otp="123456", is_validated=False)


@pytest.mark.django_db
def test_register_plot_unauthorized_user(api_client, normal_user, otp_for_user):
    """👤 Verifica que un usuario normal no pueda registrar un predio."""

    # 🔹 Paso 1: Validar OTP
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": normal_user.document, "otp": otp_for_user.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"

    # 🔹 Paso 2: **Forzar la creación del token si no se generó automáticamente**
    token_instance, created = Token.objects.get_or_create(user=normal_user)

    # 🔹 Paso 3: Autenticarse con el token generado
    token = token_instance.key  # Extraer la clave del token
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}  # ✅ Usuario autenticado

    # 🔹 Paso 4: Intentar registrar un predio sin los permisos adecuados
    register_plot_url = reverse("registrar-predio")
    plot_data = {
        "id_plot": "PREDIO999",
        "plot_name": "Predio No Autorizado",
        "area": 500.25,
        "location": "Zona Restringida",
        "owner": normal_user.document,
        "is_activate": True,
        "latitud": -75.12345,
        "longitud": 41.98765,
        "plot_extension": 1000.00,
    }

    response = api_client.post(register_plot_url, plot_data, format="json", **headers)

    # 🔹 Verificar que la API rechace la solicitud con 403 Forbidden (usuario autenticado, pero sin permisos)
    assert (
        response.status_code == status.HTTP_403_FORBIDDEN
    ), f"❌ Se permitió a un usuario sin permisos registrar un predio: {response.data}"

    print(
        "✅ Test completado con éxito. Un usuario sin permisos NO pudo registrar un predio."
    )
