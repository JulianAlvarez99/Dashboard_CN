from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from db_manager import DataManager
from data_processor import DataProcessor

# Creamos un "Blueprint" (agrupador de rutas)
api_bp = Blueprint('api', __name__)

# Instanciamos el manager una sola vez al iniciar
db_manager = DataManager()

@api_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    try:
        # Parametros
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        interval = request.args.get('interval', '1h')
        lines_param = request.args.get('lines')
        product_id_param = request.args.get('product_id') # NUEVO FILTRO
        shift_param = request.args.get('shift') # NUEVO FILTRO
        
        # Fechas
        if end_str: end_date = datetime.fromisoformat(end_str)
        else: end_date = datetime.now()
        if start_str: start_date = datetime.fromisoformat(start_str)
        else: start_date = end_date - timedelta(hours=24)

        # Listas
        selected_lines = lines_param.split(',') if lines_param and lines_param != 'ALL' else None
        
        # 1. Obtener Raw Data
        df = db_manager.get_raw_production_data(start_date, end_date, selected_lines)
        
        # 2. Filtrado por Producto y Turno (NUEVO: Se hace en memoria/pandas)
        if not df.empty:
            # Filtro Producto
            if product_id_param and product_id_param != 'ALL':
                df = df[df['class_id'] == int(product_id_param)]
            
            # Filtro Turno (Nuevo)
            if shift_param and shift_param != 'all':
                df = DataProcessor.filter_by_shift(df, shift_param)

        # 3. Procesar
        downtime = DataProcessor.calculate_downtime(
            df, 
            threshold_seconds=300, 
            query_start=start_date, 
            query_end=end_date
        )
        # Pasamos 'downtime' a kpis para calcular totales
        kpis = DataProcessor.calculate_global_kpis(df, downtime)
        
        # Gráfico principal por PRODUCTO
        chart_prod = DataProcessor.get_product_chart_data(df, interval, start_date, end_date)
        
        # Gráfico comparativo (Barras)
        chart_comp = DataProcessor.get_entry_exit_comparison(df, interval, start_date, end_date)
        
        products_dist = DataProcessor.get_product_distribution(df)

        response = {
            'meta': { 'start': start_date.isoformat(), 'end': end_date.isoformat() },
            'kpis': kpis,
            'charts': {
                'main': chart_prod,
                'comparison': chart_comp
            },
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

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint simple para ver si el servidor responde"""
    return jsonify({'status': 'ok', 'env': db_manager.metadata_cache.get('classes', 'DB Error') and 'DB Connected'}), 200

@api_bp.route('/products_list', methods=['GET'])
def get_products_list():
    """Retorna lista única de productos para el filtro"""
    try:
        # Usamos el DataManager existente pero accedemos al cache o hacemos query
        # Como db_manager ya tiene metadata_cache['classes'], usémoslo.
        # Nota: db_manager está instanciado globalmente en routes.py como 'db_manager'
        
        classes = db_manager.metadata_cache.get('classes', {})
        product_list = []
        
        for class_id, data in classes.items():
            product_list.append({
                'id': class_id,
                'name': data['class_name'],
                'color': data['color']
            })
            
        # Ordenar alfabéticamente
        product_list.sort(key=lambda x: x['name'])
        
        return jsonify(product_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500