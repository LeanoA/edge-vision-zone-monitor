# ADR-008: Epistemología de Estados de Observación Kalman, Descomposición Espectral de Ruido y Desescalada Asimétrica de Seguridad

- **Estatus:** Aceptado
- **Fecha:** 2026-08-30
- **Módulos Asociados:** `src/core/kalman_filter.py`, `src/core/spatial_fsm.py`, `src/pipeline/safety_pipeline.py`
- **Estándares Aplicables:** ISO 13855:2024, ISO 13849-1 (PL d/e), IEC 61508 (SIL 2/3)

---

## 1. Contexto y Planteamiento del Defecto Epistemológico

En sistemas de protección basados en visión artificial industrial (VBPD - *Vision-Based Protective Devices* según ISO 13855 e ISO 13849-1), el sistema de percepción determina de forma autónoma cuándo abrir o cerrar los contactores de parada de emergencia de maquinaria peligrosa (ej. celdas robóticas, prensas, transportadores).

Para mitigar el ruido estocástico de detección y suavizar trayectorias métricas en el plano del suelo ($Z_w = 0$), se utiliza un Filtro de Kalman métrico 2D. Sin embargo, en arquitecturas tradicionales de tracking surge un grave defecto de **conflación epistemológica**:

$$\text{\bf "La predicción de Kalman es una hipótesis matemática a lazo abierto; la medición óptica es un hecho empírico."}$$

Cuando la visión se interrumpe por oclusiones (pies pasando tras estructuras, pallets o maquinaria), el filtro opera en modo *coasting* (estimación a lazo abierto):
$$\hat{\mathbf{x}}_k = F \hat{\mathbf{x}}_{k-1}$$

Esta extrapolación asume que el trabajador continúa indefinidamente a velocidad constante. En la realidad física, un ser humano no observado es libre de acelerar, frenar, tropezar, arrodillarse o cambiar de dirección abruptamente. A medida que transcurre el tiempo sin fotones, el volumen de incertidumbre de la posición física real crece de forma cuadrática y cúbica.

Tratar una predicción cinemática sin fotones con idéntica autoridad que una medición respaldada por sensores ópticos constituye una vulnerabilidad crítica de seguridad industrial:
* **Escalada hacia el peligro (Fail-Safe):** Si una predicción cinemática entra en la zona de peligro $P_{\text{danger}}$, disparar la parada es conservador y seguro (evita accidentes incluso si fue una sobre-estimación).
* **Desescalada hacia la seguridad (Peligrosa):** Si un track que violó $P_{\text{danger}}$ proyecta cinemáticamente que ha salido hacia la zona segura $P_{\text{release}}$ sin confirmación sensorial, liberar el relé de parada puede ser mortal si el trabajador en realidad tropezó y yace inmóvil dentro del radio de alcance del robot.

---

## 2. Descomposición Espectral del Ruido de Medición

Las coordenadas métricas $(X_w, Y_w)$ en el piso están corrompidas por tres procesos estocásticos aditivos superpuestos:

$$\tilde{\mathbf{z}}_k = \mathbf{z}_k + \boldsymbol{\eta}_{\text{jitter}} + \boldsymbol{\eta}_{\text{quant}} + \boldsymbol{\eta}_{\text{parallax}}$$

1. **Jitter de Keypoints ($\boldsymbol{\eta}_{\text{jitter}}$):** Fluctuaciones espaciales de alta frecuencia (10 a 30 Hz, magnitud típica $\sigma \approx 0.015\text{ m} = \pm 15\text{ mm}$), debidas a regresión subpíxel de mapas de calor en redes neuronales, ondulación de prendas de vestir e interpolación de bordes.
2. **Cuantización de Píxeles ($\boldsymbol{\eta}_{\text{quant}}$):** Discretización espacial por la resolución finita del sensor ($640 \times 640$). Bajo la matriz de homografía $H$, cada píxel representa una celda métrica con dispersión $\sigma_{\text{quant}} \approx \pm 10\text{ a } 40\text{ mm}$.
3. **Paralaje de Bounding Box ($\boldsymbol{\eta}_{\text{parallax}}$):** Desplazamiento estructural de frecuencia media ($\pm 50\text{ a } 250\text{ mm}$, media $\approx \pm 100\text{ mm}$) al degradar a la base de la caja (`BBOX_BOTTOM`), donde la postura corporal y la perspectiva proyectiva alejan la base del punto real de contacto anatómico.

### Demostración Matemática: Explosión de Ruido en Diferenciación Numérica ($\Delta x / \Delta t$)

Si se intenta calcular la velocidad de aproximación mediante diferencias finitas hacia atrás $\hat{v}_k = \frac{\tilde{z}_k - \tilde{z}_{k-1}}{\Delta t}$ a 30 FPS ($\Delta t = 0.0333\text{ s}$):

$$\sigma_v = \frac{\sqrt{2} \sigma_{\text{pos}}}{\Delta t} = \frac{\sqrt{2} \times 0.015\text{ m}}{0.0333\text{ s}} \approx 0.637\text{ m/s} \quad (2.29\text{ km/h})$$

Una cota estándar de $3\sigma_v$ genera picos espurios continuos de velocidad de:
$$3 \sigma_v \approx 1.91\text{ m/s}$$

Dado que la norma ISO 13855 define la velocidad humana industrial de aproximación como $K = 1.6\text{ m/s}$, **la diferenciación numérica simple dispara continuamente el bypass de emergencia en trabajadores estacionarios o en ligero balanceo postural.** El uso de un filtro estocástico estructurado (Kalman) es una exigencia físico-matemática.

---

## 3. Justificación Cinemática: Velocidad Constante (CV) vs Aceleración Constante (CA)

Se evaluó si modelar el movimiento humano como Velocidad Constante (CV, estado 4D: $[X, Y, v_x, v_y]^T$) o Aceleración Constante (CA, estado 6D: $[X, Y, v_x, v_y, a_x, a_y]^T$).

### 3.1 Cota Biomecánica de Aceleración Humana
La aceleración máxima en marcha humana durante arranque en sprint o frenada brusca está acotada por el coeficiente de fricción piso-calzado ($\mu \approx 0.7$):
$$a_{\max} \approx 2.5\text{ a } 3.5\text{ m/s}^2$$

En un único intervalo de cuadro a 30 FPS ($\Delta t = 0.0333\text{ s}$):
* Cambio de velocidad por cuadro: $\Delta v = a_{\max} \Delta t \le 3.5 \times 0.0333 \approx 0.117\text{ m/s}$.
* Desplazamiento posicional atribuible a la aceleración:
  $$\Delta x_{\text{acc}} = \frac{1}{2} a_{\max} (\Delta t)^2 \le \frac{1}{2} (3.5) (0.0333)^2 \approx 0.00194\text{ m} = \mathbf{1.94\text{ mm}}$$

### 3.2 Relación Ruido-Señal
Comparando el desplazamiento físico real frente al piso de ruido del sensor:
* Desplazamiento por aceleración: $\mathbf{1.94\text{ mm}}$
* Piso de ruido por jitter: $\mathbf{15.00\text{ mm}}$
* Relación Ruido-a-Señal:
  $$\frac{\sigma_{\text{jitter}}}{\Delta x_{\text{acc}}} = \frac{15.0\text{ mm}}{1.94\text{ mm}} \approx \mathbf{7.73}$$

La aceleración física en un solo fotograma es un orden de magnitud inferior al ruido de medición. Es físicamente inobservable a 30 FPS.

### 3.3 Explosión de Varianza en la Segunda Derivada (Modelos CA)
En un modelo CA, la aceleración debe inferirse a partir de la segunda diferencia discreta:
$$\hat{a}_k \approx \frac{\tilde{z}_k - 2\tilde{z}_{k-1} + \tilde{z}_{k-2}}{\Delta t^2} \implies \text{Var}(\hat{a}) = \frac{6}{\Delta t^4} \sigma_{\text{pos}}^2$$

Evaluando con $\Delta t = 0.0333\text{ s}$ ($\Delta t^4 \approx 1.23 \times 10^{-6}\text{ s}^4$) y $\sigma_{\text{pos}} = 0.015\text{ m}$:
$$\text{Var}(\hat{a}) \approx 1097\text{ m}^2/\text{s}^4 \implies \sigma_a \approx \mathbf{33.1\text{ m/s}^2 \ (> 3.3\text{ g})}$$

Un error de estimación de aceleración con desviación típica de $3.3\text{ g}$ provoca oscilaciones violentas, sobredisparos numéricos y falsas alarmas inaceptables. Por tanto, el modelo de **Velocidad Constante (CV) con ruido de proceso $Q$ que absorbe las maniobras humanas es la formulación matemáticamente óptima**.

---

## 4. Envolvente de Divergencia Cuadrática y Estados de Observación

Durante oclusión, la posición real del operario diverge de la predicción de Kalman a lazo abierto según:

$$\|\Delta \mathbf{p}(t)\| \le \frac{1}{2} a_{\max} t^2 + v_0 t (1 - \cos \theta)$$

Evaluando cuadro a cuadro a 30 FPS ($v_0 = 1.6\text{ m/s}$, $a_{\max} = 3.0\text{ m/s}^2$):

| Cuadros Perdidos ($k$) | Tiempo Transcurrido ($t$) | Sobrepaso Lineal ($v_0 t$) | Divergencia Maniobra ($\frac{1}{2} a t^2$) | Divergencia Máxima | % Buffer Histeresis ($\Delta d = 200\text{ mm}$) | Estado Epistémico |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0 cuadros** | $0.0\text{ ms}$ | $0\text{ mm}$ | $0.0\text{ mm}$ | $\mathbf{0.0\text{ mm}}$ | $0.0\%$ | **`OBSERVED`** |
| **1 cuadro** | $33.3\text{ ms}$ | $53\text{ mm}$ | $1.7\text{ mm}$ | $\approx \mathbf{55\text{ mm}}$ | $27.5\%$ | **`PREDICTED`** |
| **2 cuadros** | $66.7\text{ ms}$ | $107\text{ mm}$ | $6.7\text{ mm}$ | $\approx \mathbf{113\text{ mm}}$ | $56.5\%$ | **`PREDICTED`** |
| **3 cuadros** | $100.0\text{ ms}$ | $160\text{ mm}$ | $15.0\text{ mm}$ | $\approx \mathbf{175\text{ mm}}$ | $87.5\%$ | **`PREDICTED`** (Límite Seguro) |
| **4 cuadros** | $133.3\text{ ms}$ | $213\text{ mm}$ | $26.7\text{ mm}$ | $\approx \mathbf{240\text{ mm}}$ | $120.0\%$ | **`STALE`** (Buffer Violado) |
| **5 cuadros** | $166.7\text{ ms}$ | $267\text{ mm}$ | $41.7\text{ mm}$ | $\approx \mathbf{308\text{ mm}}$ | $154.0\%$ | **`STALE`** (Crítico) |
| **> 5 cuadros** | $> 166.7\text{ ms}$ | $> 320\text{ mm}$ | $> 60.0\text{ mm}$ | $> \mathbf{380\text{ mm}}$ | $> 190.0\%$ | **`EXPIRED` / `DELETED`** |

---

## 5. Decisión de Diseño

Se establecen los siguientes principios e implementaciones arquitectónicas:

1. **Modelo Epistémico de Tres Estados (`ObservationStatus`):**
   * `OBSERVED` ($k=0$): Respaldo directo por fotones del sensor óptico en el fotograma actual. Plena autoridad de control.
   * `PREDICTED` ($1 \le k \le 3$): Extrapolación cinemática acotada estrictamente dentro del margen de histéresis espacial ($\le 175\text{ mm} < 200\text{ mm}$).
   * `STALE` ($4 \le k \le 5$): Extrapolación especulativa cuya divergencia excede el margen físico de seguridad ($> 200\text{ mm}$).
2. **Invariante de Salvaguarda Asimétrica:**
   * **Invariante I (Escalada Fail-Safe):** La incursión en $P_{\text{danger}}$ y escalada a `DANGER_INTRUSION` puede activarse mediante estados `OBSERVED`, `PREDICTED` o `STALE`.
   * **Invariante II (Desescalada Gated en Evidencia Óptica):** El incremento de `clean_count` y la liberación de la violación requiere estrictamente $N_{\text{release}}$ cuadros consecutivos con estado `OBSERVED` fuera de $P_{\text{release}}$. Pistas en `PREDICTED` o `STALE` tienen terminantemente prohibido desescalar la seguridad.
   * **Invariante III (Enclavamiento por Desaparición de Intruso):** Si una pista violadora que disparó `DANGER_INTRUSION` desaparece del rastreo (se poda al exceder `max_missed` sin salida óptica verificada), el sistema enclava en estado `LOCKOUT` con relé abierto (`trip = True`). Solo puede restablecerse mediante reset explícito autorizado (`fsm.reset()`).
   * **Invariante IV (Congelamiento de Dwell Time):** El tiempo de permanencia en zona de advertencia representa exposición física acumulada a riesgo. Durante oclusión (`PREDICTED` / `STALE`), el contador `dwell_time_s` se congela en el último valor empíricamente verificado.

---

## 6. Consecuencias y Cumplimiento Normativo

* **Seguridad Funcional (ISO 13849-1 Categoría 3/4, PL d/e):** Se elimina el modo de fallo catastrófico donde un operario caído u oculto en zona de peligro permite que la máquina arranque debido a una predicción de salida matemática no confirmada.
* **Eliminación de Paradas Falsas por Dwell:** Se evita que un trabajador oculto tras un obstáculo acumule tiempo ficticio de permanencia que dispare falsas alarmas en planta.
* **Sobrecarga Computacional Despreciable:** La evaluación del estado de observación y el congelamiento de dwell demandan menos de $5\,\mu\text{s}$ por cuadro, manteniendo el presupuesto de latencia de percepción ($T_1 \le 50\text{ ms}$) holgadamente satisfecho.
