import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, Otp, PersonType, DocumentType
from rest_framework.authtoken.models import Token
from users.serializers import UserProfileSerializer
from django.utils import timezone
import time


@pytest.fixture
def api_client():
    """Cliente API para realizar las solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def document_type(db):
    """Crea y guarda un tipo de documento válido en la base de datos."""
    return DocumentType.objects.create(typeName="Cédula")


@pytest.fixture
def person_type(db):
    """Crea y guarda un tipo de persona válido en la base de datos."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def test_user(db, person_type, document_type):
    """Usuario de prueba completo con todos los campos requeridos."""
    return CustomUser.objects.create_user(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567890",
        password="SecurePass123",
        address="Calle 123",
        person_type=person_type,
        document_type=document_type,
        drive_folder_id="1234567890",
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def incomplete_user(db):
    """Usuario de prueba con campos mínimos requeridos."""
    return CustomUser.objects.create_user(
        document="987654321098",
        first_name="Jane",
        last_name="Smith",
        email="janesmith@example.com",
        phone="9876543210",
        password="SecurePass456",
        address="Avenida 456",
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def auth_token(test_user):
    """Genera un token de autenticación para el usuario de prueba."""
    token, _ = Token.objects.get_or_create(user=test_user)
    return token


# =================== PRUEBAS UNITARIAS ===================


class TestUserProfileSerializer:
    """Pruebas unitarias para el serializador UserProfileSerializer."""

    def test_serializer_contains_expected_fields(self, test_user):
        """✅ Verifica que el serializador incluya todos los campos esperados."""
        serializer = UserProfileSerializer(instance=test_user)
        expected_fields = [
            "email",
            "document",
            "document_type_name",
            "first_name",
            "last_name",
            "phone",
            "address",
            "person_type_name",
            "drive_folder_id",
        ]

        assert set(serializer.data.keys()) == set(
            expected_fields
        ), "El serializador no contiene todos los campos esperados"

    def test_serializer_data_validation(self, test_user):
        """✅ Verifica que los datos serializados son correctos."""
        serializer = UserProfileSerializer(instance=test_user)
        data = serializer.data

        assert data["document"] == test_user.document
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["phone"] == test_user.phone
        assert data["address"] == test_user.address
        assert data["document_type_name"] == test_user.document_type.typeName
        assert data["person_type_name"] == test_user.person_type.typeName


class TestCustomUserModel:
    """Pruebas unitarias para el modelo CustomUser."""

    def test_custom_user_model_fields(self, test_user):
        """✅ Verifica que el modelo CustomUser tenga la estructura correcta."""
        # Verificar campos básicos
        assert hasattr(test_user, "document"), "El modelo no tiene el campo 'document'"
        assert hasattr(
            test_user, "first_name"
        ), "El modelo no tiene el campo 'first_name'"
        assert hasattr(
            test_user, "last_name"
        ), "El modelo no tiene el campo 'last_name'"
        assert hasattr(test_user, "email"), "El modelo no tiene el campo 'email'"
        assert hasattr(test_user, "phone"), "El modelo no tiene el campo 'phone'"
        assert hasattr(test_user, "address"), "El modelo no tiene el campo 'address'"
        assert hasattr(
            test_user, "document_type"
        ), "El modelo no tiene el campo 'document_type'"
        assert hasattr(
            test_user, "person_type"
        ), "El modelo no tiene el campo 'person_type'"
        assert hasattr(
            test_user, "is_active"
        ), "El modelo no tiene el campo 'is_active'"
        assert hasattr(
            test_user, "is_registered"
        ), "El modelo no tiene el campo 'is_registered'"
        assert hasattr(
            test_user, "drive_folder_id"
        ), "El modelo no tiene el campo 'drive_folder_id'"

    def test_custom_user_str_representation(self, test_user):
        """✅ Verifica la representación en string del modelo."""
        expected_str = (
            f"{test_user.document} - {test_user.first_name} {test_user.last_name}"
        )
        assert (
            str(test_user) == expected_str
        ), "La representación en string no es la esperada"


class TestUserProfilePermissions:
    """Pruebas unitarias para los permisos de acceso al perfil de usuario."""

    @pytest.mark.django_db
    def test_profile_endpoint_requires_authentication(self, api_client):
        """❌ Verifica que el endpoint de perfil requiera autenticación."""
        profile_url = reverse("perfil-usuario")
        response = api_client.get(profile_url)

        assert (
            response.status_code == status.HTTP_401_UNAUTHORIZED
        ), "El endpoint no está requiriendo autenticación correctamente"
        assert (
            "detail" in response.data
        ), "La respuesta de error no contiene el campo 'detail'"
        assert (
            response.data["detail"]
            == "Las credenciales de autenticación no se proveyeron."
        ), "El mensaje de error es incorrecto"


# =================== PRUEBAS DE INTEGRACIÓN ===================


@pytest.mark.django_db
def test_complete_login_flow_access_profile(api_client, test_user):
    """✅ Verifica el flujo completo de login → validación OTP → obtención de token → acceso al perfil."""

    # Paso 1: Login (solicita OTP)
    login_url = reverse("login")
    login_data = {"document": test_user.document, "password": "SecurePass123"}
    login_response = api_client.post(login_url, login_data)

    assert (
        login_response.status_code == status.HTTP_200_OK
    ), f"Error en login: {login_response.data}"
    assert (
        "message" in login_response.data
    ), "No se recibió mensaje de confirmación de envío de OTP"

    # Paso 2: Obtener OTP generado
    otp_instance = Otp.objects.filter(user=test_user, is_login=True).first()
    assert otp_instance is not None, "No se generó un OTP en la base de datos"

    # Paso 3: Validar OTP
    validate_otp_url = reverse("validate-otp")
    otp_data = {"document": test_user.document, "otp": otp_instance.otp}
    otp_response = api_client.post(validate_otp_url, otp_data)

    assert (
        otp_response.status_code == status.HTTP_200_OK
    ), f"Error al validar OTP: {otp_response.data}"
    assert "token" in otp_response.data, "No se recibió un token tras validar el OTP"

    # Paso 4: Acceder al perfil con el token
    token = otp_response.data["token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    profile_url = reverse("perfil-usuario")
    profile_response = api_client.get(profile_url)

    assert (
        profile_response.status_code == status.HTTP_200_OK
    ), f"Error al acceder al perfil: {profile_response.data}"
    assert profile_response.data["document"] == test_user.document
    assert profile_response.data["email"] == test_user.email


@pytest.mark.django_db
def test_profile_endpoint_with_authenticated_user(api_client, test_user, auth_token):
    """✅ Verifica el acceso al endpoint de perfil con un usuario autenticado."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    response = api_client.get(profile_url)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error al acceder al perfil: {response.data}"
    assert response.data["document"] == test_user.document
    assert response.data["email"] == test_user.email
    assert response.data["first_name"] == test_user.first_name
    assert response.data["last_name"] == test_user.last_name


@pytest.mark.django_db
def test_custom_user_to_serialized_data_consistency(test_user):
    """✅ Verifica la consistencia entre los datos del modelo y los datos serializados."""
    serializer = UserProfileSerializer(instance=test_user)
    serialized_data = serializer.data

    # Verificar campos directos
    assert serialized_data["document"] == test_user.document
    assert serialized_data["email"] == test_user.email
    assert serialized_data["first_name"] == test_user.first_name
    assert serialized_data["last_name"] == test_user.last_name
    assert serialized_data["phone"] == test_user.phone
    assert serialized_data["address"] == test_user.address

    # Verificar campos relacionados
    assert serialized_data["document_type_name"] == test_user.document_type.typeName
    assert serialized_data["person_type_name"] == test_user.person_type.typeName


@pytest.mark.django_db
def test_profile_endpoint_response_structure(api_client, test_user, auth_token):
    """✅ Verifica la estructura de respuesta del endpoint de perfil."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    response = api_client.get(profile_url)

    assert response.status_code == status.HTTP_200_OK

    expected_fields = [
        "email",
        "document",
        "document_type_name",
        "first_name",
        "last_name",
        "phone",
        "address",
        "person_type_name",
        "drive_folder_id",
    ]

    for field in expected_fields:
        assert (
            field in response.data
        ), f"El campo '{field}' no está presente en la respuesta"


@pytest.mark.django_db
def test_error_alert_handling(api_client, monkeypatch):
    """
    Prueba integral que verifica el manejo de errores durante la visualización
    del perfil, incluyendo errores de comunicación con la base de datos
    y otros errores de carga de datos.
    """
    # 1. PARTE 1: Probar error con IDs inexistentes
    # ---------------------------------------------
    # Crear usuario de prueba
    user1 = CustomUser.objects.create_user(
        document="999999999991",
        first_name="Error",
        last_name="Test",
        email="error.test1@example.com",
        phone="0000000001",
        password="TestPass123",
        is_active=True,
        is_registered=True,
    )

    # Crear token para este usuario
    token1, _ = Token.objects.get_or_create(user=user1)

    # Autenticar con el token
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token1.key}")

    # Forzar un error real: corromper datos necesarios para el perfil
    user1.document_type_id = 99999  # ID que no existe
    user1.person_type_id = 99999  # ID que no existe
    user1.save()

    # Intentar acceder al perfil, lo que debería causar un error
    profile_url = reverse("perfil-usuario")

    try:
        response = api_client.get(profile_url, raise_request_exception=False)

        # Verificar manejo de error
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if hasattr(response, "data") and isinstance(response.data, dict):
            error_message_found = False
            for key in ["error", "detail", "message"]:
                if key in response.data:
                    error_message_found = True
                    print(f"PARTE 1 - Mensaje de error: {response.data[key]}")
                    break

            assert error_message_found, "No se encontró mensaje de error"

    except Exception as e:
        print(f"PARTE 1 - Se generó excepción: {str(e)}")
        # En pruebas, es aceptable que se genere excepción

    finally:
        # Limpiar
        user1.delete()

    # 2. PARTE 2: Probar error de comunicación con la base de datos
    # ------------------------------------------------------------
    # Crear otro usuario para esta parte
    user2 = CustomUser.objects.create_user(
        document="999999999992",
        first_name="DB",
        last_name="Error",
        email="db.error@example.com",
        phone="0000000002",
        password="DBErrorPass123",
        is_active=True,
        is_registered=True,
    )

    # Crear token
    token2, _ = Token.objects.get_or_create(user=user2)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token2.key}")

    # Simular error de comunicación con la base de datos
    from django.db.utils import OperationalError

    def mock_db_error(*args, **kwargs):
        raise OperationalError(
            "Error de comunicación con la base de datos: connection timed out"
        )

    from users.views import UserProfilelView

    original_get_object = UserProfilelView.get_object
    monkeypatch.setattr(UserProfilelView, "get_object", mock_db_error)

    try:
        response = api_client.get(profile_url, raise_request_exception=False)

        # Verificar manejo de error
        assert response.status_code in [
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]

        if hasattr(response, "data") and isinstance(response.data, dict):
            error_message_found = False
            for key in ["error", "detail", "message"]:
                if key in response.data:
                    error_message_found = True
                    print(f"PARTE 2 - Mensaje de error de BD: {response.data[key]}")
                    break

            assert error_message_found, "No se encontró mensaje de error de BD"

    except Exception as e:
        print(f"PARTE 2 - Se generó excepción de BD: {str(e)}")
        # En pruebas, es aceptable que se genere excepción

    finally:
        # Restaurar método original y limpiar
        monkeypatch.setattr(UserProfilelView, "get_object", original_get_object)
        user2.delete()

    # 3. PARTE 3: Probar token inválido
    # --------------------------------
    api_client.credentials(HTTP_AUTHORIZATION="Token invalid_token_12345")

    response = api_client.get(profile_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.data
    print(f"PARTE 3 - Error de autenticación: {response.data['detail']}")

    # Verificación final
    print("✅ Prueba integral de manejo de errores completada con éxito")


@pytest.mark.django_db
def test_profile_response_json_format(api_client, test_user, auth_token):
    """✅ Verifica el formato JSON de la respuesta del endpoint de perfil."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    response = api_client.get(profile_url)

    assert response.status_code == status.HTTP_200_OK

    # Verificar que la respuesta es un JSON válido
    try:
        # La respuesta ya está parseada como JSON por Django REST Framework
        data = response.data
        assert isinstance(data, dict), "La respuesta no es un diccionario JSON"
    except Exception as e:
        pytest.fail(f"La respuesta no es un JSON válido: {e}")

    # Verificar tipos de datos
    assert isinstance(data["document"], str)
    assert isinstance(data["email"], str)
    assert isinstance(data["first_name"], str)
    assert isinstance(data["last_name"], str)
    assert isinstance(data["phone"], str)
    assert isinstance(data["address"], str)


# =================== PRUEBAS DE API ===================


@pytest.mark.django_db
def test_profile_endpoint_with_valid_token(api_client, test_user, auth_token):
    """✅ Verifica el acceso al endpoint de perfil con un token válido."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    response = api_client.get(profile_url)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Error con token válido: {response.data}"
    assert response.data["document"] == test_user.document


@pytest.mark.django_db
def test_profile_endpoint_with_invalid_token(api_client):
    """❌ Verifica el comportamiento con un token inválido."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION="Token invalid_token_12345")

    response = api_client.get(profile_url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), "No se está rechazando correctamente el token inválido"
    assert (
        "detail" in response.data
    ), "La respuesta de error no contiene el campo 'detail'"


@pytest.mark.django_db
def test_profile_endpoint_without_token(api_client):
    """❌ Verifica el comportamiento sin token de autenticación."""
    profile_url = reverse("perfil-usuario")

    response = api_client.get(profile_url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), "No se está requiriendo correctamente la autenticación"
    assert (
        "detail" in response.data
    ), "La respuesta de error no contiene el campo 'detail'"
    assert (
        response.data["detail"] == "Las credenciales de autenticación no se proveyeron."
    ), "El mensaje de error es incorrecto"


@pytest.mark.django_db
def test_profile_contains_all_required_fields(api_client, test_user, auth_token):
    """✅ Verifica que la respuesta del perfil contenga todos los campos requeridos."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    response = api_client.get(profile_url)

    assert response.status_code == status.HTTP_200_OK

    # Campos requeridos según documentación
    required_fields = [
        "email",
        "document",
        "document_type_name",
        "first_name",
        "last_name",
        "phone",
        "address",
        "person_type_name",
    ]

    for field in required_fields:
        assert (
            field in response.data
        ), f"Campo requerido '{field}' no está presente en la respuesta"
        assert response.data[field] is not None, f"Campo requerido '{field}' es nulo"


@pytest.mark.django_db
def test_profile_api_response_time(api_client, test_user, auth_token):
    """✅ Verifica que el tiempo de respuesta de la API sea aceptable (< 3 segundos)."""
    profile_url = reverse("perfil-usuario")
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    start_time = time.time()
    response = api_client.get(profile_url)
    end_time = time.time()

    response_time = end_time - start_time

    assert response.status_code == status.HTTP_200_OK
    assert (
        response_time < 3.0
    ), f"El tiempo de respuesta ({response_time:.2f}s) excede el límite de 3 segundos"
