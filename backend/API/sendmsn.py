from django.core.mail import send_mail
from django.conf import settings

def send_email(email, otp_generado, purpose ):
    """
    Envía un correo con el OTP de recuperación de contraseña.
    """
    if purpose == "login":   
        asunto = "Otp Inicio de Sesion"
        mensaje = f"Su OTP de inicio de sesion es: {otp_generado}. Úselo iniciar sesion."    
    elif purpose == "recover":                
        asunto = "Recuperación de Contraseña"
        mensaje = f"Su OTP de recuperación es: {otp_generado}. Úselo para restablecer su contraseña."
    
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.EMAIL_HOST_USER,  # Usa el remitente de settings.py
            recipient_list=[email],
            fail_silently=False,  # Genera errores si hay fallos
        )
        return "Correo enviado exitosamente"
    except Exception as e:
        return f"Error al enviar correo: {e}"
        
def send_email2(email, otp_generado, purpose, name):
    """
    Envía un correo con el OTP de inicio de sesión o recuperación de contraseña con formato HTML.
    """
    if purpose == "login":
        asunto = "🔐 OTP para Inicio de Sesión"
        mensaje_texto = f"Su OTP de inicio de sesión es: {otp_generado}. Úselo para iniciar sesión."
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
            <h2 style="color: #2E86C1;">🔐 OTP para Inicio de Sesión</h2>
            <p style="font-size: 18px;">Hola {name},</p>
            <p style="font-size: 16px;">Su código OTP para iniciar sesión es:</p>
            <h1 style="color: #E74C3C;">{otp_generado}</h1>
            <p style="font-size: 14px; color: #555;">Este código expirará en unos minutos.</p>
        </body>
        </html>
        """
    elif purpose == "recover":
        asunto = "🔑 Recuperación de Contraseña"
        mensaje_texto = f"Su OTP de recuperación es: {otp_generado}. Úselo para restablecer su contraseña."
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
            <h2 style="color: #D35400;">🔑 Recuperación de Contraseña</h2>
            <p style="font-size: 18px;">Hola{name},</p>
            <p style="font-size: 16px;">Su código OTP para recuperar su contraseña es:</p>
            <h1 style="color: #E74C3C;">{otp_generado}</h1>
            <p style="font-size: 14px; color: #555;">Este código expirará en unos minutos.</p>
        </body>
        </html>
        """

    try:
        send_mail(
            subject=asunto,
            message=mensaje_texto,  # Mensaje en texto plano
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
            html_message=mensaje_html  # Mensaje en HTML
        )
        return "Correo enviado exitosamente"
    except Exception as e:
        return f"Error al enviar correo: {e}"