from flask import Flask, render_template
from flask_cors import CORS
from config import Config
import os

def create_app():
    # Inicializamos Flask
    app = Flask(__name__)
    
    # Habilitamos CORS (permite que una web en otro dominio/puerto consuma esta API)
    CORS(app)
    
    # Configuraciones básicas
    app.config.from_object(Config)

    # --- RUTA PRINCIPAL ---
    @app.route('/')
    def index():
        # Flask buscará 'index.html' dentro de la carpeta 'templates'
        return render_template('index.html')
    
    # Importamos y registramos las rutas
    from routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

# Instancia de la aplicación (necesaria para WSGI/Cpanel)
application = create_app()
app = application # Alias común

if __name__ == '__main__':
    # Si ejecutamos localmente:
    debug_mode = os.getenv('APP_ENV', 'local') == 'local'
    port = int(os.getenv('PORT', 5000))
    
    print(f"--- Servidor iniciando en puerto {port} (Modo: {os.getenv('APP_ENV')}) ---")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)