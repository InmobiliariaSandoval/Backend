"""
    Archivo que almacena las funciones para
    la validación de inciio de sesión
"""

# Módulos para interactuar con la base de datos
from sqlalchemy.orm import Session
from mailjet_rest import Client
import modelos
import os

# Módulo de tipo de dato
from pydantic import EmailStr

# Módulo para obtener el token
from uuid import uuid4 as generar_token

# Función para verificar el token
async def verificar_token(db: Session, token: str) -> str | None:
    try:
        # Obtener el token
        token_acceso = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.token == token
        ).first()

        # Verificar que obtenga un token
        if not token_acceso:
            return None

        return token_acceso.token
    except Exception:
        raise Exception("Ocurrió un error al verificar el token.")

# Función para cambiar el estado de cuenta del usuario
async def cambiar_estado_cuenta_usuario(db: Session, token_usuario: str) -> bool | None:
    try:
        # Obtener estado de cuenta
        estado_cuenta_usuario = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.token == token_usuario
        ).first()

        # Verficar que obtenga un valor
        if not estado_cuenta_usuario:
            return None

        # Verificar que no tenga una sesión activa
        if not estado_cuenta_usuario.estado_cuenta:
            return None

        # Asignar nuevo token
        valor_previo = estado_cuenta_usuario.estado_cuenta
        estado_cuenta_usuario.estado_cuenta = False

        # Guardar los cambios y resfrescar el usuario actualizado
        db.commit()
        db.refresh(estado_cuenta_usuario)

        return True if valor_previo != estado_cuenta_usuario.estado_cuenta else False

    except Exception:
        raise Exception("Ocurrió un error al obtener el estado de cuenta")

# Función para obtener el estado de cuenta del usuario
async def obtener_estado_cuenta_usuario(db: Session, token_usuario: str) -> str | None:
    try:
        # Obtener estado de cuenta
        estado_cuenta_usuario = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.token == token_usuario
        ).first()

        # Verficar que obtenga un valor
        if not estado_cuenta_usuario:
            return None

        return estado_cuenta_usuario.estado_cuenta
    except Exception:
        raise Exception("Ocurrió un error al obtener el estado de cuenta")

# Funcion para obtener el token del usuario
async def obtener_token_usuario(db: Session, correo_electronico: EmailStr, contrasena: str) -> str | None:
    try:
        # Obtener los valores del usuario
        token_usuario = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.correo_electronico == correo_electronico,
            modelos.Usuarios.contraseña == contrasena
        ).first()

        # Verificar que obtenga un token
        if not token_usuario:
            return None

        return token_usuario.token
    except Exception:
        raise Exception("Ocurrió un error el obtener token con credenciales.")

# Funcion para obtener el usuario
async def obtener_usuario(db: Session, correo_electronico: EmailStr, contrasena: str) -> str | None:
    try:
        # Obtener los valores del usuario
        usuario = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.correo_electronico == correo_electronico,
            modelos.Usuarios.contraseña == contrasena
        ).first()

        # Verificar que obtenga un token
        if not usuario:
            return None

        return usuario
    except Exception:
        raise Exception("Ocurrió un error el obtener usuario con credenciales.")

# Verificar que exista la palabra de acceso
async def verificar_frase(db: Session, palabra_acceso: str, correo_electronico: EmailStr, contrasena: str) -> bool:
    try:
        # Obtene la frase
        frase = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.contraseña == contrasena,
            modelos.Usuarios.correo_electronico == correo_electronico,
            modelos.Usuarios.palabra_secreta == palabra_acceso
        ).first()

        # Verificar que se tenga un valor
        if not frase or not frase.palabra_secreta:
            return False

        # Verificar que sean iguales
        if palabra_acceso != frase.palabra_secreta:
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un error al verificar la frase")

# Cerrar sesión con palabra
async def cambiar_estado_palabra(db: Session, palabra_acceso: str) -> bool | None:
    try:
        # Obtener estado de cuenta
        estado_cuenta_usuario = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.palabra_secreta == palabra_acceso
        ).first()

        # Verficar que obtenga un valor
        if not estado_cuenta_usuario:
            return None

        # Verificar que no tenga una sesión activa
        if not estado_cuenta_usuario.estado_cuenta:
            return None

        # Asignar nuevo token
        valor_previo = estado_cuenta_usuario.estado_cuenta
        estado_cuenta_usuario.estado_cuenta = False

        # Guardar los cambios y resfrescar el usuario actualizado
        db.commit()
        db.refresh(estado_cuenta_usuario)

        return True if valor_previo != estado_cuenta_usuario.estado_cuenta else False

    except Exception:
        raise Exception("Ocurrió un error al cambiar el estado de cuenta")


# Funcin para cambiar el token anterior al nuevo de inicio de sesin
async def cambiar_token_nueva_sesion(db: Session, correo_electronico: EmailStr) -> str | None:
    try:
        # Crear nuevo token de acceso
        nuevo_token = str(generar_token())

        # Obtener usuario a actualizar
        usuario_actualizar = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.correo_electronico == correo_electronico
        ).first()

        # Verificar que exista el usuario
        if not usuario_actualizar:
            return None

        # Verificar que no tenga una sesión activa
        if usuario_actualizar.estado_cuenta:
            return None

        # Asignar nuevo token
        usuario_actualizar.token = nuevo_token
        usuario_actualizar.estado_cuenta = True

        # Guardar los cambios y resfrescar el usuario actualizado
        db.commit()
        db.refresh(usuario_actualizar)

        return nuevo_token if nuevo_token == usuario_actualizar.token else None

    except Exception:
        raise Exception("Ocurrio un error al cambiar el token de acceso.")

# Función para obtener la configuración
async def obtener_configuracion(db: Session, identificador_configuracion: str) -> modelos.Configuracion | bool:
    try:
        # Obtener configuracion en base al correo
        db_configuracion = db.query(modelos.Configuracion).filter(
            modelos.Configuracion.correo_empresa == identificador_configuracion
        ).first()

        # Verificar que existe el valor
        if not db_configuracion:
            return False

        return db_configuracion.nombre_usuario
    except Exception:
        raise Exception("Ocurrió un error al obtener la configuración")

# Función para obtener una configuración
async def obtener_configuracion_especifica(db: Session, identificador_configuracion: str) -> modelos.Configuracion | bool:
    try:
        # Obtener la configuración en base al correo
        db_configuracion = db.query(modelos.Configuracion).filter(
            modelos.Configuracion.nombre_usuario == identificador_configuracion
        ).all()

        # Verificar que exista
        if not db_configuracion:
            return False

        return db_configuracion
    except Exception:
        raise Exception("Ocurrió un erro al obtener la configuración")

async def enviar_correo_contrasena(db: Session, correo_acceso: EmailStr, palabra_secreta: str) -> bool:
    try:
        # Obtener usuario
        db_usuario = db.query(modelos.Usuarios).filter(
            modelos.Usuarios.correo_electronico == correo_acceso,
            modelos.Usuarios.palabra_secreta == palabra_secreta
        ).first()

        print(db_usuario)

        # Verificar que exista
        if not  db_usuario:
            return False

        # Configuraciones
        API_KEY = os.environ['API_KEY']
        API_SECRET = os.environ['API_SECRET']

        CONTRASENA = os.environ['CONTRASENA']
        EMAIL_EMPRESA = os.environ['EMAIL_EMPRESA']

        mailjet = Client(auth=(API_KEY, API_SECRET), version='v3.1')
        data = {
        'Messages': [
            {
            "From": {
                "Email": f"{EMAIL_EMPRESA}",
                "Name": "Inmobiliaria Grupo Sandoval"
            },
            "To": [
                {
                "Email": f"{correo_acceso}",
                "Name": f"{correo_acceso}"
                }
            ],
            "Subject": "Recuperación de contraseña.",
            "TextPart": "Correo de recuperación de contraseña",
            "HTMLPart": f"<h3>Querido usuario del sistema GIS, su contraseña de acceso es: {CONTRASENA}",
            "CustomID": "InmobiliariaGrupoSandoval"
            }
        ]
        }
        result = mailjet.send.create(data=data)

        if result.status_code == 200:
            return True
        else:
            return False
    except Exception:
        raise Exception("Ocurrió un error al cambiar la contraseña")