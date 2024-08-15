# Módulos para interactuar con la base de datos
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
import modelos
import esquemas

from typing import List, Tuple

# Función para obtener todos los vendedores
async def obtener_todos_los_vendedores(db: Session, filtro: str = None, clasificacion: str = None, pagina: int = 1, tamano_pagina: int = 10) -> Tuple[List, int]:
    try:
        # Genear query para obtener losvendedores de la base de datos
        query = db.query(modelos.Vendedores)

        # Verificar que exista el tipo de búsqueda
        if clasificacion == "Suspendidos":
            query = query.filter(modelos.Vendedores.estado_vendedor == False)
        elif clasificacion == "Activos":
            query = query.filter(modelos.Vendedores.estado_vendedor == True)

        if filtro == "mas":
            query = query.order_by(desc(modelos.Vendedores.lotes_vendidos))
        elif filtro == "menos":
            query = query.order_by(asc(modelos.Vendedores.lotes_vendidos))

        # Aplicar paginación
        total_vendedores = query.count()
        vendedores = query.offset((pagina - 1) * tamano_pagina).limit(tamano_pagina).all()

        # Verificar que exista un valor en la respuesta
        if not vendedores:
            return [], 0

        return vendedores, total_vendedores
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los vendedores.")

# Función que se encarga de obtener todos los vendedores sin paginación
async def obtener_todos_vendedores(db: Session) -> modelos.Vendedores | bool:
    try:
        # Obtener todos los vendedores
        db_vendedores = db.query(modelos.Vendedores).filter(
            modelos.Vendedores.estado_vendedor == True
        ).all()

        # Verificar que existan vendedores
        if not db_vendedores:
            return False

        return db_vendedores
    except Exception:
        raise Exception("Ocurrió un error al obtener los vendedores")

# Función para obtener un vendedor en especifico
async def obtener_un_vendedor(db: Session, identificador_vendedor) -> List | None:
    try:
        # Obtener un vendedor en especifico de la base de datos
        vendedor = db.query(modelos.Vendedores).filter(
            modelos.Vendedores.id_vendedor == identificador_vendedor
        ).all()

        # Verificar que exista un valor en la respuesta
        if not vendedor:
            return None

        return vendedor
    except Exception:
        raise Exception("Ocurrió un error al obtener el vendedor.")

# Verificar valores nulos
def valores_nulos(diccionario: esquemas.VendedorCreate, valores_nulo: list) -> bool:
    try:
        # Convertir los valores a un diccionario
        valores = diccionario.model_dump()

        # Crear una lista con los valores que no estén en valores nulos
        # y, además, que su valor sea nulo, es decir, los que deberían de ser no nulos
        datos = [clave for clave, valor in valores.items() if clave not in valores_nulo and not valor]

        return True if datos else False
    except Exception as error:
        print(f"Ocurrió un error al verificar valores nulos: {error}")
        raise Exception("Ocurrió un error al verificar los valores nulos")

# Función para verificar que ya existe el registro
async def verificar_vendedor_existente(db: Session, vendedor: esquemas.VendedorCreate, identificador_vendedor: str = None, actualizando: bool = False) ->  bool:
    try:
        # Consulta para verificar RFC
        vendedor_obtenido_RFC = db.query(modelos.Vendedores).filter(
            modelos.Vendedores.RFC_vendedor == vendedor.RFC_vendedor
        ).first()

        # Verificar si existe el RFC
        if vendedor_obtenido_RFC and vendedor_obtenido_RFC.RFC_vendedor:
            return True

        # Consulta para obtener el correo electronico
        query_correo_electronico = db.query(modelos.Vendedores).filter(
            modelos.Vendedores.correo_electronico == vendedor.correo_electronico
        )

        # Verificar que se esté actualizando
        if actualizando:
            query_correo_electronico = query_correo_electronico.filter(modelos.Vendedores.id_vendedor != identificador_vendedor)

        # Obtener el correo electrónico
        correo_electronico = query_correo_electronico.first()

        # Consulta para obtener el telefono
        query_telefono = db.query(modelos.Vendedores).filter(
            modelos.Vendedores.numero_telefono == vendedor.numero_telefono
        )

        # Verificar que se esté actualizando
        if actualizando:
            query_telefono = query_telefono.filter(modelos.Vendedores.id_vendedor != identificador_vendedor)

        # Obtener el telefono
        telefono = query_telefono.first()

        # Verificar que exista un resultado
        if not correo_electronico and not telefono:
            return False

        # Verificar número de teléfono y correo electrónico
        if telefono or correo_electronico:
            return True

        # Verificar que exista el vendedor0
        return False

    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al verificar el vendedor.")

# Función para crear un vendedor
async def añadir_un_nuevo_vendedor(db: Session, vendedor: esquemas.VendedorCreate) -> modelos.Usuarios | bool:
    try:
        # Desempaquetar el diccionario utilizando (**usuario.model_dumpb())
        # para que los valores se tomen en base al modelo
        vendedor_añadir = modelos.Vendedores(**vendedor.model_dump())

        # Añadir el valor a la base de datos y guardar los cambios
        db.add(vendedor_añadir)
        db.commit()

        # Resfrecar el objeto
        db.refresh(vendedor_añadir)

        # Verificar que se haya agreado correctamente a la base de datos
        return vendedor_añadir if vendedor_añadir and vendedor_añadir.id_vendedor else False

    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al crear un nuevo vendedor")

# Función para actualizar un vendedor
async def actualizar_un_vendedor(db: Session, identificador_vendedor: str, vendedor: esquemas.VendedorCreate) -> modelos.Usuarios | bool:
    try:
        db_vendedor = db.query(modelos.Vendedores).filter(modelos.Vendedores.id_vendedor == identificador_vendedor).first()
        if not db_vendedor:
            return False

        # Actualizar los valores del vendedor
        for key, value in vendedor.model_dump(exclude_unset=True).items():
            setattr(db_vendedor, key, value)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_vendedor)
        return db_vendedor if db_vendedor else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar el vendedor.")

# Función para eliminar un vendedor
async def eliminar_un_vendedor(db: Session, identificador_vendedor: str) -> bool:
    try:
        # Obtener el vendedor a eliminar
        vendedor_eliminar = db.query(modelos.Vendedores).filter(modelos.Vendedores.id_vendedor == identificador_vendedor).first()

        # Verificar que exista el cliente
        if not vendedor_eliminar:
            return False

        # Eliminar el vendedor y guardar los cambios
        db.delete(vendedor_eliminar)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar el vendedor.")

# Función para cambiar el estado de un vendedor
async def actualizar_estado_vendedor(db: Session, identificador_vendedor: str, estado: str) -> List | bool:
    try:
        # Obtener el vendedor a actualizar
        vendedor_actualizar = db.query(modelos.Vendedores).filter(modelos.Vendedores.id_vendedor == identificador_vendedor).first()

        # Verificar que exista el cliente
        if not vendedor_actualizar:
            return False

        # Actualizar el tipo de cuenta
        vendedor_actualizar.estado_vendedor = True if estado == 'Activar' else False

        # Cuardar los cambios y refrescar el usuario actualizado
        db.commit()
        db.refresh(vendedor_actualizar)

        return vendedor_actualizar

    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al cambiar el estado de un vendedor")
