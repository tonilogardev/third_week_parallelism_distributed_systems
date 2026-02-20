# third_week_parallelism_distributed_systems
Tercera entrega de paralelismo y sistemas distribuidos
# Actividad 4: Implementación y Análisis

## Índice
1. [Preparación del Entorno](#1-preparación-del-entorno)
2. [Paradigmas de Multiprocessing Aplicados](#2-paradigmas-de-multiprocessing-aplicados)
    - [2.1. Multiplicación de Matrices (CPU-Bound)](#21-multiplicación-de-matrices-cpu-bound)
    - [2.2. Análisis Financiero (I/O-Bound)](#22-análisis-financiero-io-bound)
3. [Análisis de Resultados (Métricas)](#3-análisis-de-resultados-métricas)
    - [3.1 Estudio Paramétrico: Matrices](#31-estudio-paramétrico-matrices-p4-fijo-n-variable)
    - [3.2 Estudio Paramétrico: Finanzas](#32-estudio-paramétrico-finanzas-p4-ntickers10)
4. [Conclusión](#4-conclusión)

---

## 1. Preparación del Entorno

> El uso de `multiprocessing` en **Google Colab** nos ha dado problemas para la realización de la entrega.

Hemos extraído el código base de la entrega de la Semana 1 [001_week_CIV.ipynb](001_week_CIV.ipynb) y lo hemos convertido en dos scripts de Python independientes para facilitar la implementación de `multiprocessing`:

- **[actividad_4_matrices.py](actividad_4_matrices.py)**: Contiene la lógica de multiplicación de matrices (simple y por bloques).
- **[actividad_4_finance.py](actividad_4_finance.py)**: Contiene la lógica de descarga y procesamiento de datos financieros.

Aplicar los patrones de concurrencia requeridos (Process, Queue, Pool) en estos ficheros.

Para dejar el código limpio, hemos creado un tercer script:
- **[actividad_4_evaluacion.py](actividad_4_evaluacion.py)**: Este script utiliza a los scripts anteriores las funciones de multiplicación de matrices y descarga de cotizaciones (`actividad_4_finance.py` y `actividad_4_matrices.py`), midiendo los tiempos ($T_1$, $T_{par}$) y calculando automáticamente el *Speedup* ($S_p$) y la *Eficiencia* ($E_p$).

[↑ Volver al Índice](#índice)

## 2. Paradigmas de Multiprocessing Aplicados

### 2.1. Multiplicación de Matrices (CPU-Bound)

1.  **Secuencial ($T_1$)**: Benchmark base ejecutando la multiplicación por bloques en un solo hilo.
2.  **Process + Manager**: Se lanza una matriz de procesos (`multiprocessing.Process`), uno por cada sub-bloque resultante. A cada proceso se le pasa una referencia a un `Manager().dict()` compartido donde debe depositar su resultado final.
3.  **Process + Queue**: Similar al anterior, pero cada proceso recibe su propia `multiprocessing.Queue()`. El proceso hace `.put(resultado)` y el hilo principal hace `.get()` para reconstruir la matriz.
4.  **Pool.map**: Creamos una lista de tareas (tuplas con coordenadas `i,j` y los datos a multiplicar) y las inyectamos a un `Pool()` que reparte el trabajo automáticamente sobre un número de workers igual al número de cores del microprocesador.

### 2.2. Análisis Financiero (I/O-Bound)

Se ha utilizado un `multiprocessing.Pool` configurado con *MIN(CPU_COUNT, len(tickers))* workers.

[↑ Volver al Índice](#índice)

## 3. Análisis de Resultados (Métricas)

> [!NOTE] Hardware de pruebas
> Todas las simulaciones se ejecutaron en un entorno con CPU de 4 cores (`multiprocessing.cpu_count() == 4`). Los bloques fijos en las matrices son de $M=50$. Por lo tanto, el tamaño total simulado varía modificando el parámetro de partición $N$. 

### 3.1 Estudio Paramétrico: Matrices ($P=4$ fijo, $N$ variable)

Tabla de tiempos ($T_1$ y $T_p$) y sus correspondientes *Speedup* ($S_p = T_1 / T_p$).

| Escenario | Método | T1 (Secuencial) | Tp (Paralelo) | Speedup ($S_p$) | Eficiencia ($E_p$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **N=2 (Matriz 100x100)** | Process+Manager | 1.9199 s | 1.1859 s | **1.62x** | 40.5% |
| | Process+Queue | 1.9199 s | 1.1505 s | **1.67x** | 41.7% |
| | Pool (4 workers) | 1.9199 s | 1.1256 s | **1.71x** | 42.7% |
| **N=4 (Matriz 200x200)** | Process+Manager | 21.9717 s | 12.9368 s | **1.70x** | 42.5% |
| | Process+Queue | 21.9717 s | 10.1907 s | **2.16x** | 54.0% |
| | Pool (4 workers) | 21.9717 s | 9.8244 s | **2.24x** | 56.0% |
| **N=6 (Matriz 300x300)** | Process+Manager | 73.8385 s | 36.0659 s | **2.05x** | 51.2% |
| | Process+Queue | 73.8385 s | 30.8932 s | **2.39x** | 59.7% |
| | Pool (4 workers) | 73.8385 s | 54.1656 s | **1.36x** | 34.0% |

#### Reflexión sobre el Overhead (Wasted Resources)
La multiplicación de matrices distribuida entre procesos en Python sufre fuertemente por el IPC (Inter-Process Communication). Debido al GIL y al aislamiento de memoria por defecto, las matrices `A` y `B` tienen que "paquetizarse" vía Pickle (serialización) y enviarse a los procesos hijos a través del sistema operativo (pipes internas). 

Esto genera un overhead inmenso ($T_{overhead}$). De hecho, se observa que la eficiencia es sub-óptima con matrices pequeñas ($N=2$), mejorando al aumentar la carga de trabajo computacional ($N=4$, $N=6$ en Queue/Manager), dado que el tiempo pasado calculando en la CPU comienza a compensar el tiempo astronómico pasado serializando/recuperando datos entre procesos Python independientes.
Cabe destacar un caso particular: `Pool.map` parece saturar groseramente la memoria en Python en el caso N=6, disparando sus tiempos hasta desplomar su $S_p$ a 1.3x. 

### 3.2 Estudio Paramétrico: Finanzas ($P=4$, $N_{tickers}=10$)

A diferencia de las tareas ligadas a CPU (CPU-Bound), donde el tiempo malgastado en preparar los procesos penaliza los resultados, I/O bound brilla de forma radical.

| Ejecución Secuencial | Ejecución Pool | Speedup ($S_p$) | Eficiencia ($E_p$) |
| :---: | :---: | :---: | :---: |
| 3.3897 s | 1.1286 s | **3.00x** | **75.09%** |

En tareas bloqueantes (I/O HTTP request), ceder el control del proceso bloqueado a un proceso listo para enviar otra petición permite saturar el ancho de banda y paralelizar el tiempo de latencia del servidor externo de Yahoo. Conseguimos un speedup de 3x sobre 4 cores en una tarea sencilla limitados principalmente por TCP Handshakes de Python.

[↑ Volver al Índice](#índice)

## 4. Conclusión

1. Entendemos que **`multiprocessing` es indispensable para saltarse el GIL** en computación puramente basada en aritmética de software (CPU-bound) como el caso de nuestras matrices, logrando paralelismo por hardware.
2. **Queue vs Manager**: De forma consistente en las simulaciones, el uso de `.put()` con `Queue` es ligeramente más veloz que la delegación de punteros que hace `Manager().dict()`.
3. El paralelismo de **I/O bound es considerablemente más simple y eficiente** con Pool.