# Razonamiento de Distancias de Seguridad y Presupuestos Temporales (Marco ISO 13855:2024)

> [!CAUTION]
> **Aviso de Alcance y Seguridad Funcional (Disclaimer):**
> *Experimental vision-based intrusion monitoring system inspired by industrial safety-zone concepts and ISO 13855 safety-distance reasoning. Not a safety-rated protective device.*
> Este documento utiliza las ecuaciones y conceptos de la norma ISO 13855:2024 exclusivamente como **marco analítico para modelar el presupuesto de latencia ($T_1$) y dimensionar distancias de separación teóricas**. El software desarrollado es un prototipo experimental y no cuenta con certificación SIL/PL para gobernar circuitos de parada de emergencia en maquinaria industrial sin salvaguardas certificadas.

---

## 1. Presupuesto Temporal y Modelo de Separación Teórico

En aplicaciones industriales de zonas de peligro asistidas por visión artificial, la distancia mínima de separación de seguridad ($S$) entre el límite de detección y el punto peligroso de la maquinaria está gobernada por:

$$S = (K \times T) + C + C_{\text{dyn}} + Z_{\text{extra}}$$

Donde:
* **$K$:** Velocidad de aproximación del cuerpo humano (típicamente $1600\text{ mm/s}$ para aproximación transversal o $2000\text{ mm/s}$ para aproximación directa).
* **$T$:** Tiempo total de respuesta de la cadena de seguridad:
  $$T = t_1 + t_2 + t_3$$
  * $t_1$: Latencia total del pipeline de visión por computadora (adquisición + inferencia + homografía + tracking).
  * $t_2$: Tiempo de respuesta del controlador/PLC de seguridad o relé de disparo.
  * $t_3$: Tiempo de parada mecánica (*stopping performance*) de la máquina/robot.
* **$C$:** Distancia de penetración intrínseca según resolución y posición del sensor.
* **$C_{\text{dyn}}$:** Margen adicional por variabilidad dinámica del movimiento humano.
* **$Z_{\text{extra}}$:** Factor de incertidumbre de medición métrica y jitter del sensor.

### Presupuesto para el Pipeline de Visión ($t_1$)
* **Límite Normativo:** $t_1 \le 50\text{ ms}$ (tasa de refresco efectiva $\ge 20\text{ FPS}$).
* **Margen en Inferencia (Bloque 2):** Inferencia con YOLO Pose ONNX en Apple Silicon CoreML medida a $t_{\text{infer}} \le 20.5\text{ ms}$ ($p_{95}$).
* **Margen Disponible para Bloque 3:** $\approx 29.5\text{ ms}$ para captura de frame, proyección DLT, filtrado Kalman y evaluación de polígonos.

---

## 2. Anclaje Espacial Mediante Keypoints de Tobillos y Degradación Jerárquica (`AnchorSource`)

Para anular las falsas alarmas provocadas por la inclinación cenital o angular de la cámara enfrente de operadores cuyos torsos o cabezas intersectan la zona pero cuyos pies están fuera:
* **Prohibición del Centroide 2D:** Se prohíbe el centroide geométrico de la caja delimitadora (*bounding box centroid*), dado que proyecta el torso a mitad de altura fuera del plano $Z_w = 0$.
* **Jerarquía de Anclaje en Suelo (`extract_ground_anchor`, `conf_threshold = 0.5` por defecto):**
  1. **Tier 1 (`ANKLES_DUAL`):** Si ambos tobillos superan el umbral ($\text{conf} \ge 0.5$) y la altura aparente de la caja cumple $h_{\text{bbox}} \ge h_{\min}$ (`min_ankle_bbox_height`), se proyecta el punto medio con factor de confianza $\times 1.0$:
     $$p_{\text{ground}} = \frac{p_{\text{ankle-left}} + p_{\text{ankle-right}}}{2}$$
  2. **Tier 2 (`ANKLE_SINGLE`):** Si un solo tobillo es visible ($\text{conf} \ge 0.5$) y $h_{\text{bbox}} \ge h_{\min}$, se adopta dicho tobillo con penalización de confianza $\times 0.75$ e inflación de covarianza $R$ ($2.0\times$).
  3. **Tier 3 (`BBOX_BOTTOM`):** Si ambos tobillos están ocluidos ($\text{conf} < 0.5$) o el operario se encuentra en campo lejano ($h_{\text{bbox}} < h_{\min}$, ej. `min_ankle_bbox_height = 120.0`), se utiliza el borde inferior central de la caja $(\frac{x_1+x_2}{2}, y_2)$ con penalización de confianza $\times 0.40$ e inflación de covarianza de medición $R$ de $5.0\times$ ([ADR-007](../decisions/adr-007-occlusion-handling-confidence-propagation.md), [ADR-013](../decisions/adr-013-foveated-far-field-roi-inference.md)).
  4. **Tier 4 (`TRACKER_PREDICTED`):** Ante pérdida total de detección (*dropout*), el Filtro Kalman 2D extrapola la trayectoria cinemática en modo `COASTING` hasta $k \le 5$ cuadros con decaimiento de confianza $0.85^k$.

---

## 3. Matriz de Homografía Planar ($2D \rightarrow \text{Métrico}$)

Dado que el contacto con el piso ocurre en el plano de planta ($Z=0$), la relación entre las coordenadas de la imagen $(u, v)$ y el plano de trabajo $(X_w, Y_w)$ en metros es biyectiva y lineal en coordenadas homogéneas:

$$\begin{bmatrix} X_w' \\ Y_w' \\ W \end{bmatrix} = H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}, \quad X_w = \frac{X_w'}{W}, \quad Y_w = \frac{Y_w'}{W}$$

La matriz $H \in \mathbb{R}^{3 \times 3}$ se calcula con 4 puntos coplanares de calibración mediante DLT (*Direct Linear Transformation*).

---

## 4. Control de Estabilidad e Histéresis Espacio-Temporal

Para evitar *chattering* y conmutaciones erráticas en los relés de seguridad:
1. **Doble Polígono Concéntrico:**
   * $P_{\text{danger}}$: Zona de intrusión crítica que activa la parada de emergencia.
   * $P_{\text{release}}$: Polígono expandido por un margen $\Delta d \in [150, 300]\text{ mm}$. El sistema no transiciona de regreso a `OUTSIDE` hasta que los pies del operario no crucen completamente fuera de $P_{\text{release}}$.
2. **Ventana Temporal de Confirmación:**
   * Requiere $N_{\text{confirm}} \ge 3\text{–}5$ fotogramas consecutivos de persistencia para conmutar estados.
3. **Filtro Kalman 2D:**
   * Suavizado de coordenadas métricas $(X_w, Y_w, \dot{X}_w, \dot{Y}_w)$ que absorbe el jitter de detección de keypoints ($\pm 15\text{ mm}$).

---

## 5. Estrategia de Hardware & Cuantización

* **Fase 1 (Desarrollo local - Apple Silicon M1/M2/M3):**
  * Inferencia: ONNX Runtime con `CoreMLExecutionProvider` (346/354 ops delegados a ANE/GPU).
  * Fallback: `CPUExecutionProvider` con ARM NEON (4 hilos).
* **Trabajo Futuro (Validación PoC en Silicio Heterogéneo - NVIDIA GTX 1050 / Pascal CC 6.1):**
  * *Propósito:* Evaluar el comportamiento en hardware disponible diferente al entorno de desarrollo (Apple Silicon) como prueba de concepto de portabilidad.
  * *Arquitectura Pascal (Compute Capability 6.1):* El silicio de Pascal tiene penalización de rendimiento en cómputo FP16 (tasa 1:64 en FP16 vs FP32) por carecer de Tensor Cores dedicados.
  * *Estrategia Obligatoria en Pascal:* Cuantización **INT8** post-entrenamiento (PTQ) con TensorRT y dataset de calibración para alcanzar tasa de ejecución completa.

---

## 6. Salida de Datos: Abstracción Lógica vs Telemetría

* **Lazo Crítico de Seguridad (Abstracción Lógica / Mock):**
  * Emisión determinista en memoria de la señal `trip = True` en la estructura `SafetyOutput` (latencia interna $< 0.1\text{ ms}$).
  * > [!WARNING]
  * > **Aviso Crítico de Instalación:** Por tratarse de un prototipo experimental no certificado (sin homologación SIL/PL ni redundancia de canal Cat 3/4), este software **nunca** debe cablearse directamente a relés o circuitos de parada de emergencia de maquinaria peligrosa.
* **Capa Telemática (Monitoreo y Dwell Time):**
  * Telemetría estructurada JSONL/JSON en tiempo real para auditoría, análisis forense y visualización. Integración teórica con protocolos industriales (Modbus TCP, OPC UA, MQTT) para telemetría de monitoreo asistido en plantas industriales.
