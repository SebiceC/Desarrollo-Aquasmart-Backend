from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def _send_notification_email(subject, context, template_name, recipient_email):
    """Función helper para enviar correos electrónicos"""
    try:
        message_text = render_to_string(f'emails/{template_name}.txt', context)
        message_html = render_to_string(f'emails/{template_name}.html', context)
        
        send_mail(
            subject=subject,
            message=strip_tags(message_text),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
            html_message=message_html
        )
        return True
    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False

def _get_safe_attr(obj, *attrs, default="No especificado"):
    """Obtiene de forma segura atributos de un objeto"""
    if not obj:
        return default
        
    for attr in attrs:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            return str(value) if value is not None else default
            
    return default

def _get_plot_display(plot):
    """Obtiene representación segura de un predio"""
    return _get_safe_attr(plot, 'nombre', 'name', 'codigo', 'code', 'id_plot', default="Predio")

def _get_lot_display(lot):
    """Obtiene representación segura de un lote"""
    return _get_safe_attr(lot, 'nombre', 'name', 'codigo', 'code', 'id_lot', default="Lote")

# Funciones para notificaciones de reportes de fallos
def send_failure_report_created_notification(report):
    """Notificación de creación de reporte"""
    try:
        subject = "✅ Nuevo Reporte de Fallo Creado"
        
        context = {
            'report_id': report.id,
            'failure_type': report.get_failure_type_display(),
            'created_at': report.created_at.strftime("%d/%m/%Y %H:%M"),
            'plot_name': _get_plot_display(report.plot),
            'lot_name': _get_lot_display(report.lot),
            'observations': report.observations or "Sin observaciones",
            'status': report.get_status_display(),
            'user_name': report.created_by.get_full_name(),
        }
        
        return _send_notification_email(subject, context, 'failure_report_created', report.created_by.email)
    except Exception as e:
        print(f"Error al preparar notificación de reporte creado: {str(e)}")
        return False

def send_failure_report_status_notification(report):
    """Notificación de cambio de estado de reporte"""
    try:
        subject = f"🔄 Actualización de Estado - Reporte #{report.id}"
        
        context = {
            'report_id': report.id,
            'failure_type': report.get_failure_type_display(),
            'status': report.get_status_display(),
            'plot_name': _get_plot_display(report.plot),
            'lot_name': _get_lot_display(report.lot),
            'finalized_at': report.finalized_at.strftime("%d/%m/%Y %H:%M") if report.finalized_at else "No finalizado",
            'observations': report.observations or "Sin observaciones",
            'user_name': report.created_by.get_full_name(),
        }
        
        return _send_notification_email(subject, context, 'failure_report_status', report.created_by.email)
    except Exception as e:
        print(f"Error al preparar notificación de estado de reporte: {str(e)}")
        return False

# Funciones para notificaciones de solicitudes de caudal
def send_flow_request_created_notification(request):
    """Notificación de creación de solicitud de caudal"""
    try:
        plot = request.lot.plot if hasattr(request.lot, 'plot') else None
        
        subject = "✅ Nueva Solicitud de Caudal Creada"
        
        context = {
            'request_id': request.id,
            'request_type': request.get_flow_request_type_display(),
            'created_at': request.created_at.strftime("%d/%m/%Y %H:%M"),
            'plot_name': _get_plot_display(plot),
            'lot_name': _get_lot_display(request.lot),
            'requested_flow': f"{request.requested_flow} L/s" if request.requested_flow is not None else "No especificado",
            'observations': request.observations or "Sin observaciones",
            'status': request.get_status_display(),
            'user_name': request.created_by.get_full_name(),
            'requires_delegation': "Sí" if request.requires_delegation else "No",
        }
        
        return _send_notification_email(subject, context, 'flow_request_created', request.created_by.email)
    except Exception as e:
        print(f"Error al preparar notificación de solicitud creada: {str(e)}")
        return False

def send_flow_request_decision_notification(request):
    """Notificación de decisión sobre solicitud de caudal"""
    try:
        plot = request.lot.plot if hasattr(request.lot, 'plot') else None
        
        subject = f"📌 Decisión sobre Solicitud #{request.id}"
        
        context = {
            'request_id': request.id,
            'request_type': request.get_flow_request_type_display(),
            'status': request.get_status_display(),
            'is_approved': "Aprobada" if request.is_approved else "Rechazada",
            'plot_name': _get_plot_display(plot),
            'lot_name': _get_lot_display(request.lot),
            'finalized_at': request.finalized_at.strftime("%d/%m/%Y %H:%M") if request.finalized_at else "No finalizado",
            'observations': request.observations or "Sin observaciones",
            'user_name': request.created_by.get_full_name(),
            'new_flow': f"{request.requested_flow} L/s" if request.is_approved and request.requested_flow else "Sin cambios",
        }
        
        return _send_notification_email(subject, context, 'flow_request_decision', request.created_by.email)
    except Exception as e:
        print(f"Error al preparar notificación de decisión de solicitud: {str(e)}")
        return False

# Funciones para notificaciones de asignación y mantenimiento
def send_assignment_notification(assignment):
    """Notificación cuando se asigna una solicitud/reporte"""
    try:
        # Determinar si es para solicitud o reporte
        if assignment.flow_request:
            obj_type = f"Solicitud de {assignment.flow_request.get_flow_request_type_display()}"
            obj_id = assignment.flow_request.id
            obj_status = assignment.flow_request.get_status_display()
        else:
            obj_type = f"Reporte de {assignment.failure_report.get_failure_type_display()}"
            obj_id = assignment.failure_report.id
            obj_status = assignment.failure_report.get_status_display()

        subject = f"📌 Nueva Asignación - {obj_type} #{obj_id}"
        
        context = {
            'object_type': obj_type,
            'object_id': obj_id,
            'object_status': obj_status,
            'assigned_by': assignment.assigned_by.get_full_name(),
            'assigned_to': assignment.assigned_to.get_full_name(),
            'assignment_date': assignment.assignment_date.strftime("%d/%m/%Y %H:%M"),
            'is_reassignment': "Sí" if assignment.reassigned else "No",
        }
        
        # Enviar correo tanto al asignador como al asignado
        return all([
            _send_notification_email(subject, context, 'assignment_created', assignment.assigned_by.email),
            _send_notification_email(subject, context, 'assignment_created', assignment.assigned_to.email)
        ])
    except Exception as e:
        print(f"Error al preparar notificación de asignación: {str(e)}")
        return False

def send_maintenance_report_notification(report):
    """Notificación cuando se crea un informe de mantenimiento"""
    try:
        subject = f"📄 Informe de Mantenimiento #{report.id} - {report.get_status_display()}"
        
        # Determinar si es para solicitud o reporte
        if report.assignment.flow_request:
            obj_type = "Solicitud de Caudal"
            obj_id = report.assignment.flow_request.id
        else:
            obj_type = "Reporte de Fallo"
            obj_id = report.assignment.failure_report.id

        context = {
            'report_id': report.id,
            'object_type': obj_type,
            'object_id': obj_id,
            'intervention_date': report.intervention_date.strftime("%d/%m/%Y %H:%M"),
            'technician': report.assignment.assigned_to.get_full_name(),
            'supervisor': report.assignment.assigned_by.get_full_name(),
            'status': report.get_status_display(),
            'is_approved': "Aprobado" if report.is_approved else "Pendiente",
            'description': report.description or "No se proporcionó descripción",
        }
        
        # Enviar al técnico y al supervisor
        return all([
            _send_notification_email(subject, context, 'maintenance_report', report.assignment.assigned_to.email),
            _send_notification_email(subject, context, 'maintenance_report', report.assignment.assigned_by.email)
        ])
    except Exception as e:
        print(f"Error al preparar notificación de informe: {str(e)}")
        return False