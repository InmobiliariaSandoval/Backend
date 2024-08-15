# Módulos para interactuar con la base de datos
from sqlalchemy.orm import Session
import modelos
import esquemas

from typing import List, Tuple

# Función para obtener todos los clientes
async def obtener_todos_los_clientes(db: Session) -> modelos.Clientes | bool:
    try:
        # Obtener todos los clientes de la base de datos
        db_clientes = db.query(modelos.Clientes).all()

        # Verificar que exista un valor en la respuesta
        if not db_clientes:
            return False

        return db_clientes
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los clientes.")

# Función para obtener un cliente en especifico
async def obtener_un_cliente(db: Session, identificador_cliente: str) -> List | None:
    try:
        # Obtener el cliente en especifico
        cliente = db.query(modelos.Clientes).filter(
            modelos.Clientes.CURP_cliente == identificador_cliente
        ).all()

        # Verificar que exista un valor en la respuesta
        if not cliente:
            return None

        return cliente
    except Exception:
        raise Exception("Ocurrió un error al obtener el cliente.")

# Función que se encarga de verificar que exista un client
async def verificar_cliente_actualizar(db: Session, identificador_cliente: str) -> bool:
    try:
        # Obtener el cliente en base a su identificador
        db_cliente = db.query(modelos.Clientes).filter(
            modelos.Clientes.CURP_cliente == identificador_cliente
        ).first()

        # Verfiicar que exista el cliente
        if not db_cliente or not db_cliente.CURP_cliente:
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un error al verificar que exista el cliente")

# Función que se encarga de verificar el número de telefono
async def verificar_telefono_cliente(db: Session, cliente: esquemas.ClienteCreate, actualizando: bool = False, identificador_cliente: str = None) -> bool:
    try:
        # Obtener el telefono del cliente
        db_telefono = db.query(modelos.Clientes).filter(
            modelos.Clientes.telefono_contacto == cliente.telefono_contacto
        )

        # Verificar que se esté actualizando
        if actualizando:
            db_telefono = db_telefono.filter(
                modelos.Clientes.CURP_cliente != identificador_cliente
            )

        # Obtener valor
        telefono = db_telefono.first()

        # Verificar
        if telefono and telefono.telefono_contacto:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar el número del cliente")

# Función que se encarga de verificar que verificar que no exista el cliente
async def verificar_cliente_existente(db: Session, cliente: esquemas.ClienteCreate, actualizando: bool = False, identificador_cliente: str = None) -> bool:
    try:
        # Obtener el cliente
        db_cliente = db.query(modelos.Clientes).filter(
            modelos.Clientes.CURP_cliente == cliente.CURP_cliente
        )

        # Verificar que se esté actualizando
        if actualizando:
            db_cliente = db_cliente.filter(
                modelos.Clientes.CURP_cliente != identificador_cliente
            )

        # Obtener valores
        curp_cliente = db_cliente.first()

        # Verificar que no exista
        if curp_cliente and curp_cliente.CURP_cliente:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar el cliente")

# Función que se encarga de agregar el nuevo cliente
async def agregar_nuevo_cliente(db: Session, cliente: esquemas.ClienteCreate) -> modelos.Clientes | bool:
    try:
        # Desempaquetar el diccionario utilizando(**cliente.model_dump())
        # para que los valores se tomen en base al modelo
        cliente_agregar = modelos.Clientes(**cliente.model_dump())

        # Añadir la sección a la base de datos y guardar los cambios
        db.add(cliente_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(cliente_agregar)

        return cliente_agregar if cliente_agregar.CURP_cliente else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al agregar un nuevo cliente")

# Función que se encarga de actualizar un cliente
async def actualizar_un_cliente(db: Session, identificador_cliente: str, cliente_actualizar: esquemas.ClienteCreate) -> modelos.Clientes | bool:
    try:
        # Obtener el cliente a actualizar
        db_cliente = db.query(modelos.Clientes).filter(
            modelos.Clientes.CURP_cliente == identificador_cliente
        ).first()

        # Verificar que exista el cliente
        if not db_cliente:
            return False

        # Actualizar los valores del cliente
        for clave, valor in cliente_actualizar.model_dump(exclude_unset=True).items():
            setattr(db_cliente, clave, valor)

        # Guardar los cambios y resfrescar el objeto
        db.commit()
        db.refresh(db_cliente)

        return db_cliente if db_cliente else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar un cliente")

# Función que se encarga de eliminar un cliente
async def eliminar_un_cliente(db: Session, identificador_cliente: str) -> bool:
    try:
        # Obtener cliente a eliminar
        db_cliente = db.query(modelos.Clientes).filter(
            modelos.Clientes.CURP_cliente == identificador_cliente
        ).first()

        # Verificar que exista el cliente
        if not db_cliente:
            return False

        # Eliminar el cliente y guardar los cambios
        db.delete(db_cliente)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar un cliente")