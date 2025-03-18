from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, PermissionListView, GroupPermissionsView, GroupedPermissionsView,UserPermissionsView,AddUserPermissionsView,RemoveUserPermissionsView

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls),name="Lista-grupos-y-sus-permisos"),
    # Endpoint para asignar permisos a un grupo
    path('groups/<int:pk>/assign_permissions', GroupViewSet.as_view({'post': 'assign_permissions'}), name='asignar-permisos-a-grupos'),
    # Endpoint para quitar permisos de un grupo
    path('groups/<int:pk>/remove_permissions', GroupViewSet.as_view({'post': 'remove_permissions'}), name='remover-permisos-a-grupos'),
    # Endpoint para listar todos los permisos disponibles
    path('permissions', PermissionListView.as_view(), name='Lista-permisos-sin-agrupar'),
    # Endpoint para ver los permisos de un grupo específico
    path('groups/<int:pk>/permissions', GroupPermissionsView.as_view(), name='ver-permisos-de-un-grupo'),
    path('grouped_permissions', GroupedPermissionsView.as_view(), name='Ver-todos-los-permiso-agrupados'),
    path('users/<int:user_id>/permissions', UserPermissionsView.as_view(), name='user-permissions'),    
    path('users/<int:user_id>/add_permissions', AddUserPermissionsView.as_view(), name='asignar-permisos-a-usuarios'),    
    path('users/<int:user_id>/remove_permissions', RemoveUserPermissionsView.as_view(), name='remover-permisos-a-usuarios'),
]