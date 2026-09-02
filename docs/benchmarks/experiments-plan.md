# Plan de Ensayos Experimentales y Banco de Pruebas Edge AI (ISO 13855)

Este documento registra formalmente la serie de 4 ensayos experimentales diseñados para cuantificar el rendimiento, la varianza de latencia y la precisión geométrica de la arquitectura Edge AI frente a alternativas tradicionales. Servirá como base técnica y empírica para publicaciones, benchmarks y artículos de arquitectura.

---

## 🎯 Síntesis Arquitectónica: De la Red Neuronal a la Seguridad Determinista

```
                                  PIPELINE HETEROGÉNEO EN EDGE
 ┌────────────────────────┐       ┌─────────────────────────────────────────────────────────┐
 │   NPU / ANE / GPU      │       │                    CPU VECTORIZADA                      │
 │ 346/354 nodos CoreML   │       │               Álgebra Lineal + FSM C                    │
 ├────────────────────────┤       ├───────────────────────┬───────────────────┬─────────────┤
 │ Inferencia YOLO11-Pose │ ───►  │ Homografía DLT 3x3    │ Kalman + Munkres  │ Spatial FSM │
 │ (~10.5 ms)             │       │ (~0.1 ms)             │ (~0.4 ms)         │ (~0.6 ms)   │
 └────────────────────────┘       └───────────────────────┴───────────────────┴─────────────┘
                                  TOTAL LATENCIA T1 = 13.68 ms (Presupuesto ISO: 50 ms)
```

1. **Particionado de Hardware Heterogéneo:** Separación estricta entre tareas estocásticas de alto cómputo (percepción en NPU/GPU vía CoreML/TensorRT) y tareas analíticas deterministas en CPU (DLT, covarianza de innovación de Mahalanobis $\chi^2$, asignación global de Munkres y Statecharts).
2. **Determinismo sobre Redes Probabilísticas:** Puente entre predicciones continuas ruidosas y la norma ISO 13855 mediante anclajes anatómicos graduados, epísteme de ruido asimétrico en Kalman y compuertas estadísticas.

---

## 🔬 Catálogo de Ensayos Experimentales

### 🧪 Ensayo 1: Runtime Engine Showdown (PyTorch vs ONNX vs CoreML/GPU)
* **Objetivo:** Cuantificar el overhead del intérprete de PyTorch vs grafos compilados estáticos en ONNX Runtime con proveedores de hardware (CPU vs CoreML/ANE).
* **Variantes a Comparar:**
  1. `PyTorch Eager (CPU)`: Inferencia estándar con `torch.inference_mode()`.
  2. `PyTorch Eager (MPS / GPU)`: Inferencia sobre Metal Performance Shaders.
  3. `ONNX Runtime (CPUExecutionProvider)`: Grafo ONNX en CPU x86/ARM con multi-threading.
  4. `ONNX Runtime (CoreMLExecutionProvider)`: Grafo ONNX compilado para Apple Neural Engine y GPU.
* **Métricas Clave:**
  * Latencia Media ($\text{ms}$), Mediana ($p50$), Percentiles críticos ($p95$, $p99$).
  * **Jitter y Varianza Temporal ($\sigma^2$, $\text{IQR}$):** Estabilidad del frame time (esencial en safety para evitar violaciones de deadline).
  * Throughput sostenido ($\text{FPS}$).

---

### 🧪 Ensayo 2: Precisión Geométrica vs Cuantización (FP32 vs FP16 vs INT8)
* **Objetivo:** Evaluar si la aceleración por cuantización numérica degrada la localización métrica de los tobillos en campo lejano ($Y_w > 12\text{m}$).
* **Variantes a Comparar:**
  1. Modelo Baseline `FP32` ($640 \times 640$).
  2. Modelo Semiprecisión `FP16`.
  3. Modelo Cuantizado `INT8` (Post-Training Quantization / Dynamic Range Quantization).
* **Métricas Clave:**
  * Speedup de inferencia ($\times$).
  * Error cuadrático medio de posición métrica en suelo ($RMSE_{XY}$ en centímetros).
  * Desviación máxima angular y métrica al proyectar por la matriz de homografía $H$.

---

### 🧪 Ensayo 3: Ablation Study de Tracking Multiobjetivo (MOT)
* **Objetivo:** Demostrar cuantitativamente la eliminación de *ID Switching* y *Ghost Tracks* lograda en ADR-011.
* **Variantes a Comparar:**
  1. `Baseline Antiguo`: Asignación codiciosa euclidiana ($d \le 1.0\text{m}$) sin Spatial Birth NMS.
  2. `Core Optimizado (ADR-011)`: Covarianza de innovación $S_i$, Compuerta de Mahalanobis $\chi^2_2(0.99) \le 9.210$, Algoritmo Húngaro global y Spatial Birth NMS ($0.6\text{m}$).
* **Dataset:** `pets2009_s2_l1` (795 cuadros con múltiples cruces peatonales densos).
* **Métricas Clave:**
  * Conteo absoluto de *ID Switches* ($IDS$).
  * Tasa de tracks fantasma / propuestas duplicadas concurrentes ($N_{\text{ghost}}$).
  * Continuidad media de trayectorias ($MOTA$ / $IDF1$).

---

### 🧪 Ensayo 4: Perfil de Reacción de Seguridad ISO 13855 ($T_{\text{system}}$ vs $T_{\text{event}}$)
* **Objetivo:** Medir el retraso físico real entre la penetración de la zona de peligro y la emisión del comando de parada `TRIP / LOCKOUT`.
* **Variantes a Comparar:**
  1. Incursión lenta normal ($v \approx 0.8\text{ m/s}$) con filtro debounce de $N_{\text{confirm}} = 3$.
  2. Incursión rápida intempestiva ($v_n \ge 1.6\text{ m/s}$) con **Bypass Dinámico de Debounce** (ADR-006).
* **Métricas Clave:**
  * Tiempo físico de disparo $T_{\text{event}}$ ($\text{ms}$).
  * Distancia de penetración antes del disparo $D_{\text{penetration}}$ ($\text{cm}$).
  * Cumplimiento estricto de la ecuación de distancia mínima $S = (K \times T) + C$.
