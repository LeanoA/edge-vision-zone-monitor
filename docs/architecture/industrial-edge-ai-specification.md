# Diseño Arquitectónico y Especificación Técnica de un MVP de Visión Artificial en el Edge para la Detección de Intrusión y Permanencia en Zonas Industriales Restringidas

---

## 1. Marco Normativo y Fundamentos de Seguridad Industrial (ISO 13855:2024)

El desarrollo de un Producto Mínimo Viable (MVP) para la supervisión de zonas restringidas mediante visión artificial en el Edge exige un cumplimiento riguroso de los estándares internacionales de seguridad en maquinaria. En entornos industriales automatizados, los sistemas de visión computacional aplicados a la protección de operadores se categorizan como **Dispositivos de Protección Basados en Visión (VBPD, por sus siglas en inglés)**. Estos dispositivos forman parte de los **Equipos de Protección Electrosensibles (ESPE)**, cuya función principal es salvaguardar la integridad humana sin interponer barreras físicas mecánicas.

La norma internacional **ISO 13855:2024** regula el posicionamiento de los resguardos con respecto a las velocidades de aproximación del cuerpo humano, estableciendo las metodologías matemáticas para definir las distancias mínimas de separación que eviten que un trabajador alcance un punto de peligro antes de que la maquinaria logre un estado seguro. A diferencia de la normativa previa, la revisión ISO 13855:2024 introduce modelos de cálculo complejos para aproximaciones dinámicas, considerando variaciones en la posición espacial del riesgo y la dirección no predecible del cuerpo humano.

Para una aproximación dinámica con dirección humana desconocida, la distancia de separación requerida $S$ (medida en milímetros) se calcula mediante la siguiente formulación estándar:

$$S = (K \times T) + C + C_{\text{dyn}} + Z_{\text{extra}}$$

En esta ecuación:
* **$K$:** Representa la velocidad de aproximación del cuerpo o de las extremidades. La norma especifica una velocidad de $2000\text{ mm/s}$ para la aproximación de extremidades superiores y $1600\text{ mm/s}$ para la velocidad general de marcha humana.
* **$T$:** El tiempo total de respuesta del sistema (en segundos), que integra tres componentes temporales:
  $$T = t_1 + t_2 + t_3$$
  * $t_1$: Tiempo de respuesta del sistema de control relativo a la seguridad (latencia total del pipeline de visión Edge: captura, preprocesamiento, inferencia y lógica de control).
  * $t_2$: Tiempo de respuesta del controlador/PLC de seguridad o relé de disparo.
  * $t_3$: Tiempo de parada mecánica inercial de la máquina (*stopping performance*).
* **$C$:** Suplementos por distancia de alcance asociados a la geometría de la zona de protección.
* **$C_{\text{dyn}}$:** Suplemento dinámico que compensa el movimiento del punto de peligro durante el proceso de parada:
  $$C_{\text{dyn}} = v_{\text{hazard}} \times t_3 + \frac{1}{2} a_{\text{hazard}} \times t_3^2$$
  Donde $v_{\text{hazard}}$ es la velocidad inicial del peligro y $a_{\text{hazard}}$ la desaceleración mecánica.
* **$Z_{\text{extra}}$:** Margen suplementario para absorber incertidumbres de medición, errores en la calibración intrínseca/extrínseca de las cámaras, variaciones de reflectancia y degradación en el par de frenado.

La norma establece que bajo ninguna circunstancia la distancia $S$ puede ser inferior a un límite absoluto de **$100\text{ mm}$**. Por consiguiente, la latencia del software del MVP en el dispositivo Edge ($t_1$) limita de manera directa la distancia física mínima a la que se debe desplegar la *virtual fence* o barrera digital.

---

## 2. Arquitectura de Sistema y Pipeline de Procesamiento en Tiempo Real

El flujo de procesamiento para el MVP se estructura como un pipeline de baja latencia ejecutado íntegramente de forma local, erradicando la dependencia de la nube para decisiones críticas de seguridad:

1. **Ingestión de Video:** Flujos RTSP o sensores de visión decodificados en memoria unificada o VRAM (GStreamer / OpenCV).
2. **Preprocesamiento y Rectificación:** Corrección de distorsión radial y tangencial (aberraciones de barril/cojín) mediante parámetros intrínsecos de la cámara.
3. **Inferencia Neuronal:** Detección y estimación de pose cuantitativamente optimizada (`yolo11n-pose` / `yolov8n-pose` en ONNX Runtime / TensorRT).
4. **Mapeo Espacial Planar:** Transformación de perspectiva mediante matriz de homografía $H \in \mathbb{R}^{3 \times 3}$ que proyecta los tobillos/pies del operario al plano métrico del suelo ($Z=0$).
5. **Analytics Espacio-Temporales:** Máquina de Estados Finitos (FSM) con histéresis espacial (doble polígono $P_{\text{danger}}$ vs $P_{\text{release}}$) y temporal ($N_{\text{confirm}}$), suavizada con Filtro de Kalman 2D y control de *dwell time*.
6. **Interfaz de Control Industrial:** Salida por hardware directo (Relé / GPIO) para parada de emergencia, y telemática (Modbus TCP / OPC UA / MQTT JSON) para alertas preventivas y auditoría.

---

## 3. Evaluación de Arquitecturas Deep Learning y Plataformas de Cómputo Edge

### 3.1 Análisis Comparativo de Modelos

| Modelo | Parámetros (M) | FLOPs (G) | mAP 50-95 (%) | Latencia CPU ONNX (ms) | Latencia TensorRT INT8 (ms) | Plataforma Recomendada |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLOX-Nano** | 0.91 | 1.08 | 25.8 | ~18.2 | ~3.1 | Microcontroladores / Edge Low-Power |
| **YOLOv8n** | 3.2 | 8.7 | 37.3 | ~80.4 | ~4.2 | NVIDIA Jetson Nano / GTX 1050 (INT8) |
| **YOLOv11n** | 2.6 | 6.5 | 39.5 | ~56.1 | ~3.8 | NVIDIA Jetson Orin Nano / CPU Edge |
| **YOLO26n** | 2.4 | 5.8 | 39.8 | ~38.9 | ~2.9 | Procesadores Embebidos NMS-Free |
| **YOLOv8s** | 11.2 | 28.6 | 44.9 | ~128.4 | ~7.6 | NVIDIA Jetson Orin / GTX 1050 (INT8) |
| **YOLOv11s** | 9.4 | 21.5 | 47.0 | ~90.0 | ~6.1 | NVIDIA Jetson Orin Nano / Xavier NX |

### 3.2 Consideraciones de Hardware y Trampas de Implementación

* **Arquitectura NVIDIA Pascal (ej. GTX 1050, Compute Capability 6.1):**
  * *Restricción de Silicio:* Aunque Pascal tiene soporte *full-rate* para operaciones enteras **INT8**, su cómputo en **FP16** está penalizado de fábrica (*low-rate*, 1:64 respecto a FP32).
  * *Directriz Obligatoria:* Cualquier despliegue en Pascal requiere **cuantización post-entrenamiento (PTQ) a INT8** con TensorRT y dataset de calibración. En cambio, arquitecturas Ampere u Orin cuentan con Tensor Cores que aceleran FP16 e INT8 indistintamente.
* **Aceleradores Edge TPU (Google Coral):**
  * *Trampa de Ejecución Mixta:* Si la red incluye operadores no soportados nativamente por el compilador de la Edge TPU (atención compleja, DFL, NMS custom), se generan transferencias cíclicas de tensores por el bus del sistema entre la TPU y la CPU en cada fotograma, disparando la latencia de 20-30 ms a 1800-2100 ms y destruyendo el determinismo.

---

## 4. Analytics Espacio-Temporales: Homografía, Pose e Histéresis

### 4.1 Corrección de Perspectiva y Mapeo Planar

Se prohíbe el uso del centroide de cajas 2D debido a que la inclinación angular de la cámara proyecta el torso o la cabeza dentro de la zona peligrosa cuando los pies están en zona segura. El sistema extrae los keypoints de los tobillos (`left_ankle: 15`, `right_ankle: 16`) y calcula su punto medio:

$$p_{\text{ground}} = \frac{p_{\text{ankle\_left}} + p_{\text{ankle\_right}}}{2}$$

Dicho punto se proyecta al plano métrico mediante la matriz de homografía $H \in \mathbb{R}^{3 \times 3}$:

$$\begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix} \sim H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$

La calibración se realiza a partir de 4 o más puntos coplanares con coordenadas métricas conocidas en planta mediante el algoritmo Solve-PnP / DLT.

### 4.2 Lógica de Intrusión y Permanencia: Spatial FSM

Para erradicar el *flickering* en las alarmas, la FSM opera con 6 estados y doble histéresis:

```
       [ OUTSIDE ]
            │ (Entra a P_danger)
            ▼
    [ ENTER_PENDING ] ──(N_confirm completado)──► [ INTRUSION_ACTIVE ]
            │                                             │ (Dwell time > T_warn)
            │ (Sale antes de N_confirm)                   ▼
            └───────────────────────────────────► [ DWELL_WARNING ]
                                                          │ (Dwell time > T_violation)
                                                          ▼
                                                  [ DWELL_VIOLATION ]
                                                          │ (Sale de P_release)
                                                          ▼
                                                   [ EXIT_PENDING ]
                                                          │ (T_exit completado)
                                                          ▼
                                                      [ OUTSIDE ]
```

* **Histéresis Espacial:**
  $$P_{\text{release}} = P_{\text{danger}} \oplus \Delta d, \quad \Delta d \in [150, 300]\text{ mm}$$
* **Histéresis Temporal:** Requiere $N_{\text{confirm}} \ge 3\text{–}5$ fotogramas consecutivos de persistencia para conmutar a alarma.
* **Filtro Kalman 2D:** Suavizado de trayectoria métrica $(X_w, Y_w, \dot{X}_w, \dot{Y}_w)$ para filtrar vibraciones de keypoints ($\pm 15\text{ mm}$).

---

## 5. Corpus de Datasets Industriales y Data Augmentation

### 5.1 Datasets Abiertos

* **Roboflow Worker Safety:** ~4,280 imágenes (Person, Helmet, Vest). Inspección de EPIs en celdas industriales.
* **Roboflow Construction Site Safety:** 717 a 2,286 imágenes (Hardhat, Machinery, Person). Supervisión cerca de maquinaria pesada.
* **Mendeley Industrial Safety PPE:** 2,286 imágenes (Person, Safety Shoes, Gloves). Zonas con calzado obligatorio.
* **Roboflow Manufacturing & Forklift:** ~24,000 imágenes (Forklift, Worker). Prevención de atropellos en tráfico mixto.
* **MOT17 / MOT20 Benchmark:** 11,235 fotogramas. Calibración y benchmarking de rastreo multiobjeto.
* **VIRAT Video Dataset:** >100 horas de video HD. Pruebas de *dwell time* e intrusión perimetral.

### 5.2 Estrategias de Aumentación de Datos (Albumentations)

1. **Aumentación Fotométrica:** Variaciones drásticas de brillo/contraste y ruido gaussiano para simular destellos de soldadura y caídas de luz en planta.
2. **CutMix y Oclusión Sintética:** Superposición de fragmentos metálicos y barras de maquinaria para entrenar la red ante oclusiones corporales parciales.
3. **Aumentación Geométrica de Perspectiva:** Deformaciones homográficas aleatorias para inmunizar el modelo frente a diferentes ángulos de montaje de cámara.

---

## 6. Compilación, Inferencia e Integración Industrial

1. **Pipeline de Video Zero-Copy (NVIDIA DeepStream / GStreamer):** Evita transferencias entre memoria host y device, manteniendo la latencia de pre/post-procesamiento por debajo de $5\text{ ms}$.
2. **Cuantización INT8 (TensorRT PTQ):** Determinación de factores de escala $S$ y punto cero $Z$ mediante histogramas de activación con imágenes industriales reales.
3. **Salidas Industriales:**
   * **Capa Física (Relé de Seguridad / GPIO):** Disparo directo del bucle de paro de emergencia en $< 5\text{ ms}$.
   * **Automatización (Modbus TCP / OPC UA):** Desaceleración controlada y modo colaborativo en PLCs.
   * **Telemetría (MQTT / JSON):** Timestamp, Worker ID, coordenadas de intrusión y clips de video para auditoría SCADA/Cloud.

---

## 7. Referencias

1. *Safety standard EN ISO 13855 for the positioning of safeguards* — Pilz Safety Automation.
2. *Vision-Based Protective Devices* — IGI Global Research.
3. *Protective devices employing 3D safety zones on machines* — DGUV (IFA).
4. *AIOS in Practice: Setting Up a Virtual Fence for Industrial Applications* — DT Labs.
