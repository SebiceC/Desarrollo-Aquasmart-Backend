from django.urls import path
from .views import recibir_consumo, enviar_comando

urlpatterns = [
    path('recibir-consumo', recibir_consumo, name='recibir-consumo'),
    path('enviar-comandos', enviar_comando, name='enviar-comando'),
]
