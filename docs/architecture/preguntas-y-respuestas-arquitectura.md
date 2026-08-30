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
  * **Portabilidad:** Cuando el código se traslade a un nodo industrial con GPU NVIDIA (ej. GTX 1050), solo se cambia el Execution Provider a `CUDAExecutionProvider` o TensorRT sin alterar una sola línea de código del sistema.

### P2: ¿Por qué la NVIDIA GTX 1050 (arquitectura Pascal) exige cuantización obligatoria a INT8 y prohíbe FP16?
* **Contexto:** Se proyecta desplegar el MVP en una notebook con GTX 1050.
* **Fundamento Técnico:**
  * **Restricción de Silicio (Compute Capability 6.1):** Las GPUs basadas en Pascal no poseen Tensor Cores dedicados. A nivel de silicio, las operaciones en coma flotante de media precisión (**FP16**) están penalizadas de fábrica a una tasa de $1:64$ en comparación con precisión simple (**FP32**). Correr en FP16 en Pascal degrada el rendimiento drásticamente.
  * **Soporte Full-Rate INT8:** Pascal sí soporta instrucciones escalares de enteros de 8 bits (**INT8**) a tasa completa (*full-rate*).
  * **Conclusión de Ingeniería:** Para lograr alta velocidad en una GTX 1050 con TensorRT, es mandatorio realizar **cuantización post-entrenamiento (PTQ) a INT8** utilizando un dataset de calibración para generar los factores de escala dinámicos.

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

### P6: ¿Por qué se prohíbe el centroide de la caja delimitadora (Bounding Box)?
* **Fundamento Técnico:**
  * El centroide 2D de una caja delimitadora o la base central de la caja aproximan el centro del torso o la proyección visual del cuerpo.
  * Cuando la cámara tiene un ángulo cenital o picado, el torso o la cabeza de una persona de pie fuera de la zona restringida pueden proyectarse visualmente dentro del polígono en la imagen.
  * Esto provoca **falsos positivos críticos** que detendrían la maquinaria de la fábrica innecesariamente cuando el operario está seguro.
  * El anclaje a los tobillos (`left_ankle: 15`, `right_ankle: 16`) garantiza que solo se active la alarma si el punto de apoyo físico sobre el suelo vulnera la zona.

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
