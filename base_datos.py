"""
    Archivo que define la configuración de la base de datos
"""

# Importar los módulos correspondientes
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Credenciales
TURSO_DATABASE_URL = os.getenv('TURSO_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH')

# Definir URL de la base de datos
dbUrl = f"sqlite+{TURSO_DATABASE_URL}/?authToken={TURSO_AUTH_TOKEN}&secure=true"

# Crear el motor de conexión a la base de datos utilizando la URL
engine = create_engine(
    dbUrl, connect_args={"check_same_thread": False}
)

# Crear la sesión de conexión a la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarar la base de datos para ORM
Base = declarative_base()
