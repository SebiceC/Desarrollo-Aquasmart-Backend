import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser
from rest_framework.authtoken.models import Token
from django.utils import timezone


@pytest.fixture
def api_client():
    """Cliente API para realizar las solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Usuario de prueba ya registrado en la base de datos."""
    return CustomUser.objects.create_user(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567890",
        password="SecurePass123@",
        address="Calle 123",
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Cliente API autenticado manualmente."""
    # Crear token manualmente
    token, _ = Token.objects.get_or_create(user=test_user)

    # Configurar cliente con token
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    return api_client


class TestPasswordUpdate:
    """
    Test suite para probar la funcionalidad de actualización de contraseña.
    """

    # Pruebas de Validación de Entrada
    @pytest.mark.django_db
    def test_password_validation_success(self, authenticated_client, test_user):
        """Prueba la validación exitosa de la contraseña actual y nueva."""
        url = reverse("change-password")

        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456@",
            "confirm_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        assert "Actualización de contraseña exitosa" in response.data["message"]

        # Verificar que la contraseña fue realmente actualizada
        test_user.refresh_from_db()
        assert test_user.check_password("NewSecurePass456@")

    @pytest.mark.django_db
    def test_password_validation_incorrect_current(self, authenticated_client):
        """Prueba el rechazo cuando la contraseña actual es incorrecta."""
        url = reverse("change-password")

        data = {
            "current_password": "WrongPassword123@",
            "new_password": "NewSecurePass456@",
            "confirm_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "current_password" in response.data
        assert "incorrecta" in response.data["current_password"][0].lower()

    @pytest.mark.django_db
    def test_password_validation_format(self, authenticated_client):
        """Prueba la validación del formato de la nueva contraseña."""
        url = reverse("change-password")

        # Caso 1: Sin mayúsculas
        data = {
            "current_password": "SecurePass123@",
            "new_password": "newsecurepass456@",
            "confirm_password": "newsecurepass456@",
        }

        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

        # Caso 2: Sin minúsculas
        data = {
            "current_password": "SecurePass123@",
            "new_password": "NEWSECUREPASS456@",
            "confirm_password": "NEWSECUREPASS456@",
        }

        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

        # Caso 3: Sin números
        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass@",
            "confirm_password": "NewSecurePass@",
        }

        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

        # Caso 4: Sin caracteres especiales
        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456",
            "confirm_password": "NewSecurePass456",
        }

        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

        # Caso 5: Contraseña demasiado corta
        data = {
            "current_password": "SecurePass123@",
            "new_password": "Short1@",
            "confirm_password": "Short1@",
        }

        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

    @pytest.mark.django_db
    def test_password_validation_same_as_current(self, authenticated_client):
        """Prueba el rechazo cuando la nueva contraseña es igual a la actual."""
        url = reverse("change-password")

        data = {
            "current_password": "SecurePass123@",
            "new_password": "SecurePass123@",
            "confirm_password": "SecurePass123@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data
        assert "igual a la actual" in response.data["new_password"][0].lower()

    @pytest.mark.django_db
    def test_password_validation_mismatch(self, authenticated_client):
        """Prueba el rechazo cuando la nueva contraseña y la confirmación no coinciden."""
        url = reverse("change-password")

        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456@",
            "confirm_password": "DifferentPass789@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "confirm_password" in response.data
        assert "no coinciden" in response.data["confirm_password"][0].lower()

    # Pruebas de Flujo y Comportamiento
    @pytest.mark.django_db
    def test_unauthorized_access(self, api_client):
        """Prueba el acceso no autorizado al endpoint de cambio de contraseña."""
        url = reverse("change-password")

        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456@",
            "confirm_password": "NewSecurePass456@",
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_missing_fields(self, authenticated_client):
        """Prueba el manejo de campos faltantes en la solicitud."""
        url = reverse("change-password")

        # Falta campo current_password
        data = {
            "new_password": "NewSecurePass456@",
            "confirm_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "current_password" in response.data

        # Falta campo new_password
        data = {
            "current_password": "SecurePass123@",
            "confirm_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

        # Falta campo confirm_password
        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "confirm_password" in response.data

    # Pruebas de Seguridad e Integridad
    @pytest.mark.django_db
    def test_authentication_with_new_password(self, authenticated_client, test_user):
        """Prueba que el usuario puede iniciar sesión con la nueva contraseña después de actualizarla."""
        # Primero cambiar la contraseña
        change_url = reverse("change-password")

        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456@",
            "confirm_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(change_url, data)
        assert response.status_code == status.HTTP_200_OK

        # Comprobar que la contraseña se ha actualizado
        test_user.refresh_from_db()
        assert test_user.check_password("NewSecurePass456@")

    @pytest.mark.django_db
    def test_authentication_with_old_password_fails(
        self, authenticated_client, test_user
    ):
        """Prueba que el usuario no puede iniciar sesión con la contraseña antigua después de actualizarla."""
        # Primero cambiar la contraseña
        change_url = reverse("change-password")

        data = {
            "current_password": "SecurePass123@",
            "new_password": "NewSecurePass456@",
            "confirm_password": "NewSecurePass456@",
        }

        response = authenticated_client.post(change_url, data)
        assert response.status_code == status.HTTP_200_OK

        # Comprobar que la contraseña antigua ya no funciona
        test_user.refresh_from_db()
        assert not test_user.check_password("SecurePass123@")
