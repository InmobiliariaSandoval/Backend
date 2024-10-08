"""
    Archivo que define la configuración de la base de datos
"""

# Importar los módulos correspondientes
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Definir URL de la base de datos
SQLALCHEMY_DATABASE_URL = "sqlite:///./inmobiliaria.db"

# Crear el motor de conexión a la base de datos utilizando la URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Crear la sesión de conexión a la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarar la base de datos para ORM
Base = declarative_base()
