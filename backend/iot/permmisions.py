from rest_framework.permissions import BasePermission
from .models import VALVE_48_ID

class CanChangeValveFlowPermission(BasePermission):
    """
    Permite cambiar caudal solo si:
    - Si es válvula bocatoma (tipo 48"), el usuario tiene permiso 'change_bocatoma_flow'.
    - Si es cualquier otra válvula (por ejemplo tipo 4"), el usuario tiene permiso 'change_all_lots_flow'.
    """

    def has_permission(self, request, view):
        # Para update, primero se necesita permiso de autenticación
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj es IoTDevice instancia

        if obj.device_type_id == VALVE_48_ID:
            return request.user.has_perm('iot.change_bocatoma_flow')
        else:
            # Otros dispositivos válvulas
            return request.user.has_perm('iot.change_all_lots_flow')
