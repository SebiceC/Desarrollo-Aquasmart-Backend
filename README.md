

# Desarrollo-Aquasmart
Repositorio de desarrollo del sistema de gestion de distritos de riego acorde a la documentacion realizada el semestre pasado
## Backend

#### Clonar repositorio SSH.

    git clone git@github.com:SebiceC/Desarrollo-Aquasmart-Backend.git

    git clone git@github.com:SebiceC/Desarrollo-Aquasmart-Backend.git

#### Clonar repositorio HTTPS.

    git clone https://github.com/SebiceC/Desarrollo-Aquasmart-Backend.git

    git clone https://github.com/SebiceC/Desarrollo-Aquasmart-Backend.git

#### Entrar a la carpeta del proyecto

    cd Desarrollo-Aquasmart

    cd Desarrollo-Aquasmart

#### Crear entorno virtual

     python -m venv venv

#### Instalar las dependencias del archivo requirements.txt

    pip install -r requirements.txt


### Ejecutar instalación de hooks

    bash setup_hooks.sh


## Instalar pre-commit
    pre-commit install
    pre-commit run --all-files


#### Ejecutar las migraciones

    python manage.py migrate

    python manage.py migrate

#### Crear SuperUsuario

    python manage.py createsuperuser

#### Crear archivo .env
Dentro del el archivo .env se crea sa sigiente variable

    SECRET_KEY ='palabar secreta'

se puede dejar esa palabra o cambiar si lo desea (Recomendado).

Credenciales para hacer envia los correos mediante (Gmail):
Para sacar la contraseña de aplicaccion debe primero tener activa la verificacion de 2 pasos

    EMAIL_HOST_PASSWORD= ''
    EMAIL_HOST_USER = ''

Credenciales que se consiguen en el google cloud
[Google Cloud](https://console.cloud.google.com/projectselector2/iam-admin/)

    PROJECT_ID=""
    PRIVATE_KEY_ID=""
    PRIVATE_KEY=""
    CLIENT_EMAIL=""
    CLIENT_ID=""
    AUTH_URI=""
    TOKEN_URI=""
    AUTH_PROVIDER_CERT_URL=""
    CLIENT_X509_CERT_URL=""

    python manage.py createsuperuser

#### Crear archivo .env
Dentro del el archivo .env se crea sa sigiente variable

    SECRET_KEY ='palabar secreta'

se puede dejar esa palabra o cambiar si lo desea (Recomendado).

Credenciales para hacer envia los correos mediante (Gmail):
Para sacar la contraseña de aplicaccion debe primero tener activa la verificacion de 2 pasos

    EMAIL_HOST_PASSWORD= ''
    EMAIL_HOST_USER = ''

Credenciales que se consiguen en el google cloud
[Google Cloud](https://console.cloud.google.com/projectselector2/iam-admin/)

    PROJECT_ID=""
    PRIVATE_KEY_ID=""
    PRIVATE_KEY=""
    CLIENT_EMAIL=""
    CLIENT_ID=""
    AUTH_URI=""
    TOKEN_URI=""
    AUTH_PROVIDER_CERT_URL=""
    CLIENT_X509_CERT_URL=""

#### Lanzamiento del servidor

    python manage.py runserver
