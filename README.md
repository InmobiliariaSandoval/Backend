# Descripción

Archivos que conforman el Backend de la aplicación contando con dos versiones para diferentes escenario:

* La rama principal `main` utiliza la base de datos dentro del contenedor de la aplicación a utilizar en el hosting

* La rama `datos_persistentes` utiliza la base de datos alojada en el hosting SQLite3 [Turso](https://turso.tech/) (la inmobiliaria te dará los datos de acceso).

La única diferencia, además de la velocidad de escritura y lectura, es que, en caso de que se necesite volver a hacer una *build* de la aplicación en el hosting, puede llegar a ocurrir que se sobre escriba la base de datos y la información previa se pierda.

## Instalación local

Para trabajar con el sistema de manera local en tu dispositivo, realizar cambios y demás acciones se necesitan seguir los siguientes pasos:

1. Clona el repositorio en tu computadora, para ello asegurate de tener instalado `git` y utilizando el siguiente comando realiza el clonado del repositorio:

    ```
    git clone https://github.com/InmobiliariaSandoval/Backend
    ```


2. Una vez que se haya clonado el respositorio, en la carpeta raíz encontrarás el archivo `requirements.txt`, el cuál contiene todas las dependencias que el sistema necesita para funcionar. Para instalar dichas dependencias ejecute el siguiente comando:

    ```
    pip install -r requirements.txt
    ```

3. Finalmente, lo que necesitas hacer es crear un archivo llamado `.env` en donde deberás de agregar los siguientes valores:

   ```
    API_KEY = ''
    API_SECRET = ''
    CONTRASENA = ''
    EMAIL_EMPRESA = ''
    URL_FRONTEND = ''
    TURSO_AUTH = ''
    TURSO_URL = ''
    ```
    Todos los valores serán proporcionados por parte de la inmobiliaria, además, en caso de que se trabaje con la opción dos, es decir, en la rama `main` los últimos dos valores pueden ser omitidos

    * Si surje algún problema, intenta agregar la siguiente línea en los archivos de python donde se utilice las variables de entorno, es decir, en los archivos `main.py` y `operaciones_token.py`, en caso de que estés trabajando en la rama `datos_persistentes` también incluyelos en el archivo `base_datos.py`

        Tome como referencia el siguiente código de ejemplo:

        ```python

        from dotenv import load_dotenv
        import os

        load_dotenv()  # Carga las variables desde el archivo .env

        secret_key = os.getenv("SECRET_KEY")
        database_url = os.getenv("DATABASE_URL")

        print(f"Secret Key: {secret_key}")
        print(f"Database URL: {database_url}")

        ```



Además, una cosa que puedes realizar, es re ejecutar el `script.sql` para limpiar el archivo `inmobiliaria.db`, si deseas hacer esto, utiliza el comando:

```
sqlite3 inmobiliaria.db < script.sql
```

## Hostings

Este apartado debería de estar alojado en los siguientes hostings:

* [Zeabur](https://zeabur.com/)
* [Turso](https://turso.tech/) - Opcional

La prueba y demostración del sistema se realizo en el hosting de [Heroku](https://www.heroku.com/)

Si desea replicar el mismo proceso, solamente necesitará añadir dos archivos extras en la raíz del proyecto, uno con el nombre de `Procfile` y otro con el nombre de `runtime.txt`

* `runtime.txt` es el archivo que almacena la versión de python necesaria para ejecutar y correr el programa, durante el desarrollo se utilizó `python 3.12.4`. En el archivo se debe de representar de la siguiente manera:

    ```
    python-3.12.4
    ```
* `Procfile` es un archivo indispensable el cuál indica la manera en que se ejecutará la aplicación dentro del hosting de [Heroku](https://devcenter.heroku.com/articles/procfile), para el hosting de [Zeabur](https://zeabur.com/docs/es-ES) no es necesario, si desea saber más de ambos, puede leer sus documentaciones respectivas, solo de click enncima de cualquiera de ellos de este parrafo. El archivo debe se debe de representar de la siguiente manera:

    ```
    web: gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT main:app
    ```

<hr>

Si tiene alguna duda, problema o detalle trabajando con el sistema intente contactando a los desarrolladores.
