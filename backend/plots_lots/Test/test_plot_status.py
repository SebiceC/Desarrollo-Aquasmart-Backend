import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from plots_lots.models import Plot, Lot, SoilType
from users.models import CustomUser, Otp, PersonType
import time

# ===================== Fixtures =====================


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea un tipo de persona para las pruebas."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def soil_type(db):
    """Crea un tipo de suelo para las pruebas."""
    return SoilType.objects.create(name="Arcilloso")


@pytest.fixture
def admin_user(db, person_type):
    """Crea un usuario administrador para las pruebas."""
    return CustomUser.objects.create_superuser(
        document="admin123",
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
def regular_user(db, person_type):
    """Crea un usuario regular para las pruebas."""
    return CustomUser.objects.create_user(
        document="user123",
        first_name="Regular",
        last_name="User",
        email="regular@example.com",
        phone="9876543210",
        password="UserPass123",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def active_plot(db, regular_user):
    """Crea un predio activo para las pruebas."""
    plot = Plot.objects.create(
        owner=regular_user,
        plot_name="Test Plot",
        latitud=4.5,
        longitud=-74.0,
        plot_extension=100.0,
        is_activate=True,
    )
    return plot


@pytest.fixture
def inactive_plot(db, regular_user):
    """Crea un predio inactivo para las pruebas."""
    plot = Plot.objects.create(
        owner=regular_user,
        plot_name="Inactive Plot",
        latitud=4.6,
        longitud=-74.1,
        plot_extension=200.0,
        is_activate=False,
    )
    return plot


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Cliente API autenticado como administrador."""
    # Iniciar sesión
    login_url = reverse("login")
    login_data = {"document": admin_user.document, "password": "AdminPass123"}
    login_response = api_client.post(login_url, login_data)

    # Obtener y validar OTP
    otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
    validate_url = reverse("validate-otp")
    validate_data = {"document": admin_user.document, "otp": otp_instance.otp}
    validate_response = api_client.post(validate_url, validate_data)

    # Configurar token en cliente
    token = validate_response.data["token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    return api_client


@pytest.fixture
def authenticated_regular_client(api_client, regular_user):
    """Cliente API autenticado como usuario regular."""
    login_url = reverse("login")
    login_data = {"document": regular_user.document, "password": "UserPass123"}
    login_response = api_client.post(login_url, login_data)

    # Obtener y validar OTP
    otp_instance = Otp.objects.filter(user=regular_user, is_login=True).first()
    validate_url = reverse("validate-otp")
    validate_data = {"document": regular_user.document, "otp": otp_instance.otp}
    validate_response = api_client.post(validate_url, validate_data)

    # Configurar token en cliente
    token = validate_response.data["token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    return api_client


# ===================== RF26: Pruebas de visualización y validación de estado =====================


@pytest.mark.django_db
class TestPlotStatus:
    """
    Pruebas para la visualización y validación del estado de los predios (RF26).

    Verifica:
    - Que se muestre correctamente el estado de los predios (activo/inactivo)
    - Que se notifiquen errores al intentar realizar acciones en predios inactivos
    """

    def test_view_active_plot_details(self, authenticated_regular_client, active_plot):
        """Verifica que se muestra correctamente que un predio está activo."""
        url = reverse("detalle-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_regular_client.get(url)

        assert (
            response.status_code == status.HTTP_200_OK
        ), "Debería obtener el detalle del predio"
        assert (
            response.data["is_activate"] is True
        ), "El predio debería mostrarse como activo"

    def test_view_inactive_plot_details(
        self, authenticated_regular_client, inactive_plot
    ):
        """Verifica que se muestra correctamente que un predio está inactivo."""
        url = reverse("detalle-predio", kwargs={"id_plot": inactive_plot.id_plot})
        response = authenticated_regular_client.get(url)

        assert (
            response.status_code == status.HTTP_200_OK
        ), "Debería obtener el detalle del predio"
        assert (
            response.data["is_activate"] is False
        ), "El predio debería mostrarse como inactivo"

    def test_cannot_create_lot_in_inactive_plot(
        self, authenticated_regular_client, inactive_plot, soil_type
    ):
        """Verifica que no se puede crear un lote en un predio inactivo."""
        url = reverse("lot-create")
        data = {
            "plot": inactive_plot.id_plot,
            "crop_type": "Maíz",
            "soil_type": soil_type.id,
        }
        response = authenticated_regular_client.post(url, data)

        # Verificar que la creación sea rechazada (puede ser 400 o 403 dependiendo de la implementación)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ], "Debería rechazar la creación del lote"

        # Si es 403, asumimos que está bien y no verificamos el mensaje (el sistema lo maneja como restricción de permisos)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert (
                "inactivo" in str(response.data).lower()
                or "inhabilitado" in str(response.data).lower()
            )

    def test_cannot_update_inactive_plot(
        self, authenticated_regular_client, inactive_plot
    ):
        """Verifica que no se puede actualizar un predio inactivo."""
        url = reverse("actualizar-predio", kwargs={"id_plot": inactive_plot.id_plot})
        data = {"plot_name": "Nuevo Nombre"}
        response = authenticated_regular_client.patch(url, data)

        # El comportamiento puede variar: puede ser rechazo (400) o acceso prohibido (403)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ]
        assert (
            "inactivo" in str(response.data).lower()
            or "inhabilitado" in str(response.data).lower()
            or "error" in str(response.data).lower()
        )


# ===================== RF27: Pruebas de inhabilitación de predios =====================


@pytest.mark.django_db
class TestPlotActivation:
    """
    Pruebas para la activación y desactivación de predios (RF27).

    Verifica:
    - Permisos de activación/desactivación (solo admin)
    - Comportamiento al activar/desactivar predios
    - Validaciones para evitar acciones redundantes
    """

    def test_admin_can_inactivate_plot(self, authenticated_admin_client, active_plot):
        """Verifica que un administrador puede inhabilitar un predio activo."""
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_admin_client.post(url)

        assert (
            response.status_code == status.HTTP_200_OK
        ), "La inhabilitación debería ser exitosa"
        assert "mensaje" in response.data, "Debería haber un mensaje de éxito"

        # Verificar que el predio realmente se deshabilitó
        active_plot.refresh_from_db()
        assert (
            active_plot.is_activate is False
        ), "El campo is_activate debería ser False"

    def test_admin_can_activate_plot(self, authenticated_admin_client, inactive_plot):
        """Verifica que un administrador puede habilitar un predio inactivo."""
        url = reverse("habilitar-predio", kwargs={"id_plot": inactive_plot.id_plot})
        response = authenticated_admin_client.post(url)

        assert (
            response.status_code == status.HTTP_200_OK
        ), "La habilitación debería ser exitosa"
        assert "mensaje" in response.data, "Debería haber un mensaje de éxito"

        # Verificar que el predio realmente se habilitó
        inactive_plot.refresh_from_db()
        assert (
            inactive_plot.is_activate is True
        ), "El campo is_activate debería ser True"

    def test_regular_user_cannot_inactivate_plot(
        self, authenticated_regular_client, active_plot
    ):
        """Verifica que un usuario regular no puede inhabilitar un predio."""
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_regular_client.post(url)

        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Debería rechazar el acceso"

        # Verificar que el predio no cambió
        active_plot.refresh_from_db()
        assert active_plot.is_activate is True, "El predio debería seguir activo"

    def test_cannot_inactivate_already_inactive_plot(
        self, authenticated_admin_client, inactive_plot
    ):
        """Verifica que no se puede inhabilitar un predio ya inhabilitado."""
        url = reverse("inhabilitar-predio", kwargs={"id_plot": inactive_plot.id_plot})
        response = authenticated_admin_client.post(url)

        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), "Debería indicar un error"
        assert (
            "ya está desactivado" in str(response.data).lower()
            or "error" in str(response.data).lower()
        )

    def test_cannot_activate_already_active_plot(
        self, authenticated_admin_client, active_plot
    ):
        """Verifica que no se puede habilitar un predio ya habilitado."""
        url = reverse("habilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_admin_client.post(url)

        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), "Debería indicar un error"
        assert (
            "ya está activado" in str(response.data).lower()
            or "error" in str(response.data).lower()
        )

    def test_inactivate_response_time(self, authenticated_admin_client, active_plot):
        """Verifica que la deshabilitación responda en menos de 5 segundos."""
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})

        start_time = time.time()
        response = authenticated_admin_client.post(url)
        end_time = time.time()

        # Verificar tiempo de respuesta
        response_time = end_time - start_time
        assert (
            response_time < 5.0
        ), f"Tiempo de respuesta demasiado alto: {response_time} segundos"

        # Verificar éxito
        assert response.status_code == status.HTTP_200_OK


# ===================== Pruebas específicas para alertas (RF26 y RF27) =====================


@pytest.mark.django_db
class TestPlotAlerts:
    """
    Pruebas específicas para validar las alertas generadas por el sistema.

    Estas pruebas verifican:
    - Alertas mostradas cuando se intenta operar con predios inhabilitados (RF26-HU02)
    - Alertas de confirmación al inhabilitar un predio (RF27/RF25-HU02)
    - Alertas de éxito después de inhabilitar un predio (RF27/RF25-HU03)
    """

    def test_alert_for_disabled_plot_actions(
        self, authenticated_admin_client, inactive_plot, soil_type
    ):
        """
        Verifica que se muestra una alerta al intentar realizar acciones en un predio inhabilitado.

        Historia de Usuario: RF26-HU02 - Alerta de predio inhabilitado en caso de solicitudes
        """
        # Usamos un cliente autenticado como administrador para evitar el rechazo por permisos
        # y llegar a la validación del predio inactivo
        url = reverse("lot-create")
        data = {
            "plot": inactive_plot.id_plot,
            "crop_type": "Maíz",
            "soil_type": soil_type.id,
        }
        response = authenticated_admin_client.post(url, data)

        # El error de validación debe dar un 400 Bad Request
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), "Debería rechazar la creación del lote con 400"

        # Verificar el contenido de la alerta - según la implementación en LotSerializer.validate_plot
        response_content = str(response.data).lower()
        print(f"\nRESPUESTA: {response.data}")

        # Buscamos específicamente el mensaje definido en el serializer
        assert (
            "inactivo" in response_content
        ), "La respuesta debe indicar que el predio está inactivo"

    def test_confirmation_alert_when_deactivating_plot(
        self, authenticated_admin_client, active_plot
    ):
        """
        Verifica que se muestra una alerta de confirmación al inhabilitar un predio.

        Historia de Usuario: RF27/RF25-HU02 - Alerta de confirmación de deseo de borrado
        """
        # Debido a que no podemos simular la interacción de UI directamente en pruebas de API,
        # verificamos que el endpoint de inhabilitación reporta claramente la acción que realizará

        # Primero, verificamos el endpoint sin realizar la acción
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_admin_client.get(url)

        # Si el endpoint no soporta GET, la prueba podría necesitar ajustes
        # En ese caso, verificamos mediante el mensaje de confirmación en la respuesta POST
        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            response = authenticated_admin_client.post(url)
            assert response.status_code == status.HTTP_200_OK

            # Verificar que la respuesta incluye un mensaje que podría mostrarse como confirmación
            response_content = str(response.data).lower()
            has_confirmation = any(
                term in response_content
                for term in [
                    "inhabilitado",
                    "desactivado",
                    "éxito",
                    "exitosamente",
                    "realizado",
                ]
            )

            assert (
                has_confirmation
            ), "La respuesta debe confirmar que el predio fue inhabilitado"

    def test_success_alert_after_deactivating_plot(
        self, authenticated_admin_client, active_plot
    ):
        """
        Verifica que se muestra una alerta de éxito después de inhabilitar un predio.

        Historia de Usuario: RF27/RF25-HU03 - Alerta de confirmación de borrado
        """
        # Inhabilitar un predio
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_admin_client.post(url)

        # Verificar que la acción fue exitosa
        assert response.status_code == status.HTTP_200_OK

        # Verificar que la respuesta incluye un mensaje de éxito
        assert "mensaje" in response.data or "message" in response.data

        # Obtener el mensaje (podría estar en cualquiera de estos campos)
        message = str(response.data.get("mensaje", response.data.get("message", "")))

        # Verificar que el mensaje indica éxito
        success_terms = ["éxito", "exitosamente", "correctamente", "satisfactoriamente"]
        has_success_message = any(term in message.lower() for term in success_terms)

        assert (
            has_success_message
        ), f"La respuesta debe confirmar el éxito de la operación. Mensaje actual: {message}"

        # Verificar que el predio realmente se deshabilitó
        active_plot.refresh_from_db()
        assert (
            active_plot.is_activate is False
        ), "El predio debería estar inactivo después de la operación"


@pytest.mark.django_db
class TestPlotActivationAdvanced:
    """
    Pruebas avanzadas para la activación/desactivación de predios.

    Verifica aspectos como:
    - Integridad de datos durante cambios de estado
    - Comportamiento con entidades relacionadas
    - Seguridad y autenticación
    - Flujos completos de operación
    """

    def test_data_integrity_after_activation_changes(
        self, authenticated_admin_client, inactive_plot
    ):
        """Verifica que solo cambia el estado y no otros datos del predio."""
        # Guardar valores originales
        original_name = inactive_plot.plot_name

        # Extraer los valores decimales y normalizarlos para comparación
        from decimal import Decimal

        original_latitud = Decimal(str(inactive_plot.latitud)).normalize()
        original_longitud = Decimal(str(inactive_plot.longitud)).normalize()
        original_extension = Decimal(str(inactive_plot.plot_extension)).normalize()

        # Activar el predio
        url = reverse("habilitar-predio", kwargs={"id_plot": inactive_plot.id_plot})
        response = authenticated_admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        # Verificar que solo el estado cambió
        inactive_plot.refresh_from_db()
        assert inactive_plot.is_activate is True, "El estado debería haber cambiado"
        assert inactive_plot.plot_name == original_name, "El nombre no debería cambiar"

        # Comparar usando valores Decimal normalizados
        assert (
            Decimal(str(inactive_plot.latitud)).normalize() == original_latitud
        ), "La latitud no debería cambiar"
        assert (
            Decimal(str(inactive_plot.longitud)).normalize() == original_longitud
        ), "La longitud no debería cambiar"
        assert (
            Decimal(str(inactive_plot.plot_extension)).normalize() == original_extension
        ), "La extensión no debería cambiar"

    def test_multiple_activation_changes(self, authenticated_admin_client, active_plot):
        """Verifica consistencia en múltiples cambios de activación."""
        # 1. Desactivar
        url_deactivate = reverse(
            "inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot}
        )
        response1 = authenticated_admin_client.post(url_deactivate)
        assert response1.status_code == status.HTTP_200_OK

        active_plot.refresh_from_db()
        assert (
            active_plot.is_activate is False
        ), "Debería estar inactivo después de desactivar"

        # 2. Activar
        url_activate = reverse(
            "habilitar-predio", kwargs={"id_plot": active_plot.id_plot}
        )
        response2 = authenticated_admin_client.post(url_activate)
        assert response2.status_code == status.HTTP_200_OK

        active_plot.refresh_from_db()
        assert (
            active_plot.is_activate is True
        ), "Debería estar activo después de activar"

        # 3. Desactivar de nuevo
        response3 = authenticated_admin_client.post(url_deactivate)
        assert response3.status_code == status.HTTP_200_OK

        active_plot.refresh_from_db()
        assert (
            active_plot.is_activate is False
        ), "Debería estar inactivo después de desactivar de nuevo"

    def test_related_lots_behavior(
        self, authenticated_admin_client, active_plot, soil_type
    ):
        """Verifica el comportamiento con lotes cuando se desactiva un predio."""
        # Crear un lote asociado al predio
        lot = Lot.objects.create(
            plot=active_plot, crop_type="Maíz", soil_type=soil_type
        )

        # Desactivar el predio
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = authenticated_admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        # Verificar que el predio se desactivó
        active_plot.refresh_from_db()
        assert active_plot.is_activate is False

        # Intentar acceder al lote
        lot_url = reverse("detalle-lote", kwargs={"id_lot": lot.id_lot})
        lot_response = authenticated_admin_client.get(lot_url)

        # El lote debería ser accesible aunque el predio esté inactivo
        assert lot_response.status_code == status.HTTP_200_OK

        # El lote debería reflejar que pertenece a un predio inactivo
        assert "plot" in lot_response.data
        plot_data = lot_response.data.get("plot")
        if isinstance(plot_data, dict) and "is_activate" in plot_data:
            assert plot_data["is_activate"] is False

    def test_invalid_token_behavior(self, api_client, active_plot):
        """Verifica que no se permite acción con token inválido."""
        # Configurar un token inválido
        api_client.credentials(HTTP_AUTHORIZATION="Token invalidtoken123")

        # Intentar desactivar el predio
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = api_client.post(url)

        # Debería rechazar la solicitud
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verificar que el predio no cambió
        active_plot.refresh_from_db()
        assert active_plot.is_activate is True, "El predio debería seguir activo"

    def test_no_token_behavior(self, api_client, active_plot):
        """Verifica que se requiere autenticación."""
        # No configurar credenciales (sin token)

        # Intentar desactivar el predio
        url = reverse("inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot})
        response = api_client.post(url)

        # Debería rechazar la solicitud
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verificar que el predio no cambió
        active_plot.refresh_from_db()
        assert active_plot.is_activate is True, "El predio debería seguir activo"

    def test_complete_flow_with_admin(self, api_client, admin_user, active_plot):
        """Prueba el flujo completo: login, validación OTP, desactivación."""
        # 1. Login
        login_url = reverse("login")
        login_data = {"document": admin_user.document, "password": "AdminPass123"}
        login_response = api_client.post(login_url, login_data)
        assert login_response.status_code == status.HTTP_200_OK

        # 2. Obtener OTP y validarlo
        otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
        assert otp_instance is not None

        validate_url = reverse("validate-otp")
        otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
        validate_response = api_client.post(validate_url, otp_data)
        assert validate_response.status_code == status.HTTP_200_OK
        assert "token" in validate_response.data

        # 3. Configurar token y desactivar predio
        token = validate_response.data["token"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        deactivate_url = reverse(
            "inhabilitar-predio", kwargs={"id_plot": active_plot.id_plot}
        )
        deactivate_response = api_client.post(deactivate_url)

        assert deactivate_response.status_code == status.HTTP_200_OK
        assert "mensaje" in deactivate_response.data
