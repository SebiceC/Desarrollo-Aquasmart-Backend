# Desarrollo-Aquasmart-Backend
Repositorio de desarrollo backend del sistema de gestion de distritos de riego acorde a la documentacion realizada el semestre pasado
 

#### Clonar repositorio SSH.

    git clone git@github.com:SebiceC/Desarrollo-Aquasmart-Backend.git

#### Clonar repositorio HTTPS.

    git clone https://github.com/SebiceC/Desarrollo-Aquasmart-Backend.git
##
#### Entrar a la carpeta del proyecto

    cd Desarrollo-Aquasmart-Backend

#### Crear entorno virtual   

     python -m venv .venv

#### Instalar las dependencias del archivo requirements.txt

    pip install -r requirements.txt

#### Ejecutar las migraciones

    python manage.py migrate

#### Crear SuperUsuario

    python manage.py createsuperuser
    
## Crear archivo .env

Dentro del el archivo .env se crea sa sigiente variable

##### Palabra secreta y Billing secret token:
    SECRET_KEY ='palabar secreta'
    BILLING_SECRET_TOKEN="Token que quieran poner"

se puede dejar esa palabra o cambiar si lo desea (Recomendado).
##
##### Credenciales  para envio de correos:

Credenciales para hacer envia los correos mediante (Gmail).
- Para sacar la contraseña de aplicaccion debe primero tener activa la verificacion de 2 pasos

    EMAIL_HOST_PASSWORD= ''
    EMAIL_HOST_USER = ''
##
##### Credenciales para usar Google Drive para el almacenamiento:
Credenciales que se consiguen en [Google Cloud](https://console.cloud.google.com/projectselector2/iam-admin/)

    PROJECT_ID=""
    PRIVATE_KEY_ID=""
    PRIVATE_KEY=""
    CLIENT_EMAIL=""
    CLIENT_ID=""
    AUTH_URI=""
    TOKEN_URI=""
    AUTH_PROVIDER_CERT_URL=""
    CLIENT_X509_CERT_URL=""
##
##### Credenciales del api climatica:
Para obtener las credenciales de la API Climatica se debe ir a [Visual Crossing](https://www.visualcrossing.com/) y crear una cuenta y asi conseguir la API KEY:

    URL_CLIMATE = "Url de la api para hacer las consultas"
    KEY_CLIMATE = "API KEY de VC"
 ##
##### Credenciales del api facturacion electronica (Colombia): 
Para obtener las credenciales de la API de facturacion se debe ir [Factus](https://www.factus.com.co/) obtener un plan.

    url_api_f =""
    client_id_f=""    
    client_secret_f=""
    username_f=""
    password_f=""
 ##    

#### Lanzamiento del servidor

    python manage.py runserver
