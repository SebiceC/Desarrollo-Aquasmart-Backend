import pytest
from django.urls import reverse
from rest_framework import status
from plots_lots.models import Plot, Lot, SoilType
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
    """Crea un usuario normal en el sistema con la contraseña encriptada."""
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
    user.set_password("SecurePass123")  # ✅ Encripta la contraseña
    user.save()  # 🔥 Guarda los cambios en la BD
    return user


@pytest.fixture
def soil_type(db):
    """Crea un tipo de suelo válido en la base de datos."""
    return SoilType.objects.create(name="Arcilloso")


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


@pytest.fixture
def registered_lots(db, admin_user, normal_user, registered_plot, soil_type):
    """Crea varios lotes en la base de datos, algunos para el admin y otros para un usuario normal."""
    admin_lots = [
        Lot.objects.create(
            plot=registered_plot,
            crop_type="Maíz",
            soil_type=soil_type,
            is_activate=True,
        )
        for i in range(1, 4)
    ]

    user_plot = Plot.objects.create(
        plot_name="Predio Usuario",
        owner=normal_user,
        is_activate=True,
        latitud=-74.00111,
        longitud=40.712222,
        plot_extension=1500.00,
    )

    normal_user_lots = [
        Lot.objects.create(
            plot=user_plot,
            crop_type="Trigo",
            soil_type=soil_type,
            is_activate=True,
        )
        for i in range(1, 4)
    ]

    return admin_lots + normal_user_lots  # Devuelve todos los lotes creados


@pytest.mark.django_db
def test_admin_can_view_all_lots(api_client, admin_user, registered_lots):
    """✅ Verifica que un administrador pueda ver todos los lotes registrados en el sistema."""

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

    # 🔹 Paso 3: Consultar la lista de lotes
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_lots_url = reverse("lot-list")  # Verifica que la URL sea correcta
    response = api_client.get(list_lots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de lotes: {response.data}"

    # 🔹 Verificar que se devuelvan todos los lotes registrados
    total_lots_db = Lot.objects.count()
    total_lots_api = len(response.data)
    print("🔹 Respuesta completa de la API:", response.data)
    print("🔹 Lotes en la base de datos:", list(Lot.objects.values()))

    assert (
        total_lots_api == total_lots_db
    ), f"❌ Se esperaban {total_lots_db} lotes, pero la API devolvió {total_lots_api}."

    print(
        "✅ Test completado con éxito. El administrador puede ver todos los lotes registrados."
    )


@pytest.mark.django_db
def test_normal_user_can_only_view_own_lots(api_client, normal_user, registered_lots):
    """✅ Verifica que un usuario normal solo pueda ver sus propios lotes."""

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

    # 🔹 Paso 3: Intentar ver la lista de lotes
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_lots_url = reverse("lot-list")
    response = api_client.get(list_lots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de lotes: {response.data}"

    # 🔹 Filtrar los lotes que pertenecen al usuario normal
    user_lots = Lot.objects.filter(plot__owner=normal_user)
    user_plot_ids = Plot.objects.filter(owner=normal_user).values_list(
        "id_plot", flat=True
    )
    api_lots = [lot for lot in response.data if lot["plot"] in user_plot_ids]

    assert (
        len(api_lots) == user_lots.count()
    ), f"❌ El usuario debería ver {user_lots.count()} lotes, pero la API devolvió {len(api_lots)}."

    print("✅ Test completado con éxito. El usuario normal solo ve sus propios lotes.")


@pytest.mark.django_db
def test_unauthenticated_user_cannot_view_lots(api_client):
    """🚫 Verifica que un usuario no autenticado NO pueda acceder a la lista de lotes."""

    list_lots_url = reverse("lot-list")
    response = api_client.get(list_lots_url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"❌ Se permitió acceso sin autenticación: {response.data}"
    print("✅ Test completado con éxito. Un usuario no autenticado no puede ver lotes.")
