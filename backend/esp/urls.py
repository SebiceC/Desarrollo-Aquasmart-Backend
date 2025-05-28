from django.urls import path
from .views import recibir_consumo

urlpatterns = [
    path('recibir-consumo', recibir_consumo, name='recibir-consumo'),
    
]
