import pytest
from django.urls import reverse
from rest_framework import status
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
    """Crea un usuario administrador con permisos para ver la información de los predios."""
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
    """Crea un usuario normal sin permisos de administrador."""
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
    user.set_password("SecurePass123")
    user.save()
    return user


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
def test_view_district_plot_details(api_client, admin_user, registered_plots):
    """✅ Verifica que la API devuelva la información detallada de los predios del distrito para administradores."""

    # 🔹 Paso 1: Iniciar sesión como administrador
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

    # 🔹 Paso 4: Consultar la información de un predio específico
    plot = registered_plots[0]  # Tomamos el primer predio registrado
    plot_detail_url = reverse(
        "detalle-predio", kwargs={"id_plot": plot.id_plot}
    )  # 🔥 Verifica que este sea el nombre correcto en `urls.py`
    response = api_client.get(plot_detail_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la información del predio: {response.data}"

    # 🔹 Paso 5: Verificar que la API devuelve los datos completos del predio
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
    for field in required_fields:
        assert field in response.data, f"❌ Falta el campo '{field}' en la respuesta."

    print(
        f"✅ Test completado con éxito. Se visualizó correctamente la información del predio {plot.id_plot}."
    )


@pytest.mark.django_db
def test_normal_user_cannot_view_plot_details(api_client, normal_user, admin_user):
    """🚫 Verifica que un usuario normal NO pueda acceder a la información detallada de predios de otros usuarios."""

    # 🔹 Paso 1: Iniciar sesión como administrador para registrar un predio
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Obtener y validar OTP como administrador
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Registrar un predio con el administrador
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
    register_plot_url = reverse("registrar-predio")

    plot_data = {
        "plot_name": "Predio de Admin",
        "area": 1200.00,
        "location": "Sector 5",
        "owner": admin_user.document,
        "is_activate": True,
        "latitud": -75.12345,
        "longitud": 41.98765,
        "plot_extension": 1800.00,
    }

    register_response = api_client.post(
        register_plot_url, plot_data, format="json", **headers
    )

    assert (
        register_response.status_code == status.HTTP_201_CREATED
    ), f"Error al registrar predio: {register_response.data}"
    assert (
        "id_plot" in register_response.data
    ), "❌ No se recibió el ID del predio en la respuesta."

    registered_plot_id = register_response.data[
        "id_plot"
    ]  # 🔥 ID real del predio registrado
    print(f"✅ Predio registrado con ID: {registered_plot_id}")

    # 🔹 Paso 4: Iniciar sesión como usuario normal
    login_data_user = {"document": normal_user.document, "password": "SecurePass123"}
    login_response_user = api_client.post(login_url, login_data_user)

    assert (
        login_response_user.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response_user.data}"

    # 🔹 Paso 5: Validar OTP como usuario normal
    otp_instance_user = Otp.objects.filter(user=normal_user, is_login=True).first()
    otp_data_user = {"document": normal_user.document, "otp": otp_instance_user.otp}
    otp_response_user = api_client.post(otp_validation_url, otp_data_user)

    assert (
        otp_response_user.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response_user.data}"
    assert (
        "token" in otp_response_user.data
    ), "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 6: Intentar acceder a la información del predio del administrador
    user_token = otp_response_user.data["token"]
    headers_user = {"HTTP_AUTHORIZATION": f"Token {user_token}"}

    # 🔹 Verificar si la API usa "id_plot" o "id" en la URL
    plot_detail_url = reverse("detalle-predio", kwargs={"id_plot": registered_plot_id})

    print(f"🔹 Intentando acceder a: {plot_detail_url}")

    response = api_client.get(plot_detail_url, **headers_user)

    # 🔹 Si la API responde con 404, hay un problema en la configuración de la vista o la URL
    if response.status_code == status.HTTP_404_NOT_FOUND:
        print(
            f"⚠️ Advertencia: El servidor respondió con 404. Esto sugiere que la API no encuentra el predio con ID {registered_plot_id}."
        )
        print(
            "⚠️ Verifica que la vista permite acceder a todos los predios y no solo a los del usuario autenticado."
        )

    # 🔹 Verificar que el usuario normal NO pueda acceder al predio del administrador
    assert response.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ], f"❌ Un usuario sin permisos pudo acceder a la información del predio: {response.data}"

    print(
        "✅ Test completado con éxito. Un usuario normal no puede ver predios de otros usuarios."
    )
