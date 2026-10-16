# Bitácora de Conceptos Clave, Preguntas & Respuestas de Arquitectura

Este documento recopila las discusiones técnicas, preguntas fundamentales y fundamentos de ingeniería analizados a lo largo del diseño del proyecto **Industrial Edge Safety Guard**. Su propósito es servir como material de estudio y referencia para comprender el *por qué* detrás de cada decisión técnica.

---

## 1. Hardware y Aceleración Edge

### P1: ¿Por qué desarrollamos con ONNX Runtime en lugar de TensorRT en la máquina local?
* **Contexto:** La máquina de desarrollo es un Mac con Apple Silicon (M1 arm64).
* **Fundamento Técnico:**
  * **Incompatibilidad Física:** TensorRT es software propietario de NVIDIA acoplado a la arquitectura CUDA; no existe ni puede ejecutarse en Apple Silicon.
  * **Desacoplamiento Arquitectónico:** ONNX (*Open Neural Network Exchange*) actúa como capa de abstracción intermedia. Al encapsular la inferencia en la clase `OnnxEngine`, la lógica de negocio (homografía, FSM, tracking) no sabe ni le importa qué hardware corre debajo.
  * **Rendimiento Nativo:** En macOS, ONNX Runtime delega mediante `CoreMLExecutionProvider` en el Apple Neural Engine (ANE) y GPU de Apple, logrando latencias de inferencia de $\approx 18\text{–}20\text{ ms}$ ($>54\text{ FPS}$).
  * **Portabilidad:** Cuando el código se traslade a un nodo industrial con GPU NVIDIA (ej. GTX 1050 / Jetson), solo se cambia el Execution Provider a `CUDAExecutionProvider` o TensorRT sin alterar una sola línea de código del sistema.

### P2: ¿Por qué la NVIDIA GTX 1050 (arquitectura Pascal) exige cuantización obligatoria a INT8 y prohíbe FP16?
* **Contexto:** Se planeó como prueba de concepto (PoC) evaluar el sistema en una notebook disponible con GPU NVIDIA GTX 1050 (arquitectura Pascal CC 6.1) para contrastar la portabilidad en silicio heterogéneo fuera de Apple Silicon. Dicha evaluación queda proyectada como trabajo futuro.
* **Fundamento Técnico:**
  * **Restricción de Silicio (Compute Capability 6.1):** Las GPUs basadas en Pascal no poseen Tensor Cores dedicados. A nivel de silicio, las operaciones en coma flotante de media precisión (**FP16**) están penalizadas de fábrica a una tasa de $1:64$ en comparación con precisión simple (**FP32**). Correr en FP16 en Pascal degrada el rendimiento drásticamente.
  * **Soporte Full-Rate INT8:** Pascal sí soporta instrucciones escalares de enteros de 8 bits (**INT8**) a tasa completa (*full-rate*).
  * **Conclusión de Ingeniería:** Para lograr alta velocidad en una GTX 1050 con TensorRT como trabajo futuro, es mandatorio realizar **cuantización post-entrenamiento (PTQ) a INT8** utilizando un dataset de calibración para generar los factores de escala dinámicos.

---

## 2. Visión por Computadora & Proyección Homográfica

### P3: ¿Por qué no se pueden medir distancias en metros usando una regla de tres directa sobre los píxeles de una cámara inclinada?
* **Contexto:** Las cámaras de seguridad industrial se instalan en posiciones elevadas inclinadas en ángulo hacia el suelo.
* **Fundamento Técnico:**
  * **Deformación Proyectiva y Puntos de Fuga:** La proyección de perspectiva en una cámara no conserva distancias euclidianas ni paralelismo. Las líneas paralelas en el mundo real convergen hacia puntos de fuga en el plano de la imagen.
  * **No linealidad:** Diez píxeles en la parte inferior del encuadre (cerca de la cámara) pueden equivaler a $15\text{ cm}$ en el suelo, mientras que esos mismos diez píxeles cerca del horizonte superior equivalen a $3\text{ metros}$. Cualquier interpolación lineal o regla de tres genera errores métricos catastróficos que invalidan el cumplimiento de distancias de seguridad.

### P4: ¿Por qué usamos una Matriz de Homografía 2D ($3 \times 3$) y no necesitamos calcular el eje $Z$ (profundidad 3D)?
* **Contexto:** Tradicionalmente se cree que para conocer la posición en el mundo real se necesita una cámara 3D o estimar el eje $Z$.
* **Fundamento Técnico (El truco maestro de la arquitectura):**
  * **Pérdida de Dimensión en Cámaras 2D:** Una cámara monocular proyecta puntos 3D $(X, Y, Z)$ a píxeles 2D $(u, v)$, perdiendo la profundidad (infinitos puntos a lo largo del rayo proyectan al mismo píxel).
  * **La Restricción Planar ($Z_w = 0$):** Como el sistema utiliza estimación de pose humana para detectar **los tobillos y pies del operario**, sabemos físicamente que ese punto está en contacto con el suelo. Si definimos nuestro sistema de coordenadas del mundo en el plano del piso, fijamos **$Z_w = 0$**.
  * **Colapso de la Matriz de Cámara:** En la matriz de proyección general de cámara ($3 \times 4$):
    $$\begin{bmatrix} u \\ v \\ 1 \end{bmatrix} \sim \begin{bmatrix} p_{11} & p_{12} & p_{13} & p_{14} \\ p_{21} & p_{22} & p_{23} & p_{24} \\ p_{31} & p_{32} & p_{33} & p_{34} \end{bmatrix} \begin{bmatrix} X_w \\ Y_w \\ \mathbf{0} \\ 1 \end{bmatrix}$$
    Al multiplicarse la tercera columna ($p_{i3}$) por cero, dicha columna se anula por completo:
    $$\begin{bmatrix} u \\ v \\ 1 \end{bmatrix} \sim \underbrace{\begin{bmatrix} p_{11} & p_{12} & p_{14} \\ p_{21} & p_{22} & p_{24} \\ p_{31} & p_{32} & p_{34} \end{bmatrix}}_{H \ (3 \times 3)} \begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix}$$
  * **Biyectividad e Inversión:** La matriz resultante $H \in \mathbb{R}^{3 \times 3}$ es cuadrada, no singular e invertible. Nos permite mapear de forma exacta y bidireccional el plano de la imagen con el plano del suelo ($X_w, Y_w = H^{-1} \cdot [u, v, 1]^T$) mediante álgebra lineal pura en $<0.1\text{ ms}$, sin necesidad de sensores LiDAR ni cámaras estéreo de alto costo.

### P5: ¿Por qué se necesitan exactamente 4 puntos para calibrar la Homografía?
* **Fundamento Técnico:**
  * Una matriz de $3 \times 3$ posee 9 coeficientes.
  * Sin embargo, al operar en coordenadas proyectivas homogéneas, la matriz está definida salvo un factor de escala arbitrario $\lambda$ ($H$ y $\lambda H$ representan la misma transformación geométrica). Por lo tanto, tiene $9 - 1 = \mathbf{8\text{ grados de libertad}}$.
  * Cada par de puntos calibrados $(u_i, v_i) \rightarrow (X_i, Y_i)$ aporta dos ecuaciones algebraicas lineales independientes (una para la coordenada $X$ y otra para $Y$).
  * Para resolver 8 incógnitas necesitamos 8 ecuaciones:
    $$4\text{ puntos} \times 2\text{ ecuaciones/punto} = 8\text{ ecuaciones}$$
  * Con **4 puntos de referencia coplanares (no colineales)** marcados en el suelo, el algoritmo DLT (*Direct Linear Transformation*) calcula la matriz de forma unívoca y exacta.

### P6: ¿Por qué no usamos el borde inferior de una Bounding Box (Bottom-Center) y qué costos acarrea Pose?
* **Fundamento Técnico y Trade-Off:**
  * **El Baseline de Detección:** El enfoque tradicional de bajo costo no es el centroide 2D (que proyecta el torso), sino la base central de la caja delimitadora:
    $$p_{\text{ground-bbox}} = \left( \frac{x_{\min} + x_{\max}}{2}, y_{\max} \right)$$
  * **Por qué Pose ofrece mejor semántica:** En cámaras con ángulo cenital, el punto medio de los tobillos detecta exactamente el apoyo físico de las extremidades inferiores en el piso ($Z_w = 0$). Si el operario se inclina, estira un brazo o manipula una herramienta larga, el bounding box crece lateralmente o hacia abajo de forma artificial, mientras que los tobillos permanecen anclados al suelo real.
  * **El Costo y los Riesgos Ocultos de Pose:**
    1. *Costo Computacional:* Un modelo de Pose tiene mayor número de capas/canales de salida, requiriendo más cómputo y memoria que un detector simple de cajas.
    2. *Oclusiones Frecuentes:* En un entorno industrial, los tobillos sufren oclusiones constantes por maquinaria baja, pallets, carretillas o ropa de trabajo holgada.
    3. *Borde del Encuadre:* Si el operario camina cerca del borde inferior de la cámara, los pies pueden quedar fuera de la imagen mientras el torso sigue dentro.
    4. *Degradación de Confianza:* Cuando la confianza del keypoint decae, el sistema debe degradar a modo *coasting* (Kalman) o apoyarse en el tobillo visible.
  * **Hipótesis Experimental:** Pose se adopta como hipótesis primaria por su valor anatómico, pero se mantiene la comparación contra Bbox Bottom-Center como experimento abierto para medir si la ganancia en fidelidad geométrica compensa la tasa de oclusión y la sobrecarga computacional.

### P8: ¿Por qué con exactamente $N=4$ puntos el error de reproyección es siempre 0 y cómo se mide un error real?
* **Fundamento Técnico:**
  * En geometría proyectiva, 4 pares de puntos no colineales en el plano aportan exactamente 8 ecuaciones lineales independientes para 8 grados de libertad.
  * El sistema lineal no homogéneo resultante es determinado ($8 \times 8$), por lo que existe una solución única exacta con residuo algebraico nulo.
  * Si se introducen pequeños errores o ruido a cualquiera de los 4 puntos, el algoritmo DLT simplemente calcula la matriz $H$ que mapea con exactitud esos puntos ruidosos (residuo $\text{RMSE} = 0$).
  * Para medir y auditar el error de reproyección real ($\text{RMSE} > 0$) de una cámara en planta, el sistema de calibración debe ser **sobredeterminado ($N > 4$)** o contrastarse contra puntos de verificación independientes (*ground-truth* no usados en el ajuste).

### P9: ¿Cómo se detecta degeneración geométrica en $N > 4$ puntos sin rechazar marcadores en líneas rectas?
* **Fundamento Técnico:**
  * En un cuadrilátero ($N = 4$), si cualquier triplete de puntos es colineal ($\text{Area} \approx 0$), el polígono colapsa en un triángulo o línea y la matriz $H$ es singular.
  * Sin embargo, si en planta se calibran $N = 8$ puntos a lo largo del perímetro de un rectángulo (ej. 3 puntos en el borde inferior), esos 3 puntos *son* colineales entre sí. Rechazar la calibración por tener un triplete colineal sería un error de diseño (falso rechazo).
  * **Regla Arquitectónica:** Para $N = 4$, ningún triplete puede ser colineal. Para $N > 4$, la condición necesaria y suficiente es que el rango afín sea pleno ($\text{rank}=3$) y que **exista al menos un subconjunto de 4 puntos en posición general** (ningún triplete colineal en ese cuadrilátero).

---

## 3. Dinámica Temporal & Seguridad Funcional

### P7: ¿Cómo se previene el "chattering" o conmutación errática en los relés de seguridad?
* **Fundamento Técnico:**
  * Si un operario trabaja o camina justo sobre el límite de la zona restringida, el ruido estocástico de detección ($\pm 15\text{ mm}$) haría que un algoritmo simple conmute de alarma a seguro frame a frame (destruyendo contactores físicos y generando alarmas inútiles).
  * **Solución de Tres Niveles:**
    1. **Filtro de Kalman 2D:** Suaviza la trayectoria $(X_w, Y_w, \dot{X}_w, \dot{Y}_w)$ en el plano métrico, absorbiendo las vibraciones de los keypoints.
    2. **Histéresis Espacial:** Se configuran dos polígonos concéntricos: $P_{\text{danger}}$ (activa intrusión) y $P_{\text{release}}$ (libera intrusión), distanciados por un margen $\Delta d \in [150, 300]\text{ mm}$.
    3. **Histéresis Temporal:** Se exige una persistencia mínima de $N_{\text{confirm}} \ge 3\text{–}5$ fotogramas consecutivos antes de cambiar el estado de la Máquina de Estados Finitos (`Spatial FSM`).

### P10: ¿Por qué usamos un Filtro de Kalman 2D para estimar velocidad y no una resta numérica $\Delta x / \Delta t$?
* **Fundamento Técnico:**
  * **Explosión del Ruido por Derivación:** La cámara solo entrega coordenadas instantáneas. Si deriváramos numéricamente $v = (x_t - x_{t-1}) / \Delta t$, a 30 FPS ($\Delta t \approx 0.033\text{ s}$) un temblor estocástico de apenas $2\text{ cm}$ en la detección del tobillo genera un pico ficticio de $0.6\text{ m/s}$ ($2.16\text{ km/h}$). Esto dispararía paradas de emergencia espurias.
  * **Estimación de Estado Oculto:** Kalman mantiene un vector de estado continuo $\mathbf{x} = [X, Y, \dot{X}, \dot{Y}]^T$ con un modelo cinemático de velocidad constante (CV). La Ganancia de Kalman equilibra estadísticamente la predicción física con la medición ruidosa, entregando velocidad y trayectoria óptimas.
  * **Ventajas en Seguridad (ISO 13855):**
    1. *Vector Direccional:* Permite saber si el operario se desplaza hacia la zona de peligro o en paralelo a ella (evitando detener la máquina si camina tangencialmente).
    2. *Coast Mode (Oclusión):* Si un pie queda ocluido durante 2-3 frames por maquinaria o pallets, el paso de predicción mantiene el seguimiento activo sin perder la continuidad ni el estado de seguridad.

### P11: ¿Por qué una arquitectura de Visualización Dual (Vista de Cámara vs Vista Cenital Top-Down BEV)?
* **Fundamento Técnico:**
  * **Vista 1: Perspectiva de Cámara con Realidad Aumentada (Overlay $H^{-1}$):**
    * *Propósito Operativo:* Muestra el video RGB en tiempo real con las zonas $P_{\text{danger}}$ y $P_{\text{release}}$ reproyectadas mediante la homografía inversa $H^{-1}$, junto con las cajas delimitadoras y esqueletos.
    * *Valor de Ingeniería:* Permite al supervisor en planta validar visualmente qué "ve" el lente: corroborar que se detectan personas y no sombras, verificar la ausencia de oclusiones físicas en el lente (suciedad, cables sueltos) y monitorear la salud del sensor en el espacio de la imagen.
  * **Vista 2: Vista Cenital Métrica Top-Down (Bird's-Eye View - BEV):**
    * *Propósito Metrológico:* Genera un lienzo 2D ortogonal del suelo en metros (escala lineal constante $1\text{ m} = N\text{ px}$). Dibuja la máquina, las zonas concéntricas, los operarios rastreados y sus vectores de velocidad $[\dot{X}, \dot{Y}]$.
    * *Valor Normativo (ISO 13855):* La distancia de seguridad $S = K \times T + C$ es estrictamente métrica y no puede auditarse en píxeles debido a la distorsión proyectiva. La vista BEV permite medir distancias euclidianas reales y verificar la dirección exacta de aproximación hacia el peligro, además de integrarse directamente en gemelos digitales o pantallas HMI/SCADA industriales.

### P12: ¿Por qué aplicamos un congelamiento de alcance (Scope Freeze) separando funcionalidades en Principal, Secundario y Futuro?
* **Fundamento de Ingeniería:**
  * **Ley de Rendimientos Decrecientes:** En sistemas de seguridad y visión artificial, agregar características complejas antes de validar la cadena causal primaria introduce vectores de fallo y acoplamientos innecesarios.
  * **La Cadena Causal del Núcleo Arquitectónico:**
    $$\text{Frame} \to \text{Pose} \to \text{Tobillos} \to \text{Homografía} \to \text{Ubicación Métrica} \to \text{Kalman 2D} \to \text{FSM} \to \text{Dwell} \to \text{Visualización Dual} \to \text{Profiling}$$
    Cada eslabón responde directamente a la hipótesis central de seguridad física bajo la norma ISO 13855:2024. Si este núcleo no es determinista y no cumple el presupuesto de tiempo $T_1$, cualquier adición periférica carece de valor.
  * **Criterio de Segregación:**
    1. *Principal (Obligatorio):* Lo necesario para ingerir video, calcular distancias métricas, transicionar estados de seguridad y auditar latencias.
    2. *Trabajo Futuro (Benchmarks y Análisis):* Benchmarks comparativos (PyTorch vs ONNX, CoreML granular, detectores alternativos) que aportan métricas de análisis pero no cambian la lógica de seguridad.
    3. *Trabajo Futuro (Despliegue y Silicio):* Hardware específico alternativo (validación PoC en NVIDIA GTX 1050 Pascal CC 6.1 / Jetson), optimizaciones propietarias (TensorRT), orquestación (Docker), multi-cámara o re-entrenamiento. Evitan inflar la complejidad de la implementación de referencia antes de contar con un núcleo arquitectónico cerrado y verificado.

### P13: ¿Por qué este prototipo se presenta como "inspirado en el razonamiento de ISO 13855" y NUNCA como un "sistema que cumple ISO 13855"?
* **Fundamento de Ingeniería y Seguridad Funcional (Diferencia Conceptual Crítica):**
  * **Alcance Estricto de ISO 13855:** La norma ISO 13855 regula el cálculo de distancias de separación ($S = K \cdot T + C$) para salvaguardas mecánicas y dispositivos electrosensibles de protección (ESPE / VBPD) certificados. No aplica de manera directa a sistemas que operan exclusivamente como sensores de presencia (*presence sensing*) sin arquitectura fail-safe tolerante a fallos de hardware.
  * **Certificación vs Razonamiento:** Afirmar que un software en Python/ONNX "cumple ISO 13855" es un error conceptual grave. Una certificación de seguridad funcional exige redundancia de canal (categorías ISO 13849 PL d/e o IEC 61508 SIL 2/3), hardware calificado, análisis de modos de fallo (FMEA) y validación ante fallas sistemáticas.
  * **La Postura Técnica Correcta:** Presentar el proyecto como:
    > *Experimental vision-based intrusion monitoring system inspired by industrial safety-zone concepts and ISO 13855 safety-distance reasoning. Not a safety-rated protective device.*
### P14: ¿Qué significa exactamente que el sistema reporte que una persona está a 0.93 m del peligro?
* **Fundamento de Metrología y Visión Computacional:**
  * **La Falsa Precisión:** En una auditoría técnica o revisión de arquitectura, responder "la homografía calculó que está a exactamente 93 centímetros" denota inmadurez en visión por computadora.
  * **El Modelo de Incertidumbre Compuesta:** La coordenada en metros es una función estimada $\hat{P}_{\text{world}} = H(\hat{p}_{\text{feet}})$, donde se acumulan cinco fuentes de error independientes:
    1. *Pose estimation error:* Jitter e incertidumbre en la predicción de keypoints de tobillos.
    2. *Pixel quantization:* Resolución finita y discretización de la cuadrícula del sensor de cámara.
    3. *Camera calibration error:* Incertidumbre de medición en los puntos coplanares de referencia ground-truth.
    4. *Ground-plane assumption:* Pequeñas desviaciones o desniveles del piso respecto a la hipótesis plana ideal $Z_w = 0$.
    5. *Homography numerical error:* Amplificación de perturbaciones gobernada por el número de condición matricial $\kappa(H)$, especialmente en zonas con ángulos rasantes.
### P15: ¿Qué hace el sistema cuando los pies del trabajador no se ven (oclusión por maquinaria) y qué es la propagación de confianza?
* **Fundamento de Arquitectura y Modos de Fallo:**
  * **El Escenario Crítico:** En una planta industrial, es habitual que una máquina baja o un pallet oculte los pies de un trabajador mientras su torso se aproxima al peligro. Si el estimador de pose reporta `conf(left_ankle) = 0.12` y `conf(right_ankle) = 0.08`, ¿qué se hace?
  * **Las Cinco Opciones de Diseño:**
    * *A) Rechazar la observación:* Descartar el dato en silencio genera un **peligro ciego**: el trabajador sigue avanzando pero el sistema actúa como si no existiera nadie.
    * *B) Usar un solo tobillo:* Si un tobillo supera el umbral ($conf \ge 0.5$), usarlo como anclaje. Válido, aunque introduce un sesgo lateral de hasta $25\text{–}30\text{ cm}$.
    * *C) Fallback a Bbox Bottom-Center:* Usar la base de la caja delimitadora. Mantiene la presencia pero puede tener sesgo si la base de la caja apoya sobre el obstáculo y no sobre el piso.
    * *D) Predicción vía Tracker (Coasting):* El filtro de Kalman proyecta la trayectoria previa usando su modelo cinemático $[\dot{X}, \dot{Y}]$ durante una ventana temporal acotada ($N_{\text{missed}} \le 5$ frames $\approx 160\text{ ms}$).
    * *E) Declarar Incertidumbre Explícita (Confidence Propagation):* Asociar una etiqueta de origen y confianza a cada coordenada.
  * **La Política Implementada (Graceful Degradation):**
    El pipeline combina B, D y E en una jerarquía tipada:
    1. Si ambos tobillos son válidos $\to$ `ANKLES_DUAL` (confianza máxima).
    2. Si uno es válido $\to$ `ANKLE_SINGLE` (confianza media).
    3. Si ambos están ocluidos $\to$ Kalman retiene el track en modo `COASTING` extrapolando velocidad (`TRACKER_PREDICTED`).
    4. Si la oclusión persiste $> 160\text{ ms}$, se evalúa fallback a bbox o eliminación segura.
  * **Propagación de Confianza:** El sistema no emite simples tuplas `(x, y)`; conceptualmente emite:
    ```python
    PositionEstimate(xy_m, confidence, source="ankles | bbox | predicted", status="OBSERVED | PREDICTED | STALE", missed_count=k)
    ```
    Esto permite que la FSM distinga entre una alarma con certeza física directa y una alarma sostenida por inercia cinemática.

### P16: ¿Por qué la predicción de Kalman NO es verdad física y cómo se calculan los horizontes de divergencia cinemática?
* **Contexto Normativo y Epistemológico:** En dispositivos de protección basados en visión (VBPD / ISO 13855:2024), cuando un operario sufre una oclusión momentánea (pies pasando tras un pallet o soporte), el Filtro de Kalman continúa proyectando su movimiento a lazo abierto (*dead reckoning*).
* **Fundamento Físico-Matemático:**
  * **"Predicción no es Verdad":** La predicción matemática $\hat{\mathbf{x}}_k = F \hat{\mathbf{x}}_{k-1}$ asume velocidad constante. El operario real es libre de acelerar, frenar, tropezar o girar. Sin fotones del sensor, la certidumbre física se degrada progresivamente.
  * **Fallo de la Derivada Discreta ($\Delta x / \Delta t$):** El jitter de keypoints ($\sigma \approx 15\text{ mm}$) amplificado a 30 FPS ($\Delta t = 0.0333\text{ s}$) produce una dispersión de velocidad ficticia $\sigma_v = \frac{\sqrt{2} \sigma}{\Delta t} \approx 0.64\text{ m/s}$. El límite $3\sigma \approx 1.91\text{ m/s}$ superaría permanentemente el umbral industrial ISO 13855 ($K = 1.6\text{ m/s}$) incluso en trabajadores quietos.
  * **Justificación de Velocidad Constante (CV) frente a Aceleración Constante (CA):**
    * La aceleración humana biomecánica máxima es $a_{\max} \approx 3.5\text{ m/s}^2$ ($\mu \le 0.7$).
    * En un solo cuadro a 30 FPS, el desplazamiento por aceleración es $\Delta x_{\text{acc}} = \frac{1}{2} a \Delta t^2 \approx 1.94\text{ mm}$, casi un orden de magnitud menor al piso de ruido de los keypoints ($15\text{ mm}$). Es físicamente inobservable en un único cuadro.
    * Estimar aceleración con un modelo CA exige la segunda diferencia discreta, cuya varianza $\text{Var}(\hat{a}) = \frac{6}{\Delta t^4} \sigma_{\text{pos}}^2$ arroja un error estándar $\sigma_a \approx 33.1\text{ m/s}^2 \ (> 3.3\text{ g})$, desestabilizando el filtro. Por ello, el modelo CV es el óptimo.
  * **Envolvente Cuadrática de Divergencia vs Colchón de Histéresis ($\Delta d = 200\text{ mm}$):**
    Durante el *coasting*, la cota máxima de divergencia física obedece a $\|\Delta \mathbf{p}(t)\| \le \frac{1}{2} a_{\max} t^2 + v_0 t (1 - \cos \theta)$.
    * $k=0$ ($t = 0\text{ ms}$): $\mathbf{0\text{ mm}}$ $\to$ **`OBSERVED`** (Hecho empírico).
    * $1 \le k \le 3$ ($t \le 100\text{ ms}$): Divergencia $\le 175\text{ mm} < \Delta d$ ($200\text{ mm}$) $\to$ **`PREDICTED`** (Seguro para tracking y disparo).
    * $4 \le k \le 5$ ($133\text{ ms} \le t \le 167\text{ ms}$): Divergencia $240\text{ mm} - 308\text{ mm} > \Delta d$ $\to$ **`STALE`** (Buffer superado, puramente especulativo).
    * $k > 5$ ($t > 167\text{ ms}$): Pista eliminada (`EXPIRED`).
  * **Detalle Completo:** Ver [ADR-008](../decisions/adr-008-kalman-epistemology-noise-divergence.md).

### P17: ¿Por qué la desescalada de seguridad es asimétrica y qué ocurre cuando un intruso desaparece dentro de la zona de peligro?
* **Contexto de Seguridad Funcional (ISO 13849-1 / IEC 61508):** Los modos de fallo ante la vida humana son inherentemente asimétricos: una falsa alarma detiene la producción (costo económico), pero un falso silenciamiento de alarma reinicia la máquina con un operario en peligro (riesgo vital o fatalidad).
* **Los Cuatro Invariantes de Seguridad Asimétrica:**
  1. **Invariante I (Escalada Proactiva Fail-Safe):** La incursión en la zona de peligro $P_{\text{danger}}$ puede y debe disparar la parada de emergencia (`trip = True`) ante cualquier estado (`OBSERVED`, `PREDICTED` o `STALE`). Ante la duda cinemática, se preserva la vida.
  2. **Invariante II (Desescalada Estrictamente Verificada por Fotones):** Un intruso que sale fuera de $P_{\text{release}}$ NO puede desescalar la alarma mediante extrapolaciones cinemáticas (`PREDICTED` / `STALE`). Requiere estrictamente $N_{\text{release}} = 5$ cuadros consecutivos con estatus **`OBSERVED`** comprobado para confirmar visualmente que el operario ya no está dentro de la zona peligrosa.
  3. **Invariante III (Enclavamiento por Desaparición en Peligro - Missing Target Lockout):** Si un intruso en zona de peligro deja de detectarse (se poda al superar $k > 5$ cuadros sin verse), el sistema jamás debe asumir que "se evaporó" y apagar la alarma. Automáticamente enclava la FSM en **`LOCKOUT`** (`trip = True`), exigiendo inspección física de la celda y un reinicio manual autorizado (`SpatialFSM.reset()`).
  4. **Invariante IV (Congelamiento de Dwell Time):** El tiempo de permanencia en la zona de advertencia mide exposición acumulada al riesgo. Durante oclusiones (`PREDICTED` o `STALE`), el contador de dwell time se **congela** en el último valor observado empíricamente y no suma tiempo fantasma mientras la persona no sea visible.
* **Detalle Completo:** Ver [ADR-008](../decisions/adr-008-kalman-epistemology-noise-divergence.md).




