from rest_framework import serializers
from django.utils import timezone
from .models import Assignment, MaintenanceReport

class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Assignment"""
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id',
            'flow_request',
            'failure_report',
            'assigned_by',
            'assigned_by_name',
            'assigned_to',
            'assigned_to_name',
            'assignment_date',
            'reassigned',
        ]
        read_only_fields = ['id', 'assigned_by', 'assignment_date']

    def validate_flow_request(self, value):
        ''' Valida que no se permita crear una asignación de una solicitud que no debe ser delegada '''
        if value.requires_delegation == False:
            raise serializers.ValidationError({"error": "No se puede crear una asignación de esta solicitud."})
        
    def _validate_exclusive_assignment(self, data):
        flow_request = data.get('flow_request')
        failure_report = data.get('failure_report')
        if flow_request and failure_report:
            raise serializers.ValidationError("No se puede asignar un 'flow_request' y un 'failure_report' al mismo tiempo.")
        if not flow_request and not failure_report:
            raise serializers.ValidationError("Debe asignar al menos un 'flow_request' o un 'failure_report'.")

    def _validate_no_auto_assignment(self, data):
        if data.get('assigned_by') == data.get('assigned_to'):
            raise serializers.ValidationError("Un usuario no puede asignarse a sí mismo una solicitud o reporte.")

    def _validate_duplicate_assignment(self, data):
        flow_request = data.get('flow_request')
        failure_report = data.get('failure_report')
        assigned_to = data.get('assigned_to')

        if flow_request and Assignment.objects.filter(flow_request=flow_request, assigned_to=assigned_to).exists():
            raise serializers.ValidationError("Esta solicitud de caudal ya ha sido asignada a este usuario.")
        if failure_report and Assignment.objects.filter(failure_report=failure_report, assigned_to=assigned_to).exists():
            raise serializers.ValidationError("Este reporte de fallo ya ha sido asignado a este usuario.")

    def _validate_reassignment_logic(self, data):
        flow_request = data.get('flow_request')
        failure_report = data.get('failure_report')
        reassigned = data.get('reassigned', False)

        # Asegurar que `qs` siempre esté definido
        queryset = Assignment.objects.all()
        qs = queryset.exclude(id=self.instance.id) if self.instance else queryset

        if flow_request and qs.filter(flow_request=flow_request).exists() and not reassigned:
            raise serializers.ValidationError("Esta solicitud ya fue asignada previamente. Debe marcar como 'reassigned'.")

        if failure_report and qs.filter(failure_report=failure_report).exists() and not reassigned:
            raise serializers.ValidationError("Este reporte ya fue asignado previamente. Debe marcar como 'reassigned'.")

    def _validate_assigned_user_role(self, data):
        assigned_to = data.get('assigned_to')

        if assigned_to:
            valid_groups = ['Técnico', 'Operador']
            if not assigned_to.groups.filter(name__in=valid_groups).exists():
                raise serializers.ValidationError("Solo se puede asignar a usuarios del grupo 'Técnico' o 'Operador'.")
        
    def validate(self, data):
        self._validate_exclusive_assignment(data)
        self._validate_no_auto_assignment(data)
        self._validate_duplicate_assignment(data)
        self._validate_reassignment_logic(data)
        self._validate_assigned_user_role(data)

        return data

class MaintenanceReportSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MaintenanceReport"""
    assignment_details = AssignmentSerializer(source='assignment', read_only=True)

    class Meta:
        model = MaintenanceReport
        fields = [
            'id',
            'assignment',
            'assignment_details',
            'intervention_date',
            'images',
            'description',
            'status',
            'created_at',
            'is_approved',
        ]
        read_only_fields = ['created_at', 'id']

    def validate_assignment(self, value):
        """Evita informes duplicados para una misma asignación"""
        if self.instance is None and MaintenanceReport.objects.filter(assignment=value).exists():
            raise serializers.ValidationError("Ya existe un informe de mantenimiento para esta asignación.")
        return value

    def validate_intervention_date(self, value):
        """Valida que la fecha de intervención no sea futura"""
        if value > timezone.now():
            raise serializers.ValidationError("La fecha de intervención no puede estar en el futuro.")
        return value

    def validate(self, data):
        """Validaciones cruzadas y de usuario asignado"""
        request = self.context.get('request')
        if request:
            current_user = request.user
            assignment = data.get('assignment')

            if assignment and assignment.assigned_to != current_user:
                raise serializers.ValidationError("Solo el usuario asignado puede crear este informe.")
        images = data.get('images')
        description = data.get('description')        

        # Requiere al menos descripción o imagen
        if not images and not description:
            raise serializers.ValidationError("Debe ingresar al menos una imagen o una descripción.")        

        return data