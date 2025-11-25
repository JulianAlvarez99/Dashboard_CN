import os
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine

# Carga variables del archivo .env si existe
load_dotenv()

class Config:
    # Detectamos el entorno basado en una variable, si no existe asumimos LOCAL
    ENV = os.getenv('APP_ENV', 'local') 
    
    DB_HOST = os.getenv('MYSQL_HOST')
    DB_USER = os.getenv('MYSQL_USER')
    DB_PASS = os.getenv('MYSQL_PASSWORD')
    DB_NAME = os.getenv('MYSQL_DB')
    
    # Cadena de conexión para SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

    # Configuración específica de las líneas (Mapeo de Lógica de Negocio)
    # Aquí definimos qué area es entrada y cuál salida por defecto para cada línea
    LINES_CONFIG = {
        'linea_1': {'table': 'linea_1', 'entry_area': 12, 'exit_area': 11, 'label': 'Línea 1'},
        'linea_2': {'table': 'linea_2', 'entry_area': 23, 'exit_area': 24, 'label': 'Línea 2'},
        'linea_3': {'table': 'linea_3_semolin', 'entry_area': 1, 'exit_area': 2, 'label': 'Línea 3 Semolín'} # Asumimos config por defecto
    }

# Mantenemos la conexión raw solo para las metadatas pequeñas si queremos, 
# pero para Pandas usaremos el engine.
def get_db_connection():
    try:
        return pymysql.connect(
            host=Config.DB_HOST, user=Config.DB_USER, password=Config.DB_PASS,
            database=Config.DB_NAME, cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Error raw connection: {e}")
        return None
    
def get_db_engine():
    try:
        # pool_recycle evita que la conexión se cierre por inactividad en Cpanel
        return create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_recycle=280)
    except Exception as e:
        print(f"Error creando engine: {e}")
        return None