from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from flask_login import login_required, current_user 
import security_logger
from settings_manager import SettingsManager
from config import Config # Importar Config 

api_bp = Blueprint('api', __name__)
# 1. ELIMINAR O COMENTAR ESTA LÍNEA GLOBAL:
# db_manager = DataManager()  <-- ESTO ES LO QUE PONE LENTO EL INICIO


# 2. Reemplazar por una variable global inicializada en None
_db_manager_instance = None

def get_db_manager():
    """Patrón Singleton Lazy: Solo conecta a la BD cuando realmente se pide un dato."""
    global _db_manager_instance
    if _db_manager_instance is None:
        print("⚡ Inicializando DataManager por primera vez...")
        from db_manager import DataManager
        _db_manager_instance = DataManager()
    return _db_manager_instance

def _adjust_visualization_range_by_shift(start_dt, end_dt, shift_key):
    # Si el rango es mayor a 25 horas, no ajustamos visualmente
    if (end_dt - start_dt).total_seconds() > 90000: return start_dt, end_dt
    
    if shift_key not in Config.SHIFTS:
        return start_dt, end_dt

    shift_cfg = Config.SHIFTS[shift_key]
    base_date = start_dt.date()
    
    # Ajustamos start
    viz_start = datetime.combine(base_date, shift_cfg['start'])
    
    # Ajustamos end
    if shift_cfg['start'] < shift_cfg['end']:
        # Turno mismo día
        viz_end = datetime.combine(base_date, shift_cfg['end'])
    else:
        # Turno cruza medianoche
        viz_end = datetime.combine(base_date + timedelta(days=1), shift_cfg['end'])

    return viz_start, viz_end

# --- NUEVAS RUTAS DE CONFIGURACIÓN DE VISIBILIDAD ---

@api_bp.route('/ui_settings', methods=['GET'])
@login_required
def get_ui_settings():
    """
    Cualquier usuario logueado puede LEER la configuración
    para saber qué gráficos debe mostrar el frontend.
    """
    settings = SettingsManager.get_settings()
    return jsonify(settings), 200

@api_bp.route('/ui_settings', methods=['POST'])
@login_required
def update_ui_settings():
    """
    Solo el ADMINISTRADOR puede GUARDAR cambios en la configuración global.
    """
    if current_user.privilege != 'administrador':
        return jsonify({'error': 'No autorizado. Se requieren permisos de administrador.'}), 403
    
    try:
        new_settings = request.json
        if SettingsManager.save_settings(new_settings):
            return jsonify({'message': 'Configuración actualizada correctamente'}), 200
        else:
            return jsonify({'error': 'Error al escribir en el servidor'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------

@api_bp.route('/dashboard', methods=['GET'])
@login_required 
def get_dashboard_data():
    try:
        from data_processor import DataProcessor
        # 1. Recepción de Parámetros
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        interval = request.args.get('interval', '1h')
        lines_param = request.args.get('lines')
        product_id_param = request.args.get('product_id')
        shift_param = request.args.get('shift')
        
        try:
            threshold_seconds = int(request.args.get('threshold', 60))
        except ValueError:
            threshold_seconds = 60

        # 2. Parseo de Fechas
        if end_str: end_date = datetime.fromisoformat(end_str)
        else: end_date = datetime.now()
        if start_str: start_date = datetime.fromisoformat(start_str)
        else: start_date = end_date - timedelta(hours=24)

        # --- AUDITORÍA DE SEGURIDAD ---
        security_logger.log_query(
            username=current_user.username,
            query_params=request.args.to_dict(),
            start_date=start_date,
            end_date=end_date,
            linea=lines_param if lines_param else "ALL",
            interval_type=interval,
            ip_address=security_logger.get_user_ip(request)
        )

        # 3. Obtención de Datos
        selected_lines = lines_param.split(',') if lines_param and lines_param != 'ALL' else None
        manager = get_db_manager() 
        df = manager.get_raw_production_data(start_date, end_date, selected_lines)
        
        # 4. Filtrado
        if not df.empty:
            if product_id_param and product_id_param != 'ALL':
                df = df[df['class_id'] == int(product_id_param)]
            if shift_param and shift_param != 'all':
                df = DataProcessor.filter_by_shift(df, shift_param)

        # 5. Ajuste Visualización
        viz_start, viz_end = start_date, end_date
        if shift_param and shift_param != 'all':
            viz_start, viz_end = _adjust_visualization_range_by_shift(start_date, end_date, shift_param)

        # 6. Procesamiento
        downtime = DataProcessor.calculate_downtime(df, threshold_seconds, viz_start, viz_end)
        kpis = DataProcessor.calculate_global_kpis(df, downtime)
        
        chart_prod = DataProcessor.get_product_chart_data(df, interval, viz_start, viz_end)
        chart_comp = DataProcessor.get_entry_exit_comparison(df, interval, viz_start, viz_end)
        products_dist = DataProcessor.get_product_distribution(df)

        response = {
            'meta': { 'start': viz_start.isoformat(), 'end': viz_end.isoformat() },
            'kpis': kpis,
            'charts': { 'main': chart_prod, 'comparison': chart_comp },
            'downtime': {
                'events': downtime,
                'count': kpis['downtime_count'],
                'total_str': kpis['downtime_total_str']
            },
            'products': products_dist
        }
        return jsonify(response), 200

    except Exception as e:
        print(f"ERROR API: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products_list', methods=['GET'])
@login_required
def get_products_list():
    try:
        manager = get_db_manager() 
        classes = manager.metadata_cache.get('classes', {})
        product_list = []
        for class_id, data in classes.items():
            product_list.append({'id': class_id, 'name': data['class_name'], 'color': data['color']})
        product_list.sort(key=lambda x: x['name'])
        return jsonify(product_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500