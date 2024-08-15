"""
    Archivo que almacena los esquemas para las funciones
    de la API (modelo de respuesta, datos esperados)
"""

# Importar los módelos correspondientes
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Text, Tuple
from datetime import date

##############################################################
# Módelos para la clase de usuario (base, al crear, mostrar) #
##############################################################

class UsuarioBase(BaseModel):
    correo_electronico: EmailStr
    contraseña: str
    token: str
    estado_cuenta: bool
    palabra_secreta: str

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase):
    id_usuario: int

    class Config:
        from_attributes = True

class ConfiguracionBase(BaseModel):
    nombre_usuario: str
    nombre_empresa: str
    correo_empresa: str

class Configuracion(ConfiguracionBase):
    id_configuracion: int

    class Config:
        from_attributes = True

class RecuperarContrasena(BaseModel):
    correo_electronico: EmailStr
    frase: str

###############################################################
# Módelos para la clase de vendedor (base, al crear, mostrar) #
###############################################################

class VendedorBase(BaseModel):
    RFC_vendedor : Optional[str] = None
    nombres_vendedor: str
    primer_apellido_vendedor: str
    segundo_apellido_vendedor: Optional[str] = None
    numero_telefono: str
    correo_electronico: Optional[str] = None
    estado: str
    municipio: str
    colonia: str
    calle: str
    numero_exterior: Optional[str] = None
    codigo_postal: str

class VendedorCreate(VendedorBase):
    pass

class Vendedor(VendedorBase):
    id_vendedor: int
    lotes_vendidos: int
    estado_vendedor: bool

    class Config:
        from_attributes = True

class VendedorResponse(BaseModel):
    vendedores: List[Vendedor] = Field(..., alias='Vendedores')
    total_vendedores: int = Field(..., alias='Total de vendedores')

    class Config:
        populate_by_name = True

##############################################################
# Módelos para la clase de cliente (base, al crear, mostrar) #
##############################################################

class ClienteBase(BaseModel):
    CURP_cliente: str
    nombres_cliente: str
    primer_apellido_cliente: str
    segundo_apellido_cliente: Optional[str]
    estado_civil: str
    ocupacion: str
    telefono_contacto: str
    calle: str
    numero_exterior: Optional[str]
    colonia: str
    municipio: str
    codigo_postal: str
    estado: str
    entrega_curp: bool
    entrega_credencial_elector: bool
    entrega_comprobante_domicilio: bool

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    pass

    class Config:
        from_attributes = True

#############################################################
# Módelos para la clase de estado (base, al crear, mostrar) #
#############################################################

class EstadoBase(BaseModel):
    nombre_estado: str

class EstadoCreate(EstadoBase):
    pass

class Estado(EstadoBase):
    id_estado: int

    class Config:
        from_attributes = True

################################################################
# Módelos para la clase de municipio (base, al crear, mostrar) #
################################################################

class MunicipioBase(BaseModel):
    nombre_municipio: str
    id_estado: int

class MunicipioCreate(MunicipioBase):
    pass

class Municipio(MunicipioBase):
    id_municipio: int

    class Config:
        from_attributes = True

################################################################
# Módelos para la clase de localidad (base, al crear, mostrar) #
################################################################

class LocalidadBase(BaseModel):
    nombre_localidad: str
    id_municipio: int

class LocalidadCreate(LocalidadBase):
    pass

class Localidad(LocalidadBase):
    id_localidad: int

    class Config:
        from_attributes = True

###############################################################
# Módelos para la clase de complejo (base, al crear, mostrar) #
###############################################################

class ComplejoResidencialBase(BaseModel):
    nombre_complejo: str
    tipo_complejo: str
    id_localidad: int

class ComplejoResidencialCreate(ComplejoResidencialBase):
    pass

class ComplejoResidencial(ComplejoResidencialBase):
    id_complejo_residencial: int

    class Config:
        from_attributes = True

################################################################
# Módelos para la clase de secciones (base, al crear, mostrar) #
################################################################

class SeccionComplejoBase(BaseModel):
    nombre_seccion: str
    color_seccion: str
    cantidad_lotes: int
    id_complejo_residencial: int

class SeccionComplejoCreate(SeccionComplejoBase):
    pass

class SeccionComplejo(SeccionComplejoBase):
    id_seccion: int

    class Config:
        from_attributes = True

################################################################
# Módelos para la clase de secciones (base, al crear, mostrar) #
################################################################

class LoteSeccionExtendido(BaseModel):
    id_seccion: int
    id_lote: int
    nombre_seccion: str
    nombre_complejo: str
    numero_lote: int
    estado_terreno: str
    medida_total: float
    medida_norte: float
    medida_sur: float
    medida_este: float
    medida_oeste: float
    otras_medidas: Optional[str]
    servicio_agua: bool
    servicio_electricidad: bool
    servicio_drenaje: bool
    otros_servicios: Optional[str]

    class Config:
        from_attributes = True

class LoteSeccionBase(BaseModel):
    numero_lote: int
    estado_terreno: str
    medida_total: float
    medida_norte: float
    medida_sur: float
    medida_este: float
    medida_oeste: float
    otras_medidas: Optional[str]
    servicio_agua: bool
    servicio_electricidad: bool
    servicio_drenaje: bool
    otros_servicios: Optional[str]
    id_seccion: int

class LoteSeccionCreate(LoteSeccionBase):
    pass

class LoteSeccion(LoteSeccionBase):
    id_lote: int

    class Config:
        from_attributes = True

class LoteSeccionNombre(LoteSeccionBase):
    id_lote: int
    nombre_seccion: str

    class Config:
        from_attributes = True

class LotesSeccionColor(LoteSeccionBase):
    id_lote: int
    nombre_seccion: str
    color_seccion: str

    class Config:
        from_attributes = True


class LoteSeccionMostrar(BaseModel):
    lotes: List[LotesSeccionColor] = Field(..., alias='Lotes')
    total_lotes: int = Field(..., alias='Total de lotes')

    class Config:
        populate_by_name = True

class UbicacionLote(BaseModel):
    id_lote: int
    nombre_complejo: str
    nombre_localidad: str
    nombre_municipio: str
    nombre_estado: str

    class Config:
        from_attributes: True

class VentaLotes(BaseModel):

    id_compra: int
    id_lote: int
    id_vendedor: int
    nombres_vendedor: str
    primer_apellido_vendedor: str
    segundo_apellido_vendedor: str
    CURP_cliente: str
    nombres_cliente: str
    primer_apellido_cliente : str
    segundo_apellido_cliente: str


    class Config:
        from_attributes: True

##############################################################
# Módelos para la clase de compras (base, al crear, mostrar) #
##############################################################

class CompraExtendida(BaseModel):
    nombres_cliente: str
    primer_apellido_cliente: str
    segundo_apellido_cliente: str
    estado_compra: str
    CURP_cliente: str
    id_compra: int
    fecha_compra: date

    class Config:
        from_attributes = True

class CompraBase(BaseModel):
    tipo_pago: str
    precio_total: float
    cantidad_total_plazos: int
    estado_compra: str
    fecha_compra: date
    id_vendedor: int
    CURP_cliente: str
    id_lote: int

class CompraCreate(CompraBase):
    pass

class Compra(CompraBase):
    id_compra: int

    class Config:
        from_attributes = True

class VentasResponse(BaseModel):
    ventas: List[CompraExtendida] = Field(..., alias='Ventas')
    total_ventas: int = Field(..., alias='Total de ventas')

    class Config:
        populate_by_name = True

#############################################################
# Módelos para la clase de plazos (base, al crear, mostrar) #
#############################################################

class PlazoCompraBase(BaseModel):
    numero_plazo: int
    cantidad_esperada: float
    fecha_esperada: date
    comprobante: bool
    id_compra: int
    restante: float

class PlazoCompraCreate(PlazoCompraBase):
    pass

class PlazoCompra(PlazoCompraBase):
    id_plazo: int

    class Config:
        from_attributes = True

class PlazoCompraPaginado(BaseModel):
    plazos: List[PlazoCompra] = Field(..., alias="Plazos")
    total_plazos: int = Field(..., alias="Total de plazos")
    class Config:
        populate_by_name = True


class DatosPlazo(BaseModel):
    id_plazo: int
    id_compra: int
    fecha_esperada: date
    CURP_cliente: str
    nombres_cliente: str
    primer_apellido_cliente: str
    segundo_apellido_cliente: str

    class Config:
        from_attributes = True

###############################################################
# Módelos para la clase de detalles (base, al crear, mostrar) #
###############################################################

class DetallePagoBase(BaseModel):
    fecha_entrega: date
    cantidad_dada: float
    total_compra: float
    id_plazo: int

class DetallePagoCreate(DetallePagoBase):
    pass

class DetallePago(DetallePagoBase):
    id_detalle_pago: int

    class Config:
        from_attributes = True

class DetallePagoPaginado(BaseModel):
    detalles: List[DetallePago] = Field(..., alias="Detalles Pago")
    total_detalles: int = Field(..., alias="Total de detalles de pago")

    class Config:
        populate_by_name = True

###################################################################
# Módelos para la clase de notificacion (base, al crear, mostrar) #
###################################################################

class NotificacionBase(BaseModel):
    titulo_notificacion: str
    descripcion: str
    fecha: date
    estado_leido: bool
    id_plazo: int

class NotificacionCreate(NotificacionBase):
    pass

class Notificacion(NotificacionBase):
    id_notificacion: int

    class Config:
        from_attributes = True

class NotificacionesExtendido(BaseModel):
    notificaciones: List[Notificacion] = Field(..., alias='Notificaciones')
    total_notificaciones: int = Field(..., alias='Total de notificaciones')

    class Config:
        populate_by_name = True

#############################################