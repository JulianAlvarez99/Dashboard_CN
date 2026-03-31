import os
import sys
from flask import Flask, render_template
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user # Importamos lo necesario
from config import Config
from auth_manager import AuthManager

# Obtener ruta absoluta del directorio actual (Fix para cPanel/WSGI)
basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    # Inicializamos Flask indicando que busque templates y static en la RAÍZ ('.')
    app = Flask(__name__, 
                template_folder=basedir, 
                static_folder=basedir, 
                static_url_path='')
    
    # Habilitamos CORS
    CORS(app)
    
    # Cargar configuración
    app.config.from_object(Config)

    # --- CONFIGURACIÓN DE LOGIN ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor inicia sesión para acceder al dashboard."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return AuthManager.get_user_by_id(user_id)

    # --- REGISTRO DE BLUEPRINTS ---
    from auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from user_routes import users_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')

    # --- RUTA PRINCIPAL (PROTEGIDA) ---
    @app.route('/')
    @login_required  # <--- 1. Obliga a estar logueado
    def index():
        # <--- 2. Pasa la variable 'user' al HTML
        return render_template('dashboard_view.html', user=current_user)

    return app

# Instancia para WSGI (cPanel busca esta variable 'application')
try:
    app = create_app()
except Exception as e:
    print(f"Error iniciando la aplicación: {e}", file=sys.stderr)
    raise e

if __name__ == '__main__':
    # Si ejecutamos localmente:
    debug_mode = os.getenv('APP_ENV', 'local') == 'local'
    port = int(os.getenv('PORT', 5000))
    
    print(f"--- Servidor iniciando en puerto {port} (Modo: {os.getenv('APP_ENV')}) ---")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

application = app # Alias para WSGI