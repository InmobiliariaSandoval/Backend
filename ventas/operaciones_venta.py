# Módulos para interactuar con la base de datos
from pydantic import Json
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
import modelos
import esquemas
from datetime import date
from dateutil.relativedelta import relativedelta

from typing import List, Optional, Tuple

# Función que verificar los valores nulos de las ventas
def valores_nulos_ventas(diccionario: Json, valores_nulos: Optional[List] = None) -> bool:
    try:
        # Convertir los valores a un diccionario
        valores = diccionario.model_dump()

        datos = [clave for clave, valor in valores.items() if clave not in valores_nulos and not valor]

        return True if datos else False
    except Exception:
        raise Exception("Ocurrió un error al verificar los valors nulos")

# Función para obtener todos los compras
async def obtener_todas_las_ventas(db: Session, filtro: str = None, pagina: int = 1, tamano: int = 10) -> Tuple[List, int]:
    try:
        # Calcular el offset y el límite
        offset = (pagina - 1) * tamano
        limit = tamano

        # Generar la query para obtener las ventas
        query = db.query(modelos.ComprasCliente).order_by(desc(modelos.ComprasCliente.fecha_compra))

        # Verificar que exista el filtro
        if filtro:
            query = query.filter(modelos.ComprasCliente.estado_compra == filtro)

        total = query.count()

        compras = query.offset(offset).limit(limit).all()

        # Verificar que exista un valor en la respuesta
        if not compras:
            return [], 0

        return compras, total
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los compras.")

# Funciónq que se encarga de agregar una nueva venta
async def agregar_nueva_venta(db: Session, venta: esquemas.CompraCreate) -> modelos.Compras | bool:
    try:
        # Desempaquetar el diccionario utilizando(**venta.model_dump())
        # para que los valores se tomen en base al modelo
        venta_agregar = modelos.Compras(**venta.model_dump())

        # Añadirla venta a la base de datos y guardar los cambios
        db.add(venta_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(venta_agregar)

        if venta_agregar.id_compra:
            await crear_plazos_compra(db, venta_agregar)
            await actualizar_estado_un_lote(db, venta_agregar.id_lote, 'Proceso')
            await registrar_venta_vendedor(db, venta_agregar.id_vendedor)

        return venta_agregar if venta_agregar.id_compra else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al añadir una nueva venta")

# Función que se encarga de añadir una venta ya completa
async def agregar_nueva_venta_completa(db: Session, venta: esquemas.Compra) -> modelos.Compras | bool:
    try:
        # Desempaquetar el diccionario utilizando(**venta.model_dump())
        # para que los valores se tomen en base al modelo
        venta_agregar = modelos.Compras(**venta.model_dump())

        # Añadirla venta a la base de datos y guardar los cambios
        db.add(venta_agregar)
        db.commit()

        db.refresh(venta_agregar)

        if venta_agregar.id_compra:
            await actualizar_estado_un_lote(db, venta_agregar.id_lote, 'Vendido')
            await registrar_venta_vendedor(db, venta_agregar.id_vendedor)

        return venta_agregar if venta_agregar.id_compra else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al añadir una nueva completa")

# Función que se encarga de verificar que el lote esté disponible
async def verificar_lote_disponibilidad(db: Session, identificador_lote: int) -> bool:
    try:
        # Obtener el lote
        db_lote = db.query(modelos.LotesSecciones).filter(
            modelos.LotesSecciones.id_lote == identificador_lote
        ).first()

        # Verificar su disponibildad
        if db_lote.estado_terreno != "Disponible":
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un error al verificar la disponibilidad de un terrreno")

# Función que se encarga de verificar que el lote no esté en otra venta
async def verificar_lote_venta(db: Session, identificador_lote: int, identificador_venta: int = None, actualizando: bool = False) -> bool:
    try:
        # Buscar lote
        db_venta_lote = db.query(modelos.Compras).filter(
            modelos.Compras.id_lote == identificador_lote
        )

        # Verificar que esté actualizado
        if actualizando:
            db_venta_lote = db_venta_lote.filter(
                modelos.Compras.id_compra != identificador_venta
            )

        # Obtener el lote
        lote = db_venta_lote.first()

        # Verificar que exista
        if lote:
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un error al verificar si no está vendido el lote")

# Función que verficar que exista la venta
async def obtener_una_venta(db: Session, identificador_venta: int) -> modelos.Compras | bool:
    try:
        # Obtener una venta
        db_venta = db.query(modelos.Compras).filter(
            modelos.Compras.id_compra == identificador_venta
        ).all()

        # Verificar que exista
        if not db_venta:
            return False

        return db_venta
    except Exception:
        raise Exception("Ocurrió un error al obtener una venta")

# Función que actualiza una venta
async def actualizar_una_venta(db: Session, identificador_venta: int, venta_actualizada: esquemas.CompraCreate) -> modelos.Compras | bool:
    try:
        # Obtener la venta a actualiar
        db_venta = db.query(modelos.Compras).filter(
            modelos.Compras.id_compra == identificador_venta
        ).first()

        # Verificar que exista la venta
        if not db_venta:
            return False

        # Actualizar los valores de la venta
        for clave, valor in venta_actualizada.model_dump(exclude_unset=True).items():
            setattr(db_venta, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_venta)

        return db_venta if db_venta else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar una venta")

async def crear_plazos_compra(db: Session, venta_agregar: modelos.Compras):
    try:
        # Precio por plazo
        precio_por_plazo = venta_agregar.precio_total / venta_agregar.cantidad_total_plazos

        # Crear los plazos
        for i in range(1, venta_agregar.cantidad_total_plazos + 1):
            fecha_esperada = venta_agregar.fecha_compra + relativedelta(months=i)
            plazo = modelos.PlazosCompras(
                numero_plazo=i,
                cantidad_esperada=f"{precio_por_plazo:.1f}",
                fecha_esperada=fecha_esperada,
                comprobante=False,
                restante=f"{precio_por_plazo:.1f}",
                id_compra=venta_agregar.id_compra
            )
            db.add(plazo)

        db.commit()
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al agregar los plazos")

# Función para cambiar el estado de un lote
async def actualizar_estado_un_lote(db: Session, identificador_lote: str, estado: str) -> bool | None:
    try:
        # Obtener el lote a actualizar
        lote_actualizar = db.query(modelos.LotesSecciones).filter(
            modelos.LotesSecciones.id_lote == identificador_lote
        ).first()

        # Verificar que exista el lote
        if not lote_actualizar:
            return False

        # Actualizar el tipo estado del lote
        lote_actualizar.estado_terreno = estado

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(lote_actualizar)
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al cambiar el estado de un lote.")

# Agregar nueva venta a un vendedor
async def registrar_venta_vendedor(db: Session, identificador_vendedor: int) -> bool | None:
    try:
        # Obtener vendedor
        db_vendedor = db.query(modelos.Vendedores).filter(
            modelos.Vendedores.id_vendedor == identificador_vendedor
        ).first()

        # Verificar que exista
        if not db_vendedor:
            return False

        db_vendedor.lotes_vendidos += 1

        # Guadar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_vendedor)
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al registrar la venta del vendedor")

# Función que cambia el estado de la venta
async def cambiar_estado_una_venta(db: Session, identificador_venta: str, filtro: str = 'Finalizado') -> modelos.Compras | bool:
    try:
        # Obtener la venta
        db_venta = db.query(modelos.Compras).filter(
            modelos.Compras.id_compra == identificador_venta
        ).first()

        # Verificar que exista
        if not db_venta:
            return False

        # Cambiar el estado
        db_venta.estado_compra = filtro

        match filtro:
            case 'Proceso':
                await actualizar_estado_un_lote(db, db_venta.id_lote, 'Proceso')
            case 'Finalizado':
                await actualizar_estado_un_lote(db, db_venta.id_lote, 'Vendido')
            case 'Cancelado':
                await actualizar_estado_un_lote(db, db_venta.id_lote, 'Disponible')
            case _:
                pass

        # Guardar los cambios y refrescar el obejeto
        db.commit()
        db.refresh(db_venta)

        return db_venta
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al cambiar el estado de la venta")

# Función que crea un nuevo plazo
async def agregar_nuevo_plazo(db: Session, plazo: esquemas.PlazoCompraBase) -> modelos.PlazosCompras | bool:
    try:
        # Desempaquetar el diccionario utilizando (**plazo.model_dumpb())
        # para que los valores se tomen en base al modelo
        plazo_agregar = modelos.PlazosCompras(**plazo.model_dump())

        # Añadir el plazo a la base de datos y guardar los cambios
        db.add(plazo_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(plazo_agregar)

        # Verificar que se haya agregado correctamente
        return plazo_agregar if plazo_agregar.id_plazo else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al agregar un nuevo plazo")

# Funciń que actualizar un plazo
async def actualizar_un_plazo_compra(db: Session, identificador_plazo: str, plazo: esquemas.PlazoCompraCreate) -> modelos.PlazosCompras | bool:
    try:
        # Obtener el plazo a actualizar
        db_plazo = db.query(modelos.PlazosCompras).filter(
            modelos.PlazosCompras.id_plazo == identificador_plazo
        ).first()

        # Verificar que exista el plazo
        if not db_plazo:
            return False

        # Actualizar los valores del plazo
        for clave, valor in plazo.model_dump(exclude_unset=True).items():
            setattr(db_plazo, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_plazo)

        return db_plazo if db_plazo else False
    except Exception:
        raise Exception("Ocurrió un error al actualizar el plazo de compra")

# Función que obtiene todos los plazos de una compra
async def obtener_todos_los_plazos(db: Session, identificador_compra: str, pagina: int = 1, tamano: int = 10) -> Tuple[List, int]:
    try:
        # Calcular el offset y el limit
        offset = (pagina - 1) * tamano
        limit = tamano

        # Generar la query para obtener todos los datos
        query = db.query(modelos.PlazosCompras).filter(
            modelos.PlazosCompras.id_compra == identificador_compra
        )

        # Obtener el total
        total = query.count()

        # Obtener los plazos
        plazos = query.offset(offset).limit(limit).all()

        # Verificar que exista un valor
        if not plazos:
            return [], 0

        return plazos, total
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los plazos")

# Función que obtiene un plazo en especifico
async def obtener_plazo_especifico(db: Session, identificador_plazo: str) -> modelos.PlazosCompras | bool:
    try:
        # Obtener el plazo en especificio
        db_plazo = db.query(modelos.PlazosCompras).filter(
            modelos.PlazosCompras.id_plazo == identificador_plazo
        ).all()

        # Verificar que exista el valor
        if not db_plazo:
            return False

        return db_plazo
    except Exception:
        raise Exception("Ocurrió un error al obtener un plazo en especifico")

# Función que eliminar un plazo en especifico
async def eliminar_un_plazo(db: Session, identificador_plazo: str) -> bool:
    try:
        # Obtener plazo a eliminar
        db_plazo = db.query(modelos.PlazosCompras).filter(
            modelos.PlazosCompras.id_plazo == identificador_plazo
        ).first()

        # Verificar que exista
        if not db_plazo:
            return False

        # Eliminar y guardar los cambios
        db.delete(db_plazo)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un erro al eliminar el plazo")

# Función que crea un nuevo detalle de pago
async def agregar_nuevo_detalle(db: Session, detalle: esquemas.DetallePagoCreate) -> modelos.DetallesPago | bool:
    try:
        # Desempaquetar el diccionario utilizando (**detalle.model_dumpb())
        # para que los valores se tomen en base al modelo
        detalle_agregar = modelos.DetallesPago(**detalle.model_dump())


        # Agregar y guardar los cambios
        db.add(detalle_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(detalle_agregar)

        if detalle_agregar and detalle_agregar.id_detalle_pago:
            await registrar_pago(db, detalle.cantidad_dada, detalle.id_plazo)
            return detalle_agregar

        return False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al agregar el nuevo detalle del plazo")

# Función que actualizar un detalle de pago
async def actualizar_un_detalle_pago(db: Session, identificador_detalle: str, detalle: esquemas.DetallePagoCreate) -> modelos.DetallesPago | bool:
    try:
        # Obtener el detalle a actualizar
        db_detalle = db.query(modelos.DetallesPago).filter(
            modelos.DetallesPago.id_detalle_pago == identificador_detalle
        ).first()

        # Verificar que exista el detalle
        if not db_detalle:
            return False

        # Actualizar los valores del detalle
        for clave, valor in detalle.model_dump(exclude_unset=True).items():
            setattr(db_detalle, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_detalle)

        await registrar_pago(db, db_detalle.cantidad_dada, db_detalle.id_plazo)

        # await verificar_estado_venta(db, db_detalle.id_detalle_pago)

        return db_detalle if db_detalle else False
    except Exception:
        raise Exception("Ocurrió un error al actualizar el detalle del plazo")

# Función que obtener un detalle en base a al plazo
async def obtener_detalle_de_plazo(db: Session, identificador_plazo: str) -> modelos.DetallesPago | bool:
    try:
        # Obtener el detalle
        db_detalle = db.query(modelos.DetallesPago).filter(
            modelos.DetallesPago.id_plazo == identificador_plazo
        ).all()

        # Verificar que exista
        if not db_detalle:
            return False

        return db_detalle
    except Exception:
        raise Exception("Ocurrió un error al obtener el detalle de un plazo")

# Obtener un detalle sin necesidad del plazo
async def obtener_detalle_especifico(db: Session, identificador_detalle: str) -> modelos.DetallesPago | bool:
    try:
        # Obtener el detalle
        db_detalle = db.query(modelos.DetallesPago).filter(
            modelos.DetallesPago.id_detalle_pago == identificador_detalle
        ).all()

        # Verificar que exita
        if not db_detalle:
            return False

        return db_detalle
    except Exception:
        raise Exception("Ocurrió un error al obtener el detalle en especifico")

# Función que elimina un detalle
async def eliminar_un_detalle(db: Session, identificador_detalle: str) -> bool:
    try:
        # Obtener el detalle a eliminar
        db_detalle = db.query(modelos.DetallesPago).filter(
            modelos.DetallesPago.id_detalle_pago == identificador_detalle
        ).first()

        # Verificar que exista
        if not db_detalle:
            return False

        # Eliminar el detalle y guardar los cambios
        db.delete(db_detalle)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar un detalle de pago")

# Verificar que la compra esté finalizada
# async def verificar_estado_venta(db: Session, identificador_compra: str) -> None:
#     try:
#         # Obtener el restante
#         plazos = db.query(modelos.PlazosCompras).filter(
#             modelos.PlazosCompras.id_compra == identificador_compra
#         ).all()

#         # Verificar que exita
#         if not plazos:
#             return

#         # Calcular el restante total
#         restante_total = sum(plazo.restante for plazo in plazos)

#         # Verificar si el restante total es cero
#         if restante_total == 0:
#             await cambiar_estado_una_venta(db, identificador_compra)

#     except Exception:
#         raise Exception("Ocurrió un error al verificar la compra finalizada")

# Verificar que no se repita el número de plazo en la compra
async def verificar_numero_plazo(db: Session, plazo: esquemas.PlazoCompraCreate, actualizando: bool = False, identificador_plazo: bool = None):
    try:
        # Generar la query de filtro
        db_query = db.query(modelos.PlazosCompras).filter(
            modelos.PlazosCompras.id_compra == plazo.id_compra,
            modelos.PlazosCompras.numero_plazo == plazo.numero_plazo
        )

        # Verificar que se esté actualizando
        if actualizando:
            db_query = db_query.filter(
                modelos.PlazosCompras.id_plazo != identificador_plazo
            )

        # Obtener el plazo
        plazo = db_query.first()

        # Verificar que exista
        if not plazo:
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un error al verificar el número de plazo de la compra")


async def registrar_pago(db: Session, cantidad_dada: float, identificador_plazo: int) -> bool:
    try:
        # Obtener el plazo a actualizar
        db_plazo = db.query(modelos.PlazosCompras).filter(
            modelos.PlazosCompras.id_plazo == identificador_plazo
        ).first()

        excedente = cantidad_dada

        if db_plazo.restante > 0:
            # Aplicar el excedente al plazo actual
            pago_aplicado = min(db_plazo.restante, excedente)

            # Actualizar el restante del plazo
            db_plazo.restante -= pago_aplicado
            excedente -= pago_aplicado

            # Marcar el plazo como completado si el restante es cero
            if db_plazo.restante <= 0:
                db_plazo.comprobante = True
                db_plazo.restante = 0

        db.commit()
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al registrar el pago")