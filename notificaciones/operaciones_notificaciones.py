# Módulos para interactuar con la base de datos
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
import modelos

from typing import List, Tuple

# Función para obtener todas los notificaciones no leídas para mostrarlas en la alerta
async def obtener_todas_las_notificaciones(db: Session, pagina: int = 1, limite: int = 10, no_leidas: bool = None, orden: str = None) -> Tuple[List, int]:
    try:
        # Generar query para obtener todass las notificaciones de la base de datos
        query = db.query(modelos.Notificacines)

        # Verificar ord
        if orden == 'asc':
            query = query.order_by(asc(modelos.Notificacines.fecha))
        else:
            query = query.order_by(desc(modelos.Notificacines.fecha))

        # Verificar filtro de búsqueda
        if no_leidas:
            query = query.filter(modelos.Notificacines.estado_leido == False)
        elif no_leidas == False:
            query = query.filter(modelos.Notificacines.estado_leido == True)


        # Obtener el total de notificaciones
        query_total = query.count()

        # Obtener notificaciones
        notificaciones = query.offset((pagina - 1) * limite).limit(limite).all()

        # Verificar que exista un valor en la respuesta
        if not notificaciones:
            return [], 0

        return notificaciones, query_total
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los notificaciones.")

# Función para obtener una notificacion
async def obtener_una_notificacion(db: Session, identificador_notificacion: str) -> List | bool:
    try:
        # Obtener una notificacion
        notificacion = db.query(modelos.Notificacines).filter(
            modelos.Notificacines.id_notificacion == identificador_notificacion
        ).all()

        # Verificar que exista un valor en la respuesta
        if not notificacion:
            return False

        return notificacion
    except Exception:
        raise Exception("Ocurrió un error al intentar obtener una notificacion")


# Función para contar las notificacion
async def contar_todas_notificaciones(db: Session) -> int | bool:
    try:
        # Contar todas las notifcaciones
        notificaciones = db.query(modelos.Notificacines).count()

        # Verificar que existan notificaciones
        if not notificaciones or notificaciones < 0:
            return False

        return notificaciones
    except Exception:
        raise Exception("Ocurrió un error al contar todas las notificaciones")

# Funciń para eliminar todas las notificacione
async def eliminar_todas_notificaciones(db: Session) -> int | bool:
    try:
        # Eliminar todas las notificaciones
        cantidad_eliminadas = db.query(modelos.Notificacines).delete()
        db.commit()

        # Verificar que se haya eliminado
        if not cantidad_eliminadas or cantidad_eliminadas < 0:
            return False

        return cantidad_eliminadas
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar todas las notificaciones")


# Función para eliminar una notificacion
async def eliminar_una_notificacion(db: Session, identificador_notificacion: str) -> bool:
    try:
        # Obtener la notificación a eliminar
        notificacion_eliminar = db.query(modelos.Notificacines).filter(
            modelos.Notificacines.id_notificacion == identificador_notificacion
        ).first()

        # Verificar que exista la notificación
        if not notificacion_eliminar:
            return False

        # Eliminar el vendedor y guardar los cambios
        db.delete(notificacion_eliminar)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar una notificación.")

# Función para marcar como leída una notificacion
async def marcar_leido_notificacion(db: Session, identificador_notificacion: str) -> list | bool:
    try:
        # Obtener la notificación a actualizar
        notificacion_actualizar = db.query(modelos.Notificacines).filter(
            modelos.Notificacines.id_notificacion == identificador_notificacion
        ).first()

        # Verificar que exista la notificación
        if not notificacion_actualizar or notificacion_actualizar.estado_leido:
            return False

        # Cambiar estado a leído
        notificacion_actualizar.estado_leido = True

        # Actualizar el vendedor y guardar los cambios
        db.commit()
        db.refresh(notificacion_actualizar)

        return notificacion_actualizar
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar una notificación.")

# Función para marcar como leída todas las notificaciones
async def marcar_todas_notificaciones_leidas(db: Session) -> bool:
    try:
        # Obtener todas las notificaciones no leídas
        notificaciones_no_leidas = db.query(modelos.Notificacines).filter(
            modelos.Notificacines.estado_leido == False
        ).all()

        # Verificar si hay notificaciones no leídas
        if not notificaciones_no_leidas:
            return False

        # Marcar todas las notificaciones como leídas
        for notificacion in notificaciones_no_leidas:
            notificacion.estado_leido = True

        # Guardar los cambios
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar las notificaciones.")