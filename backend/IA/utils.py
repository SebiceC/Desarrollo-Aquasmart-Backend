import requests
import os
import json
from dotenv import load_dotenv
from django.conf import settings
import os
import tensorflow as tf
import joblib
import pandas as pd
import numpy as np
import hashlib
import uuid
from django.utils import timezone
import calendar

load_dotenv()

def formatear_predicciones(predicciones, fecha_inicio=None):
    """Convierte lista de floats en lista de diccionarios con mes y valor con 2 decimales."""
    if fecha_inicio is None:
        fecha_inicio = timezone.now()
    
    resultados = []
    for i, valor in enumerate(predicciones):
        mes_futuro = (fecha_inicio.month + i - 1) % 12 + 1
        año_futuro = fecha_inicio.year + ((fecha_inicio.month + i - 1) // 12)
        nombre_mes = calendar.month_name[mes_futuro]
        resultados.append({
            "mes": f"{nombre_mes} {año_futuro}",
            "valor": round(float(valor), 2)
        })
    return resultados

def generate_code_prediction(model,lot,meses):
        
        while True:
            fecha_actual = timezone.now()
            dia = str(fecha_actual.day)
            mes = str(fecha_actual.month)
            año = str(fecha_actual.year)
            code_prediction =f"{año[-2:]}{mes}{dia}-{lot}-{meses}"       
            if not model.objects.filter(code_prediction=code_prediction).exists():
                return code_prediction

def api_climate_request(location,date):
    
    key = os.getenv("KEY_CLIMATE")
    scope =f"{location}/{date}/{date}?unitGroup=metric&include=days&key={key}&contentType=json"
    url_api = os.getenv("URL_CLIMATE")
    campos_deseados = [
    "datetime", "tempmax", "tempmin", "precip", "precipprob", "precipcover",
    "windgust", "windspeed", "pressure", "cloudcover",
    "solarradiation", "sunrise", "sunset"
]   

    headers = {
        
        'Accept': 'application/json'
    }

    url_protegido = f"{url_api}{scope}"
    response = requests.get(url_protegido, headers=headers)   
    if response.status_code == 200:
        data = response.json()
        print("Datos recibidos desde la API:")
        #print(json.dumps(data, indent=4)) 
        dias = data.get("days", [])
        dias_filtrados = []
        print(json.dumps(dias[0], indent=4))
        for dia in dias:
            entrada = {clave: dia.get(clave) for clave in campos_deseados}          
            
            dias_filtrados.append(entrada)          
                    
        return data
    else:
        print(f"Error en solicitud protegida: {response.status_code}")
        return None


modelo_path = os.path.join(settings.BASE_DIR, 'ia', 'Modelo', 'modelo_transformer_consumo_final.h5')
features_path = os.path.join(settings.BASE_DIR, 'ia', 'Modelo', 'features_transformer.pkl')
scaler_x_path = os.path.join(settings.BASE_DIR, 'ia', 'Scaler', 'scaler_X_transformer.pkl')
scaler_y_path = os.path.join(settings.BASE_DIR, 'ia', 'Scaler', 'scaler_y_transformer.pkl')
modelo = tf.keras.models.load_model(modelo_path)
feature_names = joblib.load(features_path)
scaler_X = joblib.load(scaler_x_path)
scaler_y = joblib.load(scaler_y_path)


# Columnas usadas en el entrenamiento del scaler (sin Año y Mes_numero)
columnas_scaler = [
    'Consumo Neiva (m3-mes)', 'Temperatura Minima(°C)', 'Temperatura Maxima(°C)',
    'Precipitacion(mm)', 'Probabilidad de Precipitacion(%)',
    'Cubrimiento de Precipitacion(%)', 'Presión del nivel del Mar (mbar)',
    'Nubosidad (%)', 'Radiación Solar (W/m2)', 'Velocidad del Viento (km/h)',
    'Luminiscencia'
]

# Columnas completas del dataset
feature_columns = [
    'Año', 'Mes_numero', *columnas_scaler
]

# Función para crear la secuencia de entrada
def construir_secuencia(timesteps, datos_mes_actual, historico=None):
    if historico is not None and len(historico) >= timesteps - 1:
        secuencia = np.vstack([historico[-(timesteps - 1):], datos_mes_actual])
    else:
        secuencia = np.tile(datos_mes_actual, (timesteps, 1))
    return secuencia.reshape(1, timesteps, -1)

def predecir_n_meses( datos_actuales, historico, n_meses, columnas_scaler, timesteps):
    
    
    predicciones = []
    historial = historico.tolist() if historico is not None else []

    for i in range(n_meses):
        # Construir secuencia actual
        secuencia = construir_secuencia(timesteps, datos_actuales, np.array(historial) if historial else None)

        # Predecir consumo
        pred_esc = modelo.predict(secuencia, verbose=0)[0][0]

        # Crear dummy para desescalar solo la columna de consumo
        dummy = np.zeros((1, len(columnas_scaler)))
        indice_consumo = columnas_scaler.index('Consumo Neiva (m3-mes)')
        dummy[0, indice_consumo] = pred_esc
        pred_real = scaler_X.inverse_transform(dummy)[0,indice_consumo]
        predicciones.append(pred_real)

        # Crear nueva fila escalada con el nuevo consumo predicho (manteniendo otras variables constantes)
        nuevos_datos = datos_actuales.copy()
        nuevos_datos[indice_consumo] = pred_esc

        historial.append(nuevos_datos)
        if len(historial) > timesteps:
          historial.pop(0)

        datos_actuales = nuevos_datos

    return predicciones

