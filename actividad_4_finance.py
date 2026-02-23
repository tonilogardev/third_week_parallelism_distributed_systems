
import pandas as pd
import requests
import time
from datetime import datetime
import multiprocessing
from multiprocessing import Pool, cpu_count, Process, Queue


# CONFIGURACIÓN
START_DATE = "2013-02-01"
END_DATE = "2024-12-31"
SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "JPM", "JNJ", "V"]


# FUNCIONES DE DESCARGA Y PROCESAMIENTO

def download_and_process(ticker):
    """
    Función que ejecuta todo el flujo para UN ticker:
    1. Descarga datos de Yahoo Finance
    2. Procesa agregaciones semanales y mensuales
    3. Retorna los DataFrames resultantes
    """
    print(f"[{multiprocessing.current_process().name}] Iniciando {ticker}...")
    
    # Fecha
    try:
        period1 = int(datetime.strptime(START_DATE, "%Y-%m-%d").timestamp())
        period2 = int(datetime.strptime(END_DATE, "%Y-%m-%d").timestamp())
    except Exception as e:
        print(f"Error fechas: {e}")
        return None

    # Configurar Request
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "formatted": "true",
        "interval": "1d",
        "includeAdjustedClose": "false",
        "period1": period1,
        "period2": period2,
        "symbol": ticker
    }
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Descargar
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data.get("chart", {}).get("result")
        if not result:
            return None
            
        data_payload = result[0]
        if "timestamp" not in data_payload:
            return None
            
        timestamps = data_payload["timestamp"]
        quote = data_payload["indicators"]["quote"][0]
        
        df = pd.DataFrame({
            "Date": pd.to_datetime(timestamps, unit="s"),
            "Open": quote["open"],
            "High": quote["high"],
            "Low": quote["low"],
            "Close": quote["close"],
            "Volume": quote["volume"]
        })
        df.set_index("Date", inplace=True)
        
        
        agg_dict = {
            'Low': 'min', 'High': 'max', 
            'Open': 'first', 'Close': 'last', 'Volume': 'sum'
        }
        
        df_weekly = df.resample('W').agg(agg_dict)
        df_monthly = df.resample('ME').agg(agg_dict)
        
        print(f"[{multiprocessing.current_process().name}] {ticker} completado.")
        return (ticker, df_weekly, df_monthly)

    except Exception as e:
        print(f"Error procesando {ticker}: {e}")
        return None

def run_finance_evaluation():
    print("\n" + "="*60)
    print("--- ANÁLISIS FINANCIERO CON MULTIPROCESSING ---")
    print("="*60)
    print(f"Procesando {len(SYMBOLS)} símbolos...")
    

    # Calcular T1 - Speedup
    print("\n--- Ejecución Secuencial ---")
    start_time_sec = time.time()
    resultados_sec = []
    for symbol in SYMBOLS:
        res = download_and_process(symbol)
        if res:
            resultados_sec.append(res)
    end_time_sec = time.time()
    t1 = end_time_sec - start_time_sec
    print(f"Tiempo total ejecución secuencial (T1): {t1:.4f} s")
    
   
    # Pool - Para calcular Tp
    print("\n--- Ejecución Paralela (Pool) ---")
    num_processes = min(len(SYMBOLS), cpu_count())
    print(f"Usando {num_processes} procesos workers en el Pool.")
    
    start_time_par = time.time()
    with Pool(processes=num_processes) as pool:
        resultados_par = pool.map(download_and_process, SYMBOLS)
    end_time_par = time.time()
    tp = end_time_par - start_time_par
    
    print(f"Tiempo total ejecución paralela (Tp): {tp:.4f} s")
    # Evitar division by zero if tp is incredibly small
    sp = t1 / tp if tp > 0 else 0
    print(f"Speedup (Sp = T1 / Tp): {sp:.2f}x")
    print(f"Eficiencia (Ep = Sp / p): {(sp) / num_processes:.2%}")

    # Filtrar resultados válidos
    resultados_validos = [r for r in resultados_par if r is not None]
    
    
    semanales = [r[1] for r in resultados_validos]
    
    if semanales:
        df_global = pd.concat(semanales).groupby(level=0).agg({
            'Low': 'min', 'High': 'max', 'Volume': 'sum'
        })
        print("\n--- Resultado Global (Semanal) Correcto ---")
        print(df_global.head())


if __name__ == "__main__":
    run_finance_evaluation()
