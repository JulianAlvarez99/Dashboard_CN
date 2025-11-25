import pandas as pd
from config import get_db_connection, get_db_engine, Config

class DataManager:
    def __init__(self):
        self.metadata_cache = {}
        self.refresh_metadata()

    def refresh_metadata(self):
        """
        Carga tablas auxiliares en memoria para evitar JOINs SQL costosos.
        Ahora incluye el mapeo de Cámaras <-> Áreas.
        """
        conn = get_db_connection()
        if not conn:
            return

        try:
            with conn.cursor() as cursor:
                # 1. Cargar Clases (Productos)
                cursor.execute("SELECT class_id, class_name, color, class_weight FROM class")
                self.metadata_cache['classes'] = {row['class_id']: row for row in cursor.fetchall()}

                # 2. Cargar Areas (Nombres y Coordenadas)
                cursor.execute("SELECT id, nombre FROM areas")
                self.metadata_cache['areas'] = {row['id']: row for row in cursor.fetchall()}
                
                # 3. Cargar Relación Cámara-Area [CORREGIDO]
                # Obtenemos qué cámara es dueña de qué área y si está activa
                cursor.execute("SELECT camera_id, area_id, status FROM camera_areas")
                camera_rows = cursor.fetchall()
                
                # Creamos un diccionario de mapeo rápido: { area_id: camera_id }
                # Esto asume que un área pertenece a una única cámara activa a la vez.
                self.metadata_cache['area_to_camera'] = {
                    row['area_id']: row['camera_id'] 
                    for row in camera_rows 
                    # Opcional: filtrar si solo queremos las activas, 
                    # pero para histórico mejor traer todas para no perder datos viejos.
                }
                
            print(f"--> Metadata cargada: {len(self.metadata_cache['classes'])} clases, "
                  f"{len(self.metadata_cache['areas'])} áreas, "
                  f"{len(self.metadata_cache['area_to_camera'])} vinculaciones cámara-área.")
                  
        except Exception as e:
            print(f"Error cargando metadata: {e}")
        finally:
            conn.close()

    def get_raw_production_data(self, start_date, end_date, selected_lines=None):
        """
        Trae datos crudos y los enriquece con nombres de productos y IDs de cámaras.
        """
        if selected_lines is None:
            selected_lines = Config.LINES_CONFIG.keys()

        engine = get_db_engine()
        if not engine:
            return pd.DataFrame()

        dfs = []

        try:
            # Usamos el context manager del engine
            with engine.connect() as conn:
                for line_key in selected_lines:
                    if line_key not in Config.LINES_CONFIG:
                        continue

                    cfg = Config.LINES_CONFIG[line_key]
                    
                    # Query optimizada sin JOINS
                    query = f"""
                        SELECT id, class_id, timestamp, area_id, largo_mm, ancho_mm
                        FROM {cfg['table']} 
                        WHERE timestamp BETWEEN %s AND %s
                    """
                    
                    df_line = pd.read_sql(query, conn, params=(start_date, end_date))
                    
                    if not df_line.empty:
                        df_line['line_key'] = line_key
                        
                        # Definición de Entrada/Salida según Config
                        df_line['is_entry'] = df_line['area_id'] == cfg['entry_area']
                        df_line['is_exit'] = df_line['area_id'] == cfg['exit_area']
                        
                        dfs.append(df_line)

            if not dfs:
                return pd.DataFrame()

            final_df = pd.concat(dfs, ignore_index=True)
            
            # --- LIMPIEZA DE TIPOS ---
            final_df['timestamp'] = pd.to_datetime(final_df['timestamp'])
            final_df['class_id'] = pd.to_numeric(final_df['class_id'], errors='coerce').fillna(0).astype(int)

            # --- ENRIQUECIMIENTO (CRUCE DE DATOS EN MEMORIA) ---
            
            # 1. Mapeo de Productos
            class_dict = self.metadata_cache.get('classes', {})
            id_to_name = {k: v['class_name'] for k, v in class_dict.items()}
            id_to_color = {k: v['color'] for k, v in class_dict.items()}
            id_to_weight = {k: v['class_weight'] for k, v in class_dict.items()}
            
            final_df['product_name'] = final_df['class_id'].map(id_to_name).fillna("Desconocido")
            final_df['color'] = final_df['class_id'].map(id_to_color).fillna("#000000")
            final_df['class_weight'] = final_df['class_id'].map(id_to_weight).fillna(0)
            
            # 2. Mapeo de Cámaras (NUEVO)
            # Usamos el area_id del registro para saber qué cámara lo vió
            area_to_cam_map = self.metadata_cache.get('area_to_camera', {})
            final_df['camera_id'] = final_df['area_id'].map(area_to_cam_map).fillna(0).astype(int)

            # 3. Mapeo de Nombre de Área (Opcional, útil para debug)
            area_names_map = {k: v['nombre'] for k, v in self.metadata_cache.get('areas', {}).items()}
            final_df['area_name'] = final_df['area_id'].map(area_names_map).fillna("Desconocida")
            
            return final_df.sort_values('timestamp')

        except Exception as e:
            print(f"Error crítico en DB Manager: {e}")
            return pd.DataFrame()