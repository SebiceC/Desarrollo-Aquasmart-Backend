from .models import CustomUser, Otp
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
import re
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import NotFound


def validate_user_exist(document):
    """
    Verifica si el usuario con el documento proporcionado existe.
    """
    user = CustomUser.objects.filter(document=document).first()
    if not user:
        raise NotFound("No se encontró un usuario con este documento.")
    return user


def validate_otp(user, is_validated=False, otp=None):
    """
    Valida si existe un OTP según el estado de validación.

    - `user`: Usuario al que pertenece el OTP.
    - `is_validated`: `True` para buscar OTPs ya validados, `False` para buscar OTPs no usados.
    - `otp`: (Opcional) Código OTP a verificar.

    Retorna el objeto OTP si existe, de lo contrario lanza un error.
    """
    try:
        filters = {
            "user": user,
            "is_validated": is_validated,
        }
        if otp is not None:
            filters["otp"] = otp  # Filtrar por OTP si se proporciona

        return Otp.objects.get(**filters)

    except ObjectDoesNotExist:
        message = (
            "No hay un OTP validado para este usuario."
            if is_validated
            else "OTP inválido o ya ha sido utilizado."
        )
        raise ValidationError({"detail": message})


def validate_create_user_document(value):
    """
    Valida si el documento ya existe, si es solo numérico y maneja los mensajes personalizados.
    """
    if not re.match(r"^\d+$", value):
        raise serializers.ValidationError("El documento debe contener solo números.")

    existing_user = CustomUser.objects.filter(document=value).first()
    if existing_user:
        if not existing_user.is_registered:
            raise serializers.ValidationError("Ya tienes un pre-registro activo.")
        else:
            raise serializers.ValidationError("El usuario ya pasó el pre-registro.")
    return value


def validate_only_number_phone(value):
    """
    Valida que el número de teléfono solo contenga números.
    """
    if not re.match(r"^\d+$", value):
        raise serializers.ValidationError("El teléfono debe contener solo números.")
    return value


def validate_create_user_email(value):
    """
    Valida si el email ya existe y maneja el mensaje personalizado.
    """
    if CustomUser.objects.filter(email=value).exists():
        raise serializers.ValidationError("Este correo ya está registrado.")
    return value


def validate_user_password(value):
    """
    Valida la contraseña usando las validaciones configuradas en AUTH_PASSWORD_VALIDATORS.
    """
    try:
        validate_password(value)
    except DjangoValidationError as e:
        raise serializers.ValidationError({"detail": list(e.messages)})
    return value


def validate_user_current_password(value, user):
    """
    Valida que la contraseña actual sea correcta.
    """
    if not user.check_password(value):
        raise serializers.ValidationError("La contraseña actual es incorrecta.")
    return value
