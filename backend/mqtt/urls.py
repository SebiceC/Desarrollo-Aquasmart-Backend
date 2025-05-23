from django.urls import path
from .views import send_mqtt_command

urlpatterns = [
    path('api/mqtt/send-command/', send_mqtt_command, name='send-mqtt-command'),
]
