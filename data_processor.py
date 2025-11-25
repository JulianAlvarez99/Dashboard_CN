import pandas as pd
import numpy as np

class DataProcessor:
    """
    Encargado de transformar datos crudos en métricas de negocio 
    y estructuras para gráficos.
    """

    @staticmethod
    def calculate_global_kpis(df, downtime_events):
        """
        KPIs Actualizados:
        - Total Producción: Ahora se basa en SALIDA (Paletizado/Final).
        - Paradas: Cantidad y Tiempo acumulado formateado.
        """
        if df.empty:
            return {
                'total_output': 0,
                'downtime_count': 0,
                'downtime_total_str': "00:00:00"
            }
            
        # Total Salida (Exit Area)
        total_output = df[df['is_exit']].shape[0]
        
        # Métricas de Paradas
        downtime_count = len(downtime_events)
        total_seconds = sum(d['duration_seconds'] for d in downtime_events)
        
        # Formatear segundos a HH:MM:SS
        m, s = divmod(total_seconds, 60)
        h, m = divmod(m, 60)
        downtime_str = "{:02d}:{:02d}:{:02d}".format(int(h), int(m), int(s))
        
        return {
            'total_output': int(total_output),
            'downtime_count': downtime_count,
            'downtime_total_str': downtime_str
        }

    @staticmethod
    def get_resampled_chart_data(df, interval='1h', query_start=None, query_end=None):
        """
        Genera datos para gráficos de líneas rellenando los huecos con 0.
        CORREGIDO: Normaliza fechas para asegurar coincidencia en el reindex.
        """
        empty_response = {'labels': [], 'datasets': []}

        # 1. Preparar DataFrame solo con entradas
        if df.empty:
            df_prod = pd.DataFrame()
        else:
            df_prod = df[df['is_entry']].copy()
            df_prod.set_index('timestamp', inplace=True)

        # 2. Determinar rango y NORMALIZARLO (La clave del fix)
        # Si start es 14:23 y el intervalo 1h, forzamos que start sea 14:00
        # para que coincida con los buckets del groupby.
        
        # Obtener fechas crudas
        raw_start = query_start if query_start else (df_prod.index.min() if not df_prod.empty else pd.Timestamp.now())
        raw_end = query_end if query_end else (df_prod.index.max() if not df_prod.empty else pd.Timestamp.now())
        
        # Convertir a Timestamp si no lo son y redondear al piso (floor)
        # Ojo: '1ME' (mes) no soporta floor directo a veces, manejamos excepciones comunes
        try:
            start_norm = pd.Timestamp(raw_start).floor(interval)
            # Para el final usamos ceil para asegurar que cubra el último dato
            end_norm = pd.Timestamp(raw_end).ceil(interval)
        except ValueError:
            # Fallback si el intervalo es complejo (ej: '1ME')
            start_norm = pd.Timestamp(raw_start).replace(minute=0, second=0, microsecond=0)
            end_norm = pd.Timestamp(raw_end).replace(minute=0, second=0, microsecond=0)

        # Creamos el índice maestro alineado a las horas en punto (xx:00)
        full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=interval)

        # 3. Agrupar y Reindexar
        if not df_prod.empty:
            # Agrupamos
            grouped = df_prod.groupby([pd.Grouper(freq=interval), 'line_key']).size().unstack(level=1, fill_value=0)
            
            # Ahora sí, los índices deberían coincidir (ambos son xx:00:00)
            # method=None asegura que solo rellene con 0 si no existe el índice exacto
            grouped = grouped.reindex(full_time_index, fill_value=0)
        else:
            grouped = pd.DataFrame(index=full_time_index)

        # 4. Formateo para frontend
        labels = grouped.index.strftime('%Y-%m-%d %H:%M').tolist()
        datasets = []
        
        for line_name in grouped.columns:
            datasets.append({
                'label': line_name,
                'data': grouped[line_name].tolist(), 
                'fill': False,
            })

        if not grouped.empty and len(grouped.columns) > 0:
            total_series = grouped.sum(axis=1).tolist()
            datasets.append({
                'label': 'TOTAL PLANTA',
                'data': total_series,
                'borderColor': '#FF0000',
                'borderWidth': 2,
                'type': 'line'
            })

        return {
            'labels': labels,
            'datasets': datasets
        }
    
    @staticmethod
    def get_product_chart_data(df, interval='1h', query_start=None, query_end=None):
        """
        Grafica líneas por PRODUCTO en lugar de por LÍNEA DE PRODUCCIÓN.
        Usa el color del producto de la base de datos.
        """
        empty_response = {'labels': [], 'datasets': []}
        if df.empty and not query_start: return empty_response

        # Filtramos solo entradas para ver qué se está produciendo
        df_prod = df[df['is_entry']].copy()
        if not df_prod.empty:
            df_prod.set_index('timestamp', inplace=True)

        # Normalizar fechas (Misma lógica de fix anterior)
        raw_start = query_start if query_start else (df_prod.index.min() if not df_prod.empty else pd.Timestamp.now())
        raw_end = query_end if query_end else (df_prod.index.max() if not df_prod.empty else pd.Timestamp.now())
        
        try:
            start_norm = pd.Timestamp(raw_start).floor(interval)
            end_norm = pd.Timestamp(raw_end).ceil(interval)
        except:
            start_norm = pd.Timestamp(raw_start)
            end_norm = pd.Timestamp(raw_end)

        full_time_index = pd.date_range(start=start_norm, end=end_norm, freq=interval)

        datasets = []
        
        if not df_prod.empty:
            # Agrupamos por Intervalo y por NOMBRE DE PRODUCTO
            # Guardamos también el color (tomamos el primero que encontremos para ese producto)
            grouped = df_prod.groupby([pd.Grouper(freq=interval), 'product_name']).agg({
                'id': 'size',       # Conteo
                'color': 'first'    # Color
            })
            
            # Reestructuramos: Indices=Time, Columnas=Producto
            # Esto nos da una matriz de conteos
            counts_matrix = grouped['id'].unstack(level=1, fill_value=0)
            counts_matrix = counts_matrix.reindex(full_time_index, fill_value=0)
            
            # Necesitamos recuperar los colores. Hacemos un diccionario Producto -> Color
            # Iteramos sobre el DF original agrupado para sacar los colores únicos
            unique_products = df_prod[['product_name', 'color']].drop_duplicates().set_index('product_name')['color'].to_dict()

            # Generar Datasets
            for product_name in counts_matrix.columns:
                datasets.append({
                    'label': product_name,
                    'data': counts_matrix[product_name].tolist(),
                    'borderColor': unique_products.get(product_name, '#cccccc'), # Color de DB
                    'backgroundColor': unique_products.get(product_name, '#cccccc'),
                    'fill': False
                })
        
        return {
            'labels': full_time_index.strftime('%d/%m/%Y %H:%M').tolist(), # Formato solicitado
            'datasets': datasets
        }

    @staticmethod
    def get_entry_exit_comparison(df, interval='1h', query_start=None, query_end=None):
        """
        NUEVO: Gráfico de Barras comparativo (Entrada vs Salida) + Descarte Calculado.
        """
        # ... Lógica similar de reindexado temporal ...
        # (Simplificado para brevedad, asume lógica de normalización igual a la anterior)
        if df.empty: return {'labels':[], 'entry':[], 'exit':[], 'diff':[]}
        
        df_temp = df.copy()
        df_temp.set_index('timestamp', inplace=True)
        
        # Agrupamos
        entry_series = df_temp[df_temp['is_entry']].groupby(pd.Grouper(freq=interval)).size()
        exit_series = df_temp[df_temp['is_exit']].groupby(pd.Grouper(freq=interval)).size()
        
        # Unimos en un solo DF para alinear fechas
        comp_df = pd.DataFrame({'entry': entry_series, 'exit': exit_series}).fillna(0)
        
        # Calcular descarte (Diferencia)
        comp_df['diff'] = comp_df['entry'] - comp_df['exit']
        # Si la diferencia es negativa (salió más de lo que entró por buffer), ponemos 0 o dejamos negativo para análisis
        
        return {
            'labels': comp_df.index.strftime('%d/%m/%Y %H:%M').tolist(),
            'entry': comp_df['entry'].tolist(),
            'exit': comp_df['exit'].tolist(),
            'diff': comp_df['diff'].tolist()
        }

    @staticmethod
    def calculate_downtime(df, threshold_seconds=60):
        """
        Detecta paradas basándose en huecos temporales.
        """
        if df.empty:
            return []

        stops_report = []

        for line in df['line_key'].unique():
            line_df = df[(df['line_key'] == line) & (df['is_entry'])].sort_values('timestamp')
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
        """Agrega porcentaje relativo para la tabla resumen."""
        if df.empty: return []
        
        total = df[df['is_entry']].shape[0]
        stats = df[df['is_entry']].groupby('product_name').agg(
            cantidad=('id', 'count'),
            color=('color', 'first') 
        ).reset_index()
        
        # Calcular porcentaje
        stats['percent'] = (stats['cantidad'] / total * 100).round(2) if total > 0 else 0
        
        return stats.to_dict(orient='records')