from django.urls import path
from .views import PlotViewSet,LotCreateView,ActivateLotView, DeactivateLotView
urlpatterns = [
    path('plots/register', PlotViewSet.as_view({'post': 'create'}),name='registrar-predio' ),
    path('plots/list', PlotViewSet.as_view({'get': 'list'}), name='listar-predios'),
    # Actualizar un predio 
    path('plots/<str:pk>/update', PlotViewSet.as_view({'put': 'update', 'patch': 'partial_update'}), name='actualizar-predio'),
    path('plots/<str:pk>/inhabilitar', PlotViewSet.as_view({'post': 'inactive'}), name='inhabilitar-predio'),
    path('plots/<str:pk>/habilitar', PlotViewSet.as_view({'post': 'active'}), name='habilitar-predio'),
    path('lots/register', LotCreateView.as_view(), name='lot-create'),
    path('lots/<str:id_lot>/activate', ActivateLotView.as_view(), name='activate-lot'),
    path('lots/<str:id_lot>/desactivate', DeactivateLotView.as_view(), name='deactivate-lot'),
]