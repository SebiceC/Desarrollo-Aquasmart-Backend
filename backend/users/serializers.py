from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from API.sendmsn import send_email2
from .models import DocumentType, PersonType, CustomUser, Otp, UserUpdateLog, LoginRestriction
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from .validate import validate_user_exist,validate_otp,validate_create_user_email,validate_create_user_document,validate_user_password,validate_only_number_phone,validate_user_current_password
from rest_framework.exceptions import NotFound,PermissionDenied
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.authtoken.models import Token
from API.google.google_drive import create_folder, share_folder
import os
import re
from auditlog.models import LogEntry

class DocumentTypeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo DocumentType.
    Representa los tipos de documentos disponibles.
    """
    
    class Meta:
        model = DocumentType
        fields = ['documentTypeId', 'typeName']

class PersonTypeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo PersonType.
    Representa los tipos de personas en el sistema.
    """
    class Meta:
        model = PersonType
        fields = ['personTypeId', 'typeName']

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo CustomUser.
    Gestiona la creación de usuarios, incluyendo el manejo seguro de contraseñas.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    document_type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.all(), required=False)
    person_type = serializers.PrimaryKeyRelatedField(queryset=PersonType.objects.all(), required=False)
    drive_folder_id = serializers.CharField(read_only=True)  # Solo lectura
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )


    class Meta:
        model = CustomUser
        fields = [
            'document', 'first_name', 'last_name', 'email', 
            'document_type', 'person_type', 'phone', 'address',
            'password', 'is_registered', 'is_active','date_joined','drive_folder_id','files'
        ]
        read_only_fields = ('is_registered','drive_folder_id','date_joined')
        
        extra_kwargs = {
            'document': {'validators': []},
            'email': {'validators': []},
        }

    def validate_document(self, value):
        return validate_create_user_document(value)

    def validate_phone(self, value):
        return validate_only_number_phone(value)       

    def validate_email(self, value):
        return validate_create_user_email(value)
        
    def validate_password(self, value):
        return validate_user_password(value)
        

    def create(self, validated_data):
        """
        Crea un usuario nuevo sin manejar la subida de archivos.
        """
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_active'] = False
        user = CustomUser.objects.create(**validated_data)
        
        # Crear carpeta en Google Drive y asociarla al usuario
        folder_name = f"{user.document}_{user.first_name}_{user.last_name}"
        folder_id = create_folder(folder_name)
        user.drive_folder_id = folder_id
        user.save()

        # Compartir la carpeta con el administrador
        if folder_id:
            share_folder(folder_id, email=os.environ.get('EMAIL_HOST_USER', default=os.getenv("EMAIL_HOST_USER")), role='writer')

        return user

class LogEntrySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo LogEntry de auditlog.
    """
    class Meta:
        model = LogEntry
        fields = ['timestamp', 'actor', 'action', 'changes', 'remote_addr']

class LoginSerializer(serializers.Serializer):
    """
    Serializer para la autenticación de usuarios mediante documento y contraseña.

    Este serializer maneja la validación de usuarios, verificación de intentos fallidos,
    bloqueo de cuenta y generación de OTP en caso de autenticación exitosa.

    Campos:
        - document (str): Número de documento del usuario (máx. 12 caracteres).
        - password (str): Contraseña del usuario (solo escritura).

    Validaciones:
        - Verifica que el usuario exista y esté activo.
        - Revisa si el usuario ha completado su pre-registro.
        - Controla intentos fallidos de inicio de sesión y bloquea el usuario si es necesario.
        - Genera un código OTP en caso de autenticación exitosa.

    Errores posibles:
        - 404 NotFound: Usuario no encontrado.
        - 403 PermissionDenied: Cuenta inactiva.
        - 400 ValidationError: Usuario en pre-registro, intentos fallidos o credenciales incorrectas.

    Retorna:
        - Un diccionario con mensaje de éxito y OTP generado si la autenticación es correcta.
    """
    
    document = serializers.CharField(max_length=12, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        document = data.get('document')
        password = data.get('password')               

        user = validate_user_exist(document)   
        if not user.is_registered:
            raise serializers.ValidationError({"detail": "Usuario en espera de validar su pre-registro. Póngase en contacto con soporte para mas información."})     

        if not user.is_active:
            raise PermissionDenied({"detail": "Su cuenta está inactiva. Póngase en contacto con el servicio de soporte."})       

        # Buscar registro de intentos (si existe)
        login_restriction = LoginRestriction.objects.filter(user=user).first()

        # Verificar si el usuario está bloqueado
        if login_restriction and login_restriction.is_blocked():
            raise serializers.ValidationError({"detail": f"Demasiados intentos fallidos. Inténtalo de nuevo después {login_restriction.blocked_until.strftime('%d/%m/%Y %I:%M %p') if login_restriction.blocked_until else 'un tiempo'}."})

        # Validar la contraseña
        if not user.check_password(password):
            if not login_restriction:
                # Crear el registro solo en caso de intento fallido
                login_restriction = LoginRestriction.objects.create(user=user)

            message = login_restriction.register_attempt()
            raise serializers.ValidationError({"detail": message})

        # Si el login es exitoso, reiniciar intentos (si existía el registro)
        if login_restriction:
            login_restriction.attempts = 0
            login_restriction.last_attempt_time = timezone.now()
            login_restriction.save()

        # Generar OTP
        otp_serializer = GenerateOtpLoginSerializer(data={"document": document})
        if otp_serializer.is_valid(raise_exception=True):
            otp_data = otp_serializer.save()
            
            # Agregar información del usuario y OTP
            data["user_document"] = user.document
            data["otp"] = otp_data["otp"]
            data["message"] = otp_data["message"]

        data.pop("otp", None)    
        data.pop("user_document", None)    
        data.pop("password", None)

        return data

class GenerateOtpLoginSerializer(serializers.Serializer):
    """
    Serializador para la generación de OTP en el login.

    Este serializador permite a los usuarios recibir un código OTP para autenticación.
    """

    document = serializers.CharField(
        max_length=12,
        help_text="Número de documento del usuario."
    )

    def validate_document(self, document):
        """
        Valida si el usuario existe en la base de datos.
        """
        return validate_user_exist(document)
        

    def create(self, validated_data):
        """
        Genera un nuevo código OTP y lo envía por mensaje de texto.

        Args:
            validated_data (dict): Datos validados que contienen el documento del usuario.

        Returns:
            dict: Diccionario con el OTP generado y un mensaje de confirmación.

        Raises:
            serializers.ValidationError: Si hay un error al enviar el correo.
        """
        user = validated_data['document']  # `validate_document` ya retornó el usuario.

        # Eliminar OTPs previos y generar uno nuevo
        Otp.objects.filter(user=user).delete()
        nuevo_otp = Otp.objects.create(user=user)
        otp_generado = nuevo_otp.generate_otp()

        # Simulación de envío de correo/SMS
        try:
            send_email2(user.email, otp_generado, purpose="login",name=user.first_name)
        except Exception as e:
            raise serializers.ValidationError(f"Error al enviar el correo: {str(e)}")

        return {
            'otp': otp_generado,
            'message': 'Se ha enviado el código OTP de iniciar sesión.'
        }         

class GenerateOtpPasswordRecoverySerializer(serializers.Serializer):
    """
    Serializer para generar un OTP en el proceso de recuperación de contraseña.
    """

    document = serializers.CharField(
        max_length=12,
        help_text="Número de documento del usuario registrado."
    )
    phone = serializers.CharField(
        max_length=20,
        help_text="Número de teléfono asociado a la cuenta del usuario."
    )

    def validate(self, attrs):
        """
        Valida que el usuario exista y que el número de teléfono coincida con el registrado.
        """
        document = attrs.get("document")
        phone = attrs.get("phone")

        # Validar existencia del usuario
        user = validate_user_exist(document)
        

        # Validar que el teléfono coincida con el registrado en la base de datos
        if user.phone != phone:
            raise serializers.ValidationError({"phone": "El número de teléfono no coincide con el registrado."})

        attrs["user"] = user  # Guardamos el usuario validado en attrs
        return attrs

    def create(self, validated_data):
        """
        Genera un nuevo OTP y lo envía al usuario por correo o SMS.
        """
        user = validated_data["user"]

        # Eliminar OTPs previos y generar uno nuevo
        Otp.objects.filter(user=user).delete()
        nuevo_otp = Otp.objects.create(user=user)
        otp_generado = nuevo_otp.generate_otp()  # Asegúrate de que esta función retorne el OTP correcto

        # Intentar enviar OTP por correo
        try:
            send_email2(user.email, otp_generado, purpose="recover",name=user.first_name )
        except Exception as e:
            raise serializers.ValidationError(f"Hubo un problema al enviar el código. Inténtalo más tarde. {e}")

        return {
            "message": "Se ha enviado el código de recuperación a su correo electrónico."
        }

class ValidateOtpSerializer(serializers.Serializer):
    """
    Serializador para validar un OTP (One-Time Password).

    Este serializador permite verificar si un OTP es válido, no ha sido utilizado y no ha expirado.
    Si el OTP es para inicio de sesión (`is_login=True`), genera un token.
    
    Campos:
    - `document`: Número de documento del usuario.
    - `otp`: Código OTP de 6 dígitos.

    Respuestas:
    - Si el OTP es válido para inicio de sesión, devuelve `token`.
    - Si el OTP es válido pero no es de inicio de sesión, devuelve un mensaje de confirmación.
    - Si el OTP ha expirado o es inválido, genera un error de validación.
    """

    document = serializers.CharField(max_length=12)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        """
        Valida la existencia del usuario y la validez del OTP.

        - Verifica si el usuario existe a través de `validate_user(document)`.
        - Busca el OTP correspondiente con `validate_otp(user, otp, is_validated=False)`.
        - Revisa si el OTP ha expirado.
        - Si el OTP es para inicio de sesión (`is_login=True`):
            - Genera un token de autenticación.
            - Registra evento de inicio de sesión.
            - Elimina el OTP utilizado.
        - Si el OTP es para otro propósito, lo marca como validado sin generar token.
        """
        document = data.get("document")
        otp = data.get("otp")

        # Verificar si el usuario existe
        user = validate_user_exist(document)

        # Verificar si el OTP es válido y no ha sido utilizado
        otp_instance = validate_otp(user=user, is_validated=False, otp=otp)

        # Verificar si el OTP no ha expirado
        if not otp_instance.validate_life_otp():
            raise serializers.ValidationError({"detail": "El OTP ha expirado."})

        response_data = {}

        if otp_instance.is_login:
            # Generar tokens JWT para autenticación            
            token, created = Token.objects.get_or_create(user=user)
            user.last_login = timezone.now()
            user.save()

            # Registrar evento de inicio de sesión
            request = self.context.get('request')                                
            user_logged_in.send(sender=user.__class__, request=request, user=user)    

            response_data['token'] = str(token.key)
            

            # Eliminar OTP de inicio de sesión usados
            Otp.objects.filter(user=user, is_login=True).delete()
            return response_data
        else:
            # Marcar el OTP como validado
            otp_instance.is_validated = True
            otp_instance.save()
            response_data['message'] = 'OTP validado correctamente'

        return response_data

class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializador para restablecer la contraseña de un usuario.

    Este serializador permite a un usuario cambiar su contraseña después de validar su identidad
    mediante un OTP previamente verificado.

    Campos:
    - `document` (str): Documento de identidad del usuario.
    - `new_password` (str, write_only): Nueva contraseña a establecer.

    Validaciones:
    - Verifica que el usuario exista.
    - Comprueba que el usuario tenga un OTP validado.
    - No permite reutilizar la contraseña actual.
    - Valida la nueva contraseña según las reglas de seguridad de Django.

    Acciones al guardar:
    - Actualiza la contraseña del usuario.
    - Elimina todos los OTP validados del usuario.
    """

    document = serializers.CharField(max_length=12)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Valida la nueva contraseña y verifica la existencia del usuario y su OTP validado.

        Pasos de validación:
        1. Verifica si existe un usuario con el documento proporcionado.
        2. Comprueba si hay un OTP validado asociado al usuario.
        3. Asegura que la nueva contraseña no sea idéntica a la actual.
        4. Valida la nueva contraseña según las reglas de seguridad de Django.

        Parámetros:
        - `data` (dict): Contiene `document` y `new_password`.

        Retorno:
        - `data` (dict): Devuelve los mismos datos si la validación es exitosa.

        Excepciones:
        - `NotFound`: Si el usuario no existe.
        - `ValidationError`: Si no hay un OTP validado para el usuario.
        - `serializers.ValidationError`: Si la nueva contraseña es igual a la actual.
        - `serializers.ValidationError`: Si la nueva contraseña no cumple con las reglas de Django.
        """
        document = data.get("document")
        new_password = data.get("new_password")

        # Verificar si el usuario existe
        user = validate_user_exist(document)

        # Verificar si existe un OTP validado para este usuario
        validate_otp(user=user, is_validated=True)

        # Validar que la nueva contraseña no sea la misma que la actual
        if check_password(new_password, user.password):
            raise serializers.ValidationError({"detail": "No puedes usar la misma contraseña actual."})

        # Validar la contraseña con las reglas de Django
        try:
            validate_password(new_password, user=user)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})

        return data

    def save(self):
        """
        Guarda la nueva contraseña del usuario y elimina los OTP validados.

        Acciones:
        1. Encripta la nueva contraseña y la asigna al usuario.
        2. Guarda los cambios en la base de datos.
        3. Elimina todos los OTP validados del usuario para mayor seguridad.

        Retorno:
        - `CustomUser`: Instancia del usuario con la nueva contraseña guardada.
        """
        document = self.validated_data['document']
        new_password = self.validated_data['new_password']

        user = CustomUser.objects.get(document=document)
        user.password = make_password(new_password)  # Encripta la nueva contraseña
        user.save()

        # Eliminar todos los OTP validados del usuario
        Otp.objects.filter(user=user, is_validated=True).delete()

        return user          
        
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para representar el perfil de usuario.

    - `document_type_name`: Nombre del tipo de documento asociado al usuario.
    - `person_type_name`: Nombre del tipo de persona (natural/jurídica).
    - `email`: Correo electrónico del usuario.
    - `document`: Número de documento de identidad.
    - `first_name`: Nombre del usuario.
    - `last_name`: Apellido del usuario.
    - `phone`: Número de teléfono registrado.
    - `address`: Dirección del usuario.
    """

    document_type_name = serializers.CharField(source='document_type.typeName', read_only=True)
    person_type_name = serializers.CharField(source='person_type.typeName', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'email', 'document', 'document_type_name', 
            'first_name', 'last_name', 'phone', 
            'address', 'person_type_name','drive_folder_id'
        ] 
        
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    phone = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'phone']  # Solo permitimos estos campos

    def validate(self, data):
        """Verifica que al menos un campo haya sido enviado."""
        if not data.get("email") and not data.get("phone"):
            raise serializers.ValidationError(
                "Debes enviar al menos el email o el teléfono para actualizar el perfil."
            )
        
        # Verifica si el usuario puede realizar una actualización
        user = self.instance
        update_log, created = UserUpdateLog.objects.get_or_create(user=user)
        can_update, message = update_log.can_update(updating_user=self.context["request"].user)
        if not can_update:
            raise serializers.ValidationError(message)
        
        # Guardamos el mensaje para devolverlo en la respuesta
        self.context['update_message'] = message
        return data

    def validate_email(self, value):
        """Evita que el email sea el mismo o que esté vacío."""
        user = self.instance        
        if CustomUser.objects.filter(email=value).exclude(document=user.document).exists():
            raise serializers.ValidationError("Este email ya está en uso.")
        return value

    def validate_phone(self, value):
        """Evita que el número de teléfono sea el mismo, contenga letras o esté vacío."""   
        actual_phone = self.instance.phone       
        
        if actual_phone == value:
            raise serializers.ValidationError("El telefono a actualizar no puede ser el mismo que el actual.")
                       
        validate_only_number_phone(value)        
        return value

    def update(self, instance, validated_data):
        """Actualiza el usuario y aumenta el contador de actualizaciones."""
        # Actualiza los campos del usuario
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()

        # Incrementa el contador de actualizaciones
        update_log, created = UserUpdateLog.objects.get_or_create(user=instance)
        update_log.increment_update_count()

        # Devuelve la instancia y el mensaje de actualización
        return instance

    def to_representation(self, instance):
        """Devuelve la representación del objeto junto con el mensaje de actualización."""
        representation = super().to_representation(instance)
        representation['message'] = self.context.get('update_message', 'Datos actualizados con éxito.')
        return representation

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializador para cambio de contraseña.
    
    Permite a un usuario autenticado cambiar su contraseña proporcionando
    la contraseña actual, la nueva contraseña y su confirmación.
    """
    current_password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        help_text="Contraseña actual del usuario."
    )
    new_password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        help_text="Nueva contraseña que debe cumplir con los requisitos de seguridad."
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        help_text="Confirmación de la nueva contraseña. Debe coincidir con el campo new_password."
    )

    def validate_current_password(self, value):
        """
        Valida que la contraseña actual sea correcta.
        """
        user = self.context['request'].user  # Obtiene el usuario desde el contexto
        return validate_user_current_password(value, user)
    
    def validate(self, data):
        """
        Valida que la nueva contraseña y la confirmación coincidan,
        y que la nueva contraseña no sea igual a la actual.
        """
        # Verificar que la nueva contraseña y la confirmación coincidan
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden, por favor, verifíquelas."})
        
        # Verificar que la nueva contraseña no sea igual a la actual
        if data.get('current_password') == data.get('new_password'):
            raise serializers.ValidationError({"new_password": "La contraseña nueva es igual a la actual, por favor, verifíquelas."})
        
        # Aplicar todas las validaciones configuradas en settings.py
        try:
            validate_password(data.get('new_password'), self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
            
        return data

    def save(self):
        """
        Actualiza la contraseña del usuario.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
