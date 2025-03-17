from django.urls import path
from .views import PlotViewSet
urlpatterns = [
    path('register', PlotViewSet.as_view({'post': 'create'}),name='registrar-predio' ),
    path('list', PlotViewSet.as_view({'get': 'list'}), name='listar-predios'),
    # Actualizar un predio 
    path('<str:pk>/update/', PlotViewSet.as_view({'put': 'update', 'patch': 'partial_update'}), name='actualizar-predio'),
    path('<str:pk>/inhabilitar/', PlotViewSet.as_view({'post': 'inactive'}), name='inhabilitar-predio'),
    path('<str:pk>/habilitar/', PlotViewSet.as_view({'post': 'active'}), name='habilitar-predio'),
]