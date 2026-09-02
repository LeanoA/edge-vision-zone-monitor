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

---

## 📊 Resultados Experimentales y Discusión Técnica

### Ensayo 1: Runtime Engine Showdown (YOLO11-Pose en Apple Silicon) — ✅ EJECUTADO

Evaluación estadística cuantitativa ejecutada sobre 100 iteraciones cronometradas por motor con 20 iteraciones de calentamiento (*warmup*):

| Motor de Inferencia | Backend / Hardware | Latencia Media | Mediana ($p50$) | $p95$ Crítico | $p99$ Extremo | Jitter Temporal ($\sigma$) | Throughput | Aceleración vs CPU | Cumple ISO 13855 ($p95 \le 30\text{ms}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PyTorch Eager (CPU)** | `PyTorch_CPU` | $70.80\text{ ms}$ | $69.86\text{ ms}$ | $75.11\text{ ms}$ | $75.91\text{ ms}$ | $\pm 1.96\text{ ms}$ | $14.1\text{ FPS}$ | $1.00\times$ (Base) | ❌ **FAIL** (Inviable en safety) |
| **ONNX Runtime (CPU)** | `CPUExecutionProvider` | $40.54\text{ ms}$ | $39.92\text{ ms}$ | $44.72\text{ ms}$ | $48.18\text{ ms}$ | $\pm 2.04\text{ ms}$ | $24.7\text{ FPS}$ | **$1.75\times$** | ❌ **FAIL** ($> 30\text{ ms}$) |
| **PyTorch Eager (MPS GPU)** | `PyTorch_MPS` | $17.63\text{ ms}$ | $17.00\text{ ms}$ | $20.82\text{ ms}$ | $22.75\text{ ms}$ | $\pm 1.67\text{ ms}$ | $56.7\text{ FPS}$ | **$4.02\times$** | ✅ **PASS** |
| **ONNX Runtime (CoreML)** | `CoreMLExecutionProvider` | **$15.81\text{ ms}$** | **$15.88\text{ ms}$** | **$19.02\text{ ms}$** | **$20.88\text{ ms}$** | **$\pm 1.79\text{ ms}$** | **$63.3\text{ FPS}$** | **$4.48\times$** | ✅ **PASS** (Óptimo) |

#### Discusión y Hallazgos de Ingeniería:
1. **La Trampa de PyTorch en CPU:**
   * Con $70.80\text{ ms}$ por inferencia, el modo intérprete de PyTorch en CPU **consume por sí solo más del 140% del presupuesto total de seguridad industrial** ($T_1 \le 50\text{ ms}$ según ISO 13855 / IEC 61496), dejando cero margen para tracking, homografía y actuación electromecánica de relés.
2. **Impacto de la Compilación a Grafo Estático:**
   * La simple exportación a ONNX Runtime sobre CPU reduce la latencia de $70.80\text{ ms} \to 40.54\text{ ms}$ (**$1.75\times$ más rápido**) debido a la optimización de grafos (*constant folding*, fusión de capas Conv+BatchNorm y eliminación de overhead del runtime de Python).
3. **Aceleración por Hardware Dedicado (NPU vs GPU):**
   * `ONNX Runtime + CoreMLExecutionProvider` alcanza la menor latencia ($15.81\text{ ms}$, **$4.48\times$ más veloz**) y el mayor throughput ($63.3\text{ FPS}$).
   * **Ventaja de Particionado:** CoreML compila 346 de los 354 nodos de la red directamente en el **Apple Neural Engine (ANE)**, liberando los núcleos de CPU y GPU para ejecutar en paralelo la proyección homográfica, el Filtro de Kalman y el autómata Statecharts sin competencia de recursos.

---

### Ensayo 2: Precisión Geométrica vs Cuantización (FP32 vs FP16 vs INT8) — ✅ EJECUTADO

Evaluación cuantitativa de compresión, latencia y distorsión geométrica en el plano del suelo ($Z_w = 0$) proyectada a través de la matriz de homografía $H$:

| Modo de Precisión | Peso de Modelo | Reducción de Tamaño | Latencia Media | Throughput | Error en Píxeles ($RMSE_{\text{px}}$) | Error Métrico en Suelo ($RMSE_{XY}$) | Desvío Máximo ($E_{\max}$) | Tolerancia ISO 13855 ($RMSE \le 15\text{cm}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FP32 (Single Precision)** | $11.30\text{ MB}$ | $0.0\%$ (Base) | **$13.85\text{ ms}$** | **$72.2\text{ FPS}$** | $0.00\text{ px}$ | **$0.00\text{ cm}$** | $0.00\text{ cm}$ | ✅ **PASS** (Gold Standard) |
| **FP16 (Half Precision)** | $5.69\text{ MB}$ | $49.6\%$ | $42.49\text{ ms}$ | $23.5\text{ FPS}$ | **$0.45\text{ px}$** | **$2.15\text{ cm}$** | $43.45\text{ cm}$ | ✅ **PASS** (Geométricamente Seguro) |
| **INT8 (Dynamic Quant)** | **$3.27\text{ MB}$** | **$71.1\%$** | $97.50\text{ ms}$ | $10.3\text{ FPS}$ | $34.82\text{ px}$ | **$275.12\text{ cm}$** | $> 3000\text{ cm}$ | ❌ **FAIL** (Inviable en Safety) |

#### Discusión y Hallazgos de Ingeniería:
1. **La Lupa No-Lineal de la Homografía:**
   * Un error en apariencia "pequeño" de $34.8\text{ px}$ en el espacio de imagen se convierte en un **error catastrófico de $2.75\text{ metros}$ en el plano métrico de la fábrica**.
   * En visión perspectiva, la compresión de profundidad en el campo lejano ($Y_w > 12\text{m}$) magnifica el error de píxeles por un factor de hasta $50\times$. Por eso, evaluar cuantización solo con métricas mAP o IoU 2D es un error grave en aplicaciones de seguridad física.
2. **La Trampa de la Cuantización Dinámica en Aceleradores Edge:**
   * La cuantización dinámica ingenua (`quantize_dynamic`) inserta operadores intercalados de cuantización/descuantización en tiempo de ejecución. Esto **fragmentó el grafo compilado de CoreML de 5 particiones a 67 particiones**, destruyendo la fusión de capas en el Neural Engine y ralentizando la inferencia ($97.5\text{ ms}$) en lugar de acelerarla.
3. **Veredicto Arquitectónico:**
   * **FP32 es la opción óptima absoluta** en Apple Silicon: ofrece la mayor velocidad ($13.85\text{ ms}$ / $72.2\text{ FPS}$) porque se compila de manera monolítica y directa en el ANE con **cero distorsión espacial**.
   * **FP16** es viable para reducir un $50\%$ de memoria flash si se requiere en microcontroladores, manteniendo el error métrico en apenas $2.15\text{ cm}$.
   * **INT8** solo debe aplicarse mediante *Quantization-Aware Training (QAT)* o calibración estática post-entrenamiento (PTQ con tabla de calibración representativa de planta), nunca con cuantización dinámica pura.
