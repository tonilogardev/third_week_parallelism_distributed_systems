
import time
import multiprocessing
import numpy as np
import pprint

# Import
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
    usando un método específico, calculando estadísticas.
    """
    tiempos = []
    
    for _ in range(num_runs):
        # dDtos
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
                 print(f"ERROR: {method_name} no produjo un resultado numéricamente correcto.")
                 return None
                 
        tiempos.append(end - start)
        
    return sum(tiempos) / len(tiempos)

if __name__ == "__main__":
    cpu_cores = multiprocessing.cpu_count()
    print(f"Iniciando Evaluación de Actividad 4 (Cores detectados: {cpu_cores})")
    
    print("\n" + "="*60)
    print("--- PARTE 1: MULTIPLICACIÓN DE MATRICES (CPU-BOUND) ---")
    print("="*60)
    
    # Parámetros fijos para test: Bloques de 50x50, iremos variando el número de bloques N
    # Piden P=1, P=2, P=4, P=8 y N=1, N=2, N=4, N=8
    # N es el número de bloques horizontales/verticales, 
    # El número total de bloques es N*N. Las celdas de matriz total es (N*M)x(N*M)
    # Limitaremos los casos para que acabe en tiempo razonable.
    
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
            "N": n,
            "T1": t_sec,
            "Tp_Manager": t_man,
            "Tp_Queue": t_que,
            "Tp_Pool": t_pool
        })

    # Ejecutar la parte financiera (I/O Bound)
    run_finance_evaluation()

    print("\nSimulación Global Finalizada.")

