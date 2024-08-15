"""
    Archivo que almacena los módelos de la base de datos
    para la función ORM
"""

# Importar módulos necesarios
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

# Importar el objeto de base de datos
from base_datos import Base

# Módulo para la tabla de usuario
class Usuarios(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, nullable= False, primary_key=True, index=True, autoincrement=True)
    correo_electronico = Column(String(60), nullable=False, unique=True)
    contraseña = Column(String(255), nullable=False)
    token = Column(String(60), nullable=False)
    palabra_secreta = Column(String(60), nullable=False, unique=True)
    estado_cuenta = Column(Boolean,nullable=False, default=False)

class Configuracion(Base):
    __tablename__ = 'configuracion'

    id_configuracion = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    nombre_usuario = Column(String(250), nullable=False, unique=True)
    nombre_empresa = Column(String(250), nullable=False, unique=True)
    correo_empresa = Column(String(250), ForeignKey('usuarios.correo_electronico'), nullable=False, unique=True)

    usuario = relationship('Usuarios')


# Módulo para la tabla de vendedores
class Vendedores(Base):
    __tablename__ = "vendedores"

    id_vendedor = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    RFC_vendedor = Column(String(13), nullable=True, unique=True)
    nombres_vendedor = Column(String(150), nullable=False)
    primer_apellido_vendedor = Column(String(150), nullable=False)
    segundo_apellido_vendedor = Column(String(150), nullable=True)
    numero_telefono = Column(String(10), nullable=False, unique=True)
    correo_electronico = Column(String(60), nullable=True, unique=True)
    estado = Column(String(60), nullable=False)
    municipio = Column(String(60), nullable=False)
    colonia = Column(String(60), nullable=False)
    calle = Column(String(60), nullable=False)
    numero_exterior = Column(String(60), nullable=True)
    codigo_postal = Column(String(60), nullable=False)
    estado_vendedor = Column(Boolean, nullable=False, default=1)
    lotes_vendidos = Column(Integer, nullable=False, default=0)

# Módulo para la tabla de clientes
class Clientes(Base):
    __tablename__ = "clientes"

    CURP_cliente = Column(String(18), nullable=False, primary_key=True, index=True, autoincrement=False)
    nombres_cliente = Column(String(150), nullable=False)
    primer_apellido_cliente = Column(String(150), nullable=False)
    segundo_apellido_cliente = Column(String(150), nullable=True)
    estado_civil = Column(String(60),nullable=False)
    ocupacion = Column(String(60), nullable=False)
    telefono_contacto = Column(String(10), nullable=False)
    calle = Column(String(150), nullable=False)
    numero_exterior = Column(String(5), nullable=True)
    colonia = Column(String(150), nullable=False)
    municipio = Column(String(150), nullable=False)
    codigo_postal = Column(String(6), nullable=False)
    estado = Column(String(60), nullable=False)
    entrega_curp = Column(Boolean, nullable=False, default=False)
    entrega_credencial_elector = Column(Boolean, nullable=False, default=False)
    entrega_comprobante_domicilio = Column(Boolean, nullable=False, default=False)

# Módulo para la tabla de estados de la república
class EstadosRepublica(Base):
    __tablename__ = "estados_republica"

    id_estado = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    nombre_estado = Column(String(50), nullable=False)

    municipio = relationship('Municipios', backref='estados_republica', cascade="all, delete-orphan", overlaps="estado,municipio")

# Módulo para la tabla de municipios
class Municipios(Base):
    __tablename__ = "municipios"

    id_municipio = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    nombre_municipio = Column(String(50), nullable=False)
    id_estado = Column(Integer, ForeignKey('estados_republica.id_estado'), nullable=False)

    estado = relationship('EstadosRepublica', overlaps="estados_republica,municipio")
    localidad = relationship("Localidades", backref="municipios", cascade="all, delete-orphan")

# Módulo para la tabla de localidades
class Localidades(Base):
    __tablename__ = "localidades"

    id_localidad = Column(Integer, nullable=True, primary_key=True, index=True, autoincrement=True)
    nombre_localidad = Column(String(50), nullable=False)
    id_municipio = Column(Integer, ForeignKey('municipios.id_municipio'), nullable=False)

    municipio = relationship('Municipios', overlaps="municipios,localidad")
    complejo = relationship("ComplejosResidenciales", backref="localidades", cascade="all, delete-orphan")

# Módulo para la tabla de complejos residenciales
class ComplejosResidenciales(Base):
    __tablename__ = "complejos_residenciales"

    id_complejo_residencial = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    nombre_complejo = Column(String(60), nullable=False)
    tipo_complejo = Column(String(60), nullable=False)
    id_localidad = Column(Integer, ForeignKey('localidades.id_localidad'), nullable=False)

    localidad = relationship('Localidades', overlaps="localidades,complejo")
    seccion = relationship("SeccionesComplejo", backref="complejos_residenciales", cascade="all, delete-orphan")

# Módulo para la tabla de secciones de un complejo
class SeccionesComplejo(Base):
    __tablename__ = "secciones_complejos"

    id_seccion = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    nombre_seccion = Column(String(60), nullable=False)
    color_seccion = Column(String(60), nullable=False)
    cantidad_lotes = Column(Integer, nullable=False)
    id_complejo_residencial = Column(Integer, ForeignKey('complejos_residenciales.id_complejo_residencial'), nullable=False)

    complejo_residencial = relationship('ComplejosResidenciales', overlaps="complejos_residenciales, seccion")
    lote = relationship('LotesSecciones', backref='secciones_complejos', cascade='all, delete-orphan')

# Módulo para la tabla de secciones de un lote
class LotesSecciones(Base):
    __tablename__ = "lotes_secciones"

    id_lote = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    numero_lote = Column(Integer, nullable=False)
    estado_terreno = Column(String(60), nullable=False)
    medida_total = Column(Float, nullable=False)
    medida_norte = Column(Float, nullable=False)
    medida_sur = Column(Float, nullable=False)
    medida_este = Column(Float, nullable=False)
    medida_oeste = Column(Float, nullable=False)
    otras_medidas = Column(String(160))
    servicio_agua = Column(Boolean, default=False, nullable=False)
    servicio_electricidad = Column(Boolean, default=False, nullable=False)
    servicio_drenaje = Column(Boolean, default=False, nullable=False)
    otros_servicios = Column(String(160))
    id_seccion = Column(Integer, ForeignKey('secciones_complejos.id_seccion'), nullable=False)

    seccion = relationship("SeccionesComplejo", overlaps="lote,secciones_complejos")

# Módulo para la tabla de compras
class Compras(Base):
    __tablename__ = "compras"

    id_compra = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    tipo_pago = Column(String(60), nullable=False)
    precio_total = Column(Float, nullable=False)
    cantidad_total_plazos = Column(Integer, nullable=False)
    estado_compra = Column(String(60), nullable=False, default='Proceso')
    fecha_compra = Column(Date, nullable=False)
    id_vendedor = Column(Integer, ForeignKey('vendedores.id_vendedor'),  nullable=False)
    CURP_cliente = Column(String(18), ForeignKey('clientes.CURP_cliente'), nullable=False)
    id_lote = Column(Integer, ForeignKey('lotes_secciones.id_lote'), nullable=False)

    vendedor = relationship('Vendedores')
    cliente = relationship('Clientes')
    lote = relationship('LotesSecciones')

# Módulo para la tabla de plazos de una compra
class PlazosCompras(Base):
    __tablename__ = "plazos_compra"

    id_plazo = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    numero_plazo = Column(Integer, nullable=False)
    cantidad_esperada = Column(Float, nullable=False)
    fecha_esperada = Column(Date, nullable=False)
    comprobante = Column(Boolean, nullable=False, default=False)
    restante = Column(Float, nullable=True)
    id_compra = Column(Integer, ForeignKey('compras.id_compra'), nullable=False)

    compra = relationship('Compras')
    detalles_pago = relationship('DetallesPago', backref="plazos_compra", cascade='all, delete-orphan')

# Módulo para la tabla de detalles de un pago
class DetallesPago(Base):
    __tablename__ = "detalles_pago"

    id_detalle_pago = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    fecha_entrega = Column(Date, nullable=False)
    cantidad_dada = Column(Float, nullable=False)
    total_compra = Column(Integer, nullable=False)
    id_plazo = Column(Integer, ForeignKey('plazos_compra.id_plazo'), nullable=False)

    plazo = relationship('PlazosCompras', overlaps="detalles_pago,plazos_compra")

# Módulo para la tabla de notificaciones
class Notificacines(Base):
    __tablename__ = "notificaciones"

    id_notificacion = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=True)
    titulo_notificacion = Column(String(60), nullable=False)
    descripcion = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    estado_leido = Column(Boolean, nullable=False, default=False)
    id_plazo = Column(Integer, ForeignKey('plazos_compra.id_plazo'), nullable=False)

    plazo = relationship('PlazosCompras')

class LotesUbicaciones(Base):
    __tablename__ = "vista_lotes_ubicaciones"
    __table_args__ = {'extend_existing': True}

    id_lote = Column(Integer, primary_key=True)
    nombre_complejo = Column(String)
    nombre_localidad = Column(String)
    nombre_municipio = Column(String)
    nombre_estado = Column(String)


class VistaLotes(Base):
    __tablename__ = 'vista_lotes'
    __table_args__ = {'extend_existing': True}

    id_lote = Column(Integer, primary_key=True)
    numero_lote = Column(Integer)
    estado_terreno = Column(String)
    medida_total = Column(Float)
    medida_norte = Column(Float)
    medida_sur = Column(Float)
    medida_este = Column(Float)
    medida_oeste = Column(Float)
    otras_medidas = Column(String)
    servicio_agua = Column(Boolean)
    servicio_electricidad = Column(Boolean)
    servicio_drenaje = Column(Boolean)
    otros_servicios = Column(String)
    id_seccion = Column(Integer)
    nombre_seccion = Column(String)
    nombre_complejo = Column(String)
    color_seccion = Column(String)

class VistaLotesSeccion(Base):
    __tablename__ = 'vista_lotes_con_seccion'
    __table_args__ = {'extend_existing': True}

    id_lote = Column(Integer, primary_key=True)
    numero_lote = Column(Integer)
    estado_terreno = Column(String)
    medida_total = Column(Float)
    medida_norte = Column(Float)
    medida_sur = Column(Float)
    medida_este = Column(Float)
    medida_oeste = Column(Float)
    otras_medidas = Column(String)
    servicio_agua = Column(Boolean)
    servicio_electricidad = Column(Boolean)
    servicio_drenaje = Column(Boolean)
    otros_servicios = Column(String)
    id_seccion = Column(Integer)
    nombre_seccion = Column(String)

class ComprasCliente(Base):
    __tablename__ = 'compras_cliente'
    __table_args__ = {'extend_existing': True}

    id_compra = Column(Integer, primary_key=True)
    estado_compra = Column(String)
    nombres_cliente = Column(String)
    primer_apellido_cliente = Column(String)
    segundo_apellido_cliente = Column(String)
    CURP_cliente = Column(String)
    fecha_compra = Column(Date)

class DatosVentaLote(Base):
    __tablename__ = 'datos_venta_lote'
    __table_args__ = {'extend_existing': True}

    id_compra = Column(Integer, primary_key=True)
    id_lote = Column(Integer)
    CURP_cliente = Column(String)
    nombres_cliente = Column(String)
    primer_apellido_cliente = Column(String)
    segundo_apellido_cliente = Column(String)
    id_vendedor = Column(Integer)
    nombres_vendedor = Column(String)
    primer_apellido_vendedor = Column(String)
    segundo_apellido_vendedor = Column(String)

class DatosPlazoCompra(Base):
    __tablename__ = 'datos_plazo_compra'
    __table_args__ = {'extend_existing': True}

    id_compra = Column(Integer)
    id_plazo = Column(Integer, primary_key=True)
    fecha_esperada = Column(Date)
    estado_compra = Column(String)
    CURP_cliente = Column(String)
    nombres_cliente = Column(String)
    primer_apellido_cliente = Column(String)
    segundo_apellido_cliente = Column(String)