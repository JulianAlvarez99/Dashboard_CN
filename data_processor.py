import pandas as pd
import numpy as np
from config import Config # Importar Config

class DataProcessor:

    @staticmethod
    def filter_by_shift(df, shift_key):
        """
        Filtra el DataFrame según los horarios definidos en Config.SHIFTS.
        Soporta rangos que cruzan la medianoche (ej: 22 a 06).
        """
        if df.empty or shift_key not in Config.SHIFTS: 
            return df
            
        shift_cfg = Config.SHIFTS[shift_key]
        start_h = shift_cfg['start']
        end_h = shift_cfg['end']
        
        hours = df['timestamp'].dt.hour
        
        # Lógica para turnos normales (ej: 06 a 14) vs cruce de medianoche (ej: 22 a 06)
        if start_h < end_h:
            return df[(hours >= start_h) & (hours < end_h)]
        else:
            # Caso Noche: horas mayores a 22 O horas menores a 6
            return df[(hours >= start_h) | (hours < end_h)]
    
    @staticmethod
    def format_int_ar(value):
        """Formatea enteros con punto de miles: 1250 -> '1.250'"""
        try:
            return "{:,}".format(int(value)).replace(',', '.')
        except:
            return str(value)
        
    @staticmethod
    def calculate_global_kpis(df, downtime_events):
        if df.empty:
            return {'total_output': 0, 'downtime_count': 0, 'downtime_total_str': "00:00:00", 'total_weight_kg': "0"}
            
        if 'is_exit' in df.columns: total_output = df[df['is_exit']].shape[0]
        else: total_output = 0
        
        total_weight = 0
        if 'class_weight' in df.columns and 'is_exit' in df.columns:
             production_df = df[df['is_exit']]
             total_weight = production_df['class_weight'].sum()

        downtime_count = len(downtime_events)
        total_seconds = sum(d['duration_seconds'] for d in downtime_events)
        m, s = divmod(total_seconds, 60)
        h, m = divmod(m, 60)
        downtime_str = "{:02d}:{:02d}:{:02d}".format(int(h), int(m), int(s))
        
        return {
            # CORRECCIÓN IMPORTANTE:
            # total_output lo enviamos como INT puro. 
            # ui.js usa numFmt (es-AR) que pondrá el punto automáticamente.
            'total_output': int(total_output),
            
            'downtime_count': int(downtime_count),
            'downtime_total_str': downtime_str,
            
            # total_weight_kg NO usa numFmt en el frontend, así que lo formateamos aquí como STRING.
            'total_weight_kg': DataProcessor.format_int_ar(total_weight)
        }
    
    @staticmethod
    def get_product_chart_data(df, interval='1h', query_start=None, query_end=None):
        empty_response = {'labels': [], 'datasets': []}
        if df.empty and not query_start: return empty_response

        df_prod = pd.DataFrame()
        if not df.empty and 'is_exit' in df.columns:
            df_prod = df[df['is_exit']].copy()
            if not df_prod.empty:
                df_prod.set_index('timestamp', inplace=True)
                if 'line_key' in df_prod.columns and df_prod['line_key'].nunique() > 1:
                    line_map = {'linea_1': 'L1', 'linea_2': 'L2', 'linea_3_semolin': 'L3'}
                    df_prod['product_display'] = df_prod['product_name'] + " (" + df_prod['line_key'].map(line_map).fillna(df_prod['line_key']) + ")"
                else:
                    df_prod['product_display'] = df_prod['product_name']

        try:
            pd_interval = interval.replace('1W', 'W').replace('1ME', 'ME').replace('1M', 'ME')
            if query_start: start_norm = pd.Timestamp(query_start).floor(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_start)
            else: start_norm = pd.Timestamp.now().floor(pd_interval)
            if query_end: end_norm = pd.Timestamp(query_end).ceil(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_end)
            else: end_norm = pd.Timestamp.now().ceil(pd_interval)
        except:
            start_norm = pd.Timestamp(query_start) if query_start else pd.Timestamp.now()
            end_norm = pd.Timestamp(query_end) if query_end else pd.Timestamp.now()
            pd_interval = interval

        try:
            full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=pd_interval)
        except: return empty_response

        datasets = []
        if not df_prod.empty:
            grouped = df_prod.groupby([pd.Grouper(freq=pd_interval), 'product_display']).agg({'id': 'size', 'color': 'first'})
            counts_matrix = grouped['id'].unstack(level=1, fill_value=0)
            counts_matrix = counts_matrix.reindex(full_time_index, fill_value=0)
            unique_products = df_prod[['product_display', 'color']].drop_duplicates().set_index('product_display')['color'].to_dict()

            for prod_name in counts_matrix.columns:
                # CORRECCIÓN: Asegurar lista de enteros nativos
                data_values = counts_matrix[prod_name].fillna(0).astype(int).tolist()
                datasets.append({
                    'label': prod_name,
                    'data': data_values,
                    'borderColor': unique_products.get(prod_name, '#cccccc'),
                    'backgroundColor': unique_products.get(prod_name, '#cccccc'),
                    'fill': False
                })
        
        return {
            'labels': full_time_index.strftime('%d/%m %H:%M').tolist(),
            'datasets': datasets
        }

    @staticmethod
    def get_entry_exit_comparison(df, interval='1h', query_start=None, query_end=None):
        if df.empty: return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}
        if 'is_entry' not in df.columns or 'is_exit' not in df.columns: return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}
        
        pd_interval = interval.replace('1W', 'W').replace('1ME', 'ME').replace('1M', 'ME')
        try:
            if query_start: start_norm = pd.Timestamp(query_start).floor(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_start)
            else: start_norm = pd.Timestamp.now()
            if query_end: end_norm = pd.Timestamp(query_end).ceil(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_end)
            else: end_norm = pd.Timestamp.now()
            full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=pd_interval)
        except: return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}

        if df.empty:
             return {'labels': full_time_index.strftime('%d/%m %H:%M').tolist(), 'entry': [], 'exit': [], 'diff': []}
        
        df_temp = df.copy()
        df_temp.set_index('timestamp', inplace=True)
        
        entry_series = df_temp[df_temp['is_entry']].groupby(pd.Grouper(freq=pd_interval)).size().reindex(full_time_index, fill_value=0)
        exit_series = df_temp[df_temp['is_exit']].groupby(pd.Grouper(freq=pd_interval)).size().reindex(full_time_index, fill_value=0)
        diff_series = (entry_series - exit_series).apply(lambda x: x if x > 0 else 0)
        
        fmt = '%d/%m %H:%M'
        if 'D' in interval or 'W' in interval: fmt = '%d/%m/%Y'

        # CORRECCIÓN: Listas de enteros nativos
        return {
            'labels': full_time_index.strftime(fmt).tolist(),
            'entry': entry_series.astype(int).tolist(),
            'exit': exit_series.astype(int).tolist(),
            'diff': diff_series.astype(int).tolist()
        }
    
    @staticmethod
    def calculate_downtime(df, threshold_seconds=60, query_start=None, query_end=None):
        if df.empty: return []
        if 'line_key' not in df.columns or 'is_exit' not in df.columns: return []

        stops_report = []
        ts_start = pd.Timestamp(query_start) if query_start else None
        ts_end = pd.Timestamp(query_end) if query_end else None
        limit = pd.Timedelta(seconds=threshold_seconds)

        for line in df['line_key'].unique():
            line_df = df[(df['line_key'] == line) & (df['is_exit'])].sort_values('timestamp')
            if line_df.empty: continue
            
            # 1. Paradas Intermedias
            line_df['delta'] = line_df['timestamp'].diff()
            stops = line_df[line_df['delta'] > limit]
            
            for _, row in stops.iterrows():
                duration = row['delta']
                stops_report.append({
                    'line': line,
                    'start_time': (row['timestamp'] - duration).isoformat(),
                    'end_time': row['timestamp'].isoformat(),
                    'duration_seconds': int(duration.total_seconds()),
                    'duration_formatted': str(duration).split('.')[0]
                })
            
            # 2. Parada al Inicio
            if ts_start:
                first_detection = line_df['timestamp'].iloc[0]
                start_gap = first_detection - ts_start
                if start_gap > limit:
                    stops_report.append({
                        'line': line,
                        'start_time': ts_start.isoformat(),
                        'end_time': first_detection.isoformat(),
                        'duration_seconds': int(start_gap.total_seconds()),
                        'duration_formatted': str(start_gap).split('.')[0]
                    })

            # 3. Parada al Final
            if ts_end:
                last_detection = line_df['timestamp'].iloc[-1]
                end_gap = ts_end - last_detection
                if end_gap > limit:
                    stops_report.append({
                        'line': line,
                        'start_time': last_detection.isoformat(),
                        'end_time': ts_end.isoformat(),
                        'duration_seconds': int(end_gap.total_seconds()),
                        'duration_formatted': str(end_gap).split('.')[0]
                    })

        return sorted(stops_report, key=lambda x: x['start_time'], reverse=True)

    @staticmethod
    def get_product_distribution(df):
        if df.empty or 'is_exit' not in df.columns: return []
        total = df[df['is_exit']].shape[0]
        
        stats = df[df['is_exit']].groupby('product_name').agg({
            'id': 'count', 
            'color': 'first',
            'class_weight': 'first'
        }).reset_index()
        
        stats.rename(columns={'id': 'cantidad'}, inplace=True)
        stats['percent'] = (stats['cantidad'] / total * 100).round(2) if total > 0 else 0
        
        stats['cantidad'] = stats['cantidad'].astype(int)
        stats['percent'] = stats['percent'].astype(float)
        
        results = stats.to_dict(orient='records')
        for r in results:
            peso_unitario = r.get('class_weight', 0)
            cantidad = r.get('cantidad', 0)
            total_peso_clase = peso_unitario * cantidad
            
            # CORRECCIÓN: Formato entero sin decimales
            r['total_weight_formatted'] = DataProcessor.format_int_ar(total_peso_clase)
            
        return results