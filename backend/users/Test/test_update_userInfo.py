import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, Otp, PersonType, UserUpdateLog
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
import time


@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea un tipo de persona para usar en los tests."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def test_user(db, person_type):
    """Usuario de prueba para realizar actualizaciones."""
    return CustomUser.objects.create_user(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567890",
        password="SecurePass123@",
        person_type=person_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Cliente API autenticado manualmente."""

    token, _ = Token.objects.get_or_create(user=test_user)

    # Configurar cliente con token
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    return api_client


@pytest.mark.django_db
class TestUserProfileUpdate:
    def test_email_validation(self, authenticated_client, test_user):
        """Prueba validación de formato de correo según Django."""
        update_url = reverse("profile-update")

        validations = [
            # Correos completamente inválidos
            {
                "email": "correo_invalido",
                "expected_status": status.HTTP_400_BAD_REQUEST,
            },
            {"email": "correo@", "expected_status": status.HTTP_400_BAD_REQUEST},
            {"email": "@ejemplo.com", "expected_status": status.HTTP_400_BAD_REQUEST},
            {"email": "usuario@", "expected_status": status.HTTP_400_BAD_REQUEST},
            {"email": "usuario@.com", "expected_status": status.HTTP_400_BAD_REQUEST},
            # Correos con dominios inválidos
            {
                "email": "usuario@dominio",
                "expected_status": status.HTTP_400_BAD_REQUEST,
            },
            {
                "email": "usuario@dominio.",
                "expected_status": status.HTTP_400_BAD_REQUEST,
            },
            {"email": "usuario@.com", "expected_status": status.HTTP_400_BAD_REQUEST},
            # Correos con caracteres no permitidos
            {
                "email": "usuario espacios@ejemplo.com",
                "expected_status": status.HTTP_400_BAD_REQUEST,
            },
            {
                "email": "usuario@ejemplo,com",
                "expected_status": status.HTTP_400_BAD_REQUEST,
            },
            # Correos válidos
            {"email": "usuario@ejemplo.com", "expected_status": status.HTTP_200_OK},
            {
                "email": "usuario.nombre@ejemplo.co",
                "expected_status": status.HTTP_200_OK,
            },
            {"email": "usuario+tag@ejemplo.org", "expected_status": status.HTTP_200_OK},
            {"email": "u@ejemplo.com", "expected_status": status.HTTP_200_OK},
        ]

        for case in validations:
            response = authenticated_client.patch(update_url, {"email": case["email"]})
            update_log, _ = UserUpdateLog.objects.get_or_create(user=test_user)
            update_log.update_count = 0  # Reiniciar conteo de actualizaciones
            update_log.save()  # Guardar cambios
            if response.status_code != case["expected_status"]:
                print(f"Failed for {case['email']}")
                print(f"Response: {response.data}")
            assert (
                response.status_code == case["expected_status"]
            ), f"Falló para {case['email']}"

    def test_phone_validation(self, authenticated_client, test_user):
        """Prueba validación de formato de teléfono."""
        update_url = reverse("profile-update")
        # Verificar comportamiento actual con teléfonos
        validations = [
            # Casos que deberían fallar
            {"phone": "abcd1234", "expected_status": status.HTTP_400_BAD_REQUEST},
            {"phone": "123-456-7890", "expected_status": status.HTTP_400_BAD_REQUEST},
            {
                "phone": "3201234567890123456",
                "expected_status": status.HTTP_400_BAD_REQUEST,
            },
            {"phone": "12345678", "expected_status": status.HTTP_400_BAD_REQUEST},
            # Casos que deberían pasar
            {"phone": "3201234567", "expected_status": status.HTTP_200_OK},
        ]

        for case in validations:
            update_log, _ = UserUpdateLog.objects.get_or_create(user=test_user)
            update_log.update_count = 0
            update_log.save()
            response = authenticated_client.patch(update_url, {"phone": case["phone"]})
            if (
                response.status_code != case["expected_status"]
            ):  # Imprimir mensaje de error
                print(f"Failed for {case['phone']}")
                print(f"Response: {response.data}")
            assert (
                response.status_code == case["expected_status"]
            ), f"Falló para {case['phone']}"

    def test_weekly_update_limit(self, authenticated_client, test_user):
        """Prueba límite de actualizaciones semanales."""
        update_url = reverse("profile-update")

        # Eliminar registros previos de UserUpdateLog si es necesario
        UserUpdateLog.objects.filter(user=test_user).delete()

        # Realizar 3 actualizaciones válidas
        for i in range(3):
            response = authenticated_client.patch(
                update_url, {"email": f"correo{i}@example.com"}
            )
            assert response.status_code == status.HTTP_200_OK

        # Cuarta actualización debe fallar
        response = authenticated_client.patch(
            update_url, {"email": "cuarta_actualizacion@example.com"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "límite de 3 actualizaciones" in str(response.data).lower()

    def test_unmodifiable_fields(self, authenticated_client, test_user):
        """Prueba campos no modificables."""
        update_url = reverse("profile-update")

        # Intentar modificar campos no permitidos
        unmodifiable_fields = {
            "document": "999999999999",
            "first_name": "NewName",
            "last_name": "NewLastName",
            "is_active": False,
        }

        for field, value in unmodifiable_fields.items():
            response = authenticated_client.patch(update_url, {field: value})
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_required_fields(self, authenticated_client, test_user):
        """Prueba campos obligatorios."""
        update_url = reverse("profile-update")

        # Intentar actualizar sin campos
        response = authenticated_client.patch(update_url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Intentar actualizar con campos vacíos
        invalid_data = [{"email": ""}, {"phone": ""}, {"email": "", "phone": ""}]

        for data in invalid_data:
            response = authenticated_client.patch(update_url, data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update(self, authenticated_client, test_user):
        """Prueba actualización parcial de datos."""
        update_url = reverse("profile-update")

        # Actualizar solo correo
        response = authenticated_client.patch(
            update_url, {"email": "nuevocorreo@example.com"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Actualizar solo teléfono
        response = authenticated_client.patch(update_url, {"phone": "3212345678"})
        assert response.status_code == status.HTTP_200_OK

    def test_update_with_identical_data(self, authenticated_client, test_user):
        """Prueba actualización con datos idénticos."""
        update_url = reverse("profile-update")

        # Intentar actualizar con el mismo correo actual
        response = authenticated_client.patch(update_url, {"email": test_user.email})
        assert response.status_code == status.HTTP_200_OK

    def test_update_permissions(self, api_client, test_user):
        """Prueba permisos de actualización."""
        update_url = reverse("profile-update")

        # Sin autenticación
        response = api_client.patch(update_url, {"email": "nuevo_correo@example.com"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_outside_weekly_limit(self, authenticated_client, test_user):
        """Prueba intento de actualización fuera de límite semanal."""
        update_url = reverse("profile-update")

        # Obtener o crear el registro de actualizaciones
        update_log, _ = UserUpdateLog.objects.get_or_create(user=test_user)

        # Simular actualizaciones en semanas diferentes
        update_log.first_update_date = now().date() - timedelta(days=8)
        update_log.update_count = 3
        update_log.save()

        # Intentar actualizar después de una semana
        response = authenticated_client.patch(
            update_url, {"email": "nuevo_correo@example.com"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_email_uniqueness(self, authenticated_client, test_user):
        """Prueba unicidad de correo electrónico."""
        update_url = reverse("profile-update")

        # Crear otro usuario
        another_user = CustomUser.objects.create_user(
            document="999999999999",
            first_name="Another",
            last_name="User",
            email="another@example.com",
            phone="9876543210",
            password="SecurePass123@",
            is_active=True,
            is_registered=True,
        )

        # Intentar usar un correo ya existente
        response = authenticated_client.patch(update_url, {"email": another_user.email})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_concurrent_updates(self, authenticated_client, test_user):
        """Prueba de actualizaciones concurrentes."""
        update_url = reverse("profile-update")

        # Limpiar registros de actualización previos
        UserUpdateLog.objects.filter(user=test_user).delete()

        # Simular múltiples actualizaciones rápidas
        updates = [
            {"email": "update1@example.com"},
            {"email": "update2@example.com"},
            {"email": "update3@example.com"},
            {"email": "update4@example.com"},
        ]

        responses = []
        for update in updates:
            response = authenticated_client.patch(update_url, update)
            responses.append(response)

        # Verificar que las primeras 3 actualizaciones pasen
        success_count = sum(
            1 for resp in responses[:3] if resp.status_code == status.HTTP_200_OK
        )
        assert success_count == 3

        # La cuarta actualización debe fallar
        assert responses[3].status_code == status.HTTP_400_BAD_REQUEST

    def test_response_time(self, authenticated_client, test_user):
        """Prueba tiempo de respuesta del servicio."""
        from django.utils import timezone
        import time

        update_url = reverse("profile-update")

        start_time = time.time()
        response = authenticated_client.patch(
            update_url, {"email": "tiempo_respuesta@example.com"}
        )
        end_time = time.time()

        # Verificar que la respuesta sea menor a 3 segundos
        response_time = end_time - start_time
        assert (
            response_time < 3
        ), f"Tiempo de respuesta excedido: {response_time} segundos"
        assert response.status_code == status.HTTP_200_OK

    def test_update_with_edge_case_data(self, authenticated_client, test_user):
        """Prueba actualización con casos límite de datos."""
        update_url = reverse("profile-update")

        # Correos con casos límite
        edge_case_emails = [
            "a" * 64 + "@example.com",  # Nombre de usuario máximo
            "usuario@" + "a" * 255 + ".com",  # Dominio extenso
        ]

        for email in edge_case_emails:
            response = authenticated_client.patch(update_url, {"email": email})
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
            ]


@pytest.mark.django_db
def test_complete_profile_update(authenticated_client, test_user):
    """
    Prueba de integración que verifica el flujo completo de actualización de perfil.
    Confirma que todos los campos permitidos se actualizan correctamente,
    persisten en la base de datos y que los campos protegidos no se modifican.
    """
    update_url = reverse("profile-update")

    # Datos originales a preservar para verificación posterior
    original_document = test_user.document
    original_first_name = test_user.first_name
    original_last_name = test_user.last_name
    original_address = test_user.address

    # Datos nuevos para la actualización
    new_data = {
        "email": "updated.email@example.com",
        "phone": "9876543210",  # 10 dígitos para cumplir con la validación
    }

    # Limpiar cualquier registro previo de actualizaciones
    UserUpdateLog.objects.filter(user=test_user).delete()

    # Realizar la actualización
    response = authenticated_client.patch(update_url, new_data)

    # Verificar respuesta exitosa
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"La actualización falló: {response.data}"
    assert "message" in response.data, "No se encontró mensaje de éxito en la respuesta"
    assert (
        "éxito" in response.data["message"].lower()
    ), f"Mensaje inesperado: {response.data['message']}"

    # Refrescar el objeto de usuario desde la base de datos
    test_user.refresh_from_db()

    # Verificar que los campos se actualizaron correctamente
    assert (
        test_user.email == new_data["email"]
    ), "El email no se actualizó correctamente"
    assert (
        test_user.phone == new_data["phone"]
    ), "El teléfono no se actualizó correctamente"

    # Verificar que los campos protegidos no cambiaron
    assert test_user.document == original_document, "El documento no debería cambiar"
    assert test_user.first_name == original_first_name, "El nombre no debería cambiar"
    assert test_user.last_name == original_last_name, "El apellido no debería cambiar"
    assert test_user.address == original_address, "La dirección no debería cambiar"

    # Verificar que se registró la actualización en el log
    update_log = UserUpdateLog.objects.get(user=test_user)
    assert (
        update_log.update_count == 1
    ), "El contador de actualizaciones no se incrementó correctamente"
