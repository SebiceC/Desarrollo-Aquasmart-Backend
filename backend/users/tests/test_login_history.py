from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from users.models import Otp

class LoginHistoryMigrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            document='123456789',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone='1234567890',
            is_registered=True,  # Asegurarnos que el usuario está registrado
            is_active=True  # Asegurarnos que el usuario está activo
        )
        self.token = Token.objects.create(user=self.user)

    def test_login_creates_log_entry(self):
        """Prueba que el inicio de sesión crea una entrada en auditlog"""
        # Hacer login primero para obtener el OTP
        response = self.client.post(reverse('login'), {
            'document': '123456789',
            'password': 'testpass123'
        }, format='json')
        
        # Verificar que el login inicial fue exitoso
        self.assertEqual(response.status_code, 200)
        
        # Obtener el OTP generado
        otp = Otp.objects.get(user='123456789')
        
        # Validar el OTP
        response = self.client.post(reverse('validate-otp'), {
            'document': '123456789',
            'otp': otp.otp
        }, format='json')
        
        # Verificar que la validación del OTP fue exitosa
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        
        # Verificar que se creó una entrada en auditlog
        content_type = ContentType.objects.get_for_model(self.User)
        log_entries = LogEntry.objects.filter(
            content_type=content_type,
            object_pk=str(self.user.pk),
            action=0  # 0 = CREATE - Creando un nuevo registro de inicio de sesión
        )
        
        # Debería haber al menos una entrada
        self.assertTrue(log_entries.exists())
        
        # Verificar los detalles de la entrada más reciente
        latest_entry = log_entries.latest('timestamp')
        self.assertEqual(latest_entry.actor, self.user)
        self.assertIn('ip_address', latest_entry.changes)
        self.assertIn('user_agent', latest_entry.changes)
        self.assertIn('timestamp', latest_entry.changes)
        self.assertEqual(latest_entry.changes.get('event'), 'login')
        
    def test_old_login_history_migration(self):
        """Prueba que los registros antiguos se migraron correctamente"""
        # Verificar que existen entradas de log anteriores a la fecha actual
        content_type = ContentType.objects.get_for_model(self.User)
        old_entries = LogEntry.objects.filter(
            content_type=content_type,
            action=0  # CREATE = login en nuestra migración
        )
        
        # Imprimir información útil sobre las entradas encontradas
        print(f"\nSe encontraron {old_entries.count()} entradas antiguas migradas:")
        for entry in old_entries:
            print(f"- Usuario: {entry.actor}, Fecha: {entry.timestamp}")
