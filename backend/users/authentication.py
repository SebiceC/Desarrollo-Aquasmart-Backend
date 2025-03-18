from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .models import Otp,CustomUser
from .serializers import  GenerateOtpPasswordRecoverySerializer, ValidateOtpSerializer, ResetPasswordSerializer, LoginSerializer,GenerateOtpLoginSerializer
from rest_framework.exceptions import ValidationError, NotFound,PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from API.custom_auth import CustomTokenAuthentication
from .serializers import ChangePasswordSerializer
from API.sendmsn import send_email2
class LoginView(APIView):
    """
    Endpoint para la autenticación de usuarios con generación de OTP.
    
    Permite a los usuarios autenticarse con su documento y contraseña.
    Si la autenticación es exitosa, se genera un OTP y se asocia al usuario.
    """
    permission_classes = [AllowAny]
    @extend_schema(
        tags=["Autenticación"],
        summary="Login",
        description="Este endpoint permite a los usuarios autenticarse con su documento y contraseña. "
                    "Si la autenticación es exitosa, se genera un OTP para la verificación.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=LoginSerializer,  # Aquí se indica que la respuesta sigue la estructura del serializer
                description="Login exitoso",
                examples=[
                    OpenApiExample(
                        "Ejemplo de respuesta exitosa",
                        value={"document": "123456789012", "message": "Se ha enviado un msn con el OTP para poder iniciar sesión."},  # Ejemplo correcto
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=LoginSerializer,
                description="Error de validación",
                examples=[
                    OpenApiExample(
                        "Intentos fallidos",
                        value={
                        "error": {
                            "detail": [
                            "Credenciales inválidas.",
                            "Último intento antes de ser bloqueado.",
                            "Usuario bloqueado por 30 minutos.",
                            "Too many failed attempts. Try again after 2025-03-06 02:09:37.980678."
                            ]
                        }
                        },
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                response=LoginSerializer,
                description="Cuenta inactiva",
                examples=[
                    OpenApiExample(
                        "Cuenta deshabilitada",
                        value={
                        "error": {
                            "detail": "Your account is inactive. Please contact support."
                        }
                        },
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                response=LoginSerializer,
                description="Usuario no encontrado",
                examples=[
                    OpenApiExample(
                        "Usuario inexistente",
                        value={"error": {
                        "details": "User not found"
                    }},
                        response_only=True
                    )
                ]
            ),
            500: OpenApiResponse(
                response=LoginSerializer,
                description="Error inesperado",
                examples=[
                    OpenApiExample(
                        "Fallo interno",
                        value={"error": "Unexpected error.", "detail": "Internal server error"},
                        response_only=True
                    )
                ]
            )
        },
        
        examples=[
            OpenApiExample(
                "Ejemplo de solicitud",
                summary="Ejemplo de entrada válida",
                value={"document": "123456789012", "password": "mypassword"},
                request_only=True
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Maneja la autenticación del usuario y la generación del OTP.

        Args:
            request (Request): Datos de entrada con documento y contraseña.

        Returns:
            Response: Respuesta con mensaje de éxito o error.
        """
        try:
            serializer = LoginSerializer(data=request.data)
            
            if serializer.is_valid(raise_exception=True):
                data = serializer.validated_data
                document = data.get('document')

                # Buscar usuario y eliminar token previo
                user_instance = CustomUser.objects.filter(document=document).first()
                Token.objects.filter(user=user_instance).delete()

                # Marcar OTP como login exitoso
                otp_instance = Otp.objects.filter(user=document).first()
                otp_instance.is_login = True
                otp_instance.save()

                return Response(serializer.validated_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"error": e.detail}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": e.detail}, status=status.HTTP_403_FORBIDDEN) 
        except Exception as e:
            return Response(
                {"error": "Unexpected error.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
            
class GenerateOtpLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = GenerateOtpLoginSerializer(data=request.data)  
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data['document']  # Usuario validado en `validate_document`

                # Eliminar OTPs previos que sean para login
                Otp.objects.filter(user=user.document, is_login=True).delete()

                # Crear nuevo OTP
                nuevo_otp = Otp.objects.create(user=user, is_login=True)
                otp_generado = nuevo_otp.generate_otp()
                user_instance = CustomUser.objects.filter(document=user.document).first()
                # Enviar OTP por correo
                try:
                    send_email2(user.email, otp_generado, purpose="login",name=user_instance.first_name)
                except Exception as e:
                    return Response(
                        {"error": f"Error al enviar el correo: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                return Response(
                    {"message": "Se ha enviado el código OTP para iniciar sesión."},
                    status=status.HTTP_200_OK
                )

        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)      
        except Exception as e:
            return Response(
                {"error": "Unexpected error.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

         


class GenerateOtpPasswordRecoveryView(APIView):
    """
    Vista para generar un código OTP para la recuperación de contraseña.

    Permite a un usuario recibir un código OTP en su correo o teléfono
    para poder recuperar su cuenta.
    """
    permission_classes = [AllowAny]
    @extend_schema(
    tags=["Autenticación"],
    summary="Generar OTP para recuperación de contraseña",
    description="Este endpoint permite generar un código OTP para recuperar la contraseña de un usuario.",
    request=GenerateOtpPasswordRecoverySerializer,
    responses={
        200: OpenApiResponse(
                response=GenerateOtpPasswordRecoverySerializer,  # Aquí se indica que la respuesta sigue la estructura del serializer
                description="Respuesta exitosa",
                examples=[
                    OpenApiExample(
                        "Ejemplo de respuesta exitosa",
                        value={"document": "123456789012", "message": "Se ha enviado un msn con el OTP para poder iniciar sesión."},  # Ejemplo correcto
                        response_only=True
                    )
                ]
            ),
        400: OpenApiResponse(
                response=GenerateOtpPasswordRecoverySerializer,  # Aquí se indica que la respuesta sigue la estructura del serializer
                description="Error de validación",
                examples=[
                    OpenApiExample(
                        "Error de validación",
                        value={
                        "error": [
                            "El número de teléfono no coincide con el registrado.",
                            "Error al enviar el OTP: problema con el servicio de mensajeria"
                        ]
                        },  
                        response_only=True
                    )
                ]
            ),
        
        404: OpenApiResponse(
                response=GenerateOtpPasswordRecoverySerializer,  # Aquí se indica que la respuesta sigue la estructura del serializer
                description="Usuario no encontrado",
                examples=[
                    OpenApiExample(
                        "Ejemplo de respuesta exitosa",
                        value={
                        "error": "No se encontró un usuario con este documento."
                        },  
                        response_only=True
                    )
                ]
            ),
        
        500: OpenApiResponse(
                response=GenerateOtpPasswordRecoverySerializer,  # Aquí se indica que la respuesta sigue la estructura del serializer
                description="Error en el envío del OTP",
                examples=[
                    OpenApiExample(
                         "Error en el envío del OTP",
                        value={
                        "error": "Error al enviar el OTP: Detalles del error"
                        },  
                        response_only=True
                    )
                ]
            ),
    }
)

    def post(self, request):
        """
        Método POST para generar y enviar un código OTP al usuario.

        Args:
            request (Request): La solicitud HTTP con el documento del usuario.

        Returns:
            Response: JSON con el OTP generado o un mensaje de error.
        """
        serializer = GenerateOtpPasswordRecoverySerializer(data=request.data)
        try:
            if serializer.is_valid():
                data = serializer.save()
                return Response(data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"error": e.detail}, status=status.HTTP_404_NOT_FOUND)        
        except Exception as e:
            return Response({"error": "Unexpected error.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

  

class ValidateOtpView(APIView):
    """
    Endpoint para validar un código OTP y autenticar al usuario.

    Permisos:
    - Accesible para cualquier usuario (AllowAny).

    Flujo de trabajo:
    1. Recibe un número de documento y un código OTP en el cuerpo de la solicitud.
    2. Valida que el OTP sea correcto y aún sea válido.
    3. Si el OTP es de inicio de sesión, devuelve un token de autenticación.
    4. Si el OTP es de otro tipo, simplemente lo marca como validado.

    Respuestas:
    - 200 OK: OTP válido, devuelve un mensaje de éxito o token de autenticación.
    - 400 Bad Request: Datos inválidos o errores en la validación del OTP.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Autenticación"],
        summary="Validación de OTP",
        description="Recibe un número de documento y un código OTP. "
                    "Si el OTP es válido, se autentica al usuario o se marca como validado.",
        request=ValidateOtpSerializer,
        responses={
            200: OpenApiResponse(
                response=ValidateOtpSerializer,  
                description="OTP Valido",
                examples=[
                    OpenApiExample(
                        "Ejemplo de respuesta exitosa",
                        value={
                        "message": "OTP validado correctamente"
                        },
                    )
                ]
            ),
            400: OpenApiResponse(
                response=LoginSerializer,
                description="Error de validación",
                examples=[
                    OpenApiExample(
                        "Intentos fallidos",
                        value={
                        "error": {
                            "detail": [
                            "El OTP ha expirado.",
                            "OTP inválido o ya ha sido utilizado.",
                             "No hay un OTP validado para este usuario."
                            ]
                        }
                        },
                        response_only=True
                    )
                ]
            ),
        },
        examples=[
            OpenApiExample(
                "Ejemplo de solicitud",
                summary="Ejemplo de entrada válida",
                value={"document": "123456789012", "otp": "154687"},
                request_only=True
            )
        ]
    )
    def post(self, request):
        """
        Procesa la validación del OTP y devuelve una respuesta con el token de autenticación o un mensaje de éxito.
        """
        serializer = ValidateOtpSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    """
    Vista para restablecer la contraseña de un usuario.

    Permite a los usuarios restablecer su contraseña proporcionando su documento 
    y habiendo validado un OTP previamente. No requiere autenticación para `POST`.

    Métodos:
    - `POST`: Recibe un `document` y una `new_password` para cambiar la contraseña.
    """

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: {"message": "Contraseña restablecida correctamente."},
            400: {"message": "Errores de validación."}
        },
        description="Restablece la contraseña de un usuario si ha validado un OTP.",
        summary="Restablecer contraseña",
    )
    def post(self, request):
        """
        Procesa el restablecimiento de la contraseña.

        Recibe un documento y una nueva contraseña en el cuerpo de la solicitud. 
        Si el OTP fue validado previamente, la contraseña se actualiza.

        Parámetros:
        - `request.data` (dict): Debe contener `document` y `new_password`.

        Retorno:
        - `200 OK`: Si la contraseña fue cambiada con éxito.
        - `400 BAD REQUEST`: Si hay errores en la validación.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Contraseña restablecida correctamente."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """
    Vista para cerrar sesión de un usuario autenticado.

    Permite eliminar el token de autenticación del usuario, invalidando su sesión actual.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Cierra la sesión del usuario autenticado eliminando su token de acceso.

        Retorno:
        - `200 OK`: Si el cierre de sesión es exitoso.
        - `401 UNAUTHORIZED`: Si el usuario no está autenticado.
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "No estás autenticado. Por favor, inicia sesión."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Eliminar el token del usuario autenticado
            request.user.auth_token.delete()
            return Response({"message": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": "No se pudo cerrar la sesión.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ValidateTokenView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Verifica si el token en la cabecera es válido.
        Si el token no existe o no coincide con el del usuario, se devuelve un error.
        """
        user = request.user
        print(user)
        try:
            Token.objects.get(user=user)

            # El token ya fue validado por TokenAuthentication, así que no es necesario compararlo manualmente
            return Response({"detail": "Sesión valida."}, status=status.HTTP_200_OK)

        except Token.DoesNotExist:
            return Response(
                {"detail": "Su sesión se cerró."},
                status=status.HTTP_401_UNAUTHORIZED
            )

@extend_schema(
    tags=["Seguridad"],
    summary="Cambiar contraseña",
    description="Permite al usuario autenticado cambiar su contraseña proporcionando la actual, la nueva y la confirmación.",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(
                response=ChangePasswordSerializer,
                description="Contraseña actualizada correctamente",
                examples=[
                    {"message": "Actualización de contraseña exitosa"}
                ]
            ),
        400: OpenApiResponse(
                response=ChangePasswordSerializer,
                description="Error de validación",
                examples=[
                    {
                        "current_password": ["La contraseña actual es incorrecta."],
                        "new_password": ["La contraseña debe contener al menos una letra mayúscula."],
                        "confirm_password": ["Las contraseñas no coinciden, por favor, verifíquelas."]
                    }
                ]
            ),
        401: OpenApiResponse(
                response=ChangePasswordSerializer,
                description="No autenticado",
                examples=[
                    {"detail": "Las credenciales de autenticación no se proveyeron."}
                ]
            ),
        500: OpenApiResponse(
                response=ChangePasswordSerializer,
                description="Error en el sistema",
                examples=[
                    {"error": "ERROR, error en envío de formulario, por favor intente más tarde"}
                ]
            ),
    }
)
class ChangePasswordView(APIView):
    """
    Vista para que un usuario autenticado cambie su contraseña.
    
    Requiere autenticación y valida:
    - Que la contraseña actual sea correcta
    - Que la nueva contraseña cumpla con los requisitos de seguridad
    - Que la confirmación de contraseña coincida con la nueva
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Procesa la solicitud de cambio de contraseña.
        """
        try:
            serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Actualización de contraseña exitosa"}, 
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Captura cualquier error inesperado
            return Response(
                {"error": "ERROR, error en envío de formulario, por favor intente más tarde"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )