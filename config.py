import os
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine
import urllib.parse

# --- FIX PARA CPANEL: Cargar .env con ruta absoluta ---
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Detectamos el entorno
    ENV = os.getenv('APP_ENV', 'local')

    # Seguridad Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'clave_secreta_por_defecto_segura')
    
    # Configuración de Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # En producción con HTTPS en cPanel, esto debería ser True
    SESSION_COOKIE_SECURE = ENV == 'production' 
    
    # Sesión efímera (se borra al cerrar navegador)
    SESSION_PERMANENT = False 
    PERMANENT_SESSION_LIFETIME = 1800
    
    # Datos de BD
    DB_HOST = os.getenv('MYSQL_HOST')
    DB_USER = os.getenv('MYSQL_USER')
    DB_PASS = os.getenv('MYSQL_PASSWORD')
    DB_NAME = os.getenv('MYSQL_DB')
    
    # Codificar contraseña para SQLAlchemy
    encoded_password = urllib.parse.quote_plus(DB_PASS) if DB_PASS else ""

    # Cadena de conexión segura
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}"

    # Configuración de Líneas
    LINES_CONFIG = {
        'linea_1': {'table': 'linea_1', 'entry_area': 12, 'exit_area': 11, 'label': 'Línea 1'},
        'linea_2': {'table': 'linea_2', 'entry_area': 23, 'exit_area': 24, 'label': 'Línea 2'},
        'linea_3': {'table': 'linea_3_semolin', 'entry_area': 1, 'exit_area': 2, 'label': 'Línea 3 Semolín'} 
    }

    # Base de Datos de Autenticación
    AUTH_DB_CONFIG = {
        'host': os.getenv('AUTH_MYSQL_HOST'),
        'port': int(os.getenv('AUTH_MYSQL_PORT', 3306)),
        'user': os.getenv('AUTH_MYSQL_USER'),
        'password': os.getenv('AUTH_MYSQL_PASSWORD'),
        'database': os.getenv('AUTH_MYSQL_DB')
    }

    # Configuración de Turnos
    SHIFTS = {
        'morning':   {'start': 5,  'end': 14, 'label': 'Mañana (06-14)'},
        'afternoon': {'start': 14, 'end': 22, 'label': 'Tarde (14-22)'},
        'night':     {'start': 22, 'end': 6,  'label': 'Noche (22-06)'}
    }

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
        return create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_recycle=280)
    except Exception as e:
        print(f"Error creando engine: {e}")
        return None