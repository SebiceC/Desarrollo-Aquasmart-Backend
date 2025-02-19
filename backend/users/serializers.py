from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from API.sendmsn import send_email_recover
from .models import DocumentType, PersonType, CustomUser, LoginHistory, Otp
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .validate import validate_user,validate_otp
from rest_framework.exceptions import NotFound
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone


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

    class Meta:
        model = CustomUser
        fields = [
            'document', 'first_name', 'last_name', 'email', 
            'document_type', 'person_type', 'phone', 'address',
            'password','is_registered', 'is_active',
        ]
        read_only_fields = ('isRegistered', 'is_active')       

    def create(self, validated_data):
        """
        Crea un usuario nuevo con la contraseña hasheada y lo deja inactivo por defecto.
        """
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_active'] = False
        user = CustomUser.objects.create(**validated_data)
        user.save()
        return user

class LoginHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo LoginHistory.
    Almacena los registros de inicio de sesión de los usuarios.
    """
    class Meta:
        model = LoginHistory
        fields = ['timestamp', 'user']
        
class LoginSerializer(serializers.Serializer):
    document = serializers.CharField(max_length=12, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        document = data.get('document')
        password = data.get('password')               

        
        user = validate_user(document)
          
        
        if not user: 
            raise NotFound({'details': 'User not found'})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Your account is inactive. Please contact support."})

        if not user.is_registered:
            raise serializers.ValidationError({"detail": "User is waiting to pass pre-registration. Please contact support for more information."})

        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        # Generar OTP
        otp_serializer = GenerateOtpSerializer(data={"document": document})
        if otp_serializer.is_valid(raise_exception=True):
            otp_data = otp_serializer.save()  # `save()` devuelve el diccionario con el OTP y mensaje
            
            # Agregar la información del usuario y OTP a `data`
            data["user_document"] = user.document  # Guardamos el usuario validado
            data["otp"] = otp_data["otp"]
            data["message"] = otp_data["message"]
            
            
        data.pop("otp", None)    
        data.pop("user_document", None)    
        data.pop("password", None)
        
        return data  # Retornamos todo el diccionario validado
        
class GenerateOtpSerializer(serializers.Serializer):
    """
    Serializador para la generación de un OTP (One-Time Password).

    Este serializador permite a un usuario solicitar un OTP, que se enviará a su correo electrónico.
    El OTP puede ser utilizado para recuperación de contraseña u otras validaciones.

    Campos:
    - `document`: Número de documento del usuario.

    Respuestas:
    - Si el usuario existe, genera un OTP y lo envía por correo electrónico.
    - Si el usuario no existe o hay un problema en el envío del correo, genera un error de validación.
    """

    document = serializers.CharField(max_length=12, help_text="Número de documento del usuario.")

    def validate_document(self, document):
        """
        Valida la existencia del usuario asociado al documento.

        Parámetros:
        - `document` (str): Número de documento del usuario.

        Retorno:
        - `CustomUser`: Instancia del usuario si es encontrado.

        Excepciones:
        - `serializers.ValidationError`: Si el usuario no existe.
        """
        user = validate_user(document)
        return user

    def create(self, validated_data):
        """
        Genera un nuevo OTP para el usuario y lo envía por correo electrónico.

        - Elimina OTPs previos asociados al usuario.
        - Crea un nuevo OTP.
        - Envía el OTP al correo del usuario.

        Parámetros:
        - `validated_data` (dict): Contiene `document` con la información del usuario.

        Retorno:
        - `dict`: Contiene el OTP generado y un mensaje de confirmación.

        Excepciones:
        - `serializers.ValidationError`: Si hay un error al enviar el correo.
        """
        user = validated_data['document']  # El método `validate_document` ya retornó el usuario.

        # Eliminar OTPs previos y generar uno nuevo
        Otp.objects.filter(user=user).delete()
        nuevo_otp = Otp.objects.create(user=user)
        otp_generado = nuevo_otp.generateOTP()

        # Simulación de envío de correo (en desarrollo, el mensaje se imprime en consola)
        try:
            send_email_recover(user.email, otp_generado)
        except Exception as e:
            raise serializers.ValidationError(f"Error al enviar el correo: {str(e)}")

        return {
            'otp': otp_generado,
            'message': 'Se ha enviado un correo con el OTP para recuperar la contraseña.'
        }  

class ValidateOtpSerializer(serializers.Serializer):
    """
    Serializador para validar un OTP (One-Time Password).

    Este serializador permite verificar si un OTP es válido, no ha sido utilizado y no ha expirado.
    Si el OTP es para inicio de sesión (`is_login=True`), genera un token JWT.
    
    Campos:
    - `document`: Número de documento del usuario.
    - `otp`: Código OTP de 6 dígitos.

    Respuestas:
    - Si el OTP es válido para inicio de sesión, devuelve `access` y `refresh` (tokens JWT).
    - Si el OTP es válido pero no es de inicio de sesión, devuelve un mensaje de confirmación.
    - Si el OTP ha expirado o es inválido, genera un error de validación.
    """

    document = serializers.CharField(max_length=12, help_text="Número de documento del usuario.")
    otp = serializers.CharField(max_length=6, help_text="Código OTP de 6 dígitos.")

    def validate(self, data):
        """
        Valida la existencia del usuario y la validez del OTP.

        - Verifica si el usuario existe a través de `validate_user(document)`.
        - Busca el OTP correspondiente con `validate_otp(user, otp, is_validated=False)`.
        - Revisa si el OTP ha expirado.
        - Si el OTP es para inicio de sesión (`is_login=True`), genera un token JWT.
        - Si no es de inicio de sesión, marca el OTP como validado.

        Parámetros:
        - `data` (dict): Contiene `document` y `otp`.

        Retorno:
        - `dict`: Dependiendo del caso:
            - `{ "access": <token>, "refresh": <token> }` si el OTP es para login.
            - `{ "message": "OTP validado correctamente" }` si el OTP es solo de validación.
        - En caso de error, lanza `serializers.ValidationError`.
        """
        document = data.get("document")
        otp = data.get("otp")

        print(f"Contexto recibido en el serializador: {self.context}")

        # Verificar si el usuario existe
        user = validate_user(document)

        # Verificar si el OTP es válido y no ha sido utilizado
        otp_instance = validate_otp(user=user, is_validated=False, otp=otp)

        # Verificar si el OTP no ha expirado
        if not otp_instance.validate_life_otp():
            raise serializers.ValidationError({"detail": "El OTP ha expirado."})

        response_data = {}

        if otp_instance.is_login:
            # Generar tokens JWT para autenticación
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.save()

            # Registrar evento de inicio de sesión
            request = self.context.get('request')                                
            user_logged_in.send(sender=user.__class__, request=request, user=user)    

            response_data['access'] = str(refresh.access_token)
            response_data['refresh'] = str(refresh)

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
        user = validate_user(document)

        # Verificar si existe un OTP validado para este usuario
        otp_instance = validate_otp(user=user, is_validated=True)

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
    
class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializador para la renovación de tokens de autenticación.

    Permite a los usuarios obtener un nuevo token de acceso (`access token`)
    a partir de un `refresh token` válido.

    Campos:
    - `refresh` (str): Token de actualización enviado por el cliente.

    Respuestas:
    - Si el token es válido, retorna un nuevo `access token`.
    - Si el token es inválido o ha expirado, genera un error de validación.
    """

    refresh = serializers.CharField(help_text="Token de actualización proporcionado por el usuario.")

    def validate(self, data):
        """
        Valida el token de actualización y genera un nuevo token de acceso.

        Parámetros:
        - `data` (dict): Contiene el `refresh token`.

        Retorno:
        - `dict`: Diccionario con un nuevo `access token`.

        Excepciones:
        - `serializers.ValidationError`: Si el token es inválido o ha expirado.
        """
        try:
            refresh = RefreshToken(data["refresh"])
            return {"access": str(refresh.access_token)}
        except Exception:
            raise serializers.ValidationError("Token inválido o expirado.")   
        
