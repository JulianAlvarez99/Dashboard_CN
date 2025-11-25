import pandas as pd
import numpy as np

class DataProcessor:

    @staticmethod
    def filter_by_shift(df, shift):
        """Filtra el DataFrame según el horario del turno."""
        if df.empty: return df
        
        # Extraemos la hora
        hours = df['timestamp'].dt.hour
        
        if shift == 'morning': # 06:00 - 14:00
            return df[(hours >= 6) & (hours < 14)]
        elif shift == 'afternoon': # 14:00 - 22:00
            return df[(hours >= 14) & (hours < 22)]
        elif shift == 'night': # 22:00 - 06:00
            return df[(hours >= 22) | (hours < 6)]
        return df
    
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

        # Normalización Fechas
        try:
            # Soporte para 1W y 1M (pandas usa 'W' y 'ME')
            pd_interval = interval.replace('1W', 'W').replace('1ME', 'ME').replace('1M', 'ME')
            
            if query_start: start_norm = pd.Timestamp(query_start).floor(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_start)
            else: start_norm = pd.Timestamp.now().floor(pd_interval)

            if query_end: end_norm = pd.Timestamp(query_end).ceil(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_end)
            else: end_norm = pd.Timestamp.now().ceil(pd_interval)
        except:
            start_norm = pd.Timestamp(query_start) if query_start else pd.Timestamp.now()
            end_norm = pd.Timestamp(query_end) if query_end else pd.Timestamp.now()
            pd_interval = interval # Fallback

        # Generamos el índice de tiempo completo
        try:
            full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=interval)
        except:
             return empty_response

        datasets = []
        
        if not df_prod.empty:
            grouped = df_prod.groupby([pd.Grouper(freq=pd_interval), 'product_display']).agg({'id': 'size', 'color': 'first'})
            counts_matrix = grouped['id'].unstack(level=1, fill_value=0)
            counts_matrix = counts_matrix.reindex(full_time_index, fill_value=0)
            unique_products = df_prod[['product_display', 'color']].drop_duplicates().set_index('product_display')['color'].to_dict()

            for prod_name in counts_matrix.columns:
                datasets.append({
                    'label': prod_name,
                    'data': counts_matrix[prod_name].tolist(),
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
        
        # Verificación de seguridad
        if 'is_entry' not in df.columns or 'is_exit' not in df.columns:
             return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}
        
        pd_interval = interval.replace('1W', 'W').replace('1ME', 'ME').replace('1M', 'ME')
        try:
            if query_start: start_norm = pd.Timestamp(query_start).floor(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_start)
            else: start_norm = pd.Timestamp.now()
            if query_end: end_norm = pd.Timestamp(query_end).ceil(pd_interval) if 'M' not in pd_interval else pd.Timestamp(query_end)
            else: end_norm = pd.Timestamp.now()
            full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=pd_interval)
        except: return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}

        if df.empty:
             return {
                'labels': full_time_index.strftime('%d/%m %H:%M').tolist(),
                'entry': [0]*len(full_time_index), 'exit': [0]*len(full_time_index), 'diff': [0]*len(full_time_index)
             }
        
        df_temp = df.copy()
        df_temp.set_index('timestamp', inplace=True)
        
        # Usamos el full_time_index para reindexar y asegurar sincronía
        entry_series = df_temp[df_temp['is_entry']].groupby(pd.Grouper(freq=pd_interval)).size().reindex(full_time_index, fill_value=0)
        exit_series = df_temp[df_temp['is_exit']].groupby(pd.Grouper(freq=pd_interval)).size().reindex(full_time_index, fill_value=0)
        
        diff_series = (entry_series - exit_series).apply(lambda x: x if x > 0 else 0)
        
        fmt = '%d/%m %H:%M'
        if 'D' in interval or 'W' in interval: fmt = '%d/%m/%Y'

        return {
            'labels': full_time_index.strftime(fmt).tolist(),
            'entry': entry_series.tolist(),
            'exit': exit_series.tolist(),
            'diff': diff_series.tolist()
        }
    
  
    @staticmethod
    def calculate_downtime(df, threshold_seconds=60, query_start=None, query_end=None):
        """
        Detecta paradas incluyendo huecos al inicio y final del intervalo consultado.
        """
        if df.empty: return []
        if 'line_key' not in df.columns or 'is_entry' not in df.columns: return []

        stops_report = []
        
        # Convertir query dates a Timestamp para comparar
        ts_start = pd.Timestamp(query_start) if query_start else None
        ts_end = pd.Timestamp(query_end) if query_end else None
        limit = pd.Timedelta(seconds=threshold_seconds)

        for line in df['line_key'].unique():
            line_df = df[(df['line_key'] == line) & (df['is_entry'])].sort_values('timestamp')
            if line_df.empty: continue
            
            # 1. Paradas Intermedias (Huecos entre bolsas)
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
            
            # 2. Parada al Inicio (Desde 'query_start' hasta 1ra bolsa)
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

            # 3. Parada al Final (Desde ultima bolsa hasta 'query_end')
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
        if df.empty: return []
        # Usamos is_exit para contar producto terminado real
        if 'is_exit' not in df.columns: return []
        total = df[df['is_exit']].shape[0]
        stats = df[df['is_exit']].groupby('product_name').agg({
            'id': 'count',
            'color': 'first' 
        }).reset_index()
        stats.rename(columns={'id': 'cantidad'}, inplace=True)
        stats['percent'] = (stats['cantidad'] / total * 100).round(2) if total > 0 else 0
        return stats.to_dict(orient='records')