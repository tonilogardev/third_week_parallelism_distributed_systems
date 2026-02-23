
import time
import multiprocessing
import numpy as np
import pprint

# Importar funciones de las otras actividades
from actividad_4_matrices import (
    run_secuencial, 
    run_process_manager, 
    run_process_queue, 
    run_pool
)
from actividad_4_finance import run_finance_evaluation

def run_simulation(N, M, method_name, method_func, num_runs=3):
    """
    Ejecuta una simulación con un tamaño N bloques de MxM 
    """
    tiempos = []
    
    for _ in range(num_runs):
        # Generar datos limpios para cada run
        np.random.seed(int(time.time() * 1000) % 2**32)
        A_bloques = [[np.random.rand(M, M) for _ in range(N)] for _ in range(N)]
        B_bloques = [[np.random.rand(M, M) for _ in range(N)] for _ in range(N)]
        
        start = time.time()
        res = method_func(A_bloques, B_bloques)
        end = time.time()
        
        # Validar numéricamente (solo primer run para no penalizar mucho)
        if _ == 0:
             A_full = np.block(A_bloques)
             B_full = np.block(B_bloques)
             C_ref = np.dot(A_full, B_full)
             if not np.allclose(np.block(res), C_ref):
                 print(f"ERROR: {method_name} ERROR")
                 return None
                 
        tiempos.append(end - start)
        
    return sum(tiempos) / len(tiempos)


def run_simulation_seccion4(N, M, num_processes, num_runs=2):
    """Ejecuta simulación para la variabilidad paramétrica"""
    tiempos = []
    
    for _ in range(num_runs):
        np.random.seed(42)
        A_bloques = [[np.random.rand(M, M) for _ in range(N)] for _ in range(N)]
        B_bloques = [[np.random.rand(M, M) for _ in range(N)] for _ in range(N)]
        
        start = time.time()
        if num_processes == 0:
            res = run_secuencial(A_bloques, B_bloques)
        else:
            res = run_pool(A_bloques, B_bloques, num_processes)
        end = time.time()
        tiempos.append(end - start)
        
    return sum(tiempos) / len(tiempos)

if __name__ == "__main__":
    cpu_cores = multiprocessing.cpu_count()
    print(f"Evaluación de Actividad 4 (Cores detectados: {cpu_cores})")
    
    print("\n" + "="*60)
    print("--- 1: MULTIPLICACIÓN DE MATRICES (CPU-BOUND) ---")
    print("="*60)
    
    # Parámetros fijos para test: Bloques de 50x50, iremos variando el número de bloques N
    M = 50 
    escenarios_N = [2, 4, 6] # Matriz de 2x2 bloques, 4x4, 6x6. 
    
    resultados_sim = []
    
    for n in escenarios_N:
        print(f"\n[{n}x{n} Bloques de {M}x{M} -> Matriz Total: {n*M}x{n*M}]")
        print("-" * 40)
        
        # 1. Secuencial (Benchmark T1)
        t_sec = run_simulation(n, M, "Secuencial", run_secuencial)
        print(f"  Secuencial (T1)\t: {t_sec:.4f} s")
        
        # 2. Process + Manager
        t_man = run_simulation(n, M, "Manager", run_process_manager)
        sp_man = t_sec / t_man if t_man > 0 else 0
        print(f"  Process+Manager\t: {t_man:.4f} s (Speedup: {sp_man:.2f}x)")
        
        # 3. Process + Queue
        t_que = run_simulation(n, M, "Queue", run_process_queue)
        sp_que = t_sec / t_que if t_que > 0 else 0
        print(f"  Process+Queue  \t: {t_que:.4f} s (Speedup: {sp_que:.2f}x)")
        
        # 4. Pool (cpu_count cores)
        t_pool = run_simulation(n, M, "Pool", run_pool)
        sp_pool = t_sec / t_pool if t_pool > 0 else 0
        print(f"  Pool ({cpu_cores} workers)\t: {t_pool:.4f} s (Speedup: {sp_pool:.2f}x)")
        
        resultados_sim.append({
            "N": n, "T1": t_sec, "Tp_Manager": t_man, "Tp_Queue": t_que, "Tp_Pool": t_pool
        })

    # Ejecutar la parte financiera (I/O Bound)
    run_finance_evaluation()

    print("\n" + "="*60)
    print("--- ESTUDIO DE ESCALABILIDAD (Pool) ---")
    print("="*60)
    
    size_total = 200
    M_fijo = 50
    N_fijo = size_total // M_fijo
    
    print(f"\n[4.a] Variabilidad de Procesos (Matriz {size_total}x{size_total}, {N_fijo}x{N_fijo} bloques de {M_fijo}x{M_fijo})")
    print("T1 Secuencial base...")
    t1_s4 = run_simulation_seccion4(N_fijo, M_fijo, 0)
    print(f"  T1 (Secuencial)\t: {t1_s4:.4f} s")
    
    procesos_test = [1, cpu_cores, cpu_cores*2, cpu_cores*4, cpu_cores*7]
    for p in procesos_test:
        tp_s4 = run_simulation_seccion4(N_fijo, M_fijo, p)
        sp_s4 = t1_s4 / tp_s4 if tp_s4 > 0 else 0
        ep_s4 = sp_s4 / p if p > 0 else 0
        print(f"  Pool ({p:2d} workers)\t: Tp = {tp_s4:.4f} s | Sp = {sp_s4:.2f}x | Ep = {ep_s4:.2%}")

    print(f"\n[4.b] Variabilidad de Bloques (Chunks) en Matriz {size_total}x{size_total} con {cpu_cores} workers fijos")
    chunks_test = [(1, 200), (2, 100), (4, 50), (5, 40), (8, 25), (10, 20)]
    mejor_t, mejor_conf = float('inf'), None
    
    for n, m in chunks_test:
        tp_chunk = run_simulation_seccion4(n, m, cpu_cores)
        sp_chunk = t1_s4 / tp_chunk if tp_chunk > 0 else 0
        print(f"  Chunks: {n*n:3d} (Bloques N={n} de {m}x{m})\t: Tp = {tp_chunk:.4f} s | Sp = {sp_chunk:.2f}x")
        if tp_chunk < mejor_t:
            mejor_t, mejor_conf = tp_chunk, (n, m)
            
    print(f"\n[4.c] Conclusión Óptima Experimental:")
    print(f"-> Workers óptimos: {cpu_cores} (Igual a cores hardware)")
    print(f"-> Partición ideal: {mejor_conf[0]*mejor_conf[0]} chunks (N={mejor_conf[0]} de sub-bloques {mejor_conf[1]}x{mejor_conf[1]})")
    print(f"-> Tiempo óptimo Tp: {mejor_t:.4f} s")

    print("\nSimulación Global Finalizada.")


