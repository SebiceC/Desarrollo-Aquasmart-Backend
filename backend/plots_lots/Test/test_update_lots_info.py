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
def test_admin_can_update_lot(api_client, admin_user, admin_lots):
    """✅ Verifica que un administrador pueda actualizar un lote correctamente."""

    # 🔹 Paso 1: Iniciar sesión como administrador
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123@"}
    login_response = api_client.post(login_url, login_data)
    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"

    # 🔹 Paso 2: Validar OTP
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    otp_validation_url = reverse("validate-otp")
    otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(otp_validation_url, otp_data)
    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "❌ No se recibió un token tras validar el OTP."

    # 🔹 Paso 3: Seleccionar un lote del administrador
    lot_to_update = admin_lots[0]  # Tomamos el primer lote del admin
    update_lot_url = reverse("lot-update", kwargs={"id_lot": lot_to_update.id_lot})

    # 🔹 Paso 4: Enviar solicitud de actualización
    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    update_data = {
        "crop_type": "Cebada",  # Cambio de cultivo
        "is_activate": False,  # Desactivar el lote
    }

    update_response = api_client.patch(
        update_lot_url, update_data, format="json", **headers
    )
    assert (
        update_response.status_code == status.HTTP_200_OK
    ), f"Error al actualizar el lote: {update_response.data}"

    # 🔹 Paso 5: Verificar que los cambios se reflejan en la base de datos
    lot_to_update.refresh_from_db()
    assert lot_to_update.crop_type == "Cebada", "❌ El tipo de cultivo no se actualizó."
    assert not lot_to_update.is_activate, "❌ El estado de activación no se actualizó."

    print("✅ Test completado: El administrador pudo actualizar un lote correctamente.")


@pytest.mark.django_db
def test_normal_user_cannot_update_other_users_lot(api_client, normal_user, admin_lots):
    """🚫 Un usuario normal NO puede actualizar un lote de otro usuario."""

    # 🔹 Paso 1: Iniciar sesión como usuario normal
    login_url = reverse("login")
    login_data = {"document": normal_user.document, "password": "SecurePass123@"}
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

    # 🔹 Paso 3: Intentar actualizar un lote del administrador
    lot_to_update = admin_lots[0]  # Lote de un admin
    update_lot_url = reverse("lot-update", kwargs={"id_lot": lot_to_update.id_lot})

    token = otp_response.data["token"]
    headers = {"HTTP_AUTHORIZATION": f"Token {token}"}

    update_data = {"crop_type": "Cebada"}

    update_response = api_client.patch(
        update_lot_url, update_data, format="json", **headers
    )

    # 🔹 Debe devolver un error 403 Forbidden
    assert (
        update_response.status_code == status.HTTP_403_FORBIDDEN
    ), f"❌ Un usuario normal pudo modificar el lote de otro usuario: {update_response.data}"

    print(
        "✅ Test completado: Un usuario normal NO puede actualizar lotes de otros usuarios."
    )


@pytest.mark.django_db
def test_unauthenticated_user_cannot_update_lot(api_client, admin_lots):
    """🚫 Un usuario no autenticado no puede actualizar un lote."""

    lot_to_update = admin_lots[0]  # Lote del administrador
    update_lot_url = reverse("lot-update", kwargs={"id_lot": lot_to_update.id_lot})

    update_data = {"crop_type": "Cebada"}
    update_response = api_client.patch(update_lot_url, update_data, format="json")

    # 🔹 Debe devolver un error 401 Unauthorized
    assert (
        update_response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"❌ Un usuario no autenticado pudo modificar el lote: {update_response.data}"

    print("✅ Test completado: Un usuario no autenticado NO puede actualizar lotes.")
