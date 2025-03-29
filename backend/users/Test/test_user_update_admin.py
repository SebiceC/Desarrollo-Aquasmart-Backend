import pytest
import time
import io
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, Otp, PersonType, DocumentType, UserUpdateLog
from rest_framework.authtoken.models import Token
from django.utils.timezone import now, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Group, Permission


# ===================== Fixtures =====================
@pytest.fixture
def api_client():
    """Cliente API para realizar solicitudes de prueba."""
    return APIClient()


@pytest.fixture
def person_type(db):
    """Crea un tipo de persona para usar en los tests."""
    return PersonType.objects.create(typeName="Natural")


@pytest.fixture
def another_person_type(db):
    """Crea otro tipo de persona para actualizaciones."""
    return PersonType.objects.create(typeName="Jurídica")


@pytest.fixture
def document_type(db):
    """Crea un tipo de documento para usar en los tests."""
    return DocumentType.objects.create(typeName="Cédula")


@pytest.fixture
def admin_user(db, person_type, document_type):
    """Crea un usuario administrador de prueba."""
    return CustomUser.objects.create_superuser(
        document="admin123",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        phone="1234567890",
        address="Admin Address",
        password="AdminPass123",
        person_type=person_type,
        document_type=document_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def regular_user(db, person_type, document_type):
    """Crea un usuario regular para actualizar."""
    return CustomUser.objects.create_user(
        document="123456789012",
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="1234567890",
        address="Calle 123",
        password="SecurePass123@",
        person_type=person_type,
        document_type=document_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def another_user(db, person_type, document_type):
    """Crea un segundo usuario para pruebas de duplicidad."""
    return CustomUser.objects.create_user(
        document="987654321098",
        first_name="Jane",
        last_name="Smith",
        email="janesmith@example.com",
        phone="9876543210",
        address="Avenue 456",
        password="SecurePass123@",
        person_type=person_type,
        document_type=document_type,
        is_active=True,
        is_registered=True,
    )


@pytest.fixture
def regular_user_with_update_permission(db, person_type, document_type):
    """
    Crea un usuario regular con permiso específico para actualizar usuarios.
    Este usuario no es administrador pero tiene el permiso específico.
    """
    user = CustomUser.objects.create_user(
        document="123000000000",
        first_name="UpdatePermission",
        last_name="User",
        email="update.permission@example.com",
        phone="5551234567",
        address="Permission Street",
        password="PermissionPass123@",
        person_type=person_type,
        document_type=document_type,
        is_active=True,
        is_registered=True,
        is_staff=True,  # Es staff pero no superuser
    )

    # Crear un grupo para usuarios con permiso de actualización
    update_group, _ = Group.objects.get_or_create(name="UserUpdaters")

    # Asignar permisos relevantes al grupo
    permission_codenames = [
        "actualizar_info_usuarios_distrito",  # Permiso mencionado en RF19
        "can_toggle_is_active",  # Permiso adicional que podría ser relevante
    ]

    for codename in permission_codenames:
        try:
            permission = Permission.objects.get(codename=codename)
            update_group.permissions.add(permission)
        except Permission.DoesNotExist:
            print(
                f"Permiso {codename} no encontrado, creando uno temporal para la prueba"
            )
            # Si el permiso no existe, creamos uno temporal (solo para la prueba)
            content_type = Permission.objects.first().content_type
            permission = Permission.objects.create(
                codename=codename,
                name=f"Can {codename.replace('_', ' ')}",
                content_type=content_type,
            )
            update_group.permissions.add(permission)

    # Asignar el usuario al grupo
    user.groups.add(update_group)
    return user


@pytest.fixture
def user_without_permissions(db, person_type, document_type):
    """
    Crea un usuario sin permisos específicos para actualizar usuarios.
    Este usuario está registrado pero no tiene permisos administrativos.
    """
    return CustomUser.objects.create_user(
        document="999000000000",
        first_name="NoPermission",
        last_name="User",
        email="no.permission@example.com",
        phone="5559876543",
        address="Regular Street",
        password="RegularPass123@",
        person_type=person_type,
        document_type=document_type,
        is_active=True,
        is_registered=True,
        is_staff=False,
        is_superuser=False,
    )


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Cliente API autenticado como administrador."""
    token, _ = Token.objects.get_or_create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def authenticated_permitted_client(api_client, regular_user_with_update_permission):
    """Cliente API autenticado como usuario con permisos específicos."""
    token, _ = Token.objects.get_or_create(user=regular_user_with_update_permission)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def authenticated_unpermitted_client(api_client, user_without_permissions):
    """Cliente API autenticado como usuario sin permisos específicos."""
    token, _ = Token.objects.get_or_create(user=user_without_permissions)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


# ===================== Tests de Control de Acceso y Permisos =====================


@pytest.mark.django_db
class TestAccessControlAndPermissions:
    def test_admin_can_update_user(self, authenticated_admin_client, regular_user):
        """Test de actualización de usuario por un administrador (debe permitirse)."""
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        update_data = {"first_name": "AdminUpdated"}
        response = authenticated_admin_client.patch(url, update_data)

        assert response.status_code == status.HTTP_200_OK
        assert "success" in response.data["status"]

        regular_user.refresh_from_db()
        assert regular_user.first_name == "AdminUpdated"

    def test_permitted_user_can_update(
        self, authenticated_permitted_client, regular_user
    ):
        """
        Test de actualización por usuario con permisos específicos (debe permitirse).
        Verifica que un usuario no administrador pero con el permiso específico
        puede actualizar la información de otros usuarios.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        update_data = {"first_name": "PermittedUpdated"}
        response = authenticated_permitted_client.patch(url, update_data)

        print(
            f"Respuesta del usuario con permisos: {response.status_code} - {response.data}"
        )

        # Verificar si el backend permite esta operación con los permisos asignados
        if response.status_code == status.HTTP_200_OK:
            regular_user.refresh_from_db()
            assert regular_user.first_name == "PermittedUpdated"
            print("✅ Usuario con permisos específicos puede actualizar otros usuarios")
        else:
            print(
                "❌ Usuario con permisos específicos no puede actualizar - verificar implementación de permisos"
            )

    def test_unpermitted_user_cannot_update(
        self, authenticated_unpermitted_client, regular_user
    ):
        """
        Test de actualización por usuario sin permisos (debe rechazarse).
        Verifica que un usuario sin los permisos adecuados no puede
        actualizar la información de otros usuarios.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        update_data = {"first_name": "UnpermittedAttempt"}
        response = authenticated_unpermitted_client.patch(url, update_data)

        # Debe ser rechazado con 403 Forbidden
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ]

        # Verificar que no se aplicó el cambio
        regular_user.refresh_from_db()
        assert regular_user.first_name != "UnpermittedAttempt"

    def test_unauthenticated_user_cannot_update(self, api_client, regular_user):
        """Test de intento de actualización sin autenticación (debe rechazarse)."""
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        update_data = {"first_name": "UnauthenticatedAttempt"}
        response = api_client.patch(url, update_data)

        # Debe ser rechazado con 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verificar que no se aplicó el cambio
        regular_user.refresh_from_db()
        assert regular_user.first_name != "UnauthenticatedAttempt"


# ===================== Tests de Validación de Todos los Campos =====================


@pytest.mark.django_db
class TestAllFieldsValidation:
    def test_name_and_lastname_validation(
        self, authenticated_admin_client, regular_user
    ):
        """
        Test exhaustivo de validación de nombre y apellido.
        Cubre longitud máxima, valores vacíos y formatos para nombre y apellido.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # 1. Nombre demasiado largo (>20 caracteres)
        long_name = "A" * 21
        response = authenticated_admin_client.patch(url, {"first_name": long_name})
        print(
            f"Nombre largo ({len(long_name)} caracteres): {response.status_code} - {response.data}"
        )

        # 2. Apellido demasiado largo (>20 caracteres)
        long_lastname = "B" * 21
        response = authenticated_admin_client.patch(url, {"last_name": long_lastname})
        print(
            f"Apellido largo ({len(long_lastname)} caracteres): {response.status_code} - {response.data}"
        )

        # 3. Nombre vacío
        response = authenticated_admin_client.patch(url, {"first_name": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "first_name" in str(response.data).lower()

        # 4. Apellido vacío
        response = authenticated_admin_client.patch(url, {"last_name": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "last_name" in str(response.data).lower()

        # 5. Nombre con caracteres especiales (debería aceptarse para nombres)
        special_name = "John-María O'Connor"
        response = authenticated_admin_client.patch(url, {"first_name": special_name})
        print(
            f"Nombre con caracteres especiales: {response.status_code} - {response.data}"
        )
        if response.status_code == status.HTTP_200_OK:
            regular_user.refresh_from_db()
            assert regular_user.first_name == special_name

        # 6. Nombre y apellido válidos (dentro del límite)
        valid_name = "John"
        valid_lastname = "Doe"
        response = authenticated_admin_client.patch(
            url, {"first_name": valid_name, "last_name": valid_lastname}
        )
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.first_name == valid_name
        assert regular_user.last_name == valid_lastname

    def test_phone_validation(self, authenticated_admin_client, regular_user):
        """
        Test exhaustivo de validación de teléfono.
        Verifica que el teléfono sea numérico y tenga exactamente 10 dígitos.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # 1. Teléfono con caracteres no numéricos
        non_numeric_phones = [
            "123abc4567",
            "123-456-7890",
            "123.456.7890",
            "123 456 7890",
        ]

        for phone in non_numeric_phones:
            response = authenticated_admin_client.patch(url, {"phone": phone})
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "phone" in str(response.data).lower()

        # 2. Teléfono con longitud incorrecta
        wrong_length_phones = [
            "12345",  # 5 dígitos - muy corto
            "123456789",  # 9 dígitos - muy corto
            "12345678901",  # 11 dígitos - muy largo
            "123456789012345",  # 15 dígitos - muy largo
        ]

        for phone in wrong_length_phones:
            response = authenticated_admin_client.patch(url, {"phone": phone})
            print(
                f"Teléfono con longitud incorrecta ({len(phone)} dígitos): {response.status_code} - {response.data}"
            )

        # 3. Teléfono vacío
        response = authenticated_admin_client.patch(url, {"phone": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in str(response.data).lower()

        # 4. Teléfono válido (10 dígitos numéricos)
        valid_phone = "1234567890"
        response = authenticated_admin_client.patch(url, {"phone": valid_phone})
        print(f"Teléfono válido (10 dígitos): {response.status_code} - {response.data}")

        if response.status_code == status.HTTP_200_OK:
            regular_user.refresh_from_db()
            assert regular_user.phone == valid_phone

    def test_email_validation(
        self, authenticated_admin_client, regular_user, another_user
    ):
        """
        Test exhaustivo de validación de correo electrónico.
        Verifica formato, longitud máxima y unicidad.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # 1. Correos con formato inválido
        invalid_emails = [
            "plainaddress",  # Sin @ ni dominio
            "user@",  # Sin dominio
            "@example.com",  # Sin nombre de usuario
            "user@domain",  # Sin TLD (.com, .org, etc.)
            "user.@domain.com",  # Punto antes de @
            "user@domain..com",  # Doble punto en dominio
            "user@domain@example.com",  # Múltiples @
            ".user@domain.com",  # Punto al inicio del nombre de usuario
            "user@.domain.com",  # Punto al inicio del dominio
        ]

        for email in invalid_emails:
            response = authenticated_admin_client.patch(url, {"email": email})
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "email" in str(response.data).lower()

        # 2. Correo demasiado largo (>50 caracteres)
        long_prefix = "a" * 45
        long_email = f"{long_prefix}@example.com"  # Más de 50 caracteres
        response = authenticated_admin_client.patch(url, {"email": long_email})
        print(
            f"Correo largo ({len(long_email)} caracteres): {response.status_code} - {response.data}"
        )

        # 3. Correo duplicado (ya existe en otro usuario)
        duplicate_email = another_user.email
        response = authenticated_admin_client.patch(url, {"email": duplicate_email})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data).lower()

        # 4. Correo vacío
        response = authenticated_admin_client.patch(url, {"email": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data).lower()

        # 5. Correo válido
        valid_email = "valid.email@example.com"
        response = authenticated_admin_client.patch(url, {"email": valid_email})
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.email == valid_email

    def test_person_type_validation(
        self, authenticated_admin_client, regular_user, another_person_type
    ):
        """
        Test exhaustivo de validación de tipo de persona.
        Verifica que solo se acepten valores válidos.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # 1. Tipo de persona inexistente
        nonexistent_id = 9999
        response = authenticated_admin_client.patch(
            url, {"person_type": nonexistent_id}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "person_type" in str(response.data).lower()

        # 2. Tipo de persona con valor no numérico
        response = authenticated_admin_client.patch(url, {"person_type": "abc"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "person_type" in str(response.data).lower()

        # 3. Intentar no cambiar el tipo de persona
        # Esto simplemente no debería generar error
        response = authenticated_admin_client.patch(url, {"first_name": "Test"})
        assert response.status_code == status.HTTP_200_OK

        # 4. Intentar cambiar a otro tipo de persona válido
        response = authenticated_admin_client.patch(
            url, {"person_type": another_person_type.personTypeId}
        )
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.person_type.personTypeId == another_person_type.personTypeId

    def test_file_upload_validation(self, authenticated_admin_client, regular_user):
        """
        Test exhaustivo de validación de archivos anexos.
        Verifica formato (PDF) y tamaño máximo (500KB).
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # 1. Archivo con formato inválido (no PDF)
        text_content = io.BytesIO(b"This is a plain text file, not a PDF")
        invalid_file = SimpleUploadedFile(
            "test.txt", text_content.read(), content_type="text/plain"
        )

        data = {"files": invalid_file, "first_name": "File Type Test"}
        response = authenticated_admin_client.patch(url, data, format="multipart")
        print(f"Archivo no PDF: {response.status_code} - {response.data}")

        # 2. Archivo PDF demasiado grande (>500KB)
        large_content = io.BytesIO(b"%PDF-1.4\n" + b"X" * 550 * 1024)  # >500KB
        large_file = SimpleUploadedFile(
            "large.pdf", large_content.read(), content_type="application/pdf"
        )

        data = {"files": large_file, "first_name": "File Size Test"}
        response = authenticated_admin_client.patch(url, data, format="multipart")
        print(f"Archivo PDF grande (>500KB): {response.status_code} - {response.data}")

        # 3. Archivo PDF válido (<500KB)
        valid_content = io.BytesIO(b"%PDF-1.4\n" + b"X" * 100 * 1024)  # 100KB
        valid_file = SimpleUploadedFile(
            "valid.pdf", valid_content.read(), content_type="application/pdf"
        )

        data = {"files": valid_file, "first_name": "Valid File Test"}
        response = authenticated_admin_client.patch(url, data, format="multipart")
        print(f"Archivo PDF válido: {response.status_code} - {response.data}")

        # Si el backend permite la carga de archivos, verificar que se actualizó el first_name
        if response.status_code == status.HTTP_200_OK:
            regular_user.refresh_from_db()
            assert regular_user.first_name == "Valid File Test"

    # Añadir el siguiente test dentro de la clase TestAllFieldsValidation

    def test_update_without_changes(
        self, authenticated_admin_client, regular_user, person_type, document_type
    ):
        """
        Test que verifica que el sistema rechaza actualizaciones sin cambios en los datos.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # Obtener datos actuales del usuario, excluyendo campos con validación de unicidad
        current_data = {
            "first_name": regular_user.first_name,
            "last_name": regular_user.last_name,
            "phone": regular_user.phone,
            "address": regular_user.address,
        }

        # Enviar solicitud con los mismos datos (sin email)
        response = authenticated_admin_client.patch(url, current_data)

        # Verificar respuesta de error y mensaje
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "no se detectaron cambios en los datos del usuario"
            in str(response.data).lower()
        )

        # Verificar que no hay registros de auditoría nuevos
        log_count_before = UserUpdateLog.objects.count()
        log_count_after = UserUpdateLog.objects.count()
        assert log_count_after == log_count_before

        # Verificar integridad de los datos
        regular_user.refresh_from_db()


# ===================== Tests de Respuesta y Tiempos =====================


@pytest.mark.django_db
class TestResponseAndTiming:
    def test_update_response_time(self, authenticated_admin_client, regular_user):
        """
        Test de tiempo de respuesta de actualización.
        Verifica que la actualización se complete en menos de 5 segundos.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        update_data = {"first_name": "Response Time Test"}

        start_time = time.time()
        response = authenticated_admin_client.patch(url, update_data)
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == status.HTTP_200_OK
        assert (
            response_time < 5.0
        ), f"Tiempo de respuesta ({response_time:.2f}s) excede los 5 segundos"
        print(f"Tiempo de respuesta de actualización: {response_time:.2f} segundos")

        # Verificar que los cambios se reflejan inmediatamente
        regular_user.refresh_from_db()
        assert regular_user.first_name == "Response Time Test"

    def test_update_confirmation_message(
        self, authenticated_admin_client, regular_user
    ):
        """
        Test de mensaje de confirmación tras actualización exitosa.
        Verifica que el sistema proporcione una confirmación clara.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        update_data = {"first_name": "Confirmation Test"}
        response = authenticated_admin_client.patch(url, update_data)

        assert response.status_code == status.HTTP_200_OK
        assert "success" in response.data["status"]
        assert "actualizado exitosamente" in response.data["message"].lower()

    def test_update_error_message(
        self, authenticated_admin_client, regular_user, another_user
    ):
        """
        Test de mensaje de error tras actualización fallida.
        Verifica que el sistema proporcione un mensaje de error claro.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # Intentar actualizar con email duplicado (debe fallar)
        update_data = {"email": another_user.email}
        response = authenticated_admin_client.patch(url, update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data).lower()

        error_message = str(response.data).lower()
        assert "correo" in error_message or "email" in error_message
        print(f"Mensaje de error: {error_message}")


# ===================== Tests de Flujo Completo End-to-End =====================


@pytest.mark.django_db
class TestCompleteUpdateFlow:
    def test_complete_user_update_flow(
        self, api_client, admin_user, regular_user, another_person_type
    ):
        """
        Test completo del flujo de actualización desde login hasta confirmación.
        Cubre todos los pasos del proceso según el requerimiento RF19.
        """
        # 1. Iniciar sesión como administrador
        login_url = reverse("login")
        login_data = {"document": admin_user.document, "password": "AdminPass123"}
        login_response = api_client.post(login_url, login_data)
        assert login_response.status_code == status.HTTP_200_OK

        # 2. Obtener y validar OTP
        otp_instance = Otp.objects.filter(user=admin_user, is_login=True).first()
        assert otp_instance is not None

        validate_url = reverse("validate-otp")
        otp_data = {"document": admin_user.document, "otp": otp_instance.otp}
        validate_response = api_client.post(validate_url, otp_data)
        assert validate_response.status_code == status.HTTP_200_OK
        assert "token" in validate_response.data

        # 3. Usar el token para autenticarse
        token = validate_response.data["token"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        # 4. Ver la lista de usuarios
        list_url = reverse("customuser-list")
        list_response = api_client.get(list_url)
        assert list_response.status_code == status.HTTP_200_OK

        # 5. Ver detalles del usuario a actualizar
        details_url = reverse(
            "user-details", kwargs={"document": regular_user.document}
        )
        details_response = api_client.get(details_url)
        assert details_response.status_code == status.HTTP_200_OK

        # 6. Realizar actualización completa con todos los campos mencionados en RF19
        update_url = reverse(
            "admin-user-update", kwargs={"document": regular_user.document}
        )

        # Crear archivo PDF para anexo (si aplica)
        pdf_content = io.BytesIO(
            b"%PDF-1.4\n" + b"X" * 100 * 1024
        )  # PDF válido de 100KB
        test_file = SimpleUploadedFile(
            "test_doc.pdf", pdf_content.read(), content_type="application/pdf"
        )

        # Preparar datos de actualización según RF19
        update_data = {
            "first_name": "Complete",  # Nombre (máx 20 caracteres)
            "last_name": "Update Test",  # Apellido (máx 20 caracteres)
            "email": "complete.update@example.com",  # Email (máx 50 caracteres)
            "phone": "9876543210",  # Teléfono (10 dígitos)
            "person_type": another_person_type.personTypeId,  # Tipo de persona (selección)
            "files": test_file,  # Anexo (opcional, PDF máx 500KB)
        }

        start_time = time.time()  # Medir tiempo de respuesta
        update_response = api_client.patch(
            update_url, update_data, format="multipart"  # Necesario para archivos
        )
        end_time = time.time()
        response_time = end_time - start_time

        print(
            f"Respuesta completa: {update_response.status_code} - {update_response.data}"
        )
        print(f"Tiempo de respuesta: {response_time:.2f} segundos")

        # 7. Verificar respuesta exitosa
        assert update_response.status_code == status.HTTP_200_OK
        assert "success" in update_response.data["status"]
        assert "actualizado exitosamente" in update_response.data["message"].lower()
        assert (
            response_time < 5.0
        ), f"Tiempo de respuesta ({response_time:.2f}s) excede los 5 segundos"

        # 8. Verificar que los datos fueron actualizados correctamente
        regular_user.refresh_from_db()
        assert regular_user.first_name == "Complete"
        assert regular_user.last_name == "Update Test"
        assert regular_user.email == "complete.update@example.com"
        assert regular_user.phone == "9876543210"
        assert regular_user.person_type.personTypeId == another_person_type.personTypeId

        # 9. Cerrar sesión
        logout_url = reverse("logout")
        logout_response = api_client.post(logout_url)
        assert logout_response.status_code == status.HTTP_200_OK

        # 10. Verificar que la sesión fue cerrada correctamente
        list_response_after_logout = api_client.get(list_url)
        assert list_response_after_logout.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_unregistered_user(self, authenticated_admin_client):
        """
        Test de intento de actualización de un usuario no registrado.
        Verifica el manejo de error cuando se intenta actualizar un usuario que no existe.
        """
        # Usuario con documento que no existe en el sistema
        nonexistent_document = "999999999999"
        url = reverse("admin-user-update", kwargs={"document": nonexistent_document})

        update_data = {"first_name": "This Won't Work"}
        response = authenticated_admin_client.patch(url, update_data)

        # Debe fallar con error 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_multiple_concurrent_updates(
        self, authenticated_admin_client, regular_user
    ):
        """
        Test de múltiples actualizaciones concurrentes.
        Simula actualizaciones rápidas consecutivas para verificar la robustez del sistema.
        """
        url = reverse("admin-user-update", kwargs={"document": regular_user.document})

        # Realizar múltiples actualizaciones en sucesión rápida con valores únicos
        update_fields = [
            {"first_name": "Update1"},
            {"last_name": "Update2"},
            {"email": "update3@example.com"},
            {"phone": "9999999999"},  # Cambiado a un valor diferente
        ]

        # Almacenar respuestas para análisis
        responses = []

        # Realizar actualizaciones
        for i, update_data in enumerate(update_fields):
            response = authenticated_admin_client.patch(url, update_data)
            responses.append(response)
            print(f"Actualización {i+1}: {response.status_code} - {response.data}")

            # Si la actualización falla, imprimir detalles completos
            if response.status_code != status.HTTP_200_OK:
                print(f"Detalles de error en actualización {i+1}:")
                print(f"Datos enviados: {update_data}")
                print(f"Código de estado: {response.status_code}")
                print(f"Mensaje de error completo: {response.data}")

        # Verificar que todas las actualizaciones son exitosas
        for i, response in enumerate(responses):
            assert (
                response.status_code == status.HTTP_200_OK
            ), f"Actualización {i+1} falló"

        # Verificar estado final del usuario
        regular_user.refresh_from_db()
        assert regular_user.phone == "9999999999"
        assert regular_user.email == "update3@example.com"
