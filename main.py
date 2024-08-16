from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import asyncio
import os

# Funciones para el manejo de datos
from lotes.operaciones_lotes import *
from ventas.operaciones_venta import *
from validacion.operaciones_token import *
from clientes.operaciones_clientes import *
from vendedores.operaciones_vendedores import *
from notificaciones.operaciones_notificaciones import *

# Módulos de la base de datos
import esquemas
from base_datos import SessionLocal, engine

# Módulos de manejo de la base de datos
from sqlalchemy.orm import Session

# Módulos de las funciones del archivo usuarios

# Módulos de fastapi (seguridad y conexión)
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, Query, status, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Módulo de tipo de datos
from typing import List

# Módulo de encriptación
import hashlib

load_dotenv()


# Inicializar los módelos de la base de datos
modelos.Base.metadata.create_all(bind=engine)

# Objeto de la aplicacion
app = FastAPI()

# Objetos de seguridad
security = HTTPBasic()
securityBearer = HTTPBearer()

# Orígenes que se permiten conectar a la API
origins = [os.getenv('URL_FRONTEND')]

# Configuración de origenes, métodoso, credenciales y cabeceras
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Dependencia de la base de datos
def obtener_db():
    # Inicializar base de datos
    base_datos = SessionLocal()

    # Crear la conexión y cerrarla
    try:
        yield base_datos
    finally:
        base_datos.close()

#########################################
# Función para manejar errores globales #
#########################################

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error inesperado con el servidor"}
    )

# Función de validación reutilizable
async def validar_token_api(db: Session, token_acceso: str) -> None:

    # Verificar que se proporcione un token de acceso
    if not token_acceso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Token no proporcionado o invalido')

    # Obtener el token actual de la base de datos
    token_actual = await verificar_token(db, token_acceso)

    # Verificar que el token exista en la db
    if not token_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token no válido')

    # Verificar que el token sea igual al de la db
    if token_acceso != token_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token no válido')

    # Obtener el estado de la sesión
    estado_cuenta = await obtener_estado_cuenta_usuario(db, token_acceso)

    # Verificar que esté en una sesión activa
    if not estado_cuenta:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='No tienes una sesión activa.')

########################################################
# Funciones para la validación del usuario y su acceso #
########################################################

# Endpoint para obtener el token de acceso
@app.get("/token/", status_code=status.HTTP_202_ACCEPTED, summary="Endpoint para obtener el token")
async def validar_token(base_datos: Session = Depends(obtener_db), credenciales_token: HTTPBasicCredentials = Depends(security)):
    """
        # Endpoint que obtiene que el token de acceso

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 202 - Código de confirmación de token aceptado
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el correo electronico y la contraseña ingresada por el usuario
    correo_electronico = credenciales_token.username
    contrasena = credenciales_token.password

    # Verificar que se haya ingresado correo y contraseña
    if not correo_electronico or not contrasena:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Correo electronico o contraseña no proporcionada')

    # Encriptar la contraseña
    contrasena_encriptada = hashlib.md5(contrasena.encode()).hexdigest()

    # Obtener el token del usuario
    token_usuario = await obtener_token_usuario(base_datos, correo_electronico, contrasena_encriptada)

    # Verificar que le usuario exista en la db
    if not token_usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales no válidas")

    # Obtener el estado de cuenta
    estado_cuenta = await obtener_estado_cuenta_usuario(base_datos, token_usuario)

    # Verificar que exista el usuario
    if estado_cuenta == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

    # Verificar que la sesión no esté activa
    if estado_cuenta:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ya has iniciado sesión.")

    # Obtener nuevo token
    nuevo_token = await cambiar_token_nueva_sesion(base_datos, correo_electronico)

    # Nombre del usuario
    nombre_usuario = await obtener_configuracion(base_datos, correo_electronico)

    # Verificar que el cambio se haya realizado
    if not nuevo_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado o sesión activa")

    # Verificar que exista el nombre de usuario
    if not nombre_usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nombre de usuario no encontrado")

    return {'Token': nuevo_token, 'Nombre_usuario': nombre_usuario}

# Endpoint para cerrar sesión del usuario
@app.get("/cerrar_sesion", status_code=status.HTTP_200_OK, summary="Endpont para cerrar sesión")
async def cerrar_sesion(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que valida que el token sea válido

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Cerrar sesión
    estado_cuenta = await cambiar_estado_cuenta_usuario(base_datos, token_acceso)

    # Verificar que se haya podido cerrar la sesión
    if not estado_cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se pudo cerrar sesión.')

    return {"success":True}

# Endpoint para reiniciar una sesión
@app.get("/reiniciar_sesion", status_code=status.HTTP_200_OK, summary="Reinicia la asesión del usuario")
async def reiniciar_sesion(frase: str, base_datos: Session = Depends(obtener_db), credenciales_acceso: HTTPBasicCredentials = Depends(security)):
    """
        # Endpoint que reinicia la sesión del usuario

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 404 - Código de error de datos no encontrados
        * 500 - Código de error del servidor
    """
    # Obtener el correo electronico y la contraseña ingresada por el usuario
    correo_electronico = credenciales_acceso.username
    contrasena = credenciales_acceso.password

    # Verificar que se haya ingresado correo y contraseña
    if not correo_electronico or not contrasena:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Correo electronico o contraseña no proporcionada')

    # Encriptar la contraseña
    contrasena_encriptada = hashlib.md5(contrasena.encode()).hexdigest()
    frase_obtenida = hashlib.md5(frase.encode()).hexdigest()

    # Obtener el usuario
    usuario_verificar = await obtener_usuario(base_datos, correo_electronico, contrasena_encriptada)

    # Verificar que exista
    if not usuario_verificar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró al usuario")

    # Obtener frase para verificar
    frase_verificar = await verificar_frase(base_datos, frase_obtenida, correo_electronico, contrasena_encriptada)

    # Verificar que sea correcta
    if not frase_verificar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Frase incorrecta")

    # Cambio de sesión
    comprobador = await cambiar_estado_palabra(base_datos, frase_obtenida)

    # Verificar
    if not comprobador:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se logró reiniciar la sesión")

    return {"success": True}

# Endpoint para reiniciar una sesión
@app.post("/recuperar_contrasena", status_code=status.HTTP_200_OK, summary="Recupera la contraseña")
async def recuperar_contrasena(datos: esquemas.RecuperarContrasena, base_datos: Session = Depends(obtener_db)):
    """
        # Endpoint que reinicia la sesión del usuario

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 404 - Código de error de datos no encontrados
        * 500 - Código de error del servidor
    """
    # Verificar que se haya ingresado correo y contraseña
    if not datos.correo_electronico or not datos.frase:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Correo electronico o frase no proporcionada')

    # Encriptar la contraseña
    frase_obtenida = hashlib.md5(datos.frase.encode()).hexdigest()

    # Cambio de sesión
    comprobador = await enviar_correo_contrasena(base_datos, datos.correo_electronico, frase_obtenida)

    # Verificar
    if not comprobador:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se logró enviar la contraseña")

    return {"success": True}

# Endpoint para validar el acceso al sistema
@app.get("/", status_code=status.HTTP_200_OK, summary="Endpoint para validar el acceso")
async def endpoint_raiz(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que valida que el token sea válido

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    return {'Mensaje': 'Token válido'}

# Función que lista la información de un configuración en especifico de la base de datos
@app.get('/configuracion_especifica/{identificador_usuario}', response_model=List[esquemas.Configuracion], status_code=status.HTTP_200_OK, summary="Muestra una configuración en especifico")
async def configuracion_especifica(identificador_usuario, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista una configuración especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información de la configuracio
    configuracion = await obtener_configuracion_especifica(base_datos, identificador_usuario)

    # Verificar que la respuesta no esté vacía
    if not configuracion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return configuracion

# Función que lista la información de un estado en especifico de la base de datos
@app.get('/obtener_estado_especifico/{identificador_estado}', response_model=List[esquemas.Estado], status_code=status.HTTP_200_OK, summary="Muestra un estado en especifico")
async def obtener_estado_especifico(identificador_estado, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un estado especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del estado
    estado = await obtener_un_estado(base_datos, identificador_estado)

    # Verificar que la respuesta no esté vacía
    if not estado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return estado

# Función que lista todos los estados disponibles en la base de datos
@app.get("/estados_republica", response_model=List[esquemas.Estado], status_code=status.HTTP_200_OK, summary="Enpoint para listar todos los estados")
async def obtener_estados_republica(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los estados disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener  el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    estado_republica = await obtener_todos_los_estados(base_datos)

    # Verificar que la respuesta no esté vacía
    if not estado_republica:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return estado_republica

# Función que se encarga de insertar un nuevo estado
@app.post("/agregar_estado", response_model=esquemas.Estado, status_code=status.HTTP_201_CREATED, summary="Añade un nuevo estado")
async def agregar_estado(estado_agregar: esquemas.EstadoCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agregar un estado a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(estado_agregar, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el comprobador de que no exista el estado
    comprobador_estado = await verificar_estado_existente(base_datos, estado=estado_agregar)

     # Verificar que no exista el estado
    if comprobador_estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe el estado o datos repetidos.")

    # Añadir el estado
    resultado_agregar = await agregar_un_nuevo_estado(base_datos, estado=estado_agregar)

    # Verificar que se ingresó correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar el estado.")

    return resultado_agregar

# Función que se encarga de actualizar un estado en la base de datos
@app.put("/actualizar_estado/{identificador_estado}", response_model=esquemas.Estado, status_code=status.HTTP_200_OK, summary="Actualiza un estado")
async def actualizar_estado(
    identificador_estado: str,
    estado_actualizar: esquemas.EstadoCreate,
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint actualiza la información de un estado disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(estado_actualizar, [""])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el estado
    comprobador_estado = await verficar_estado_municipio(base_datos, identificador_estado)

    # Verificar que exista el estado
    if not comprobador_estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el estado")

    # Verificar que no se repitan los datos
    comprobador_datos = await verificar_estado_existente(base_datos, estado_actualizar)

    # Verificar sus valores
    if comprobador_datos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos repetidos")

    # Actualizar el estado
    estado_actualizar = await actualizar_un_estado(base_datos, identificador_estado, estado_actualizar)

    # Verificar que se actuaizó correctamente
    if not estado_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el estado.")

    return estado_actualizar

# Función que se encarga de eliminar un estado en la base de datos
@app.delete("/eliminar_estado/{identificador_estado}", status_code=status.HTTP_200_OK, summary="Elimina un estado")
async def eliminar_estado(identificador_estado: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un estado en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el estado a eliminar
    estado_eliminar = await verficar_estado_municipio(base_datos, identificador_estado)

    # Verificar que exista el estado
    if not estado_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el estado.")

    # Eliminar el municipio
    resultado_eliminar = await eliminar_un_estado(base_datos, identificador_estado=identificador_estado)

    # Verificar que se eliminó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el estado.")

    return resultado_eliminar

# Función que lista la información de un munipicio en especifico de la base de datos
@app.get('/obtener_municipio_especifico/{identificador_municipio}', response_model=List[esquemas.Municipio], status_code=status.HTTP_200_OK, summary="Muestra un estado en especifico")
async def obtener_municipio_especifico(identificador_municipio, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un estado especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del municipio
    municipio = await obtener_un_municipio(base_datos, identificador_municipio)

    # Verificar que la respuesta no esté vacía
    if not municipio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return municipio

# Función que lista todos los municipios disponibles de la base de datos
@app.get("/obtener_todos_municipios", response_model=List[esquemas.Municipio], status_code=status.HTTP_200_OK, summary="Endpoint que lista todos los municipios")
async def obtener_todos_municipios(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los municipios disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los municipios
    muncipios = await obtener_todos_los_municipio_sin_estado(base_datos)

    # Verificar que la respuesta no esté vacia
    if not muncipios:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return muncipios

# Función que lista todos los municipios en base al estado seleccionado
@app.get("/{identificador_estado}/municipios", response_model=List[esquemas.Municipio], status_code=status.HTTP_200_OK, summary="Endpoint que lista los municipios")
async def obtener_municipios_estados(identificador_estado: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los municipios disponibles de un estado en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los municipios
    muncipios = await obtener_todos_los_municipios(base_datos, identificador_estado)

    # Verificar que la respuesta no esté vacia
    if not muncipios:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return muncipios

# Función que insertar un nuevo municipio a la base de datos
@app.post("/agregar_municipio", response_model=esquemas.Municipio, status_code=status.HTTP_201_CREATED, summary="Añade un nuevo municipio")
async def agregar_municipio(municipio: esquemas.MunicipioCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agregar un municipio a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(municipio, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Comprobar que exisate el estado
    comprobador_estado = await verficar_estado_municipio(base_datos, municipio.id_estado)

    if not comprobador_estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el estado.")

    # Comprobar que no se repite el municipio en un Estado
    comprobador_municipio = await verificar_municipio_existente(base_datos, municipio)

    if comprobador_municipio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Municipio ya existente en el estado.")

    # Añadir el municipio
    resultado_agregar = await agregar_nuevo_municipio(base_datos, municipio)

    # Verificar que se haya ingresado correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar el muniicipio.")

    return resultado_agregar

# Función que se encarga de actualizar un municipio en la base de datos
@app.put("/actualizar_municipio/{identificador_municipio}", response_model=esquemas.Municipio, status_code=status.HTTP_200_OK, summary="Actualizar una localidad")
async def actualizar_municipio(
    identificador_municipio: str,
    municipio_actualizar: esquemas.MunicipioCreate,
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint actualiza la información de un municipi disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(municipio_actualizar, [""])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el estado
    comprobador_estado = await verficar_estado_municipio(base_datos, municipio_actualizar.id_estado)

    # Verificar que exista el estado
    if not comprobador_estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el estado")

    # Obtener comprobador de que exista el municipio
    comprobador_municipio = await verificar_municipio_localidad(base_datos, identificador_municipio)

    # Verificar que exista el complejo
    if not comprobador_municipio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el municipio.")

    # Verificar que no se repitan los datos
    comprobador_datos = await verificar_municipio_actualizar(base_datos, identificador_municipio, municipio_actualizar)

    # Verificar sus valores
    if comprobador_datos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos repetidos")

    # Actualizar el complejo
    municipio_actualizar = await actualizar_un_municipio(base_datos, identificador_municipio, municipio_actualizar)

    # Verificar que se ingresó correctamente
    if not municipio_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el complejo.")

    return municipio_actualizar

# Función que se encarga de eliminar un municipio en la base de datos
@app.delete("/eliminar_municipio/{identificador_municipio}", status_code=status.HTTP_200_OK, summary="Elimina un municipio")
async def eliminar_municipio(identificador_municipio: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de una localidad en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el municipio a eliminar
    municipio_eliminar = await verificar_municipio_localidad(base_datos, identificador_municipio)

    # Verificar que exista el municipio
    if not municipio_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el municipio.")

    # Eliminar el municipio
    resultado_eliminar = await eliminar_un_municipio(base_datos, identificador_municipio=identificador_municipio)

    # Verificar que se eliminó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el municipio.")

    return resultado_eliminar

# Función que lista la información de una localidad en especifico de la base de datos
@app.get('/obtener_localidad_especifica/{identificador_localidad}', response_model=List[esquemas.Localidad], status_code=status.HTTP_200_OK, summary="Muestra un estado en especifico")
async def obtener_localidad_especifica(identificador_localidad, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un estado especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del localidad
    localidad = await obtener_una_localidad(base_datos, identificador_localidad)

    # Verificar que la respuesta no esté vacía
    if not localidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return localidad

# Función que lista todos los municipios disponibles de la base de datos
@app.get("/obtener_todas_localidades", response_model=List[esquemas.Localidad], status_code=status.HTTP_200_OK, summary="Lista todas las localidades")
async def obtener_todas_localidades(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todas las localidades disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los municipios
    localidades = await obtener_todas_las_localidades_sin_municipio(base_datos)

    # Verificar que la respuesta no esté vacia
    if not localidades:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return localidades

# Función que lista todas las localidades en base al muninicpio seleccionado
@app.get("/{identificador_municipio}/localidades", response_model=List[esquemas.Localidad], status_code=status.HTTP_200_OK, summary="Endpoint que lista las localidades")
async def obtener_localidades_municipios(identificador_municipio: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todas las localidades disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos las localidades
    localidades = await obtener_todas_las_localidades(base_datos, identificador_municipio)

    # Verificar que la respuesta no esté vacía
    if not localidades:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return localidades

# Función que insertar una nueva localidad a la base de datos
@app.post("/agregar_localidad", response_model=esquemas.Localidad, status_code=status.HTTP_201_CREATED, summary="Añade una nueva localidad")
async def agregar_localidad(localidad: esquemas.LocalidadCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agregar una localidad la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(localidad, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Comprobar que existe el municipio
    comprobador_municipio = await verificar_municipio_localidad(base_datos, localidad.id_municipio)

    if not comprobador_municipio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el municipio.")

    # Comprobar que no se repite la localidad en un Municipio
    comprobador_localidad = await verificar_localidad_existente(base_datos, localidad)

    if comprobador_localidad:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Localidad ya existente en el municipio.")

    # Añadir el municipio
    resultado_agregar = await agregar_nueva_localidad(base_datos, localidad)

    # Verificar que se haya ingresado correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar la localidad.")

    return resultado_agregar

# Función que se encarga de actualizar una localidad en la base de datos
@app.put("/actualizar_localidad/{identificador_localidad}", response_model=esquemas.Localidad, status_code=status.HTTP_200_OK, summary="Actualizar una localidad")
async def actualizar_localidad(
    identificador_localidad: str,
    localidad_actualizar: esquemas.LocalidadCreate,
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint actualiza la información de una localida  disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(localidad_actualizar, [""])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el municipio
    comprobador_municipio = await verificar_municipio_localidad(base_datos, localidad_actualizar.id_municipio)

    # Verificar que exista la localidad
    if not comprobador_municipio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el municipio")

    # Obtener comprobador de que exista la localidad
    comprobador_localidad = await verificar_localidad_complejo(base_datos, identificador_localidad)

    # Verificar que exista el complejo
    if not comprobador_localidad:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la localidad.")

    # Verificar que no se repitan los datos
    comprobador_datos = await verificar_localidad_actualizar(base_datos, identificador_localidad, localidad_actualizar)

    # Verificar sus valores
    if comprobador_datos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos repetidos")

    # Actualizar el complejo
    localidad_actualizar = await actualizar_una_localidad(base_datos, identificador_localidad, localidad_actualizar)

    # Verificar que se ingresó correctamente
    if not localidad_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el complejo.")

    return localidad_actualizar

# Función que se encarga de eliminar una localidad en la base de datos
@app.delete("/eliminar_localidad/{identificador_localidad}", status_code=status.HTTP_200_OK, summary="Elimina una localidad")
async def eliminar_localidad(identificador_localidad: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de una localidad en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el localidad a eliminar
    localidad_eliminar = await verificar_localidad_complejo(base_datos, identificador_localidad)

    # Verificar que exista la localidad
    if not localidad_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe la localidad.")

    # Eliminar la localidad
    resultado_eliminar = await eliminar_una_localidad(base_datos, identificador_localidad=identificador_localidad)

    # Verificar que se eliminó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar la localidad.")

    return resultado_eliminar

# Función que lista la información de un complejo en especifico de la base de datos
@app.get('/obtener_complejo_especifico/{identificador_complejo}', response_model=List[esquemas.ComplejoResidencial], status_code=status.HTTP_200_OK, summary="Muestra un estado en especifico")
async def obtener_complejo_especifico(identificador_complejo, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un estado especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del complejo
    complejo = await obtener_un_complejo(base_datos, identificador_complejo)

    # Verificar que la respuesta no esté vacía
    if not complejo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return complejo

# Función que lista todos los complejos disponibles de la base de datos
@app.get("/obtener_todos_complejos", response_model=List[esquemas.ComplejoResidencial], status_code=status.HTTP_200_OK, summary="Lista todas los complejos")
async def obtener_todos_complejos(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los complejos disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los municipios
    complejos = await obtener_todos_complejos_sin_localidad(base_datos)

    # Verificar que la respuesta no esté vacia
    if not complejos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return complejos

# Función que lista todos los complejos residenciales disponibles en base a la localidad
@app.get("/{identificador_localidad}/complejo_residencial/", response_model=List[esquemas.ComplejoResidencial], status_code=status.HTTP_200_OK, summary="Endpoint que lista los complejos residenciales")
async def obtener_complejo_residencial(
    identificador_localidad: str,
    tipo_complejo: str = Query(None, description="Filtrar por tipo de complejo residencial"),
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)
    ):
    """
        # Endpoint que lista todos los complejos residenciales disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar filtro válido
    if tipo_complejo and tipo_complejo not in ['Residencial', 'Privada', 'Fraccionamiento']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Filtro no válido')

    # Obtener todos los complejos de una localidad
    complejos = await obtener_todos_los_complejos(base_datos, identificador_localidad, tipo_complejo)

    # Verificar que la respuesta no esté vacia
    if not complejos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return complejos

# Función que insertar un nuevo complejo residencial a la base de datos
@app.post("/agregar_complejo_residencial", response_model=esquemas.ComplejoResidencial, status_code=status.HTTP_201_CREATED, summary="Añade un nuevo complejo")
async def agregar_complejo_residencial(complejo_residencial: esquemas.ComplejoResidencialCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega un complejo residencial a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(complejo_residencial, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Comprobar que existe el municipio
    comprobador_localidad = await verificar_localidad_complejo(base_datos, complejo_residencial.id_localidad)

    if not comprobador_localidad:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la localidad.")

    # Comprobar que no se repite la localidad en un Municipio
    comprobador_complejo = await verificar_complejo_existente(base_datos, complejo_residencial)

    if comprobador_complejo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complejo residencial ya existente en la localidad.")

    # Verificar tipo de complejo
    tipo_complejos = ["Fraccionamiento", "Residencial", "Privada"]
    if complejo_residencial.tipo_complejo not in tipo_complejos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de complejo no válido (Fraccionamiento, Residencial, Privada)")

    # Añadir el municipio
    resultado_agregar = await agregar_nuevo_complejo(base_datos, complejo_residencial)

    # Verificar que se haya ingresado correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar el complejo residencial.")

    return resultado_agregar

# Función que se encarga de actualizar un complejo en la base de datos
@app.put("/actualizar_complejo/{identificador_complejo}", response_model=esquemas.ComplejoResidencial, status_code=status.HTTP_200_OK, summary="Actualizar una sección")
async def actualizar_complejo(
    identificador_complejo: str,
    complejo_actualizar: esquemas.ComplejoResidencialCreate,
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint actualiza la información de una sección disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(complejo_actualizar, [""])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener la localidad
    comprobador_localidad = await verificar_localidad_complejo(base_datos, complejo_actualizar.id_localidad)

    # Verificar que exista el la localidad
    if not comprobador_localidad:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la localidad")

    # Obtener comprobador de que exista el complejo
    comprobador_complejo = await verificar_complejo_seccion(base_datos, identificador_complejo)

    # Verificar que exista el complejo
    if not comprobador_complejo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el complejo")

    # Verificar que no se repitan los datos
    comprobador_datos = await verificar_complejo_actualizar(base_datos, identificador_complejo, complejo_actualizar)

    # Verificar sus valores
    if comprobador_datos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos repetidos")

    # Actualizar el complejo
    complejo_actualizar = await actualizar_un_complejo(base_datos, identificador_complejo, complejo_actualizar)

    # Verificar que se ingresó correctamente
    if not complejo_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el complejo.")

    return complejo_actualizar

# Función que se encarga de eliminar un complejo en la base de datos
@app.delete("/eliminar_complejo/{identificador_complejo}", status_code=status.HTTP_200_OK, summary="Elimina un complejo")
async def eliminar_complejo(identificador_complejo: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un complejo en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el complejo a eliminar
    complejo_eliminar = await verificar_complejo_seccion(base_datos, identificador_complejo)

    # Verificar que exista el complejo
    if not complejo_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el complejo.")

    # Añadir el vendedor
    resultado_eliminar = await eliminar_un_complejo(base_datos, identificador_complejo=identificador_complejo)

    # Verificar que se ingresó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el complejo.")

    return resultado_eliminar

# Función que lista la información de un seccion en especifico de la base de datos
@app.get('/obtener_seccion_especifico/{identificador_seccion}', response_model=List[esquemas.SeccionComplejo], status_code=status.HTTP_200_OK, summary="Muestra una sección en especifico")
async def obtener_seccion_especifico(identificador_seccion, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista una sección especifico de un seccion disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del seccion
    seccion = await obtener_una_seccion(base_datos, identificador_seccion)

    # Verificar que la respuesta no esté vacía
    if not seccion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return seccion

# Función que lista todos los secciones disponibles de la base de datos
@app.get("/obtener_todas_secciones", response_model=List[esquemas.SeccionComplejo], status_code=status.HTTP_200_OK, summary="Lista todas los complejos")
async def obtener_todas_secciones(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todas las secciones disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los municipios
    seccion = await obtener_todas_secciones_sin_complejo(base_datos)

    # Verificar que la respuesta no esté vacia
    if not seccion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return seccion

# Función para obtener todas las secciones disponibles en base al complejo residencial
@app.get("/{identificador_complejo_residencial}/secciones", response_model=List[esquemas.SeccionComplejo], status_code=status.HTTP_200_OK, summary='Endpoint que lista las secciones')
async def obtener_secciones_complejo(
    identificador_complejo_residencial: str,
    base_datos : Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos las secciones de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todas las secciones
    secciones = await obtener_todas_las_secciones(base_datos, identificador_complejo_residencial)

    # Verificar que la respuesta no esté vacia
    if not secciones:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return secciones

# Función que inserta una nueva sección a la base de datos
@app.post("/agregar_seccion", response_model=esquemas.SeccionComplejo, status_code=status.HTTP_201_CREATED, summary="Añade una nueva sección")
async def agregar_seccion(seccion: esquemas.SeccionComplejoCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agregar una nueva sección a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporcionan todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verifiar valores nulos
    comprobador_nulos = valores_nulos_lotes(seccion, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blaco no permitidos')

    # Comprobar que exista el municipio
    comprobador_complejo = await verificar_complejo_seccion(base_datos, seccion.id_complejo_residencial)

    if not comprobador_complejo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el complejo residencial")

    # Comprobar que no se repite la sección en un complejo
    comprobador_seccion = await verificar_seccion_existente(base_datos, seccion)

    if comprobador_seccion:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sección ya existente en el complejo residencial")

    # Añadir la sección
    resultado_agregar = await agregar_nueva_seccion(base_datos, seccion)

    # Verificar que se haya ingresado correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar la sección")

    return resultado_agregar

# Función que se encarga de actualizar una sección en la base de datos
@app.put("/actualizar_seccion/{identificador_seccion}", response_model=esquemas.SeccionComplejo, status_code=status.HTTP_200_OK, summary="Actualizar una sección")
async def actualizar_seccion(
    identificador_seccion: str,
    seccion_actualizar: esquemas.SeccionComplejoCreate,
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint actualiza la información de una sección disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(seccion_actualizar, [""])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el complejo residencial
    comprobador_complejo = await verificar_complejo_seccion(base_datos, seccion_actualizar.id_complejo_residencial)

    # Verificar que exista el complejo
    if not comprobador_complejo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el complejo")

    # Obtener comprobador de que exista la sección
    comprobador_seccion = await verificar_seccion_lote(base_datos, identificador_seccion)

    # Verificar que exista la sección
    if not comprobador_seccion:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la sección")

    # Verificar que no se repitan los datos
    comprobador_datos = await verificiar_seccion_actualizar(base_datos, identificador_seccion, seccion_actualizar)

    # Verificar sus valores
    if comprobador_datos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos repetidos")

    # Actualizar la sección
    seccion_actualizado = await actualizar_una_seccion(base_datos, identificador_seccion, seccion_actualizar)

    # Verificar que se ingresó correctamente
    if not seccion_actualizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar la sección.")

    return seccion_actualizado

# Función que se encarga de eliminar una sección en la base de datos
@app.delete("/eliminar_seccion/{identificador_seccion}", status_code=status.HTTP_200_OK, summary="Elimina una sección")
async def eliminar_seccion(identificador_seccion: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de una sección en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener vendedor a eliminar
    lote_eliminar = await verificar_seccion_eliminar(base_datos, identificador_seccion)

    # Verificar que exista el vendedor
    if not lote_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe la sección.")

    # Añadir el vendedor
    resultado_eliminar = await eliminar_una_seccion(base_datos, identificador_seccion=identificador_seccion)

    # Verificar que se ingresó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar la sección.")

    return resultado_eliminar

# Función para obtener todos los lotes disponibles en base al complejo residencial
@app.get("/{identificador_complejo_residencial}/lotes/", response_model=esquemas.LoteSeccionMostrar, status_code=status.HTTP_200_OK, summary="Endpoint que lista los lotes")
async def obtener_lotes_complejo(
    identificador_complejo_residencial: str,
    numero_seccion: str = Query(None, description="Filtrar por sección perteneciente"),
    min_tamano: str = Query(None, description="Filtrar por tamaño del lote"),
    max_tamano: str = Query(None, description="Filtrar por tamaño del lote"),
    estado_vendido: str = Query(None, description="Filtrar por estado del lote"),
    nombre_lote: str = Query(None, description="Filtrar por nombre del lote 'Lote 1, Lote 10, Lote..x'"),
    pagina: int = Query(1, description="Número de la página"),
    tamano: int = Query(10, description="Tamaño de la página"),
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los lotes de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 404 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Validar filtro
    if estado_vendido and estado_vendido not in ['Proceso', 'Vendido', 'Disponible']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Filtro no válido')

    # Obtener todos los lotes de un complejo
    lotes, total_lotes = await obtener_todos_los_lotes(base_datos, identificador_complejo_residencial, numero_seccion,
                                                       max_tamano, min_tamano, estado_vendido, pagina, tamano, nombre_lote)

    # Verificar que la respuesta no está vacia
    if not lotes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return esquemas.LoteSeccionMostrar(lotes=lotes, total_lotes=total_lotes)



# Funcion para obtener la ubicación de un lote disponible
@app.get("/ubicacion_lote/{identificador_lote}", response_model=esquemas.UbicacionLote, status_code=status.HTTP_200_OK, summary="Consultar la ubicación de un lote")
async def obtener_ubicacion_lote(identificador_lote: str,
                                base_datos: Session = Depends(obtener_db),
                                credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que muestra la ubicación de un lote disponible

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 404 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar que exista el lote
    lote = await obtener_un_lote(base_datos, identificador_lote)

    # Verificar que la respuesta no esté vacía
    if not lote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontró el lote.')

    # Obtener la ubicaciónd e un lote
    ubicacion_lote = await obtener_ubicacion_un_lote(base_datos, identificador_lote)

    # Verificar que exista una ubicación
    if not ubicacion_lote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se obtuvo una ubicación.')

    return ubicacion_lote

# Función que lista la información de un lote en especifico de la base de datos
@app.get('/lote_informacion_extra/{identificador_lote}', response_model=List[esquemas.LoteSeccionExtendido], status_code=status.HTTP_200_OK, summary="Información extra de un lote")
async def lote_informacion_extra(identificador_lote, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un lote especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del lote
    lote = await obtener_un_lote_extra(base_datos, identificador_lote)

    # Verificar que la respuesta no esté vacía
    if not lote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return lote

# Función que lista la información de un lote en especifico de la base de datos
@app.get('/{identificador_lote}/lote_especifico', response_model=List[esquemas.LoteSeccionNombre], status_code=status.HTTP_200_OK, summary="Endpoint para mostrar un lote")
async def obtener_lote_especifico(identificador_lote, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un lote especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del lote
    lote = await obtener_un_lote(base_datos, identificador_lote)

    # Verificar que la respuesta no esté vacía
    if not lote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return lote

# Función que lista la información de venta de un lote
@app.get('/informacion_venta_lote/{identificador_lote}', response_model=esquemas.VentaLotes, status_code=status.HTTP_200_OK, summary="Información extra de un lote")
async def informacion_venta_lote(identificador_lote, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información extra de una venta de un lote disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el tokenden las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del lote
    lote = await obtener_informacion_lote_vendido(base_datos, identificador_lote)

    # Verificar que la respuesta no esté vacía
    if not lote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return lote

# Función que insertar un nuevo lote a la base de datos
@app.post("/agregar_lote", response_model=esquemas.LoteSeccion, status_code=status.HTTP_201_CREATED, summary="Añade una nueva seccion")
async def agregar_lote(lote: esquemas.LoteSeccionCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega una nueva seccion a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(lote, ["otras_medidas", "otros_servicios", "servicio_agua", "servicio_electricidad", "servicio_drenaje"])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Comprobar que existe el municipio
    comprobador_complejo = await verificar_seccion_lote(base_datos, lote.id_seccion)

    if not comprobador_complejo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la sección.")

    # Comprobar que no se repite la localidad en un Municipio
    comprobador_seccion = await verificar_lote_existente(base_datos, lote)

    if comprobador_seccion:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lote ya existente en la sección.")

    # Verificar estado del terreno
    estados_validos = ["Vendido", "Disponible"]
    if lote.estado_terreno not in estados_validos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado del terreno no válido")

    # Añadir el municipio
    resultado_agregar = await agregar_nuevo_lote(base_datos, lote)

    # Verificar que se haya ingresado correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar la sección.")

    return resultado_agregar

# Función que se encarga de actualizar un lote en la base de datos
@app.put("/actualizar_lote/{identificador_lote}", response_model=esquemas.LoteSeccion, status_code=status.HTTP_200_OK, summary="Actualizar un lote")
async def actualizar_lote(
    identificador_lote: str,
    lote_actualizar: esquemas.LoteSeccionCreate,
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint actualiza la información de un lote disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(lote_actualizar, ["otras_medidas", "otros_servicios", "servicio_agua", "servicio_electricidad", "servicio_drenaje"])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener comprobador de que no exista el lote
    comprobador_lote = await verificar_lote_existente_actualizar(base_datos, identificador_lote=identificador_lote)

    # Verificar que no se repita el lote
    if not comprobador_lote:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el lote")

    # Obtener comprobador de que exista la sección
    comprobador_seccion = await verificar_seccion_lote(base_datos, lote_actualizar.id_seccion)

    # Verificar que exista la sección
    if not comprobador_seccion:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la sección")

    # Verificar que no se repitan los datos
    comprobador_datos = await verificar_lote_actualiza(base_datos, identificador_lote, lote_actualizar)

    # Verificar sus valores
    if comprobador_datos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos repetidos")

    # Actualizar el lote
    lote_actualizado = await actualizar_un_lote(base_datos, identificador_lote, lote_actualizar)

    # Verificar que se ingresó correctamente
    if not lote_actualizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el lote.")

    return lote_actualizado

# Función que se encarga de suspender or activar a un vendedor en la base de datos
@app.get("/cambiar_estado_lote/{identificador_lote}", response_model=esquemas.LoteSeccion, status_code=status.HTTP_200_OK, summary="Cambiar estado de un vendedor")
async def cambiar_estado_lote(
    identificador_lote: str,
    estado: str = Query('Proceso', description="Cambiar estado de un lote, puede ser 'Vendido', 'Disponible' o 'Proceso'"),
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener comprobador de que no exista el lote
    comprobador_lote = await verificar_lote_existente_actualizar(base_datos, identificador_lote=identificador_lote)

    # Verificar que no se repita el lote
    if not comprobador_lote:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el lote")

    # Actualizar el lote
    lote_actualizado = await actualizar_estado_un_lote(base_datos, identificador_lote, estado)

    # Verificar que se ingresó correctamente
    if not lote_actualizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el estado del lote.")

    return lote_actualizado

# Función que se encarga de eliminar un vendedor en la base de datos
@app.delete("/eliminar_lote/{identificador_lote}", status_code=status.HTTP_200_OK, summary="Endpoint para eliminar un vendedor")
async def eliminar_lote(identificador_lote: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un lote en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener vendedor a eliminar
    lote_eliminar = await verificar_lote_existente_actualizar(base_datos, identificador_lote)

    # Verificar que exista el vendedor
    if not lote_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el lote.")

    # Añadir el vendedor
    resultado_eliminar = await eliminar_un_lote(base_datos, identificador_lote=identificador_lote)

    # Verificar que se ingresó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el lote.")

    return resultado_eliminar

#############################################
# Funciones para el apartado de vendedores #
############################################

@app.get("/vendedores/", response_model=esquemas.VendedorResponse, status_code=status.HTTP_200_OK, summary="Endpoint que lista todos los vendedores")
async def obtener_vendedores(
    base_datos: Session = Depends(obtener_db),
    orden: str = Query(None, description="El orden de las ventas realizadas, puede ser 'mas' o 'menos'"),
    tipo: str = Query(None, description="El estado del vendedor, puede ser 'Activos' o 'Suspendidos'"),
    pagina: int = Query(1, description="Número de la página"),
    tamano: int = Query(10, description="Tamaño de la página"),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los vendedores disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Validar filtros
    if (orden and orden not in ['mas', 'menos']
        or tipo and tipo not in ['Activos', 'Suspendidos']):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Filtro o filtro no válido')

    # Obtener todos los vendedores
    vendedores, total_vendedores = await obtener_todos_los_vendedores(base_datos, orden, tipo, pagina, tamano)

    # Verificar que la respuesta no esté vacia
    if not vendedores:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return esquemas.VendedorResponse(vendedores=vendedores, total_vendedores=total_vendedores)

@app.get("/vendedores_sin_filtro", response_model=List[esquemas.Vendedor], status_code=status.HTTP_200_OK, summary="Lista todos los vendedores")
async def vendedores_sin_filtro(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los vendedores disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """

    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los vendedores
    vendedores = await obtener_todos_vendedores(base_datos)

    # Verificar que la respuesta no esté vacía
    if not vendedores:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return vendedores

# Función que lista la información de los vendedores disponibles en la base de datos
@app.get("/{identificador_vendedor}/vendedor_especifico", response_model=List[esquemas.Vendedor], status_code=status.HTTP_200_OK, summary="Endpoint que lista un vendedor")
async def obtener_vendedor_especifico(identificador_vendedor: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el vendedor especifico
    vendedor = await obtener_un_vendedor(base_datos, identificador_vendedor)

    # Verificar que la respuesta no esté vacia
    if not vendedor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return vendedor

# Función que se encarga de agregar un nuevo vendedor en la base de datos
@app.post("/añadir_vendedor", response_model=esquemas.Vendedor, status_code=status.HTTP_201_CREATED, summary="Endpoint para añadir un vendedor")
async def agregar_vendedor(vendedor_añadir: esquemas.VendedorCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos(vendedor_añadir, ['RFC_vendedor', 'segundo_apellido_vendedor', 'correo_electronico', 'numero_exterior'])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener comprobador de que no exista el vendedor
    comprabador_vendedor = await verificar_vendedor_existente(base_datos, vendedor=vendedor_añadir)

    # Verificar que no exista el vendedor
    if comprabador_vendedor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe el vendedor o datos repetidos.")

    # Añadir el vendedor
    resultado_agregar = await añadir_un_nuevo_vendedor(base_datos, vendedor=vendedor_añadir)

    # Verificar que se ingresó correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar el usuario.")

    return resultado_agregar

# Función que se encarga de actualizar un vendedor en la base de datos
@app.put("/actualizar_vendedor/{identificador_vendedor}", response_model=esquemas.Vendedor, status_code=status.HTTP_200_OK, summary="Endpoint para actualizar un vendedor")
async def actualizar_vendedor(identificador_vendedor: str, vendedor_actualizar: esquemas.VendedorCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos(vendedor_actualizar, ['RFC_vendedor', 'segundo_apellido_vendedor', 'correo_electronico', 'numero_exterior'])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener comprobador de que no exista el vendedor
    comprabador_vendedor = await verificar_vendedor_existente(base_datos, \
                            vendedor=vendedor_actualizar, identificador_vendedor=identificador_vendedor, actualizando=True)

    # Verificar que no exista el vendedor
    if comprabador_vendedor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe el vendedor o datos repetidos.")

    # Actualizar el vendedor
    vendedor_actualizado = await actualizar_un_vendedor(base_datos, identificador_vendedor, vendedor_actualizar)

    # Verificar que se ingresó correctamente
    if not vendedor_actualizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el vendedor.")

    return vendedor_actualizado

# Función que se encarga de suspender or activar a un vendedor en la base de datos
@app.get("/cambiar_estado_vendedor/{identificador_vendedor}", response_model=esquemas.Vendedor, status_code=status.HTTP_200_OK, summary="Endpoint para cambiar estado de un vendedor")
async def cambiar_estado_vendedor(
    identificador_vendedor: str,
    estado: str = Query('Activar', description="Cambiar estado de un vendedor, puede ser 'Suspender' o 'Activar'"),
    base_datos: Session = Depends(obtener_db),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Validar filtro
    if estado and estado not in ['Suspender', 'Activar']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filtro no válido")

    # Obtener vendedor a actualizar
    vendedor_actualizar = await obtener_un_vendedor(base_datos, identificador_vendedor)

    # Verificar que exista el vendedor
    if not vendedor_actualizar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el vendedor.")

    # Obtener el resultado de la actualización
    estado_actualizado = await actualizar_estado_vendedor(base_datos, identificador_vendedor, estado)

    # Verificar que se ingresó correctamente
    if not estado_actualizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar el usuario.")

    return estado_actualizado

# Función que se encarga de eliminar un vendedor en la base de datos
@app.delete("/eliminar_vendedor/{identificador_vendedor}", status_code=status.HTTP_200_OK, summary="Endpoint para eliminar un vendedor")
async def eliminar_vendedor(identificador_vendedor: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un vendedor en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener vendedor a eliminar
    vendedor_eliminar = await obtener_un_vendedor(base_datos, identificador_vendedor)

    # Verificar que exista el vendedor
    if not vendedor_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el vendedor.")

    # Añadir el vendedor
    resultado_eliminar = await eliminar_un_vendedor(base_datos, identificador_vendedor=identificador_vendedor)

    # Verificar que se ingresó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el usuario.")

    return resultado_eliminar

##################################################
# Funciones para el apartado de ventas / compras #
##################################################

# Función que lista todas las ventas disponibles de la base de datos
@app.get("/ventas/", response_model=esquemas.VentasResponse, status_code=status.HTTP_200_OK, summary="Endpoint que lista ventas")
async def obtener_ventas(
    base_datos: Session = Depends(obtener_db),
    pagina: int = Query(1, description="Número de la página"),
    tamano: int = Query(10, description="Tamaño de la página"),
    filtro: str = Query(None, description="El estado de la venta / compra, puede ser 'Proceso', 'Finalizado', 'Cancelado'"),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de todas las ventas disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener token  en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Validar filtro
    if filtro and filtro not in ['Proceso', 'Finalizado', 'Cancelado']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Filtro no válido')

    # Obtener todas las compras / ventas de la base de datos
    ventas, total_ventas = await obtener_todas_las_ventas(base_datos, filtro, pagina, tamano)

    # Verificar que la respuesta no esté vacía
    if not ventas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return esquemas.VentasResponse(ventas=ventas, total_ventas=total_ventas)

# Función que lista la información de una venta en especifico de la base de datos
@app.get("/venta_especifica/{identificador_venta}", response_model=List[esquemas.Compra], status_code=status.HTTP_200_OK, summary="Muestra una venta en especifico")
async def venta_especifica(identificador_venta: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un cliente disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """

    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la venta en especifico
    venta = await obtener_una_venta(base_datos, identificador_venta)

    # Verificar que la respuesta no esté vacía
    if not venta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron datos")

    return venta

# Función que se encarga de agregar una nueva en la base de datos
@app.post("/agregar_venta", response_model=esquemas.Compra, status_code=status.HTTP_201_CREATED, summary="Agregar una venta")
async def agregar_venta(venta_agregar: esquemas.CompraCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega una nueva compra/venta a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(venta_agregar, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el lote de la compra
    comprobador_lote = await verificar_lote_existente_actualizar(base_datos, venta_agregar.id_lote)

    # Verificar que exista el lote
    if not comprobador_lote:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el lote")

    # Verificar que el lote esté disponible
    comprobador_disponilibidad_lote = await verificar_lote_disponibilidad(base_datos, venta_agregar.id_lote)
    comprobador_lote_venta = await verificar_lote_venta(base_datos, venta_agregar.id_lote)

    # Verificar
    if not comprobador_disponilibidad_lote or not comprobador_lote_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lote no disponible para su venta")

    # Verifiar que el vendedor exista
    comprobador_vendedor = await obtener_un_vendedor(base_datos, venta_agregar.id_vendedor)

    # Verificar que exista el lote
    if not comprobador_vendedor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el vendedor")

    # Verificar que el cliente ya exista
    comprobador_cliente = await verificar_cliente_actualizar(base_datos, venta_agregar.CURP_cliente)

    # Verificar que exista el cliente
    if not comprobador_cliente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el cliente")

    if venta_agregar.estado_compra == 'Proceso':
        # Añadir la venta
        resultado_agregar = await agregar_nueva_venta(base_datos, venta_agregar)
    else:
        resultado_agregar = await agregar_nueva_venta_completa(base_datos, venta_agregar)

    # Verificar que se ingresó correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar la venta")

    return resultado_agregar

# Función que se encarga de actualizar los datos de una venta/compra en l abase de datos
@app.put("/actualizar_venta", response_model=esquemas.Compra, status_code=status.HTTP_200_OK, summary="Actualiza una venta")
async def actualizar_venta(identificador_venta: str, venta_actualizada: esquemas.CompraCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
    # Endpoint que actualiza la información de una venta/compra disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos(venta_actualizada, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valores en blanco no permitidos")

    # Obtener la venta
    comprobador_venta = await obtener_una_venta(base_datos, identificador_venta)

    # Verificar que exista la venta
    if not comprobador_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la venta")

    # Obtener el lote de la compra
    comprobador_lote = await verificar_lote_existente_actualizar(base_datos, venta_actualizada.id_lote)

    # Verificar que exista el lote
    if not comprobador_lote:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el lote")

    # Verificar que el lote esté disponible
    comprobador_disponilibidad_lote = await verificar_lote_disponibilidad(base_datos, venta_actualizada.id_lote)
    comprobador_lote_venta = await verificar_lote_venta(base_datos, venta_actualizada.id_lote, identificador_venta, actualizando=True)

    # Verificar disponibilidad
    if not comprobador_disponilibidad_lote or not comprobador_lote_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lote no disponible para su venta")

    # Verifiar que el vendedor exista
    comprobador_vendedor = await obtener_un_vendedor(base_datos, venta_actualizada.id_vendedor)

    # Verificar que exista el lote
    if not comprobador_vendedor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el vendedor")

    # Verificar que el cliente ya exista
    comprobador_cliente = await verificar_cliente_actualizar(base_datos, venta_actualizada.CURP_cliente)

    # Verificar que exista el cliente
    if not comprobador_cliente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el cliente")

    # Actualizar la venta
    venta_actualizar = await actualizar_una_venta(base_datos, identificador_venta, venta_actualizada)

    # Verificar que se actualizó correctamente
    if not venta_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar la venta.")

    return venta_actualizar

# Función que se encarga de cambiar el estado de un venta
@app.get("/cambiar_estado_venta/{identificador_venta}", response_model=esquemas.Compra, status_code=status.HTTP_200_OK, summary="Cambia el estado de la venta")
async def cambiar_estado_venta(identificador_venta: str,
                                estado: str = Query('Finalizado', description="Cambiar el estado de una compra, puede ser 'Proceso', 'Cancelado' o 'Finalizado' "),
                                base_datos: Session = Depends(obtener_db),
                                credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la venta a actualiar
    venta_actuaizar = await obtener_una_venta(base_datos, identificador_venta)

    # Verificar que exista la venta
    if not venta_actuaizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la venta")

    # Actualizar la venta
    resultado_actualizar = await cambiar_estado_una_venta(base_datos, identificador_venta, filtro=estado)

    # Verificar que se haya actualizado
    if not resultado_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el estado de la venta")

    return resultado_actualizar

########################################
# Funciones para el apartado de plazos #
########################################

# Función que se encarga de listar todos los plazos de compra de una venta
@app.get("/plazo_compra/{identificador_venta}", response_model=esquemas.PlazoCompraPaginado, status_code=status.HTTP_200_OK, summary="Muestra los plazos de una compra")
async def plazo_compra(identificador_venta: int,
                        pagina: int = Query(1, description="Número de la página"),
                        tamano: int = Query(10, description="Tamaño de la página"),
                        base_datos: Session = Depends(obtener_db),
                        credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los plazos de una compra disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 404 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los plazos de una compra
    plazos, total_plazos = await obtener_todos_los_plazos(base_datos, identificador_venta, pagina, tamano)

    # Verificar que la respuesta no esté vacía
    if not plazos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return esquemas.PlazoCompraPaginado(plazos=plazos, total_plazos=total_plazos)

# Función que se encarga de devolver un plazo en especifico
@app.get("/plazo_compra_especifico/{identificador_plazo}", response_model=List[esquemas.PlazoCompra], status_code=status.HTTP_200_OK, summary="Muestra un plazo en especifico")
async def plazo_compra_especifico(identificador_plazo: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un plazo en especifico de un complejo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acesso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acesso)

    # Obtener la información del plazo
    plazo = await obtener_plazo_especifico(base_datos, identificador_plazo)

    # Verificar que la respuesta no esté vacía
    if not plazo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return plazo

# Función que se encarga de crear un plazo de compra
@app.post("/agregar_plazo_compra", response_model=esquemas.PlazoCompra, status_code=status.HTTP_201_CREATED, summary="Agregar un nuevo plazo")
async def agregar_plazo_compra(plazo_agregar: esquemas.PlazoCompraCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega una nuevo detalle de pago a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciaes
    token_acceso = credenciales_validacion.credentials

    # Valdiar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_ventas(plazo_agregar, ['comprobante'])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blaco no permitidos')

    # Comprobar que la compra exista
    comprobador_venta = await obtener_una_venta(base_datos, plazo_agregar.id_compra)

    # Verificar el resultado
    if not comprobador_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la venta")

    # Comprobar que no exista el número de plazo
    comprobador_numero_venta = await verificar_numero_plazo(base_datos, plazo_agregar)

    # Verificar la respuetsa
    if comprobador_numero_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El número de plazo ya existe en la compra")

    # Agregar el plazo
    resultado_agregar = await agregar_nuevo_plazo(base_datos, plazo_agregar)

    # Veriicar resultado al agregar
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo insertar el plazo")

    return resultado_agregar

# Función que se encarga de modificar un plazo en especifico
@app.put("/actualizar_plazo_compra/{identificador_plazo}", response_model=esquemas.PlazoCompra, status_code=status.HTTP_200_OK, summary="Modifica un plazo en especifico")
async def actualizar_plazo_compra(identificador_plazo: str, plazo_modificador: esquemas.PlazoCompraCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega una nuevo detalle de pago a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciaes
    token_acceso = credenciales_validacion.credentials

    # Valdiar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_ventas(plazo_modificador, ['comprobante'])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blaco no permitidos')

    # Comprobar que exista el plazo a actualizar
    comprobador_plazo = await obtener_plazo_especifico(base_datos, identificador_plazo)

    # Verificar que exista el resultado
    if not comprobador_plazo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el plazo a actualizar")

    # Comprobar que la compra exista
    comprobador_venta = await obtener_una_venta(base_datos, plazo_modificador.id_compra)

    # Verificar el resultado
    if not comprobador_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe la venta")

    # Comprobar que no exista el número de plazo
    comprobador_numero_venta = await verificar_numero_plazo(base_datos, plazo_modificador, actualizando=True, identificador_plazo=identificador_plazo)

    # Verificar la respuetsa
    if comprobador_numero_venta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El número de plazo ya exista en la compra")

    # Actualizar el plazo
    resultado_actualizar = await actualizar_un_plazo_compra(base_datos, identificador_plazo, plazo_modificador)

    # Veriicar resultado al actualizar
    if not resultado_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el plazo")

    return resultado_actualizar

@app.delete("/eliminar_plazo_compra/{identificador_plazo}", status_code=status.HTTP_200_OK, summary="Elimina un plazo en especifico")
async def eliminar_plazo(identificador_plazo: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un plazo en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el plazo a eliminar
    plazo_eliminar = await obtener_plazo_especifico(base_datos, identificador_plazo)

    # Verificar que exista el plazo
    if not plazo_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el plazo a eliminar")

    # Eliminar el plazo
    resultado_eliminar = await eliminar_un_plazo(base_datos, identificador_plazo)

    # Verificar el resultado
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo elimiar el plazo")

    return resultado_eliminar

#################################################
# Funciones pra el apartado de detalles de pago #
#################################################

# Función que se encarga de crear un nuevo detalle pago
@app.post("/agregar_detalle_pago/{identificador_plazo}", response_model=esquemas.DetallePago, status_code=status.HTTP_201_CREATED, summary="Agregar un detalle de pago")
async def agregar_detalle_pago(identificador_plazo: int, detalle_agregar: esquemas.DetallePagoCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega una nuevo detalle de pago a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciaes
    token_acceso = credenciales_validacion.credentials

    # Valdiar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_ventas(detalle_agregar, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blaco no permitidos')

    # Comprobar que el plazo exista
    comprobador_plazo = await obtener_plazo_especifico(base_datos, identificador_plazo)

    # Verificar el resultado
    if not comprobador_plazo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el plazo")

    # Agregar el detalle de pago
    resultado_agregar = await agregar_nuevo_detalle(base_datos, detalle_agregar)

    # Veriicar resultado al agregar
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo insertar el plazo")

    return resultado_agregar

# Función que se encarga de listar un detalle pago en base a su plazo
@app.get("/detalle_pago_plazo/{identificador_plazo}", response_model=List[esquemas.DetallePago], status_code=status.HTTP_200_OK, summary="Muestra la información de un detalle")
async def detalle_pago_plazo(identificador_plazo: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un detalle especifico de un plazo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del detalle de pago
    detalle_pago = await obtener_detalle_de_plazo(base_datos, identificador_plazo)

    # Verificar que la repuesta no esté vacía
    if not detalle_pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return detalle_pago

# Función que se encarga de listar un detalle pago
@app.get("/detalle_pago_especifico/{identificador_detalle}", response_model=List[esquemas.DetallePago], status_code=status.HTTP_200_OK, summary="Muestra la información de un detalle")
async def detalle_pago_especifico(identificador_detalle: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista un detalle especifico de un plazo disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token de las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar el token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la información del detalle de pago
    detalle_pago = await obtener_detalle_especifico(base_datos, identificador_detalle)

    # Verificar que la repuesta no esté vacía
    if not detalle_pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos')

    return detalle_pago

# Función que se encarga de modificar un detalle pago
@app.put("/actualizar_detalle_pago/{identificador_detalle}", response_model=esquemas.DetallePago, status_code=status.HTTP_200_OK, summary="Actualiza un detalle pago")
async def actualizar_detalle_pago(identificador_detalle: str, detalle_actualizar: esquemas.DetallePagoCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agrega una nuevo detalle de pago a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciaes
    token_acceso = credenciales_validacion.credentials

    # Valdiar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_ventas(detalle_actualizar, [''])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blaco no permitidos')

    # Comprobar que el detalle exista
    comprobador_detalle = await obtener_detalle_especifico(base_datos, identificador_detalle)

    # Verificar el detalle
    if not comprobador_detalle:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el detalle")

    # Comprobar que el plazo exista
    comprobador_plazo = await obtener_plazo_especifico(base_datos, detalle_actualizar.id_plazo)

    # Verificar el resultado
    if not comprobador_plazo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el plazo")

    # Actualizar el detalle de pago
    resultado_actualizar = await actualizar_un_detalle_pago(base_datos, identificador_detalle, detalle_actualizar)

    # Veriicar resultado al Actualizar
    if not resultado_actualizar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo insertar el plazo")

    return resultado_actualizar

# Función que se encarga de eliminar un detalle de pago
@app.delete("/eliminar_detalle_pago/{identificador_detalle}", status_code=status.HTTP_200_OK, summary="Elimina un detalle pago")
async def eliminar_detalle_pago(identificador_detalle: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un lote en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el detalle a eliminar
    detalle_eliminar = await obtener_detalle_especifico(base_datos, identificador_detalle)

    # Verificar que exista el detalle
    if not detalle_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No exista el detalle de pago")

    # Eliminar el detalle de pago
    resultado_eliminar = await eliminar_un_detalle(base_datos, identificador_detalle)

    # Verificar que se eliminó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el detalle del pago")

    return resultado_eliminar

##########################################
# Funciones para el apartado de clientes #
##########################################

# Función que lista todos los clientes disponbiles en la base de datos
@app.get("/clientes", response_model=List[esquemas.Cliente], status_code=status.HTTP_200_OK, summary="Endpoint que lista los clientes")
async def obtener_clientes(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todos los clientes disponibles en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener todos los clientes
    clientes = await obtener_todos_los_clientes(base_datos)

    # Verificar que la respuesta no esté vacia
    if not clientes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return clientes

# Función que lista la información de los clientes disponibles en la base de daots
@app.get("/{identificador_cliente}/cliente_especifico", response_model=List[esquemas.Cliente], status_code=status.HTTP_200_OK, summary="Endpoint para listar información del cliente")
async def obtener_cliente_especifico(identificador_cliente: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista la información de un cliente disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """

    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Validar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener el cliente en especifico
    cliente = await obtener_un_cliente(base_datos, identificador_cliente)

    # Verificar que la respuesta no esté vacía
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return cliente

# Función que se encarga de insertar un nuevo cliente
@app.post("/agregar_cliente", response_model=esquemas.Cliente, status_code=status.HTTP_201_CREATED, summary="Añade un nuevo cliente")
async def agregar_cliente(cliente_agregar: esquemas.ClienteCreate, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que agregar un cliente a la base de datos

        ## 1.- Códigos de estado
        * 201 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos_lotes(cliente_agregar, ['segundo_apellido_cliente', 'numero_exterior', 'entrega_credencial_elector', 'entrega_curp', 'entrega_comprobante_domicilio'])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el comprobador de que no exista el cliente
    comprobador_cliente = await verificar_cliente_existente(base_datos, cliente_agregar)
    comprobador_telefono = await verificar_telefono_cliente(base_datos, cliente_agregar)

     # Verificar que no exista el cliente
    if comprobador_cliente or comprobador_telefono:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe el cliente o valores repetidos")

    # Añadir el cliente
    resultado_agregar = await agregar_nuevo_cliente(base_datos, cliente=cliente_agregar)

    # Verificar que se ingresó correctamente
    if not resultado_agregar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo ingresar el cliente.")

    return resultado_agregar

# Función que se encarga de actualizar los datos de un cliente en la base de datos
@app.put("/actualizar_cliente/{identificador_cliente}", response_model=esquemas.Cliente, status_code=status.HTTP_200_OK, summary="Actualiza un cliente")
async def actualizar_cliente(identificador_cliente: str, cliente_actualizar: esquemas.ClienteCreate, base_datos: Session = Depends(obtener_db), credenciales_validacoin: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que actualiza la información de un vendedor disponible en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacoin.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Verificar valores nulos
    comprobador_nulos = valores_nulos(cliente_actualizar, ['segundo_apellido_cliente', 'numero_exterior', 'entrega_credencial_elector', 'entrega_curp', 'entrega_comprobante_domicilio'])

    # Verificar que no se incumplan
    if comprobador_nulos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Valores en blanco no permitidos')

    # Obtener el cliente
    comprobador_existencia = await verificar_cliente_actualizar(base_datos, identificador_cliente)

    # Verificar que exista
    if not comprobador_existencia:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No existe el cliente")

    # Obtener el comprobador de que no exista el cliente
    comprobador_cliente = await verificar_cliente_existente(base_datos, cliente_actualizar, actualizando=True, identificador_cliente=identificador_cliente)
    comprobador_telefono = await verificar_telefono_cliente(base_datos, cliente_actualizar, actualizando=True, identificador_cliente=identificador_cliente)

     # Verificar que no exista el cliente
    if comprobador_cliente or comprobador_telefono:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe el cliente o valores repetidos")

    # Actualizar el cliente
    cliente_actualizado = await actualizar_un_cliente(base_datos, identificador_cliente, cliente_actualizar)

    # Verificar que se actualizó correctamente
    if not cliente_actualizado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo actualizar el cliente.")

    return cliente_actualizado

# Función que se encarga de eliminar un cliente en la base de datos
@app.delete("/eliminar_cliente/{identificador_cliente}", status_code=status.HTTP_200_OK, summary="Endpoint para eliminar un cliente")
async def eliminar_cliente(identificador_cliente: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un cliente en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra al vendedor
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener cliente a eliminar
    cliente_eliminar = await verificar_cliente_actualizar(base_datos, identificador_cliente)

    # Verificar que exista el cliente
    if not cliente_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el cliente.")

    # Añadir el cliente
    resultado_eliminar = await eliminar_un_cliente(base_datos, identificador_cliente=identificador_cliente)

    # Verificar que se ingresó correctamente
    if not resultado_eliminar:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo eliminar el cliente.")

    return resultado_eliminar

################################################
# Funciones para el apartado de notificaciones #
################################################

# Función que lista todas las notificaciones de la base de datos
@app.get("/notificaciones", response_model=esquemas.NotificacionesExtendido, status_code=status.HTTP_200_OK, summary="Endpoint que lista notificaciones")
async def obtener_notificaciones(
    base_datos: Session = Depends(obtener_db),
    pagina: int = Query(1, description="Número de la página"),
    limite: int = Query(5, description="Cantidad de notificaciones a mostrar"),
    no_leidas: bool = Query(None, description="Mostrar no leídas o mostrar todas"),
    orden: str = Query(None, description="Orden de aparición de las notificaciones 'asc' o 'desc'"),
    credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que lista todas las notificaciones existentes en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 204 - Código de no contenido
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Validar filtro
    if orden and orden not in ['asc', 'desc']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Filtro no válido')

    # Obtener todas las notificaciones
    notificaciones, total_notificaciones = await obtener_todas_las_notificaciones(base_datos, pagina, limite, no_leidas, orden)

    # Verificar que la respuesta no esté vacia
    if not notificaciones:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron datos.')

    return esquemas.NotificacionesExtendido(notificaciones=notificaciones, total_notificaciones=total_notificaciones)

@app.delete("/borrar_notificacion/{identificador_notificacion}", status_code=status.HTTP_200_OK, summary="Endpoint para eliminar una notificación")
async def borrar_una_notificacion(identificador_notificacion: str, base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra una notificacion de la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra la notificación
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la notificación a eliminar
    notificacion_eliminar = await obtener_una_notificacion(base_datos, identificador_notificacion)

    # Verificar que exista la notificación a eliminar
    if not notificacion_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontró la notificación')

    # Eliminar la notificación correspondiente
    comprobador = await eliminar_una_notificacion(base_datos, identificador_notificacion)

    if not comprobador:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No se logró eliminar la notificación, no existe u ocurrió un error')

    return comprobador

@app.get("/marcar_leida_notificacion/{identificador_notificacion}", response_model=esquemas.Notificacion, status_code=status.HTTP_200_OK, summary="Marcar como leída una notificación")
async def marcar_leida_notificacion(identificador_notificacion: str,
                                    base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que marca como leída una notificación en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentra la notificaciones
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la notificación a eliminar
    notificacion_actualizar = await obtener_una_notificacion(base_datos, identificador_notificacion)

    # Verificar que exista la notificación a eliminar
    if not notificacion_actualizar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontró la notificación')

    # Eliminar la notificación correspondiente
    comprobador = await marcar_leido_notificacion(base_datos, identificador_notificacion)

    if not comprobador:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No se logró actualizar la notificación, no existe o ya está actualizada')

    return comprobador

@app.get("/marcar_leidas_todas", status_code=status.HTTP_200_OK, summary="Marcar como leídas todas las notificaciones")
async def marcar_leidas_todas(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que marca como leídas todas las notificaciones de la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentran las notificaciones
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la cantidad de notificaciones
    verificar_notificaciones = await contar_todas_notificaciones(base_datos)

    # Verificar que existan notificaciones
    if not verificar_notificaciones or verificar_notificaciones < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron notificaciones')

    # Actualizar todas las notificaciones
    comprobador = await marcar_todas_notificaciones_leidas(base_datos)

    if not comprobador:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='No se pudieron actualizar las notificaciones o ya están actualizadas')

    return comprobador

@app.delete("/borrar_notificaciones", status_code=status.HTTP_200_OK, summary="Eliminar todas las notificaciones")
async def borrar_notificaciones(base_datos: Session = Depends(obtener_db), credenciales_validacion: HTTPAuthorizationCredentials = Depends(securityBearer)):
    """
        # Endpoint que borra la información de un vendedor en la base de datos

        ## 1.- Códigos de estado
        * 200 - Código de confirmación
        * 400 - Código de error cuando no se proporciona todos los datos
        * 401 - Código de error de no autorizado
        * 404 - Código de error cuando no se encuentran las notificaciones
        * 500 - Código de error del servidor
    """
    # Obtener el token en las credenciales
    token_acceso = credenciales_validacion.credentials

    # Verificar token de acceso
    await validar_token_api(base_datos, token_acceso)

    # Obtener la cantidad de notificaciones
    verificar_notificaciones = await contar_todas_notificaciones(base_datos)

    # Verificar que existan notificaciones
    if not verificar_notificaciones or verificar_notificaciones < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraron notificaciones')

    # Eliminar todas las notificaciones
    comprobador = await eliminar_todas_notificaciones(base_datos)

    if not comprobador or comprobador < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='No se pudieron eliminar las notificaciones o no hay notificaciones')

    return comprobador

# Obtiene las notificaciones en base a la compra
async def obtener_notificacion_compra(id_plazo: int) -> modelos.Notificacines | bool:
    try:
        db = SessionLocal()

        # Obtener las notificaciones
        db_venta = db.query(modelos.Notificacines).filter(
            modelos.Notificacines.id_plazo == id_plazo
        ).first()

        # Verificar que exista la venta
        if not db_venta:
            return False

        db.close()
        return db_venta
    except Exception:
        raise Exception("Ocurrió un error al obtener las notificaciones en base a la compra")

########################################
# Apartado que crea las notificaciones #
########################################

# Función que se encarga de obtener todas las compras sin paginación
async def obtener_plazos_sin_paginacion() -> List[modelos.DatosPlazoCompra]:
    # Inicia la conexión
    db = SessionLocal()
    try:
        # Obtener todas los plazos
        return db.query(modelos.DatosPlazoCompra).filter(modelos.DatosPlazoCompra.estado_compra == 'Proceso').all()
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los plazos sin paginación")
    finally:
        db.close()

async def obtener_notificacion_plazo(id_plazo: int) -> modelos.Notificacines:
    # Inicia la conexión
    db = SessionLocal()
    try:
        return db.query(modelos.Notificacines).filter(modelos.Notificacines.id_plazo == id_plazo).first()
    except Exception:
        raise Exception("Ocurrió un error al obtener la notificación")
    finally:
        db.close()

async def crear_notificacion(mensaje: str, id_plazo: int, fecha: date) -> None:
    # Inicia la conexión
    db = SessionLocal()
    try:
        # Crear la notificación
        db_notificacion = modelos.Notificacines(
            titulo_notificacion = 'Fecha de pago',
            descripcion = mensaje,
            fecha = fecha,
            estado_leido = False,
            id_plazo = id_plazo
        )
        db.add(db_notificacion)
        db.commit()
        db.refresh(db_notificacion)
    except Exception:
        raise Exception("Ocurrió un error al crear la notificación")
    finally:
        db.close()

async def actualizar_notificacion(mensaje: str, id_notificacion: str, nueva_fecha: str) -> None:
    # Realiza la conexión
    db = SessionLocal()
    try:
        # Obtener notificación a actualizar
        db_notificacion = db.query(modelos.Notificacines).filter(
            modelos.Notificacines.id_notificacion == id_notificacion
        ).first()

        # Verificar que exista
        if not db_notificacion:
            return None

        db_notificacion.descripcion = mensaje
        db_notificacion.fecha = nueva_fecha
        db_notificacion.estado_leido = False

        db.commit()
        db.refresh(db_notificacion)
    except Exception:
        raise Exception("Ocurrió un error al actualizar la notificación")
    finally:
        db.close()

async def verificar_y_crear_notificacion():
    try:
        # Obtener fecha actual
        fecha_actual = date.today()

        # Obtener todas las plazos
        plazos = await obtener_plazos_sin_paginacion()

        for plazo in plazos:
            # Datos principales del plazo
            fecha_plazo = plazo.fecha_esperada
            id_plazo = plazo.id_plazo
            comprador = f'{plazo.nombres_cliente} - {plazo.CURP_cliente}'

            print(plazo.id_plazo, plazo.nombres_cliente)

            # Verificar que exista una notificación del plazo
            notificacion = await obtener_notificacion_plazo(id_plazo=id_plazo)
            diferencia_fechas = fecha_plazo - fecha_actual
            mensaje = None

            # Verificar que exista una notificación
            if not notificacion and diferencia_fechas.days in [5, 4, 3, 2, 1]:
                mensaje = f'Faltan {diferencia_fechas.days} para que el comprador {comprador} realice su pago'
                await crear_notificacion(mensaje=mensaje, id_plazo=id_plazo, fecha=fecha_actual)
            elif notificacion:
                id_notificacion = notificacion.id_notificacion
                if diferencia_fechas.days in [4, 3, 2, 1]:
                    mensaje = f'Faltan {diferencia_fechas.days} para que el comprador {comprador} realice su pago.'
                    await actualizar_notificacion(mensaje=mensaje, id_notificacion=id_notificacion, nueva_fecha=fecha_actual)
                elif diferencia_fechas.days == 0:
                    mensaje = f'El pago del comprador {comprador} debe realizarse el día de hoy.'
                    await actualizar_notificacion(mensaje=mensaje, id_notificacion=id_notificacion, nueva_fecha=fecha_actual)
                elif diferencia_fechas.days == -1:
                    mensaje = f'La fecha de pago del comprador {comprador} se venció.'
                    await actualizar_notificacion(mensaje=mensaje, id_notificacion=id_notificacion, nueva_fecha=fecha_actual)

    except Exception:
        raise Exception("Ocurrió un error al verificar y crear las notificaciones")

# Llama a la función para verificar y crear notificaciones
def manejar_notificaciones():
    asyncio.run(verificar_y_crear_notificacion())

# Creamos el objeto y asignamos la tarea a realizar
agenda = BackgroundScheduler()
agenda.add_job(manejar_notificaciones, 'interval', days=1)
agenda.start()
