import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from plots_lots.models import Plot
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
    """Crea un usuario administrador con permisos para ver los predios."""
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
    return user


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


@pytest.fixture
def normal_user(db, person_type):
    """Crea un usuario normal en el sistema."""
    user = CustomUser.objects.create(
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
    user.set_password("SecurePass123")  # 🔹 Establecer contraseña correctamente
    user.save()  # 🔹 Guardar el usuario en la base de datos
    return user  # 🔹 Retornar el usuario correctamente


@pytest.fixture
def registered_plots(db, admin_user, normal_user):
    """Crea predios registrados para un administrador y un usuario normal."""
    admin_plots = [
        Plot.objects.create(
            id_plot=f"PREDIO_ADMIN_{i}",
            plot_name=f"Predio Admin {i}",
            latitud=-75.12345 + i,
            longitud=41.98765 - i,
            plot_extension=1000.00 + i * 5,
            is_activate=True,
            owner=admin_user,
        )
        for i in range(1, 4)
    ]

    normal_user_plots = [
        Plot.objects.create(
            id_plot=f"PREDIO_USER_{i}",
            plot_name=f"Predio User {i}",
            latitud=-75.54321 + i,
            longitud=42.12345 - i,
            plot_extension=500.00 + i * 3,
            is_activate=True,
            owner=normal_user,
        )
        for i in range(1, 4)
    ]

    return admin_plots + normal_user_plots  # Retorna una lista con todos los predios


@pytest.mark.django_db
def test_view_district_plots(api_client, admin_user, registered_plots):
    """✅ Verifica que la API devuelva la lista de predios del distrito correctamente."""

    # 🔹 Paso 1: Iniciar sesión y obtener OTP
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Obtener y validar OTP
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    assert otp_instance, "❌ No se generó un OTP en la base de datos."

    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Autenticarse con el token generado
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    # 🔹 Paso 4: Consultar la lista de predios
    list_plots_url = reverse(
        "listar-predios"
    )  # 🔥 Verifica que este sea el nombre correcto en `urls.py`
    response = api_client.get(list_plots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de predios: {response.data}"

    # 🔹 Paso 5: Validar la cantidad de predios devueltos
    total_plots_db = Plot.objects.count()
    total_plots_api = len(response.data)

    assert (
        total_plots_api == total_plots_db
    ), f"❌ Se esperaban {total_plots_db} predios, pero la API devolvió {total_plots_api}."

    # 🔹 Paso 6: Verificar que cada predio tiene los atributos requeridos
    required_fields = [
        "id_plot",
        "plot_name",
        "is_activate",
        "latitud",
        "longitud",
        "plot_extension",
        "registration_date",
        "owner",
    ]
    for plot_data in response.data:
        for field in required_fields:
            assert field in plot_data, f"❌ Falta el campo '{field}' en la respuesta."

    print(
        "✅ Test completado con éxito. Se listaron correctamente los predios del distrito."
    )


@pytest.mark.django_db
def test_admin_can_view_all_plots(api_client, admin_user, registered_plots):
    """✅ Verifica que un administrador pueda ver todos los predios registrados en el sistema."""

    # 🔹 Paso 1: Iniciar sesión como administrador
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"
    assert (
        "message" in login_response.data
    ), "❌ No se recibió un mensaje de confirmación de envío de OTP."

    # 🔹 Paso 2: Obtener el OTP y validarlo
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    assert otp_instance, "❌ No se generó un OTP en la base de datos."

    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Usar el token para visualizar los predios
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_plots_url = reverse("listar-predios")
    response = api_client.get(list_plots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error en la lista de predios: {response.data}"

    # 🔹 Verificar que la API devuelve todos los predios del sistema
    total_plots_db = Plot.objects.count()
    total_plots_api = len(response.data)

    assert (
        total_plots_api == total_plots_db
    ), f"❌ Se esperaban {total_plots_db} predios, pero la API devolvió {total_plots_api}."

    print(
        "✅ Test completado con éxito. El administrador puede ver todos los predios registrados."
    )


@pytest.mark.django_db
def test_normal_user_can_only_view_own_plots(api_client, normal_user, registered_plots):
    """✅ Verifica que un usuario normal solo pueda ver sus propios predios."""

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

    # 🔹 Paso 3: Intentar ver todos los predios
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_plots_url = reverse("listar-predios")
    response = api_client.get(list_plots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error en la lista de predios: {response.data}"

    # 🔹 Filtrar los predios que pertenecen al usuario normal
    user_plots = Plot.objects.filter(owner=normal_user)
    api_plots = [
        plot for plot in response.data if plot["owner"] == normal_user.document
    ]

    assert (
        len(api_plots) == user_plots.count()
    ), f"❌ El usuario debería ver {user_plots.count()} predios, pero la API devolvió {len(api_plots)}."

    print("✅ Test completado con éxito. El usuario normal solo ve sus propios predios.")


@pytest.mark.django_db
def test_unauthenticated_user_cannot_view_plots(api_client):
    """🚫 Verifica que un usuario sin autenticación no pueda acceder a los predios."""

    list_plots_url = reverse("listar-predios")
    response = api_client.get(list_plots_url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"❌ Se permitió acceso sin autenticación: {response.data}"
    print(
        "✅ Test completado con éxito. Un usuario no autenticado no puede ver predios."
    )
