
import numpy as np
import time
import multiprocessing
from multiprocessing import Pool, cpu_count


def multiply_manual(A, B):
    """Multiplicación de matrices (filas x columnas) en Python puro"""
    n = len(A)
    # Inicializar matriz resultado con ceros
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            val = 0
            for k in range(n):
                val += A[i][k] * B[k][j]
            C[i][j] = val
    return np.array(C)

def sumar_manual(A, B):
    """Suma simple de dos matrices en Python puro"""
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            C[i][j] = A[i][j] + B[i][j]
    return np.array(C)


# Para comparar T1
def calcular_un_bloque_secuencial(i, j, fila_A, col_B):
    N = len(fila_A)
    M = len(fila_A[0])
    bloque_res = np.zeros((M, M))
    for k in range(N):
        prod = multiply_manual(fila_A[k], col_B[k])
        bloque_res = sumar_manual(bloque_res, prod)
    return bloque_res

def run_secuencial(A_bloques, B_bloques):
    N = len(A_bloques)
    C_bloques = [[None]*N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            fila_A = A_bloques[i]
            col_B = [B_bloques[k][j] for k in range(N)]
            C_bloques[i][j] = calcular_un_bloque_secuencial(i, j, fila_A, col_B)
    return C_bloques


# Multiprocessing con manager
def calcular_un_bloque_manager(i, j, fila_A, col_B, dict_manager):
    N = len(fila_A)
    M = len(fila_A[0])
    bloque_res = np.zeros((M, M))
    for k in range(N):
        prod = multiply_manual(fila_A[k], col_B[k])
        bloque_res = sumar_manual(bloque_res, prod)
    dict_manager["resultado"] = bloque_res

def run_process_manager(A_bloques, B_bloques):
    N = len(A_bloques)
    C_bloques = []
    procesos = []
    
    for i in range(N):
        proceso_fila = []
        resultado_fila = []
        C_bloques.append(resultado_fila)
        for j in range(N):
            manager_actual = multiprocessing.Manager().dict()
            resultado_fila.append(manager_actual)
            
            fila_A = A_bloques[i]
            col_B = [B_bloques[k][j] for k in range(N)]
            
            p = multiprocessing.Process(
                target=calcular_un_bloque_manager, 
                args=(i, j, fila_A, col_B, manager_actual)
            )
            p.start()
            proceso_fila.append(p)
        procesos.append(proceso_fila)
        
    for i in range(N):
        for j in range(N):
            procesos[i][j].join()
            
    # Recuperar resultados
    for i in range(N):
        for j in range(N):
            C_bloques[i][j] = C_bloques[i][j]["resultado"]
            
    return C_bloques


# Multiprocessing con queue
def productor_multiplicaciones(fila_A, col_B, cola):
    """Productor: Solo calcula multiplicaciones y las encola"""
    N = len(fila_A)
    for k in range(N):
        prod = multiply_manual(fila_A[k], col_B[k])
        cola.put(prod) # Encolar cada producto intermedio

def run_process_queue(A_bloques, B_bloques):
    N = len(A_bloques)
    colas = []
    procesos = []
    
    # Lanzar Procesos Productores NxN
    for i in range(N):
        proceso_fila = []
        colas_fila = []
        colas.append(colas_fila)
        for j in range(N):
            cola_actual = multiprocessing.Queue()
            colas_fila.append(cola_actual)
            
            fila_A = A_bloques[i]
            col_B = [B_bloques[k][j] for k in range(N)]
            
            p = multiprocessing.Process(
                target=productor_multiplicaciones,
                args=(fila_A, col_B, cola_actual)
            )
            p.start()
            proceso_fila.append(p)
        procesos.append(proceso_fila)
        
    # Escucha las colas, extrae y suma
    C_bloques = []
    M = len(A_bloques[0][0])
    for i in range(N):
        fila_res = []
        for j in range(N):
            bloque_res = np.zeros((M, M))
            # Para cada bloque de salida, extraemos N multiplicaciones de la cola
            for k in range(N):
                prod = colas[i][j].get() # Consumir de la cola iterativamente
                bloque_res = sumar_manual(bloque_res, prod) # Agregación (Suma)
            fila_res.append(bloque_res)
        C_bloques.append(fila_res)
        
    # Esperar finalización de Productores
    for i in range(N):
        for j in range(N):
            procesos[i][j].join()
            
    return C_bloques


# # Multiprocessing con pool
def calcular_un_bloque_pool(datos):
    """
    Función para Pool. Recibe todo en una tupla porque usa map.
    """
    i, j, fila_A, col_B = datos
    N = len(fila_A)
    M = len(fila_A[0])
    bloque_res = np.zeros((M, M))
    for k in range(N):
        prod = multiply_manual(fila_A[k], col_B[k])
        bloque_res = sumar_manual(bloque_res, prod)
    return (i, j, bloque_res)

def run_pool(A_bloques, B_bloques, num_processes=None):
    N = len(A_bloques)
    if num_processes is None:
        num_processes = cpu_count()
    
    lista_tareas = []
    for i in range(N):
        for j in range(N):
            fila_A = A_bloques[i]
            col_B = [B_bloques[k][j] for k in range(N)]
            lista_tareas.append((i, j, fila_A, col_B))
            
    with Pool(processes=num_processes) as pool:
        resultados = pool.map(calcular_un_bloque_pool, lista_tareas)
        
    C_bloques = [[None]*N for _ in range(N)]
    for i, j, blq in resultados:
        C_bloques[i][j] = blq
        
    return C_bloques


if __name__ == "__main__":
    print("--- MULTIPLICACIÓN DE MATRICES (TODAS LAS VARIANTES) ---")
    
    # Configuración pequeña para testeo rápido
    N = 2    # Bloques (NxN)
    M = 20   # Tamaño bloque (MxM)
    Total = N * M
    
    print(f"Configuración de test: {N}x{N} bloques de {M}x{M} (Matriz total: {Total}x{Total})")
    
    np.random.seed(42)
    A_bloques = [[np.random.rand(M, M) for _ in range(N)] for _ in range(N)]
    B_bloques = [[np.random.rand(M, M) for _ in range(N)] for _ in range(N)]
    
    A_full = np.block(A_bloques)
    B_full = np.block(B_bloques)
    C_ref = np.dot(A_full, B_full)
    
    print("\nValidando Variante 1 (Secuencial)...")
    res_sec = run_secuencial(A_bloques, B_bloques)
    print("✅ CORRECTO" if np.allclose(np.block(res_sec), C_ref) else "❌ ERROR")

    print("Validando Variante 2 (Process + Manager)...")
    res_man = run_process_manager(A_bloques, B_bloques)
    print("✅ CORRECTO" if np.allclose(np.block(res_man), C_ref) else "❌ ERROR")
    
    print("Validando Variante 3 (Process + Queue)...")
    res_que = run_process_queue(A_bloques, B_bloques)
    print("✅ CORRECTO" if np.allclose(np.block(res_que), C_ref) else "❌ ERROR")

    print("Validando Variante 4 (Pool)...")
    res_pool = run_pool(A_bloques, B_bloques)
    print("✅ CORRECTO" if np.allclose(np.block(res_pool), C_ref) else "❌ ERROR")
