from db_manager import DataManager
from data_processor import DataProcessor
from datetime import datetime, timedelta
import time

def test_full_architecture():
    print("=== INICIANDO TEST DE ARQUITECTURA (Etapa 2) ===")
    
    # 1. Instancia de Capa de Datos
    db = DataManager()
    
    # 2. Definir rango (Ej: Últimos 2 días para ver más datos)
    end = datetime.now()
    start = end - timedelta(days=2)
    
    print(f"1. Consultando DB desde {start.date()} hasta {end.date()}...")
    t0 = time.time()
    
    # Traemos TODO de una sola vez
    df_raw = db.get_raw_production_data(start, end)
    
    print(f"   -> Datos obtenidos: {len(df_raw)} filas en {time.time()-t0:.2f}s")
    
    if df_raw.empty:
        print("   [!] No hay datos para procesar. Verifica tu DB o el rango de fechas.")
        return

    # 3. Procesamiento (Capa de Negocio)
    print("\n2. Calculando KPIs Globales...")
    kpis = DataProcessor.calculate_global_kpis(df_raw)
    print(f"   -> Total Producción: {kpis['total_bags']}")
    print(f"   -> Descarte Estimado: {kpis['estimated_discard']}")

    print("\n3. Generando Gráfico de Línea (Resampleo 1min) CON RELLENO DE CEROS...")
    # Pasamos start y end para que rellene los huecos desde el inicio hasta el fin
    chart = DataProcessor.get_resampled_chart_data(df_raw, interval='1min', query_start=start, query_end=end)
    print(f"   -> Eje X (Labels): {len(chart['labels'])} puntos.")
    
    # Verificamos si hay datos
    if chart['datasets']:
        print(f"   -> Series generadas: {[ds['label'] for ds in chart['datasets']]}")
    
    for ds in chart['datasets']:
        # 1. Sumamos todo para ver si coincide con los KPIs
        total_en_grafico = sum(ds['data'])
        
        # 2. Buscamos valores distintos de cero para mostrarlos
        valores_no_cero = [val for val in ds['data'] if val > 0]
        
        print(f"\n   AUDITORÍA SERIE '{ds['label']}':")
        print(f"     - Suma Total en Gráfico: {total_en_grafico}")
        print(f"     - Cantidad de intervalos con producción: {len(valores_no_cero)} de {len(ds['data'])}")
        
        if valores_no_cero:
            # Mostrar los primeros 5 valores reales encontrados y sus índices
            # Necesitamos los índices para saber a qué hora corresponden
            indices_con_datos = [i for i, x in enumerate(ds['data']) if x > 0][:5]
            ejemplos = []
            for i in indices_con_datos:
                fecha = chart['labels'][i]
                valor = ds['data'][i]
                ejemplos.append(f"{fecha} -> {valor}")
            
            print(f"     - Ejemplo de datos reales: {ejemplos}")
        else:
            print("     - [ALERTA] Esta serie está plana (todo 0).")
    
    print("\n4. Detectando Paradas (Umbral > 5 min)...")
    # Usamos 300 segundos (5 min) como umbral
    stops = DataProcessor.calculate_downtime(df_raw, threshold_seconds=300)
    print(f"   -> Se detectaron {len(stops)} paradas mayores a 5 min.")
    
    if stops:
        # CORRECCIÓN AQUÍ: Usamos 'duration_formatted' en lugar de 'duration_text'
        print(f"   -> Última parada registrada: Línea {stops[0]['line']} - Duración: {stops[0]['duration_formatted']}")

    print("\n5. Distribución de Productos (Torta)...")
    pie_data = DataProcessor.get_product_distribution(df_raw)
    for p in pie_data:
        print(f"   -> {p['product_name']}: {p['cantidad']} ({p.get('color', 'No Color')})")

if __name__ == "__main__":
    test_full_architecture()