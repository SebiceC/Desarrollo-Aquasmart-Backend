import pytest
from django.urls import reverse
from rest_framework import status
from plots_lots.models import Plot
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
    """Crea un usuario administrador válido."""
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
    user.set_password(
        "SecurePass123"
    )  # 🔹 Asegurar que la contraseña se guarde encriptada
    user.save()
    return user


@pytest.fixture
def registered_plot(db, admin_user):
    """Crea y registra un predio en la base de datos usando un administrador."""
    return Plot.objects.create(
        plot_name="Predio de Prueba",
        owner=admin_user,
        is_activate=True,
        latitud=-74.00597,
        longitud=40.712776,
        plot_extension=2000.75,
    )


@pytest.mark.django_db
def test_admin_can_update_plot(api_client, admin_user, registered_plot):
    """✅ Verifica que un administrador pueda actualizar un predio exitosamente."""

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

    # 🔹 Paso 3: Actualizar la información del predio
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    update_plot_url = reverse(
        "actualizar-predio", kwargs={"id_plot": registered_plot.id_plot}
    )

    update_data = {
        "plot_name": "Predio Actualizado",
        "plot_extension": 2500.00,
    }

    update_response = api_client.patch(
        update_plot_url, update_data, format="json", **headers
    )
    assert (
        update_response.status_code == status.HTTP_200_OK
    ), f"Error al actualizar el predio: {update_response.data}"

    # 🔹 Paso 4: Verificar que los datos fueron actualizados
    registered_plot.refresh_from_db()  # 🔥 Recargar la información desde la base de datos
    assert (
        registered_plot.plot_name == "Predio Actualizado"
    ), "❌ El nombre del predio no se actualizó."
    assert (
        registered_plot.plot_extension == 2500.00
    ), "❌ La extensión del predio no se actualizó."

    print(
        "✅ Test completado con éxito. El administrador pudo actualizar un predio correctamente."
    )


@pytest.mark.django_db
def test_unauthenticated_user_cannot_update_plot(api_client, registered_plot):
    """🚫 Verifica que un usuario no autenticado NO pueda actualizar un predio."""

    update_plot_url = reverse(
        "actualizar-predio", kwargs={"id_plot": registered_plot.id_plot}
    )
    update_data = {"plot_name": "Intento de Cambio"}

    response = api_client.patch(update_plot_url, update_data, format="json")

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"❌ Un usuario no autenticado pudo modificar el predio: {response.data}"

    print(
        "✅ Test completado con éxito. Un usuario no autenticado no puede actualizar predios."
    )


@pytest.mark.django_db
def test_normal_user_cannot_update_plot(api_client, normal_user, registered_plot):
    """🚫 Verifica que un usuario normal NO pueda actualizar un predio que no le pertenece."""

    # 🔹 Paso 1: Iniciar sesión como usuario normal
    login_url = reverse("login")
    login_data = {"document": normal_user.document, "password": "SecurePass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Obtener y validar OTP
    otp_instance = Otp.objects.filter(user=normal_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": normal_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Intentar actualizar el predio
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    update_plot_url = reverse(
        "actualizar-predio", kwargs={"id_plot": registered_plot.id_plot}
    )

    update_data = {"plot_name": "Intento de Cambio"}

    response = api_client.patch(update_plot_url, update_data, format="json", **headers)

    # 🔹 Debe fallar con un error 403 Forbidden
    assert (
        response.status_code == status.HTTP_403_FORBIDDEN
    ), f"❌ Un usuario sin permisos pudo modificar el predio: {response.data}"

    print(
        "✅ Test completado con éxito. Un usuario normal no puede actualizar predios de otros usuarios."
    )
