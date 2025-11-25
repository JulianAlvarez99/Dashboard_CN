import pandas as pd
import numpy as np

class DataProcessor:

    @staticmethod
    def calculate_global_kpis(df, downtime_events):
        if df.empty:
            return {
                'total_output': 0,
                'downtime_count': 0,
                'downtime_total_str': "00:00:00",
                'total_weight_kg': 0
            }
            
        # Total Salida (Exit Area)
        # Verificamos que exista la columna antes de filtrar
        if 'is_exit' in df.columns:
            total_output = df[df['is_exit']].shape[0]
        else:
            total_output = 0
        
        # Calcular Peso Total
        total_weight = 0
        if 'class_weight' in df.columns and 'is_exit' in df.columns:
             # Multiplicar cantidad x peso unitario
             # Filtramos solo entradas válidas
             production_df = df[df['is_exit']]
             total_weight = production_df['class_weight'].sum()

        # Métricas de Paradas
        downtime_count = len(downtime_events)
        total_seconds = sum(d['duration_seconds'] for d in downtime_events)
        
        m, s = divmod(total_seconds, 60)
        h, m = divmod(m, 60)
        downtime_str = "{:02d}:{:02d}:{:02d}".format(int(h), int(m), int(s))
        
        return {
            'total_output': int(total_output),
            'downtime_count': downtime_count,
            'downtime_total_str': downtime_str,
            'total_weight_kg': f"{total_weight:,.2f}" # Formato string
        }
    
    @staticmethod
    def get_product_chart_data(df, interval='1h', query_start=None, query_end=None):
        empty_response = {'labels': [], 'datasets': []}
        if df.empty and not query_start: return empty_response

        # Preparamos df_prod de forma segura
        df_prod = pd.DataFrame()

        # SOLO intentamos filtrar si el DataFrame tiene datos y columnas
        if not df.empty and 'is_exit' in df.columns:
            df_prod = df[df['is_exit']].copy()
            
            if not df_prod.empty:
                df_prod.set_index('timestamp', inplace=True)
                
                # Lógica de nombres de línea (si existe la columna)
                if 'line_key' in df_prod.columns and df_prod['line_key'].nunique() > 1:
                    line_map = {'linea_1': 'L1', 'linea_2': 'L2', 'linea_3_semolin': 'L3'}
                    df_prod['product_display'] = df_prod['product_name'] + " (" + df_prod['line_key'].map(line_map).fillna(df_prod['line_key']) + ")"
                else:
                    df_prod['product_display'] = df_prod['product_name']

        # Normalización de fechas (Igual que antes)
        try:
            # Intentamos normalizar al intervalo (floor/ceil)
            if query_start:
                start_norm = pd.Timestamp(query_start).floor(interval) if interval not in ['1M', '1ME'] else pd.Timestamp(query_start)
            else:
                start_norm = pd.Timestamp.now().floor(interval)

            if query_end:
                end_norm = pd.Timestamp(query_end).ceil(interval) if interval not in ['1M', '1ME'] else pd.Timestamp(query_end)
            else:
                end_norm = pd.Timestamp.now().ceil(interval)
                
        except Exception:
            # Fallback si falla el redondeo temporal
            start_norm = pd.Timestamp(query_start) if query_start else pd.Timestamp.now()
            end_norm = pd.Timestamp(query_end) if query_end else pd.Timestamp.now()

        # Generamos el índice de tiempo completo
        try:
            full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=interval)
        except:
             return empty_response

        datasets = []
        
        if not df_prod.empty:
            # Agrupamos por product_display (Nombre + Linea)
            grouped = df_prod.groupby([pd.Grouper(freq=interval), 'product_display']).agg({
                'id': 'size',
                'color': 'first'
            })
            
            counts_matrix = grouped['id'].unstack(level=1, fill_value=0)
            counts_matrix = counts_matrix.reindex(full_time_index, fill_value=0)
            
            # Recuperar colores (usamos product_display para mapear)
            unique_products = df_prod[['product_display', 'color']].drop_duplicates().set_index('product_display')['color'].to_dict()

            for prod_name in counts_matrix.columns:
                datasets.append({
                    'label': prod_name,
                    'data': counts_matrix[prod_name].tolist(),
                    'borderColor': unique_products.get(prod_name, '#ccc'),
                    'backgroundColor': unique_products.get(prod_name, '#ccc'),
                    'fill': False
                })
        
        return {
            'labels': full_time_index.strftime('%d/%m %H:%M').tolist(),
            'datasets': datasets
        }

    @staticmethod
    def get_entry_exit_comparison(df, interval='1h', query_start=None, query_end=None):
        if df.empty: return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}
        
        # Verificación de seguridad
        if 'is_entry' not in df.columns or 'is_exit' not in df.columns:
             return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}
        
        df_temp = df.copy()
        df_temp.set_index('timestamp', inplace=True)
        
        entry_series = df_temp[df_temp['is_entry']].groupby(pd.Grouper(freq=interval)).size()
        exit_series = df_temp[df_temp['is_exit']].groupby(pd.Grouper(freq=interval)).size()
        
        comp_df = pd.DataFrame({'entry': entry_series, 'exit': exit_series}).fillna(0)
        
        # Descarte: Diferencia Entrada - Salida. Si es negativo (salió más buffer), es 0.
        comp_df['diff'] = (comp_df['entry'] - comp_df['exit']).apply(lambda x: x if x > 0 else 0)
        
        return {
            'labels': comp_df.index.strftime('%d/%m %H:%M').tolist(),
            'entry': comp_df['entry'].tolist(),
            'exit': comp_df['exit'].tolist(),
            'diff': comp_df['diff'].tolist()
        }
    
    # ... calculate_downtime se mantiene igual ...
    @staticmethod
    def calculate_downtime(df, threshold_seconds=60):
        if df.empty: return []
        stops_report = []
        for line in df['line_key'].unique():
            line_df = df[(df['line_key'] == line) & (df['is_exit'])].sort_values('timestamp')
            line_df['delta'] = line_df['timestamp'].diff()
            stops = line_df[line_df['delta'] > pd.Timedelta(seconds=threshold_seconds)]
            for _, row in stops.iterrows():
                duration = row['delta']
                stops_report.append({
                    'line': line,
                    'start_time': (row['timestamp'] - duration).isoformat(),
                    'end_time': row['timestamp'].isoformat(),
                    'duration_seconds': int(duration.total_seconds()),
                    'duration_formatted': str(duration).split('.')[0]
                })
        return sorted(stops_report, key=lambda x: x['start_time'], reverse=True)

    @staticmethod
    def get_product_distribution(df):
        if df.empty: return []
        total = df[df['is_exit']].shape[0]
        stats = df[df['is_exit']].groupby('product_name').agg(
            cantidad=('id', 'count'),
            color=('color', 'first') 
        ).reset_index()
        stats['percent'] = (stats['cantidad'] / total * 100).round(2) if total > 0 else 0
        return stats.to_dict(orient='records')