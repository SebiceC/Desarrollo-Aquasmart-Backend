
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClimateRecordViewSet, get_latest_climate_data,ConsuptionPredictionLotListCreateView

router = DefaultRouter()
router.register(r'climate-records', ClimateRecordViewSet)

urlpatterns = [
    #path('', include(router.urls)),
    path('latest-climate', get_latest_climate_data, name='latest-climate'),
    path('fetch-climate-data',ClimateRecordViewSet.as_view({'post': 'fetch_climate_data'}), name='fetch-climate-data'),
    path('predicciones-lote', ConsuptionPredictionLotListCreateView.as_view(), name='predicciones-lote'),
]