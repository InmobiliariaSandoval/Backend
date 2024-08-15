"""
    Archivo que almacena las funciones para
    la validación de inciio de sesión
"""

# Módulos para interactuar con la base de datos
from pydantic import Json
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import between
import modelos
import esquemas

from typing import List, Tuple

# Función para obtener todos los estados
async def obtener_todos_los_estados(db: Session) -> List | None:
    try:
        # Obtener todos los estados de la base de datos
        estados_republica = db.query(modelos.EstadosRepublica).all()

        # Verificar que exista una valor en la respuesta
        if not estados_republica:
            return None

        return estados_republica
    except Exception:
        raise Exception("Ocurrió un error al obtener los estados.")

# Función que se encarga de obtener todos los municipios de la base de datos
async def obtener_todos_los_municipio_sin_estado(db: Session) -> List | None:
    try:
        # Obtener todos los municipios
        municipios = db.query(modelos.Municipios).all()

        # Verificar que existan los municipios
        if not municipios:
            return None

        return municipios
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los muncipios")

# Función para obtener todos los municipios de un estado
async def obtener_todos_los_municipios(db: Session, estado: str) -> List | None:
    try:
        # Obtener todos los municipios de un estado
        municipios = db.query(modelos.Municipios).join(modelos.Municipios.estado).filter(
            modelos.EstadosRepublica.nombre_estado == estado
        ).all()

        # Verificar que exista un valor en la respuesta
        if not municipios:
            return None

        return municipios
    except Exception:
        raise Exception("Ocurrió un error al obtener los municipios de un estado.")

# Función que se encarga de obtener todas las localidades de la base de datos
async def obtener_todas_las_localidades_sin_municipio(db: Session) -> List | None:
    try:
        # Obtener todos las localidades
        localidades = db.query(modelos.Localidades).all()

        # Verificar que existan las localidades
        if not localidades:
            return None

        return localidades
    except Exception:
        raise Exception("Ocurrió un error al obtener todas las localidades")

# Función para obtener todas las localidades de un municipio
async def obtener_todas_las_localidades(db: Session, municipio: str) -> List | None:
    try:
        # Obtener todas las localidades de un municipio
        localidades = db.query(modelos.Localidades).join(modelos.Localidades.municipio).filter(
            modelos.Municipios.nombre_municipio == municipio
        ).all()

        # Verificar que exista un valor en la respuesa
        if not localidades:
            return None

        return localidades
    except Exception:
        raise Exception("Ocurrió un error al obtener las localidades.")

# Función que se encarga de obtener todos los complejos de la base de datos
async def obtener_todos_complejos_sin_localidad(db: Session) -> List | None:
    try:
        # Obtener todos los complejos_residenciales
        complejos_residenciales = db.query(modelos.ComplejosResidenciales).all()

        # Verificar que existan las complejos_residenciales
        if not complejos_residenciales:
            return None

        return complejos_residenciales
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los complejos residenciales")

# Función para obtener todos los complejos de una localidad
async def obtener_todos_los_complejos(db: Session, localidad: str, tipo_complejo: str) -> List | None:
    try:
        # Genear búsqueda inicial con  todos los complejos de una localidad
        query = db.query(modelos.ComplejosResidenciales).join(modelos.ComplejosResidenciales.localidad).filter(
            modelos.Localidades.nombre_localidad == localidad
        )

        # Verificar que exista el filtro
        if tipo_complejo:
            query = query.filter(modelos.ComplejosResidenciales.tipo_complejo == tipo_complejo)

        # Obtener todos los complejos
        complejos = query.all()

        # Verificar que exista un valor en la respuesta
        if not complejos:
            return None

        return complejos
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los lotes.")

# Función que se encarga de obtener todos los complejos de la base de datos
async def obtener_todas_secciones_sin_complejo(db: Session) -> List | None:
    try:
        # Obtener todos los complejos_residenciales
        secciones = db.query(modelos.SeccionesComplejo).all()

        # Verificar que existan las complejos_residenciales
        if not secciones:
            return None

        return secciones
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los complejos residenciales")

# Función para obtener todos las secciones de un complejo
async def obtener_todas_las_secciones(db: Session, complejo: str) -> List | None:
    try:
        # Obtener todas las secciones de un complejo
        secciones = db.query(modelos.SeccionesComplejo).join(modelos.SeccionesComplejo.complejo_residencial).filter(
            modelos.ComplejosResidenciales.nombre_complejo == complejo
        ).all()

        # Verificar que exista un valor en la respuesta
        if not secciones:
            return None

        return secciones
    except Exception:
        raise Exception("Ocurrió un error al obtener todas las secciones de un complejo.")

# Función para obtener todos los lotes de un complejo
async def obtener_todos_los_lotes(db: Session, complejo: str, numero_seccion: Optional[str] = None, max_tamano: Optional[str] = None,
                                  min_tamano: Optional[str] = None, estado_vendido: Optional[str] = None, pagina: int = 1,
                                  tamano: int = 10, nombre_lote: Optional[str] = None) -> Tuple[List, int]:
    try:
        # Calcular el offset y el límite
        offset = (pagina - 1) * tamano
        limit = tamano

        # Generar la query de la base de datos
        query = db.query(modelos.VistaLotes).filter(modelos.VistaLotes.nombre_complejo == complejo)

        # Verificar filtros
        if numero_seccion:
            query = query.filter(modelos.VistaLotes.nombre_seccion == numero_seccion)

        if estado_vendido:
            query = query.filter(modelos.VistaLotes.estado_terreno == estado_vendido)

        if min_tamano and max_tamano:
            query = query.filter(between(modelos.VistaLotes.medida_total, min_tamano, max_tamano))

        if nombre_lote:
            numero = int(nombre_lote.split(' ')[1])
            query = query.filter(modelos.VistaLotes.numero_lote == numero)

        total = query.count()

        lotes = query.offset(offset).limit(limit).all()

        # Verificar que exista un valor en la respuesta
        if not lotes:
            return [], 0

        return lotes, total
    except Exception:
        raise Exception("Ocurrió un error al obtener todos los lotes de un complejo.")

# Función para obtener un lote con información extra
async def obtener_un_lote_extra(db: Session, identificador_lote) -> modelos.VistaLotes | bool:
    try:
        # Obtener el lote especifico
        db_lote = db.query(modelos.VistaLotes).filter(
            modelos.VistaLotes.id_lote == identificador_lote
        ).all()

        # Verificar que exista el lote
        if not db_lote:
            return False

        return db_lote
    except Exception:
        raise Exception("Ocurrió un error al obtener la información extra de un lote")

# Función para obtener un lote en especifico
async def obtener_un_lote(db: Session, identificador_lote: str) -> List | None:
    try:
        # Obtener al lote especifioc
        lote = db.query(modelos.VistaLotesSeccion).filter(
            modelos.VistaLotesSeccion.id_lote == identificador_lote
        ).all()

        # Verificar que exista un valor en la respuesta
        if not lote:
            return None

        return lote
    except Exception:
        raise Exception("Ocurrió un erro al obtener la información del lote.")

# Función para obtener la ubicación de un lote
async def obtener_ubicacion_un_lote(db: Session, identificador_lote: str ) -> List | bool:
    try:
        ubicacion = db.query(modelos.LotesUbicaciones).filter(
            modelos.LotesUbicaciones.id_lote == identificador_lote
        ).first()

        # Verificar que exista un valor en la respuesta
        if not ubicacion:
            return False

        return ubicacion
    except Exception:
        raise Exception("Ocurrió un error al obtener la ubicación.")

# Verificar valores nulos
def valores_nulos_lotes(diccionario: Json, valores_nulos: Optional[list] = None) -> bool:
    try:
        # Convertir los valores a un diccionario válido
        valores = diccionario.model_dump()

        datos = [clave for clave, valor in valores.items() if clave not in valores_nulos and not valor]

        return True if datos else False
    except Exception:
        raise Exception("Ocurrió un error al verificar los valores nulos")

# Función que verificar que no exista el estado
async def verificar_estado_existente(db: Session, estado: esquemas.EstadoCreate) -> bool:
    try:
        # Obtener el estado en base al nombre
        estado = db.query(modelos.EstadosRepublica).filter(
            modelos.EstadosRepublica.nombre_estado == estado.nombre_estado
        ).first()

        # Verificar que exista
        if estado and estado.nombre_estado:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar que exista el estado")

# Función para añadir un nuevo estado
async def agregar_un_nuevo_estado(db: Session, estado: esquemas.EstadoCreate) -> modelos.EstadosRepublica | bool:
    try:
        # Desempaquetar el diccionario utilizando (**estado.model_dumpb())
        # para que los valores se tomen en base al modelo
        estado_agregar = modelos.EstadosRepublica(**estado.model_dump())

        # Añadir el estado a la base de datos y guardar los cambios
        db.add(estado_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(estado_agregar)

        # Verificar que se haya agregado correctamente
        return estado_agregar if estado_agregar and estado_agregar.id_estado else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al ingresar el estado.")

# Función que se encargar de verificar si un estado existe al añadir un municipio
async def verficar_estado_municipio(db: Session, identificador_estado: int) -> bool:
    try:
        # Obtener el estado en base al nombre
        estado = db.query(modelos.EstadosRepublica).filter(
            modelos.EstadosRepublica.id_estado == identificador_estado
        ).first()

        # Verificar que exista
        if estado and estado.nombre_estado:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar que exista el estado al añadir un municipio")

# Verificar que no se repita el municipio dentro de un estao
async def verificar_municipio_existente(db: Session, municipio: esquemas.MunicipioCreate) -> bool:
    try:
        # Obtener el municipio en base al nombre
        municipio_verificar = db.query(modelos.Municipios).filter(
            modelos.Municipios.id_estado == municipio.id_estado,
            modelos.Municipios.nombre_municipio == municipio.nombre_municipio,
        ).first()

        # Verificar que exista
        if municipio_verificar and municipio_verificar.nombre_municipio:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar que exista el estado")

# Función para añadir un nuevo municipio
async def agregar_nuevo_municipio(db: Session, municipio: esquemas.MunicipioCreate) -> modelos.Municipios | bool:
    try:
        # Desempaquetar el diccionario utilizando (**municipio.model_dumpb())
        # para que los valores se tomen en base al modelo
        municipio_agregar = modelos.Municipios(**municipio.model_dump())

        # Añadir el estado a la base de datos y guardar los cambios
        db.add(municipio_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(municipio_agregar)

        # Verificar que se haya agregado correctamente
        return municipio_agregar if municipio_agregar and municipio_agregar.id_municipio else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al ingresar el estado.")

# Función que se encarga de verificar que existe el municipio
async def verificar_municipio_localidad(db: Session, identificador_municipio: int) -> bool:
    try:
        # Obtener municipio en base al identificador
        municipio = db.query(modelos.Municipios).filter(
            modelos.Municipios.id_municipio == identificador_municipio
        ).first()

        # Verificar que exista
        if municipio and municipio.id_municipio:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar el municipio de la localidad")

# Función que se encarga de verificar que existe la localidad en ese municipio
async def verificar_localidad_existente(db: Session, localidad: esquemas.LocalidadCreate) -> bool:
    try:
        # Obtener la localidad en base al nombre
        localidad_verficar = db.query(modelos.Localidades).filter(
            modelos.Localidades.id_municipio == localidad.id_municipio,
            modelos.Localidades.nombre_localidad == localidad.nombre_localidad
        ).first()

        # Verificar que exista la localidad
        if localidad_verficar and localidad_verficar.nombre_localidad:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error verificar")

# Función que se encarga de agregar una nueva localidad
async def agregar_nueva_localidad(db: Session, localidad: esquemas.LocalidadCreate) -> modelos.Localidades | bool:
    try:
        # Desempaquetar el diccionario utilizando (**localidad.model_dumpb())
        # para que los valores se tomen en base al modelo
        localidad_agregar = modelos.Localidades(**localidad.model_dump())

        # Añadir el estado a la base de datos y guardar los cambios
        db.add(localidad_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(localidad_agregar)

        # Verificar que se haya agregado correctamente
        return localidad_agregar if localidad_agregar and localidad_agregar.id_localidad else False
    except Exception:
        raise Exception("Ocurrió un error al agregar una nueva localidad.")

# Función que se encarga de verificar que exista la localidad
async def verificar_localidad_complejo(db: Session, identificador_localidad: int) -> bool:
    try:
        # Obtener localidad
        localidad = db.query(modelos.Localidades).filter(
            modelos.Localidades.id_localidad == identificador_localidad
        ).first()

        # Verificar que exista la localidad
        if localidad and localidad.id_localidad:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar la localidad al ingresar un complejo.")

# Función que se encarga de verificar que exista el complejo en la localidad
async def verificar_complejo_existente(db: Session, complejo: esquemas.ComplejoResidencialCreate) -> bool:
    try:
        # Obtener el complejo
        complejo_verificar = db.query(modelos.ComplejosResidenciales).filter(
            modelos.ComplejosResidenciales.id_localidad == complejo.id_localidad,
            modelos.ComplejosResidenciales.nombre_complejo == complejo.nombre_complejo
        ).first()

        # Verificar que exista el valor
        if complejo_verificar and complejo_verificar.id_complejo_residencial:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar el complejo residencial.")

# Función que se encarga de agregar un nuevo complejo
async def agregar_nuevo_complejo(db: Session, complejo: esquemas.ComplejoResidencialCreate) -> modelos.ComplejosResidenciales | bool:
    try:
        # Desempaquetar el diccionario utilizando (**localidad.model_dumpb())
        # para que los valores se tomen en base al modelo
        complejo_agregar = modelos.ComplejosResidenciales(**complejo.model_dump())

        # Añadir el estado a la base de datos y guardar los cambios
        db.add(complejo_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(complejo_agregar)

        # Verificar que se haya agregado correctamente
        return complejo_agregar if complejo_agregar and complejo_agregar.id_complejo_residencial else False
    except Exception:
        raise Exception("Ocurrió un error al ingrasar un nuevo complejo.")

# Función que se encarga de verificar que exista el complejo residencial
async def verificar_complejo_seccion(db: Session, identificador_complejo: int) -> bool:
    try:
        # Obtener el complejo residencial
        complejo = db.query(modelos.ComplejosResidenciales).filter(
            modelos.ComplejosResidenciales.id_complejo_residencial == identificador_complejo
        ).first()

        # Verificar que exista el complejo
        if complejo and complejo.id_complejo_residencial:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verifiar el complejo residencial al agregar la seccion")

# Función que se encarga de verificar si ya existe una seccion en el complejo residencial
async def verificar_seccion_existente(db: Session, seccion: esquemas.SeccionComplejoCreate) -> bool:
    try:
        # Obtener seccion
        seccion_verificar = db.query(modelos.SeccionesComplejo).filter(
            modelos.SeccionesComplejo.id_complejo_residencial == seccion.id_complejo_residencial,
            modelos.SeccionesComplejo.nombre_seccion == seccion.nombre_seccion
        ).first()

        # Verificar que exista el valor
        if seccion_verificar and seccion_verificar.id_seccion:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al comprobar que exista la seccion.")

# Función que se encarga de verificar que exista la seccion
async def verificar_seccion_lote(db: Session, identificador_seccion: int) -> bool:
    try:
        # Obtener sección
        seccion = db.query(modelos.SeccionesComplejo).filter(
            modelos.SeccionesComplejo.id_seccion == identificador_seccion
        ).first()

        # Verificar que exista el valor
        if seccion and seccion.id_seccion:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar la sección al ingresar un lote")

# Función que se encarga de veriifcar si ya existe el lote en la sección
async def verificar_lote_existente(db: Session, lote: esquemas.LoteSeccionCreate) -> bool:
    try:
        # Obtener lote
        lote_verficar = db.query(modelos.LotesSecciones).filter(
            modelos.LotesSecciones.id_seccion == lote.id_seccion,
            modelos.LotesSecciones.numero_lote == lote.numero_lote
        ).first()

        # Verificar si ya existe el valor
        if lote_verficar and lote_verficar.id_lote:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar si ya existe el lote.")

# Función que se encarga de agregar un nuevo lote
async def agregar_nuevo_lote(db: Session, lote: esquemas.LoteSeccionCreate) -> modelos.LotesSecciones | bool:
    try:
        # Desempaquetar el diccionario utilizando (**lote.model_dumpb())
        # para que los valores se tomen en base al modelo
        lote_agregar = modelos.LotesSecciones(**lote.model_dump())

        # Añadir el estado a la base de datos y guardar los cambios
        db.add(lote_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(lote_agregar)

        # Verificar que se haya agregado correctamente
        return lote_agregar if lote_agregar and lote_agregar.id_lote else False
    except Exception:
        raise Exception("Ocurrió un error al agregar un nuevo lote.")

# Función que se encarga de verificar si existe el lote al actualizarlo
async def verificar_lote_existente_actualizar(db: Session, identificador_lote : str) -> bool:
    try:
        # Verificiar lote a actualizar
        lote = db.query(modelos.LotesSecciones).filter(modelos.LotesSecciones.id_lote == identificador_lote).first()

        # Verificar que exista el lote
        if lote and lote.id_lote:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar el lote a actualizar")

# Función que se encarga de verificar si no se repiten datos del lote al actualizarlo
async def verificar_lote_actualiza(db: Session, identificador_lote : str, lote: esquemas.LoteSeccionCreate) -> bool:
    try:
        # Verificiar lote a actualizar
        lote = db.query(modelos.LotesSecciones). \
        filter(modelos.LotesSecciones.id_lote != identificador_lote). \
        filter(
            modelos.LotesSecciones.id_seccion == lote.id_seccion,
            modelos.LotesSecciones.numero_lote == lote.numero_lote
        ).first()

        # Verificar que exista el lote
        if lote and lote.id_lote:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar el lote a actualizar")


# Función que se encarga de actualizar un lote
async def actualizar_un_lote(db: Session, identificador_lote: str, lote: esquemas.LoteSeccionCreate) -> modelos.LotesSecciones | bool:
    try:
        # Obtener el lote a actualizar
        db_lote = db.query(modelos.LotesSecciones).filter(
            modelos.LotesSecciones.id_lote == identificador_lote
        ).first()

        # Verificar que exista el lote
        if not db_lote:
            return False

        # Actualizar los valores del lote
        for clave, valor in lote.model_dump(exclude_unset=True).items():
            setattr(db_lote, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_lote)

        return db_lote if db_lote else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar el lote")

# Función para cambiar el estado de un lote
async def actualizar_estado_un_lote(db: Session, identificador_lote: str, estado: str) -> modelos.LotesSecciones | bool:
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

        return lote_actualizar
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al cambiar el estado de un lote.")

# Función que se encarga de eliminar un lote
async def eliminar_un_lote(db: Session, identificador_lote: str) -> bool:
    try:
        # Obtener el vendedor a eliminar
        lote_eliminar = db.query(modelos.LotesSecciones).filter(modelos.LotesSecciones.id_lote == identificador_lote).first()

        # Verificar que exista el cliente
        if not lote_eliminar:
            return False

        # Eliminar el vendedor y guardar los cambios
        db.delete(lote_eliminar)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar el lote.")

# Función que se encarga de verificar los datos de una seccción
async def verificiar_seccion_actualizar(db: Session, identificador_seccion: str, seccion: esquemas.SeccionComplejoCreate) -> bool:
    try:
        # Obtener sección
        seccion_actualizar = db.query(modelos.SeccionesComplejo). \
        filter(
            modelos.SeccionesComplejo.id_complejo_residencial == seccion.id_complejo_residencial,
            modelos.SeccionesComplejo.id_seccion != identificador_seccion,
            modelos.SeccionesComplejo.nombre_seccion == seccion.nombre_seccion,
        ).first()

        # Verficar que exista el dato
        if seccion_actualizar and seccion_actualizar.id_seccion:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar los datos de la sección al actualizar")

# Función que se encarga de devolver una sección
async def obtener_una_seccion(db: Session, identificador_seccion: int) -> modelos.SeccionesComplejo | bool:
    try:
        # Obtener el seccion
        db_seccion = db.query(modelos.SeccionesComplejo).filter(
            modelos.SeccionesComplejo.id_seccion == identificador_seccion
        ).all()

        # Verificar que exista el seccion
        if not db_seccion:
            return False

        return db_seccion
    except Exception:
        raise Exception("Ocurrió un error al obtener el seccion")

# Función que se encarga de agregar una nueva sección
async def agregar_nueva_seccion(db: Session, seccion: esquemas.SeccionComplejo) -> modelos.SeccionesComplejo | bool:
    try:
        # Desempaquetar el diccionario utilizando(**secion.model_dump())
        # para que los valores se tomen en base al modelo
        seccion_agregar = modelos.SeccionesComplejo(**seccion.model_dump())

        # Añadir la sección a la base de datos y guardar los cambios
        db.add(seccion_agregar)
        db.commit()

        # Refrescar el objeto
        db.refresh(seccion_agregar)

        return seccion_agregar if seccion_agregar and seccion_agregar.id_seccion else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un erro al agregar una nueva sección")

# Función que se encarga de actualizar una sección
async def actualizar_una_seccion(db: Session, identificador_seccion: str, seccion: esquemas.SeccionComplejoCreate) -> modelos.SeccionesComplejo | bool:
    try:
        # Obtener la sección a actualizar
        db_seccion = db.query(modelos.SeccionesComplejo).filter(
            modelos.SeccionesComplejo.id_seccion == identificador_seccion
        ).first()

        # Verificar que exista la sección
        if not db_seccion:
            return False

        # Actulizar los valores de la seccioń
        for clave, valor in seccion.model_dump(exclude_unset=True).items():
            setattr(db_seccion, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_seccion)

        return db_seccion if db_seccion else False
    except Exception:
        raise Exception("Ocurrió un error al actualizar la sección")

# Función que se encarga de verficiar la sección a eliminar
async def verificar_seccion_eliminar(db: Session, identificador_seccion: str) -> bool:
    try:
        # Obtener sección a eliminar
        db_seccion = db.query(modelos.SeccionesComplejo).filter(
            modelos.SeccionesComplejo.id_seccion == identificador_seccion
        ).first()

        # Verificar que exista
        if not db_seccion:
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un erro al verficiar la sección a eliminar")

# Función que se encarga de eliminar una sección
async def eliminar_una_seccion(db: Session, identificador_seccion: str) -> bool:
    try:
        # Obtener sección a eliminar
        seccion_eliminar = db.query(modelos.SeccionesComplejo).filter(
            modelos.SeccionesComplejo.id_seccion == identificador_seccion
        ).first()

        # Verificar que exista la sección
        if not seccion_eliminar:
            return False

        # Eliminar sección
        db.delete(seccion_eliminar)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar la sección.")

# Función que se encarga de verificar los datos de un complejo al actualizar
async def verificar_complejo_actualizar(db: Session, identificador_complejo: str, complejo: esquemas.ComplejoResidencialCreate) -> bool:
    try:
        # Obtener el complejo
        complejo = db.query(modelos.ComplejosResidenciales).filter(
            modelos.ComplejosResidenciales.id_complejo_residencial != identificador_complejo
        ).filter(
            modelos.ComplejosResidenciales.id_localidad == complejo.id_localidad,
            modelos.ComplejosResidenciales.nombre_complejo == complejo.nombre_complejo
        ).first()

        # Verficiar valor
        if complejo:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un erro al verificar los datos del complejo al actualizar")

# Función que se encarga de devolver un complejo
async def obtener_un_complejo(db: Session, identificador_complejo: int) -> modelos.ComplejosResidenciales | bool:
    try:
        # Obtener el complejo
        db_complejo = db.query(modelos.ComplejosResidenciales).filter(
            modelos.ComplejosResidenciales.id_complejo_residencial == identificador_complejo
        ).all()

        # Verificar que exista el complejo
        if not db_complejo:
            return False

        return db_complejo
    except Exception:
        raise Exception("Ocurrió un error al obtener el complejo")

# Función que se encarga de actualizar un complejo
async def actualizar_un_complejo(db: Session, identificador_complejo: str, complejo: esquemas.ComplejoResidencialCreate) -> modelos.ComplejosResidenciales | bool:
    try:
        # Obtener el complejo a actualizar
        complejo_actualizar = db.query(modelos.ComplejosResidenciales).filter(
            modelos.ComplejosResidenciales.id_complejo_residencial == identificador_complejo
        ).first()

        # Verficiar que exita
        if not complejo_actualizar:
            return False

        # Actualizar cada valor
        for clave, valor in complejo.model_dump(exclude_unset=True).items():
            setattr(complejo_actualizar, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(complejo_actualizar)

        return complejo_actualizar if complejo_actualizar else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar el complejo")

# Función que se encarga de eliminar un complejo
async def eliminar_un_complejo(db: Session, identificador_complejo: str) -> bool:
    try:
        # Obtener el complejo a eliminar
        complejo_eliminar = db.query(modelos.ComplejosResidenciales).filter(
            modelos.ComplejosResidenciales.id_complejo_residencial == identificador_complejo
        ).first()

        # Verificar que exista el complejo
        if not complejo_eliminar:
            return False

        # Eliminar objeto y guardar los cambios
        db.delete(complejo_eliminar)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar el complejo.")

# Función que se encarga de verificar que no repitan datos al actualizar una localidad
async def verificar_localidad_actualizar(db: Session, identificador_localidad: int, localidad: esquemas.LocalidadCreate) -> bool:
    try:
        # Obtener la localidad
        db_localidad = db.query(modelos.Localidades).filter(
            modelos.Localidades.id_localidad != identificador_localidad
        ).filter(
            modelos.Localidades.id_municipio == localidad.id_municipio,
            modelos.Localidades.nombre_localidad == localidad.nombre_localidad
        ).first()

        # Verificar que exista la localidad
        if db_localidad:
            return True

        return False
    except Exception:
        raise Exception("Ocurrió un error al verificar los datos de la localidad")

# Función que se encarga de devolver una localidad
async def obtener_una_localidad(db: Session, identificador_localidad: int) -> modelos.Localidades | bool:
    try:
        # Obtener el localidad
        db_localidad = db.query(modelos.Localidades).filter(
            modelos.Localidades.id_localidad == identificador_localidad
        ).all()

        # Verificar que exista el localidad
        if not db_localidad:
            return False

        return db_localidad
    except Exception:
        raise Exception("Ocurrió un error al obtener el localidad")

# Función que sen encarga de actualizar una localidad
async def actualizar_una_localidad(db: Session, identificador_localidad: int, localidad: esquemas.LocalidadCreate) -> modelos.Localidades | bool:
    try:
        # Obtener localidad a actualizar
        db_localidad = db.query(modelos.Localidades).filter(
            modelos.Localidades.id_localidad == identificador_localidad
        ).first()

        # Verificar que exista la localidad
        if not db_localidad:
            return False

        # Actualizamos los valores
        for clave, valor in localidad.model_dump(exclude_unset=True).items():
            setattr(db_localidad, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_localidad)

        return db_localidad if db_localidad else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar una localidad")

# Función que sen encarga de eliminar una localidad
async def eliminar_una_localidad(db: Session, identificador_localidad: int) -> bool:
    try:
        # Obtener localidad a a eliminar
        localidad_eliminar = db.query(modelos.Localidades).filter(
            modelos.Localidades.id_localidad == identificador_localidad
        ).first()

        # Verificar que exista la localidad
        if not localidad_eliminar:
            return False

        # Eliminar localidad y guardar los cambios
        db.delete(localidad_eliminar)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar la localidad.")

# Función que se encarga de verificar los datos al actualizar un municipio
async def verificar_municipio_actualizar(db: Session, identificador_municipio: int, municipio: esquemas.MunicipioCreate) -> bool:
    try:
        # Obtener municipio
        db_municipio = db.query(modelos.Municipios).filter(
            modelos.Municipios.id_municipio != identificador_municipio
        ).filter(
            modelos.Municipios.id_estado == municipio.id_estado,
            modelos.Municipios.nombre_municipio == municipio.nombre_municipio
        ).first()

        # Verificar que exista
        if not db_municipio:
            return False

        return True
    except Exception:
        raise Exception("Ocurrió un error al actualizar el municipio")

# Función que se encarga de devolver un municipio
async def obtener_un_municipio(db: Session, identificador_municipio: int) -> modelos.Municipios | bool:
    try:
        # Obtener el municipio
        db_municipio = db.query(modelos.Municipios).filter(
            modelos.Municipios.id_municipio == identificador_municipio
        ).all()

        # Verificar que exista el municipio
        if not db_municipio:
            return False

        return db_municipio
    except Exception:
        raise Exception("Ocurrió un error al obtener el municipio")

# Función que se encarga de actualizar un municipo
async def actualizar_un_municipio(db: Session, identificador_municipio: int, municipio: esquemas.MunicipioCreate) -> modelos.Municipios | bool:
    try:
        # Obtener municipio a actualizar
        db_municipio = db.query(modelos.Municipios).filter(
            modelos.Municipios.id_municipio == identificador_municipio
        ).first()

        # Verficiar que exista el municipio
        if not db_municipio:
            return False

        # Actualizar el municipio
        for clave, valor in municipio.model_dump(exclude_unset=True).items():
            setattr(db_municipio, clave, valor)

        # Guardar los cambios y refrescar el objeto
        db.commit()
        db.refresh(db_municipio)

        return db_municipio if db_municipio else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar un municipio")

# Función que se encarga de eliminar un municipio
async def eliminar_un_municipio(db: Session, identificador_municipio: int) -> bool:
    try:
        # Obtener municipio a eliminar
        db_municipio = db.query(modelos.Municipios).filter(
            modelos.Municipios.id_municipio == identificador_municipio
        ).first()

        # Verificar que exista el municipio
        if not db_municipio:
            return False

        # Eliminar el municipio y guardar los cambios
        db.delete(db_municipio)
        db.commit()

        return True
    except Exception:
        raise Exception("Ocurrió un error al eliminar el municipio")

# Función que se encarga de devolver un estado
async def obtener_un_estado(db: Session, identificador_estado: int) -> modelos.EstadosRepublica | bool:
    try:
        # Obtener el estado
        db_estado = db.query(modelos.EstadosRepublica).filter(
            modelos.EstadosRepublica.id_estado == identificador_estado
        ).all()

        # Verificar que exista el estado
        if not db_estado:
            return False

        return db_estado
    except Exception:
        raise Exception("Ocurrió un error al obtener el estado")

# Función que se encarga de verificar los datos al actualizar un estado
async def actualizar_un_estado(db: Session, identificador_estado: int, estado: esquemas.EstadoCreate) -> modelos.EstadosRepublica | bool:
    try:
        # Obtener estado a actualizar
        db_estado = db.query(modelos.EstadosRepublica).filter(
            modelos.EstadosRepublica.id_estado == identificador_estado
        ).first()

        # Verificar que exista el estado
        if not db_estado:
            return False

        # Actualizar los valores del estado
        for clave, valor in estado.model_dump(exclude_unset=True).items():
            setattr(db_estado, clave, valor)

        # Guardar los cambios y refrescar el estado
        db.commit()
        db.refresh(db_estado)

        return db_estado if db_estado else False
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al actualizar un estado")

# Función que eliminar un estado
async def eliminar_un_estado(db: Session, identificador_estado: int) -> bool:
    try:
        # Obtener el estado a eliminar
        db_estado = db.query(modelos.EstadosRepublica).filter(
            modelos.EstadosRepublica.id_estado == identificador_estado
        ).first()

        # Verificar que exista el estado
        if not db_estado:
            return False

        # Eliminar el estado y guardar los cambios
        db.delete(db_estado)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise Exception("Ocurrió un error al eliminar el estado")

# Función que obtiene la información de un lote vendido
async def obtener_informacion_lote_vendido(db: Session, identificador_lote: int) -> modelos.DatosVentaLote | bool:
    try:
        # Obtener el lote
        db_lote = db.query(modelos.DatosVentaLote).filter(
            modelos.DatosVentaLote.id_lote == identificador_lote
        ).first()

        # Verificar
        if not db_lote:
            return False

        return db_lote
    except Exception:
        raise Exception("Ocurrió un error al obtener la informaión del lote vendido")