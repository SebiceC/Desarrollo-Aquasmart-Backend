"""
Django settings for API project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os
import dj_database_url
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', default=os.getenv("SECRET_KEY"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'drf_spectacular',
    'storages',
    'rest_framework.authtoken',
    'rest_framework',
    'users',
    'iot',
    'plots_lots',
    'AquaSmart'
    
]

AUTH_USER_MODEL ='users.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'API.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'API.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""
# Database documentation https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        # Replace this value with your local database's connection string.
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

class MaximumLengthValidator:
    """
    Valida que la contraseña no exceda un número máximo de caracteres.
    """
    def __init__(self, max_length=20):
        self.max_length = max_length
        
    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _("La contraseña no puede tener más de %(max_length)d caracteres."),
                code='password_too_long',
                params={'max_length': self.max_length},
            )
            
    def get_help_text(self):
        return _("Tu contraseña no puede tener más de %(max_length)d caracteres.") % {'max_length': self.max_length}
        
class UppercaseValidator:
    """
    Valida que la contraseña contenga al menos una letra mayúscula.
    """
    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper',
            )
            
    def get_help_text(self):
        return _("Tu contraseña debe contener al menos una letra mayúscula.")
        
class LowercaseValidator:
    """
    Valida que la contraseña contenga al menos una letra minúscula.
    """
    def validate(self, password, user=None):
        if not any(char.islower() for char in password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra minúscula."),
                code='password_no_lower',
            )
            
    def get_help_text(self):
        return _("Tu contraseña debe contener al menos una letra minúscula.")
        
class SpecialCharValidator:
    """
    Valida que la contraseña contenga al menos un carácter especial.
    """
    def __init__(self, special_chars="@#$%^&*()_+-=[]{}|;:'\",.<>/?`~"):
        self.special_chars = special_chars
        
    def validate(self, password, user=None):
        if not any(char in self.special_chars for char in password):
            raise ValidationError(
                _("La contraseña debe contener al menos un carácter especial (como @, #, $, etc.)."),
                code='password_no_symbol',
            )
            
    def get_help_text(self):
        return _("Tu contraseña debe contener al menos un carácter especial (como @, #, $, etc.).")


# Luego, busca la sección AUTH_PASSWORD_VALIDATORS en tu settings.py y reemplázala con:

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ['document', 'first_name', 'last_name', 'email', 'phone'],
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'API.settings.MaximumLengthValidator',  # Usa la ruta completa al módulo
        'OPTIONS': {
            'max_length': 20,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'API.settings.UppercaseValidator',  # Usa la ruta completa al módulo
    },
    {
        'NAME': 'API.settings.LowercaseValidator',  # Usa la ruta completa al módulo
    },
    {
        'NAME': 'API.settings.SpecialCharValidator',  # Usa la ruta completa al módulo
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'es-CO'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# This production code might break development mode, so we check whether we're in DEBUG mode
if not DEBUG:
    # Tell Django to copy static assets into a path called `staticfiles` (this is specific to Render)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Enable the WhiteNoise storage backend, which compresses static files to reduce disk use
    # and renames the files with unique names for each version to support long-term caching
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'API.custom_auth.CustomTokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
    
}


# Configurar los dominios permitidos
CORS_ALLOWED_ORIGINS = [
    "https://tu-frontend.com",
    "http://localhost:5173",  # Para desarrollo con React
    "http://localhost:8081",
    "https://desarrollo-aqua-smart-frontend-mu.vercel.app",
    "https://desarrollo-aquasmart-frontend2.vercel.app",
    "https://desarrollo-aqua-smart-frontend-six.vercel.app",
]

# También puedes permitir todas las solicitudes (NO recomendado en producción)
#CORS_ALLOW_ALL_ORIGINS = True  # O usar CORS_ALLOWED_ORIGINS para mayor control

SPECTACULAR_SETTINGS = {
    "TITLE": "AQUASMART",
    "DESCRIPTION": "API creada para la gestion de sistemas de reigo en colombia",
    "VERSION": "0.1.0",  # Aquí defines la versión
    "SERVE_INCLUDE_SCHEMA": False,
}

#EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', default=os.getenv("EMAIL_HOST_USER"))
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', default=os.getenv("EMAIL_HOST_PASSWORD"))  
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuración de Google Drive
GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE = os.path.join(BASE_DIR, 'API/google/client_secret.json')
GOOGLE_DRIVE_STORAGE_MEDIA_ROOT = 'Prueba'

# Configuración de Django Storages
DEFAULT_FILE_STORAGE = 'storages.backends.google_drive.GoogleDriveStorage'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]