from django.urls import path
from .views import FlowMeasurementViewSet, FlowMeasurementPredioViewSet, FlowMeasurementLoteViewSet,FlowInconsistencyViewSet

urlpatterns = [
    # Endpoints para FlowMeasurement bocatoma
    path('flow-measurements/bocatoma', FlowMeasurementViewSet.as_view({'get': 'list'}), name='flowmeasurement-list'),    
    path('flow-measurements/bocatoma/create', FlowMeasurementViewSet.as_view({'post': 'create'}), name='flowmeasurement-create'),      
      
    # Endpoints para FlowMeasurementPredio
    path('flow-measurements/predio/listar', FlowMeasurementPredioViewSet.as_view({'get': 'list'}), name='flowmeasurement-predio-list'),
    path('flow-measurements/predio/crear', FlowMeasurementPredioViewSet.as_view({'post': 'create'}), name='flowmeasurement-predio-create'),   
    
    # Endpoints para FlowMeasurementLote
    path('flow-measurements/lote/listar', FlowMeasurementLoteViewSet.as_view({'get': 'list'}), name='flowmeasurement-lote-list'),
    path('flow-measurements/lote/crear', FlowMeasurementLoteViewSet.as_view({'post': 'create'}), name='flowmeasurement-lote-create'),  
    
      # Endpoints para FlowInconsistencies  
    path ('flow-inconsistencies', FlowInconsistencyViewSet.as_view({'get': 'list'}),name='flow-inconsistency-list' ),
    path('flow-inconsistencies/<int:pk>',FlowInconsistencyViewSet.as_view({'get': 'retrieve'}),name='flow-inconsistency-detail')
 
]