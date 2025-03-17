from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, PermissionListView, GroupPermissionsView, GroupedPermissionsView,UserPermissionsView

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint para asignar permisos a un grupo
    path('groups/<int:pk>/assign_permissions', GroupViewSet.as_view({'post': 'assign_permissions'}), name='assign-permissions'),
    # Endpoint para quitar permisos de un grupo
    path('groups/<int:pk>/remove_permissions', GroupViewSet.as_view({'post': 'remove_permissions'}), name='remove-permissions'),
    # Endpoint para listar todos los permisos disponibles
    path('permissions', PermissionListView.as_view(), name='permission-list'),
    # Endpoint para ver los permisos de un grupo específico
    path('groups/<int:pk>/permissions', GroupPermissionsView.as_view(), name='group-permissions'),
    path('grouped_permissions', GroupedPermissionsView.as_view(), name='grouped-permissions'),
    path('users/<int:user_id>/permissions/', UserPermissionsView.as_view(), name='user-permissions'),
]