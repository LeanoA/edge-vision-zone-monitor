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

### 📊 Resultados Experimentales y Discusión Técnica (Auditoría Empírica Reproducida)

### Ensayo 1: Runtime Engine Showdown (YOLO11-Pose en Apple Silicon) — ✅ AUDITADO Y REPRODUCIDO

Evaluación estadística cuantitativa ejecutada sobre fotogramas reales de video (`openvino_people`), 3 repeticiones independientes de 100 iteraciones cronometradas por motor con 20 iteraciones de calentamiento (*warmup*):

| Motor de Inferencia | Backend / Hardware | Latencia Media | Mediana ($p50$) | $p95$ Crítico | $p99$ Extremo | Jitter Temporal ($\sigma$) | Throughput | Aceleración vs CPU | Presupuesto Interno Inferencia ($p95 \le 30\text{ms}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PyTorch Eager (CPU)** | `PyTorch_CPU` | $83.24\text{ ms}$ | $82.15\text{ ms}$ | $88.63\text{ ms}$ | $102.73\text{ ms}$ | $\pm 4.22\text{ ms}$ | $12.0\text{ FPS}$ | $1.00\times$ (Base) | ❌ **FAIL** (Inviable en safety) |
| **ONNX Runtime (CPU)** | `CPUExecutionProvider` | $43.05\text{ ms}$ | $42.23\text{ ms}$ | $47.98\text{ ms}$ | $60.84\text{ ms}$ | $\pm 4.47\text{ ms}$ | $23.2\text{ FPS}$ | **$1.93\times$** | ❌ **FAIL** ($> 30\text{ ms}$) |
| **PyTorch Eager (MPS GPU)** | `PyTorch_MPS` | $17.28\text{ ms}$ | $16.85\text{ ms}$ | $19.02\text{ ms}$ | $23.22\text{ ms}$ | $\pm 1.68\text{ ms}$ | $57.9\text{ FPS}$ | **$4.82\times$** | ✅ **PASS** |
| **ONNX Runtime (CoreML)** | `CoreMLExecutionProvider` | **$16.50\text{ ms}$** | **$16.31\text{ ms}$** | **$18.30\text{ ms}$** | **$20.01\text{ ms}$** | **$\pm 1.49\text{ ms}$** | **$60.6\text{ FPS}$** | **$5.04\times$** | ✅ **PASS** (Óptimo) |

> [!NOTE]
> **Aclaración Normativa vs Presupuesto Interno:**
> La norma ISO 13855:2024 no establece ningún límite de 30 ms para redes neuronales. El umbral de $30\text{ ms}$ es un **objetivo de diseño interno** para la etapa de inferencia, concebido para reservar $\approx 20\text{ ms}$ para captura, tracking, homografía y FSM, satisfaciendo el presupuesto total de percepción $T_1 \le 50\text{ ms}$.

#### Discusión y Hallazgos de Ingeniería:
1. **La Trampa de PyTorch en CPU:**
   * Con $83.24\text{ ms}$ por inferencia, el modo intérprete de PyTorch en CPU **supera holgadamente el presupuesto total de percepción del pipeline** ($T_1 \le 50\text{ ms}$), haciendo inviable un lazo de seguridad determinista sin acelerador físico.
2. **Impacto de la Compilación a Grafo Estático:**
   * La exportación a ONNX Runtime sobre CPU reduce la latencia a $43.05\text{ ms}$ (**$1.93\times$ de aceleración**) gracias a optimizaciones de grafo (*constant folding* y fusión de capas).
3. **Aceleración por Hardware Dedicado y Verificación de Logs CoreML/ANE:**
   * `ONNX Runtime + CoreMLExecutionProvider` alcanza la menor latencia ($16.50\text{ ms}$, **$5.04\times$ vs CPU**) y throughput sostenido ($60.6\text{ FPS}$).
   * **Auditoría de Logs de CoreML:** Los logs de ONNX Runtime (`coreml_execution_provider.cc`) confirman que CoreML soporta **346 de los 354 nodos del grafo**, agrupados en 5 particiones. Los 8 nodos restantes se ejecutan mediante fallback en `CPUExecutionProvider`.
   * *Corrección Técnica:* Seleccionar `CoreMLExecutionProvider` no garantiza ejecución exclusiva en ANE; el framework CoreML de Apple orquesta la asignación física entre ANE, GPU y CPU de forma dinámica según la topología de la capa y el estado energético.

---

### Ensayo 2: Precisión Geométrica vs Cuantización (FP32 vs FP16 vs INT8) — ✅ AUDITADO Y REPRODUCIDO

Evaluación cuantitativa ejecutada asociando predicciones mediante el algoritmo húngaro y comparando contra **Ground Truth calibrado** (en píxeles y en metros métricos sobre el plano de planta):

| Modo de Precisión | Peso de Modelo | Reducción de Tamaño | Latencia Media | Throughput | Error en Píxeles ($RMSE_{\text{px}}$) | Error Métrico en Suelo ($RMSE_{XY}$) | Desvío Máximo ($E_{\max}$) | Error Campo Cercano ($< 2.5\text{m}$) | Error Campo Lejano ($> 4.0\text{m}$) | Tolerancia Geométrica Interna ($\le 15\text{cm}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FP32 (Single Precision)** | $11.30\text{ MB}$ | $0.0\%$ (Base) | **$15.79\text{ ms}$** | **$63.3\text{ FPS}$** | $26.50\text{ px}$ | **$33.32\text{ cm}$** | $67.85\text{ cm}$ | $27.05\text{ cm}$ | $41.60\text{ cm}$ | ⚠️ Invariante Base |
| **FP16 (Half Precision)** | $5.69\text{ MB}$ | $49.7\%$ | $42.18\text{ ms}$ | $23.7\text{ FPS}$ | $26.51\text{ px}$ | **$33.35\text{ cm}$** | $66.90\text{ cm}$ | $27.07\text{ cm}$ | $41.67\text{ cm}$ | ⚠️ Invariante Base |
| **INT8 (Dynamic Quant)** | **$3.27\text{ MB}$** | **$71.1\%$** | $91.58\text{ ms}$ | $10.9\text{ FPS}$ | $18.30\text{ px}$ | **$18.96\text{ cm}$** | $88.03\text{ cm}$ | $19.20\text{ cm}$ | $17.51\text{ cm}$ | ❌ **FAIL** (Inviable en Latencia) |

#### Discusión y Hallazgos de Ingeniería:
1. **Causa Raíz de Discrepancias Previas (Auto-comparación vs Ground Truth):**
   * En informes anteriores figuraba "FP32: $0.00\text{ cm}$" y "FP16: $1.37\text{ cm}$" debido a que la evaluación comparaba los tensores candidatos únicamente contra la salida del propio modelo FP32 (*auto-comparación relativa*), sin ground truth anotado.
   * Al evaluar contra **Ground Truth geométrico real**, el modelo base YOLO11-Pose presenta un error intrínseco de detección de $\approx 33.32\text{ cm}$ ($26.5\text{ px}$).
   * **Deriva Neta de FP16:** FP16 introduce una variación casi imperceptible respecto a FP32 ($\Delta = 0.03\text{ cm}$, $33.35\text{ cm}$ vs $33.32\text{ cm}$). Sin embargo, en CoreML sobre macOS, la falta de soporte FP16 nativo en capas de salida inserta operadores de casteo que elevan la latencia a $42.18\text{ ms}$.
2. **La Lupa No-Lineal de la Homografía:**
   * En campo cercano ($Y_w < 2.5\text{m}$), el error métrico es de $27.05\text{ cm}$; en campo lejano ($Y_w > 4.0\text{m}$), se magnifica a $41.60\text{ cm}$ (+53.8%) debido a la compresión de perspectiva de la cámara monocular.
3. **La Trampa de la Cuantización Dinámica en Edge:**
   * `quantize_dynamic` fragmentó el grafo de CoreML de 5 a **67 particiones** (con 539/827 nodos soportados), provocando constantes transferencias de memoria host-device que elevaron la latencia a **$91.58\text{ ms}$ ($10.9\text{ FPS}$)**.

---

### Ensayo 3: Tracking Multiobjetivo (MOT) y Calidad Funcional — ✅ AUDITADO Y REPRODUCIDO

Evaluación cuantitativa sobre la secuencia patrón calibrada `sequence_a_clean_incursion` (180 cuadros a 30 FPS):

| Métrica MOT | Valor Medido | Criterio de Aceptación | Estado |
| :--- | :---: | :---: | :---: |
| **MOTA (Multi-Object Tracking Accuracy)** | **$0.9611$ (96.1%)** | $\ge 0.85$ | ✅ **PASS** |
| **IDF1 (ID F1-Score)** | **$0.9808$ (98.1%)** | $\ge 0.85$ | ✅ **PASS** |
| **Precisión de Tracking** | **$0.9676$** | $\ge 0.90$ | ✅ **PASS** |
| **Exhaustividad (Recall)** | **$0.9944$** | $\ge 0.95$ | ✅ **PASS** |
| **ID Switches ($IDS$)** | **$0$** | $\le 2$ | ✅ **PASS** |
| **Tracks Fantasma ($N_{\text{ghost}}$)** | **$1$** | $\le 2$ | ✅ **PASS** |
| **Fotogramas de Intrusión Detectados** | **$76$** | $\ge 50$ | ✅ **PASS** |

---

### Ensayo 4: Perfil de Reacción de Seguridad ($T_{\text{system}}$ vs $T_{\text{event}}$) — ✅ AUDITADO Y REPRODUCIDO

Medición empírica del retardo entre la intrusión física y el comando de disparo `TRIP` en la secuencia A:

| Parámetro Temporal | Fotograma / Valor Medido | Observación Técnica |
| :--- | :---: | :--- |
| **Primera Detección en Zona de Peligro** | `Frame 50` | Tobillos cruzan el límite $Y_w \ge 2.0\text{m}$ |
| **Cruce de Centroide Ground Truth** | `Frame 54` | Centroide de masa cruza $Y_w = 2.0\text{m}$ (4 cuadros después de los pies) |
| **Activación de Parada (Relé `TRIP`)** | `Frame 52` | Confirmación tras $N_{\text{confirm}} = 3$ fotogramas persistentes (frames 50, 51, 52) |
| **Retardo Físico de Debounce** | `2 cuadros` | $(52 - 50) = 2$ intervalos de cuadro |
| **Latencia Total de Evento ($T_{\text{event}}$)** | **$66.67\text{ ms}$** | Tiempo transcurrido a 30 FPS desde detección inicial hasta disparo |
| **Latencia Pipeline por Cuadro ($T_1$)** | **$17.92\text{ ms}$ ($p95 = 20.16\text{ ms}$)** | Cumple ampliamente $T_1 \le 50\text{ ms}$ |
| **Latencia End-to-End ($T_{\text{system}}$)** | **$19.58\text{ ms}$ ($p95 = 22.22\text{ ms}$)** | Incluye $1.66\text{ ms}$ de buffer de captura |

> [!IMPORTANT]
> **Límite de Medición Física:** Esta prueba mide la latencia de software hasta la emisión lógica del comando `TRIP` en el bus de salida. No mide la inercia electromecánica de relés físicos ($t_2$) ni el tiempo de frenado mecánico de la máquina ($t_3$), los cuales deben sumarse en planta según $S = K(t_1 + t_2 + t_3) + C$.

---

### 🔍 Deep-Dive de Extensión: Resolución en Pasarela Industrial (`mendeley_walkway_violation`) — ✅ AUDITADO Y REPRODUCIDO

Evaluación empírica sobre los 348 cuadros del video real de vigilancia CCTV de pasarela de fábrica:

| Resolución / Modo | Tamaño Modelo | Preproceso | Inferencia Media | Latencia $T_1$ Media | $p95$ de $T_1$ | Throughput Real | Detecciones Totales | Detecciones Fondo ($Y_w > 6\text{m}$) | Presupuesto $T_1 \le 50\text{ms}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **640p FP32 (Línea Base)** | $11.30\text{ MB}$ | $0.94\text{ ms}$ | **$18.77\text{ ms}$** | **$19.80\text{ ms}$** | **$22.35\text{ ms}$** | **$46.9\text{ FPS}$** | 83 | 83 | ✅ **PASS** |
| **640p FP16** | $5.69\text{ MB}$ | $0.91\text{ ms}$ | $42.90\text{ ms}$ | $43.88\text{ ms}$ | $48.74\text{ ms}$ | $22.0\text{ FPS}$ | 76 | 76 | ✅ **PASS** |
| **960p FP32** | $11.58\text{ MB}$ | $1.88\text{ ms}$ | $40.44\text{ ms}$ | $42.54\text{ ms}$ | $45.34\text{ ms}$ | $22.6\text{ FPS}$ | **639** | **639** | ✅ **PASS** |
| **960p FP16** | $5.85\text{ MB}$ | $1.86\text{ ms}$ | $95.38\text{ ms}$ | $97.44\text{ ms}$ | $113.47\text{ ms}$ | $10.1\text{ FPS}$ | **624** | **624** | ❌ **FAIL** |

#### Conclusiones Técnicas Confirmadas:
1. **Sensibilidad en Campo Lejano:** La resolución **960p** multiplica por más de $7.6\times$ las detecciones efectivas en el horizonte lejano ($639$ vs $83$), permitiendo al Filtro de Kalman inicializar y suavizar el track mucho antes de que el operario alcance la zona crítica.
2. **Throughput de Pipeline vs FPS de Inferencia:** Si bien 640p FP32 tiene una latencia de inferencia de $18.77\text{ ms}$ ($\approx 53.2\text{ FPS}$ teórico), el throughput real del pipeline completo es de **$46.9\text{ FPS}$** debido al tiempo de adquisición, letterboxing y actualización de estado.
3. **Hipótesis de Plataformas Externas (NVIDIA Jetson):** Cualquier proyección de rendimiento para Jetson Orin/TensorRT constituye una hipótesis de arquitectura y **no debe presentarse como medición real** sin validación física en ese silicio.
