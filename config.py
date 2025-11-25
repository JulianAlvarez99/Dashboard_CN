import os
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine

# Carga variables de entorno
load_dotenv()

class Config:
    """Clase de configuración global de la aplicación."""
    
    ENV = os.getenv('APP_ENV', 'local') 
    
    # Credenciales BD
    DB_HOST = os.getenv('MYSQL_HOST')
    DB_USER = os.getenv('MYSQL_USER')
    DB_PASS = os.getenv('MYSQL_PASSWORD')
    DB_NAME = os.getenv('MYSQL_DB')
    
    # URI para SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

    # Configuración de Negocio: Definición de Líneas y Áreas
    # entry_area: ID del área que cuenta como "Producción Bruta"
    # exit_area: ID del área que cuenta como "Salida/Paletizado"
    LINES_CONFIG = {
        'linea_1': {'table': 'linea_1', 'entry_area': 12, 'exit_area': 11, 'label': 'Línea 1'},
        'linea_2': {'table': 'linea_2', 'entry_area': 23, 'exit_area': 24, 'label': 'Línea 2'},
        'linea_3': {'table': 'linea_3_semolin', 'entry_area': 1, 'exit_area': 2, 'label': 'Línea 3 Semolín'}
    }

def get_db_connection():
    """Obtiene una conexión 'raw' (pymysql) para consultas simples."""
    try:
        return pymysql.connect(
            host=Config.DB_HOST, user=Config.DB_USER, password=Config.DB_PASS,
            database=Config.DB_NAME, cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Error raw connection: {e}")
        return None
    
def get_db_engine():
    """Obtiene un Engine de SQLAlchemy para uso con Pandas."""
    try:
        # pool_recycle evita desconexiones por timeout en servidores MySQL
        return create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_recycle=280)
    except Exception as e:
        print(f"Error creando engine: {e}")
        return None