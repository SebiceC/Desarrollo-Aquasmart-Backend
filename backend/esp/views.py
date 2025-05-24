from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import Consumo
from .serializers import ConsumoSerializer
import requests

@api_view(["POST"])
@permission_classes([AllowAny])
def recibir_consumo(request):
    serializer = ConsumoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"mensaje": "Consumo registrado"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([AllowAny])

def enviar_comando(request):
    data = request.data
    comando = data.get("comando")
    angulo = data.get("angulo")
    caudal = data.get("caudal")

    if not comando:
        return Response({"error": "El campo 'comando' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    payload = {"comando": comando}
    if angulo is not None:
        payload["angulo"] = angulo
    if caudal is not None:
        payload["caudal"] = caudal

    try:
        response = requests.post("https://mqtt-flask-api-production.up.railway.app/publicar_comando", json=payload)
        return Response(response.json(), status=response.status_code)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

