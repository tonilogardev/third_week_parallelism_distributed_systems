# Entrega tercera semana: Paralelismos y Sistemas Distribuidos

**Profesor:** Ramon Amela Milian
**Alumnos:**
- Steven Louis Allus
- Carlos Jaime Iglesias Vicente
- Antonio López García

---

## Preparación del Entorno

> El uso de `multiprocessing` en **Google Colab** nos ha causado problemas para la realización de la entrega.

Por eso hemos extraído el código base de la entrega de la Semana 1 [001_week_CIV.ipynb](week_01/001_week_CIV.ipynb) y lo hemos convertido en dos scripts de Python independientes:

- **[actividad_4_matrices.py](actividad_4_matrices.py)**: Lógica de multiplicación de matrices.
- **[actividad_4_finance.py](actividad_4_finance.py)**: Lógica de procesamiento de datos financieros.

A partir de los cuales se requiere aplicar los patrones de concurrencia requeridos (Process, Queue, Pool).

Para orquestar limpiamente las pruebas comparativas exigidas, hemos automatizado toda la validación en un tercer script unificado:
- **[actividad_4_evaluacion.py](actividad_4_evaluacion.py)**: Importa y valida las métricas.

[↑ Volver al Índice](#índice)

---

## Índice
- [Preparación del Entorno](#preparación-del-entorno)
- [Descripción de las tareas](#descripción-de-las-tareas)
- [Tarea 1: Multiplicación de matrices (Procesos)](#tarea-1-multiplicación-de-matrices-procesos)
- [Tarea 2: Análisis de mercados (Pool)](#tarea-2-análisis-de-mercados-pool)
- [Tarea 3: Tiempos de ejecución y ganancia](#tarea-3-tiempos-de-ejecución-y-ganancia)
- [Tarea 4: Estudio de escalabilidad algorítmica](#tarea-4-estudio-de-escalabilidad-algorítmica)

---

## Descripción de las tareas
El punto de partida de esta actividad son los dos algoritmos desarrollados en la primera entrega.
Se piden realizar las siguientes tareas:

### Tarea 1: Multiplicación de matrices (Procesos)

1. Modificar el programa de multiplicación de matrices para que todas las funciones paralelas sean ejecutadas en un proceso.
   - **a.** Implementar una versión donde no haga falta coordinación porque cada bloque de salida se calcule en una función.
   - **b.** Implementar una versión donde las multiplicaciones de bloques que tienen que ser sumadas para obtener el resultado se pongan en sendas colas que será consumidas para realizar las sumar y calcular el resultado final.
   - **c.** Modificar la versión a) para utilizar Pools.

**Respuesta a la Tarea 1:**

Implementadas en el script `actividad_4_matrices.py`:
- **1.a / 1.b (Process+Manager / Process+Queue)**: Se instancia un `multiprocessing.Process` por cada sub-bloque. Los resultados se devuelven usando `Manager().dict()` y `Queue()` respectivamente.
- **1.c (Pool.map)**: Se declara un `Pool.map()` recibiendo tuplas funcionales con las multiplicaciones requeridas.

[↑ Volver al Índice](#índice)

---

### Tarea 2: Análisis de mercados (Pool)

2. Modificar el programa de análisis de mercados para ejecutar todas las funciones paralelas en un proceso.

**Respuesta a la Tarea 2:**

Implementado en `actividad_4_finance.py`. Se utiliza `multiprocessing.Pool` configurado con *MIN(cores, len(tickers))* workers para distribuir asíncronamente las peticiones HTTP I/O-bound.

[↑ Volver al Índice](#índice)

---

### Tarea 3: Tiempos de ejecución y ganancia

3. Medir los tiempos de ejecución de todos los algoritmos, presentarlos en una tabla resumen y explicar la ganancia o ausencia de ésta. En la explicación, tener en cuenta:
   - a. Tipología de problema
   - b. Librerías utilizadas y su efecto en el tiempo de ejecución

**Respuesta a la Tarea 3:**

Métricas obtenidas mediante el orquestador `actividad_4_evaluacion.py`:

![Resultados Matrices](img/evaluation_01.png)
![Resultados Finanzas](img/evaluation_02.png)

**Conclusión de Tarea 3**: 
- En operaciones **CPU-bound** (Aritmética matricial Python, sujeta al GIL), el elevado esfuerzo de serialización inter-procesos (*Pickling IPC Overhead*) penaliza enormemente las ganancias en matrices pequeñas. Experimentalmente, `Queue` ha demostrado un rendimiento marginal superior a la delegación vía `Manager.dict()`.
- En operaciones **I/O-Bound** (Descargas bursátiles limitadas por latencia de red TCP), el multiprocesamiento escala linealmente liberando el cuello de botella sin sufrir apenas penalización por IPC.

[↑ Volver al Índice](#índice)

---

### Tarea 4: Estudio de escalabilidad algorítmica

4. Para el algoritmo 1.c:
   - a. Realizar un estudio analizando la variabilidad del tiempo de ejecución en función del número de procesos indicados en la Pool. Se debe llegar, como mínimo, un número de procesos igual a 7 veces el número de procesadores disponibles en la máquina donde se ejecute el experimento. Comentar los resultados obtenidos.

**Respuesta a la Tarea 4.a:**

*Matriz base de 200x200 (Python puro secuencial $T_1 \approx 22.13$ s). Partición fija de 16 bloques (50x50).*
Variación del número de *workers* del `Pool` desde 1 hasta 28 ($7 \times \text{cores físicos disponibles}$):

| Workers ($P$) | $T_p$ (segundos) | Speedup ($S_p$) | Eficiencia ($E_p$) |
|:---:|:---:|:---:|:---:|
| 1 | 22.31 s | 0.99x | 99.18% |
| 4 (Cores físicos) | 9.39 s | 2.36x | 58.90% |
| 8 | 9.10 s | 2.43x | 30.39% |
| 16 | 7.17 s | 3.09x | 19.29% |
| 28 | 7.86 s | 2.82x | 10.06% |

**Observación**: Sobrepasar los 4 núcleos lógicos ofrece un minúsculo *Speedup* marginal a costa de recursos astronómicos. Exceder la capacidad hardware con 28 workers desploma la Eficiencia al 10%, originando severos *Wasted Resources* debidos a la latencia de cambios de contexto del *Scheduler* del SO y la saturación del bus IPC.

---

   - b. Realizar un estudio analizando, para un mismo tamaño de matriz resultado, el impacto de aumentar o disminuir el número de chunks.
     - i. Por ejemplo, para una matriz de medida total 2000x2000, calcular y explicar el tiempo de ejecución para las configuraciones 1 chunk de 2000, 2 chunks de 1000, 4 chunks de 500...

**Respuesta a la Tarea 4.b:**

> *Nota sobre la parametrización elegida:*
> Se ha fijado experimentalmente la medida de la matriz en **200x200** elementos para cumplir con la recomendación de *"ejecución base alrededor de un minuto"* u oscilaciones viables para iteración ($T_1 \approx 22.13$ s). Usar directamente el ejemplo numérico de 2000x2000 impartido en teoría en un algoritmo Python puro de complejidad $O(n^3)$ dispararía el tiempo $T_1$ a múltiples horas, invalidando el viñeteado experimental.

Fijando $P=4$ workers (óptimo físico), fragmentación paramétrica de la matriz:

| Chunks Totales | Dimensiones de Sub-bloque | $T_p$ (segundos) | Speedup ($S_p$) |
|:---:|:---:|:---:|:---:|
| 1 | 200x200 | 21.79 s | 1.02x |
| **4** | **100x100** | **6.63 s** | **3.33x** |
| 16 | 50x50 | 6.96 s | 3.18x |
| 25 | 40x40 | 7.43 s | 2.98x |
| 64 | 25x25 | 7.08 s | 3.12x |
| 100 | 20x20 | 8.65 s | 2.56x |

---

   - c. Intentar escoger la combinación idónea entre número de procesos y chunks/medida de los chunks para que el tiempo de ejecución sea el mínimo posible. Razonar el proceso seguido, así como las decisiones tomadas.
   - d. Calcular T1, T∞, Tp, Sp y los recursos gastados para las ejecuciones del apartado 4. Utilizar estos parámetros en los razonamientos realizados y la toma de decisiones.

**Respuesta a las Tareas 4.c y 4.d:**

**4.c Decisión Idónea**: **4 Workers trabajando sobre 4 Chunks de 100x100.**
- *Razón P*: Exceder 4 workers (límite físico) incurre en graves recortes de eficiencia sin mejorar de forma significativa el tiempo global.
- *Razón Chunks*: 1 solo bloque impide derivar paralelismo efectivo. Dividir excesivamente (100 sub-bloques) ralentiza el sistema al abrumar el *throughput* del canal de comunicaciones IPC entre procesos superando la capacidad aritmética de cálculo. La partición en **4 grandes chunks** permite dar de comer exactamente 1 macro-bloque íntegro por core nativo, disipando la latencia IPC.

**4.d Desempeño Teórico (Caso Óptimo)**:
- **T1** (Secuencial Base): **22.13 s** 
- **Tp** (Paralelo Óptimo experimental logrado): **6.63 s**
- **Sp** (Speedup logrado): $T_1 / T_p = 22.13 / 6.63 =$ **3.33x**
- **T∞** (Tiempo Infinito Teórico): $\approx 1.99$ s
- **Recursos Gastados (Wasted Resources)**: Si calculamos la eficiencia paramétrica, $E_p = S_p/P = 3.33 / 4 = 83.25\%$. Por lo tanto, el *Wasted Resources* se sitúa en un ínfimo **16.75%**. Es un desempeño altísimo considerando el *overhead* nativo de serialización de objetos en Python, originado por la ideal correspondencia $1:1$ entre los 4 trozos de matriz (100x100) y los 4 hilos de hardware de nuestra CPU.

[↑ Volver al Índice](#índice)
