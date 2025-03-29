import pytest
from django.urls import reverse
from rest_framework import status
from plots_lots.models import Lot, SoilType, Plot
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
    user = CustomUser.objects.create_superuser(
        document="123456789012",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        person_type=person_type,
        is_active=True,
        is_registered=True,
        password="AdminPass123@",  # 🔥 NO ENCRIPTAR AQUÍ
    )
    user.set_password("AdminPass123@")  # 🔥 Aplicar `set_password` antes de guardar
    user.save()

    print(f"🔹 Admin creado: {user.document}, contraseña en hash: {user.password}")
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
        person_type=person_type,
        is_active=True,
        is_registered=True,
        password="SecurePass123@",  # 🔥 NO ENCRIPTAR AQUÍ
    )
    user.set_password("SecurePass123@")  # 🔥 Aplicar `set_password` antes de guardar
    user.save()

    print(f"🔹 Usuario creado: {user.document}, contraseña en hash: {user.password}")
    return user


@pytest.fixture
def soil_type(db):
    """Crea un tipo de suelo válido en la base de datos."""
    return SoilType.objects.create(name="Arcilloso")  # 🔥 Asegura que exista en la DB


@pytest.fixture
def admin_plots(db, admin_user):
    """Crea varios predios que pertenecen al administrador."""
    return [
        Plot.objects.create(
            plot_name=f"Predio Admin {i+1}",
            owner=admin_user,
            is_activate=True,
            latitud=-74.00597 + i,
            longitud=40.712776 - i,
            plot_extension=2000.75 + (i * 100),
        )
        for i in range(2)  # 🔹 Se crean 2 predios para el admin
    ]


@pytest.fixture
def user_plots(db, normal_user):
    """Crea varios predios que pertenecen a un usuario normal."""
    return [
        Plot.objects.create(
            plot_name=f"Predio Usuario {i+1}",
            owner=normal_user,
            is_activate=True,
            latitud=-74.00597 + i,
            longitud=40.712776 - i,
            plot_extension=1500.50 + (i * 50),
        )
        for i in range(2)  # 🔹 Se crean 2 predios para el usuario normal
    ]


@pytest.fixture
def admin_lots(db, admin_plots, soil_type):
    """Crea lotes en los predios del administrador."""
    lots = []
    for plot in admin_plots:
        for i in range(2):  # 🔹 Cada predio tendrá 2 lotes
            lot = Lot.objects.create(
                plot=plot,
                crop_type="Maíz",
                soil_type=soil_type,
                is_activate=True,
            )
            lots.append(lot)
    return lots


@pytest.fixture
def user_lots(db, user_plots, soil_type):
    """Crea lotes en los predios de un usuario normal."""
    lots = []
    for plot in user_plots:
        for i in range(2):  # 🔹 Cada predio tendrá 2 lotes
            lot = Lot.objects.create(
                plot=plot,
                crop_type="Trigo",
                soil_type=soil_type,
                is_activate=True,
            )
            lots.append(lot)
    return lots


@pytest.mark.django_db
def test_admin_can_view_all_lots(api_client, admin_user, admin_lots, user_lots):
    """✅ Verifica que un administrador pueda ver todos los lotes registrados en el sistema."""

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

    # 🔹 Consultar la lista de lotes
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_lots_url = reverse("lot-list")
    response = api_client.get(list_lots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de lotes: {response.data}"

    # 🔹 Verificar que se devuelvan todos los lotes
    total_lots_db = Lot.objects.count()
    total_lots_api = len(response.data)

    assert (
        total_lots_api == total_lots_db
    ), f"❌ Se esperaban {total_lots_db} lotes, pero la API devolvió {total_lots_api}."

    print("✅ Test completado: El administrador puede ver todos los lotes.")


@pytest.mark.django_db
def test_normal_user_can_only_view_own_lots(
    api_client, normal_user, user_lots, admin_lots
):
    """✅ Verifica que un usuario normal solo pueda ver sus propios lotes."""

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

    # 🔹 Consultar la lista de lotes
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    list_lots_url = reverse("lot-list")
    response = api_client.get(list_lots_url, **headers)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al obtener la lista de lotes: {response.data}"

    # 🔹 Verificar que solo aparecen los lotes del usuario
    user_lots_db = Lot.objects.filter(plot__owner=normal_user)
    api_lots = [
        lot
        for lot in response.data
        if lot["id_lot"] in list(user_lots_db.values_list("id_lot", flat=True))
    ]

    print("🔹 Respuesta completa de la API:", response.data)

    assert (
        len(api_lots) == user_lots_db.count()
    ), f"❌ El usuario debería ver {user_lots_db.count()} lotes, pero la API devolvió {len(api_lots)}."

    print("✅ Test completado: El usuario normal solo puede ver sus propios lotes.")


@pytest.mark.django_db
def test_normal_user_cannot_view_other_users_lots(api_client, normal_user, admin_lots):
    """🚫 Un usuario normal NO puede ver los lotes de otro usuario (los del admin)."""

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

    # 🔹 Intentar acceder a un lote del administrador
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    admin_lot = admin_lots[0]  # 🔥 Tomamos un lote del administrador
    lot_detail_url = reverse("detalle-lote", kwargs={"id_lot": admin_lot.id_lot})
    response = api_client.get(lot_detail_url, **headers)

    assert response.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ], f"❌ El usuario normal pudo acceder a un lote del admin. Respuesta: {response.data}"

    print("✅ Test completado: El usuario normal NO puede ver lotes de otros usuarios.")


@pytest.mark.django_db
def test_unauthenticated_user_cannot_view_lot_info(api_client, user_lots):
    """🚫 Un usuario no autenticado no puede acceder a la información de un lote."""

    lot_detail_url = reverse("detalle-lote", kwargs={"id_lot": user_lots[0].id_lot})
    response = api_client.get(lot_detail_url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), "❌ Un usuario no autenticado pudo acceder al lote."

    print(
        "✅ Test completado: Un usuario no autenticado NO puede ver información de lotes."
    )
