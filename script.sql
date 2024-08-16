/*
    Script de administración de la base de
    datos de la Inmobiliaria
*/

-- Tabla de usuarios --
DROP TABLE IF EXISTS usuarios;

CREATE TABLE IF NOT EXISTS usuarios(
    id_usuario INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    correo_electronico VARCHAR(60) NOT NULL UNIQUE,
    contraseña VARCHAR(256) NOT NULL,
    token VARCHAR(60) NOT NULL,
    estado_cuenta BOOLEAN NOT NULL DEFAULT FALSE,
    palabra_secreta VARCHAR(60) NOT NULL UNIQUE
);

INSERT INTO usuarios(correo_electronico, contraseña, token, palabra_secreta, estado_cuenta) VALUES
('inmobiliariagruposandoval06@gmail.com', '90d2393d7875b18f4bd2199d233355c6', 'ffff','c08ffd2968a5f0c885d054935e45685d', FALSE),
('sandovalinmobiliaria30@gmail.com', '90d2393d7875b18f4bd2199d233355c6', 'ffff','50c44f3a8d7006fafd977107edb18742', FALSE),
('sandovalinmobiliariagrupo@gmail.com', '90d2393d7875b18f4bd2199d233355c6', 'ffff','befea81bbd4d596fa35050599ddbf6c2', FALSE);

DROP TABLE IF EXISTS configuracion;

CREATE TABLE IF NOT EXISTS configuracion(
    id_configuracion INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nombre_usuario VARCHAR(250) NOT NULL UNIQUE,
    nombre_empresa VARCHAR(250) NOT NULL,
    correo_empresa VARCHAR(250) NOT NULL UNIQUE,
    FOREIGN KEY (correo_empresa) REFERENCES usuarios(correo_electronico)
);

INSERT INTO configuracion(nombre_usuario, nombre_empresa, correo_empresa) VALUES
('Primer usuario', 'Inmobiliaria Grupo Sandoval', 'inmobiliariagruposandoval06@gmail.com'),
('Segundo usuario', 'Inmobiliaria Grupo Sandoval', 'sandovalinmobiliaria30@gmail.com'),
('Tercer usuario', 'Inmobiliaria Grupo Sandoval', 'sandovalinmobiliariagrupo@gmail.com');

-- Tabla de vendedores --
DROP TABLE IF EXISTS vendedores;

CREATE TABLE IF NOT EXISTS vendedores(
    id_vendedor INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    RFC_vendedor VARCHAR(13) UNIQUE,
    nombres_vendedor VARCHAR(150) NOT NULL,
    primer_apellido_vendedor VARCHAR(150) NOT NULL,
    segundo_apellido_vendedor VARCHAR(150),
    numero_telefono VARCHAR(10) NOT NULL UNIQUE,
    correo_electronico VARCHAR(60) UNIQUE,
    estado VARCHAR(60) NOT NULL,
    municipio VARCHAR(60) NOT NULL,
    colonia VARCHAR(60) NOT NULL,
    calle VARCHAR(60) NOT NULL,
    numero_exterior VARCHAR(5),
    codigo_postal VARCHAR(5) NOT NULL,
    estado_vendedor INTEGER NOT NULL DEFAULT 1,
    lotes_vendidos INTEGER NOT NULL DEFAULT 0
);

-- INSERT INTO vendedores (RFC_vendedor, nombres_vendedor, primer_apellido_vendedor, segundo_apellido_vendedor, numero_telefono, correo_electronico, estado, municipio, colonia, calle, numero_exterior, codigo_postal, estado_vendedor, lotes_vendidos)
-- VALUES
-- ('VND1234567890', 'Juan', 'Pérez', 'García', '5551234567', 'juan.perez@example.com', 'Ciudad de México', 'Benito Juárez', 'Nápoles', 'Dakota', '123', '03810', 1, 0),
-- ('VND2345678901', 'María', 'López', 'Hernández', '5552345678', 'maria.lopez@example.com', 'Jalisco', 'Guadalajara', 'Centro', 'Juárez', '456', '44100', 1, 0);

-- Tabla de clientes --
DROP TABLE IF EXISTS clientes;

CREATE TABLE IF NOT EXISTS clientes(
    CURP_cliente VARCHAR(18) NOT NULL PRIMARY KEY,
    nombres_cliente VARCHAR(150) NOT NULL,
    primer_apellido_cliente VARCHAR(150) NOT NULL,
    segundo_apellido_cliente VARCHAR(150),
    estado_civil VARCHAR(60) NOT NULL,
    ocupacion VARCHAR(60) NOT NULL,
    telefono_contacto VARCHAR(10) NOT NULL,
    calle VARCHAR(150) NOT NULL,
    numero_exterior VARCHAR(5),
    colonia VARCHAR(150) NOT NULL,
    municipio VARCHAR(150) NOT NULL,
    codigo_postal VARCHAR(6) NOT NULL,
    estado VARCHAR(60) NOT NULL,
    entrega_curp BOOLEAN NOT NULL DEFAULT FALSE,
    entrega_credencial_elector BOOLEAN NOT NULL DEFAULT FALSE,
    entrega_comprobante_domicilio BOOLEAN NOT NULL DEFAULT FALSE
);

-- INSERT INTO clientes(CURP_cliente, nombres_cliente, primer_apellido_cliente, segundo_apellido_cliente, estado_civil, ocupacion,
-- telefono_contacto, calle, numero_exterior, colonia, municipio, codigo_postal, estado, entrega_curp,
-- entrega_credencial_elector, entrega_comprobante_domicilio) VALUES
-- ('VARP040924HHGRMTA0', 'Patricio', 'Vargas', 'Ramírez', 'Soltero', 'Estudiante', '7752060936', 'La Araucaria', '123', 'Rinconadas del Bosque Napateco',
-- 'Tulancingo de Bravo', '43629', 'Hidalgo', TRUE, TRUE, TRUE),
-- ('SAMJ010331MHGNLNA7', 'Juan', 'Vargas', 'Ramírez', 'Soltero', 'Estudiante', '7752061936', 'La Araucaria', '123', 'Rinconadas del Bosque Napateco',
-- 'Tulancingo de Bravo', '43629', 'Hidalgo', TRUE, TRUE, TRUE),
-- ('SAPO041024HHGRMTA0', 'Fabricia', 'Vargas', 'Ramírez', 'Soltero', 'Maestra', '7752061036', 'La Araucaria', '123', 'Rinconadas del Bosque Napateco',
-- 'Tulancingo de Bravo', '43629', 'Hidalgo', TRUE, TRUE, TRUE);

-- Tabla de estados --
DROP TABLE IF EXISTS estados_republica;

CREATE TABLE IF NOT EXISTS estados_republica(
    id_estado INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nombre_estado VARCHAR(50) NOT NULL
);

INSERT INTO estados_republica(nombre_estado) VALUES ('Hidalgo');

-- Tabla de municipios --
DROP TABLE IF EXISTS municipios;

CREATE TABLE IF NOT EXISTS municipios(
    id_municipio INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nombre_municipio VARCHAR(50) NOT NULL,
    id_estado INTEGER NOT NULL,
    FOREIGN KEY (id_estado) REFERENCES estados_republica(id_estado) ON DELETE CASCADE
);

-- INSERT INTO municipios(nombre_municipio, id_estado) VALUES ('Tulancingo de Bravo', 1);

-- Tabla de localidades --
DROP TABLE IF EXISTS localidades;

CREATE TABLE IF NOT EXISTS localidades(
    id_localidad INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nombre_localidad VARCHAR(50) NOT NULL,
    id_municipio INTEGER NOT NULL,
    FOREIGN KEY (id_municipio) REFERENCES municipios(id_municipio) ON DELETE CASCADE
);

-- INSERT INTO localidades(nombre_localidad, id_municipio) VALUES ('Parque Urbano Napateco', 1);

-- Tabla de complejos residenciales --
DROP TABLE IF EXISTS complejos_residenciales;

CREATE TABLE IF NOT EXISTS complejos_residenciales(
    id_complejo_residencial INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nombre_complejo VARCHAR(60) NOT NULL,
    tipo_complejo VARCHAR(60) NOT NULL,
    id_localidad INTEGER NOT NULL,
    FOREIGN KEY (id_localidad) REFERENCES localidades(id_localidad) ON DELETE CASCADE
);

-- INSERT INTO complejos_residenciales(nombre_complejo, tipo_complejo, id_localidad) VALUES ('Fraccionamiento la Loma', 'Fraccionamiento', 1);

-- Tabla de secciones de complejos --
DROP TABLE IF EXISTS secciones_complejos;

CREATE TABLE IF NOT EXISTS secciones_complejos(
    id_seccion INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nombre_seccion VARCHAR(60) NOT NULL,
    color_seccion VARCHAR(60) NOT NULL,
    cantidad_lotes INTEGER NOT NULL,
    id_complejo_residencial INTEGER NOT NULL,
    FOREIGN KEY (id_complejo_residencial) REFERENCES complejos_residenciales(id_complejo_residencial) ON DELETE CASCADE
);

-- INSERT INTO secciones_complejos(nombre_seccion, color_seccion, cantidad_lotes, id_complejo_residencial) VALUES ('Sección 1', '#4a9898', 5, 1);

-- Tabla de lotes secciones --
DROP TABLE IF EXISTS lotes_secciones;

CREATE TABLE IF NOT EXISTS lotes_secciones(
    id_lote INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    numero_lote INTEGER NOT NULL,
    estado_terreno VARCHAR(60) NOT NULL,
    medida_total FLOAT NOT NULL,
    medida_norte FLOAT NOT NULL,
    medida_sur FLOAT NOT NULL,
    medida_este FLOAT NOT NULL,
    medida_oeste FLOAT NOT NULL,
    otras_medidas VARCHAR(160),
    servicio_agua BOOLEAN NOT NULL DEFAULT FALSE,
    servicio_electricidad BOOLEAN NOT NULL DEFAULT FALSE,
    servicio_drenaje BOOLEAN NOT NULL DEFAULT FALSE,
    otros_servicios VARCHAR(160),
    id_seccion INTEGER NOT NULL,
    FOREIGN KEY (id_seccion) REFERENCES secciones_complejos(id_seccion) ON DELETE CASCADE
);

-- INSERT INTO lotes_secciones(numero_lote, estado_terreno, medida_total, medida_norte, medida_sur, medida_este,
-- medida_oeste, servicio_agua, servicio_electricidad, servicio_drenaje, id_seccion) VALUES
-- (1, 'Disponible', 450, 112.5, 112.5, 112.5, 112.5, TRUE, TRUE, TRUE, 1),
-- (2, 'Disponible', 500, 125, 125, 125, 125, TRUE, TRUE, TRUE, 1),
-- (3, 'Disponible', 550, 137.5, 137.5, 137.5, 137.5, TRUE, TRUE, TRUE, 1),
-- (4, 'Disponible', 600, 150, 150, 150, 150, TRUE, TRUE, TRUE, 1),
-- (5, 'Disponible', 650, 162.5, 162.5, 162.5, 162.5, TRUE, TRUE, TRUE, 1);

-- Tabla de compras --
DROP TABLE IF EXISTS compras;

CREATE TABLE IF NOT EXISTS compras(
    id_compra INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    tipo_pago VARCHAR(60) NOT NULL,
    precio_total FLOAT NOT NULL,
    cantidad_total_plazos INTEGER NOT NULL,
    estado_compra VARCHAR(10) NOT NULL DEFAULT 'Proceso',
    fecha_compra DATE NOT NULL DEFAULT CURRENT_DATE,
    id_vendedor INTEGER NOT NULL,
    CURP_cliente VARCHAR(18) NOT NULL,
    id_lote INTEGER NOT NULL,
    FOREIGN KEY (id_vendedor) REFERENCES vendedores(id_vendedor),
    FOREIGN KEY (CURP_cliente) REFERENCES clientes(CURP_cliente),
    FOREIGN KEY (id_lote) REFERENCES lotes_secciones(id_lote)
);

-- Tabla de plazos compra --
DROP TABLE IF EXISTS plazos_compra;

CREATE TABLE IF NOT EXISTS plazos_compra(
    id_plazo INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    numero_plazo INTEGER NOT NULL,
    cantidad_esperada FLOAT NOT NULL,
    fecha_esperada DATE NOT NULL,
    comprobante BOOLEAN DEFAULT FALSE,
    restante FLOAT,
    id_compra INTEGER NOT NULL,
    FOREIGN KEY (id_compra) REFERENCES compras(id_compra)
);

-- Tabla de detalles de pago --
DROP TABLE IF EXISTS detalles_pago;

CREATE TABLE IF NOT EXISTS detalles_pago(
    id_detalle_pago INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    fecha_entrega DATE NOT NULL,
    cantidad_dada FLOAT NOT NULL,
    total_compra FLOAT NOT NULL,
    id_plazo INTEGER NOT NULL,
    FOREIGN KEY (id_plazo) REFERENCES plazos_compra(id_plazo) ON DELETE CASCADE
);

-- Tabla de notificaciones --
DROP TABLE IF EXISTS notificaciones;

CREATE TABLE IF NOT EXISTS notificaciones(
    id_notificacion INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    titulo_notificacion VARCHAR(60) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    estado_leido BOOLEAN NOT NULL DEFAULT FALSE,
    id_plazo INTEGER NOT NULL,
    FOREIGN KEY (id_plazo) REFERENCES plazos_compra(id_plazo)
);

-- INSERT INTO notificaciones(titulo_notificacion, descripcion, fecha, estado_leido, id_compra) VALUES
-- ('Fecha de pago atrasada', 'La fecha de pagó del comprador Patricio se atrasó','2023-06-01', FAlSE, 1),
-- ('Compra procesada', 'Tu compra ha sido procesada exitosamente.', '2023-06-01', FALSE, 1),
-- ('Compra enviada', 'Tu compra ha sido enviada y está en camino.', '2023-06-02', FALSE, 1),
-- ('Compra entregada', 'Tu compra ha sido entregada. ¡Gracias por comprar con nosotros!', '2023-06-03', FALSE, 1),
-- ('Nueva oferta disponible', 'Tenemos una nueva oferta especial para ti. ¡No te la pierdas!', '2023-06-04', FALSE, 1);

-- Vista para consultar la ubicación de un lote
DROP VIEW IF EXISTS vista_lotes_ubicaciones;

CREATE VIEW IF NOT EXISTS vista_lotes_ubicaciones AS
SELECT lotes_secciones.id_lote, complejos_residenciales.nombre_complejo, localidades.nombre_localidad, municipios.nombre_municipio, estados_republica.nombre_estado
FROM lotes_secciones
INNER JOIN secciones_complejos
ON lotes_secciones.id_seccion = secciones_complejos.id_seccion
INNER JOIN complejos_residenciales
ON secciones_complejos.id_complejo_residencial = complejos_residenciales.id_complejo_residencial
INNER JOIN localidades
ON complejos_residenciales.id_localidad = localidades.id_localidad
INNER JOIN municipios
ON localidades.id_municipio = municipios.id_municipio
INNER JOIN estados_republica
ON municipios.id_estado = estados_republica.id_estado;

-- Vista para consultar la información de un lote
DROP VIEW IF EXISTS vista_lotes;

CREATE VIEW IF NOT EXISTS vista_lotes AS
SELECT lotes_secciones.*, secciones_complejos.nombre_seccion, complejos_residenciales.nombre_complejo,
secciones_complejos.color_seccion
FROM lotes_secciones
INNER JOIN secciones_complejos
ON lotes_secciones.id_seccion = secciones_complejos.id_seccion
INNER JOIN complejos_residenciales
ON secciones_complejos.id_complejo_residencial = complejos_residenciales.id_complejo_residencial;

-- Vista para obtener un lote con nombre de sección
DROP VIEW IF EXISTS vista_lotes_con_seccion;

CREATE VIEW IF NOT EXISTS vista_lotes_con_seccion AS
SELECT lotes.*, secciones.nombre_seccion
FROM lotes_secciones lotes
INNER JOIN secciones_complejos secciones
ON lotes.id_seccion = secciones.id_seccion;

-- Vsita para obtener las compras
DROP VIEW IF EXISTS compras_cliente;

CREATE VIEW IF NOT EXISTS compras_cliente AS
SELECT compras.id_compra, compras.estado_compra, compras.fecha_compra, clientes.nombres_cliente,
clientes.primer_apellido_cliente, clientes.segundo_apellido_cliente,
compras.CURP_cliente
FROM compras
INNER JOIN clientes
ON compras.CURP_cliente = clientes.CURP_cliente;

-- Vista para obtener el nombre e identificador de un cliente y vendedor
-- en base a buscar una compra por id
DROP VIEW IF EXISTS datos_venta_lote;

CREATE VIEW IF NOT EXISTS datos_venta_lote AS
SELECT compras.id_compra, compras.id_lote, vendedores.id_vendedor, vendedores.nombres_vendedor,
vendedores.primer_apellido_vendedor, vendedores.segundo_apellido_vendedor,
clientes.nombres_cliente, clientes.primer_apellido_cliente, clientes.segundo_apellido_cliente,
compras.CURP_cliente
FROM compras
INNER JOIN clientes
ON compras.CURP_cliente = clientes.CURP_cliente
INNER JOIN vendedores
ON compras.id_vendedor = vendedores.id_vendedor;

DROP VIEW IF EXISTS datos_plazo_compra;

CREATE VIEW IF NOT EXISTS datos_plazo_compra AS
SELECT compras.id_compra, compras.estado_compra, plazos_compra.id_plazo, plazos_compra.fecha_esperada, compras.CURP_cliente, clientes.nombres_cliente,
clientes.primer_apellido_cliente, clientes.segundo_apellido_cliente
FROM plazos_compra
INNER JOIN compras
ON plazos_compra.id_compra = compras.id_compra
INNER JOIN clientes
ON compras.CURP_cliente = clientes.CURP_cliente;