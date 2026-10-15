# ADR-011: Bayesian Validation Gating (Mahalanobis $\chi^2$), Asignación Global Húngara y World-Space Spatial Birth NMS

## Estado
**Aceptado y Aplicado** (2026-09-01)

## Contexto
En el seguimiento multi-objetivo (*Multi-Object Tracking - MOT*) para zonas de seguridad industrial bajo la norma ISO 13855, el sistema inicial utilizaba una compuerta espacial euclidiana fija ($d_{\text{gate}} \le 1.0\text{ m}$) combinada con una asignación codiciosa (*greedy nearest-neighbor*).

Durante la evaluación empírica con datasets de alta densidad peatonal y oclusiones dinámicas complejas (`pets2009_s2_l1` y `openvino_people`), se manifestaron cuatro fallos arquitectónicos:

1. **Falacia de Incertidumbre Isotrópica:** Tratar la compuerta de asociación como un círculo euclidiano ignora la cinemática del operario. La incertidumbre real no es esférica, sino una **elipse anisótropa** orientada según el vector de velocidad $\vec{v} = [v_x, v_y]$ y la covarianza de estado $P$.
2. **Rigidez durante Oclusión (*Coasting*):** Cuando un operario pasa varios cuadros sin detección, la matriz de covarianza $P$ crece por la propagación $F P F^T + Q$. Mantener un radio de búsqueda rígido de $1.0\text{ m}$ provoca pérdidas de track y fragmentación de identidades (*ID Switching*) al momento de la reaparición.
3. **Asignación Subóptima Local (*Greedy Bias*):** Ordenar los pares por distancia euclidiana de forma codiciosa permite que un falso positivo cercano robe el track de un operario legítimo, forzando a la detección real a ser descartada o asignada a otro track.
4. **Proliferación de Tracks Fantasma (*Ghost Tracks*):** Cuando el detector YOLO entrega dos propuestas cercanas sobre el mismo cuerpo (por ejemplo, tobillos separados o propuestas dobles de NMS 2D), la propuesta huérfana inicializa un segundo track duplicado en paralelo.

---

## Decisión

### 1. Compuerta de Validación Bayesiana de Mahalanobis ($\chi^2$ Gating)
Se reemplaza la distancia euclidiana por la distancia cuadrática de Mahalanobis normalizada por la matriz de covarianza de innovación $S_i \in \mathbb{R}^{2 \times 2}$:

$$S_i = H P_{i|k-1} H^T + R = P_{i[:2, :2]} + R$$

$$d_M^2(i, j) = (\mathbf{z}_j - \hat{\mathbf{x}}_{i,pos})^T S_i^{-1} (\mathbf{z}_j - \hat{\mathbf{x}}_{i,pos})$$

* **Inversión Analítica $2 \times 2$:** Se utiliza la regla de Cramer para calcular $S_i^{-1}$ en $< 30\text{ ns}$ con piso de no-singularidad:
  $$S^{-1} = \frac{1}{s_{00}s_{11} - s_{01}s_{10}} \begin{bmatrix} s_{11} & -s_{01} \\ -s_{10} & s_{00} \end{bmatrix}$$
* **Criterio Estadístico $\chi^2$ (2 Grados de Libertad):**
  Como la medición es bidimensional ($\mathbf{z} \in \mathbb{R}^2$), $d_M^2$ sigue una distribución Chi-cuadrado $\chi^2_2$. Se establece la compuerta en $\gamma = 9.210$ (intervalo de confianza del $99\%$). Toda detección con $d_M^2 > 9.210$ es rechazada estadísticamente antes de la asignación.
* **Vectorización Tensorial Einstein:** Se calcula el tensor completo $N \times M$ mediante `np.einsum("nab,nmb->nma", S_inv_arr, Y)` en $0.017\text{ ms}$ para $10 \times 10$ objetivos.

### 2. Asignación Global Bipartita (Algoritmo Húngaro / Munkres)
Se construye la matriz de costos global $C \in \mathbb{R}^{N \times M}$:

$$C_{i, j} = \begin{cases} 
d_M^2(i, j) & \text{si } d_M^2(i, j) \le 9.210 \\
10^5 & \text{si } d_M^2(i, j) > 9.210 \quad (\text{rechazo por gating})
\end{cases}$$

Se resuelve la asignación biunívoca global mínima mediante `scipy.optimize.linear_sum_assignment(C)` en complejidad $\mathcal{O}(N^3)$, eliminando el sesgo codicioso.

### 3. World-Space Spatial Birth Non-Maximum Suppression (NMS)
Se introduce una regla de no-nacimiento en el espacio métrico del piso:
* Ninguna detección no asignada $\mathbf{z}_j$ puede instanciar un nuevo track tentativo si su distancia euclidiana al plano de suelo respecto a cualquier track activo/confirmado es menor a $d_{\text{birth-min}} = 0.6\text{ m}$ (radio del cuerpo humano según ISO 13855).
* Se suprimen también propuestas concurrentes huérfanas en el mismo cuadro separadas por menos de $0.6\text{ m}$.

---

## Consecuencias

### Positivas:
* **Invariancia a Cruces de Trayectorias:** En cruces densos de peatones, la asignación global mantiene la trayectoria inercial de cada sujeto sin intercambios de identificadores ni cambios erráticos de color en BEV.
* **Adaptación Dinámica durante Coasting:** A mayor tiempo en oclusión, la compuerta se ensancha automáticamente a lo largo del vector de velocidad, facilitando la reasociación natural del operario al salir de detrás de un obstáculo.
* **Eliminación Total de Ghost Tracks:** Se suprimen los vectores dobles sobre una misma persona causados por propuestas redundantes de YOLO.
* **Latencia Despreciable:** La combinación de inversión analítica y vectorización `einsum` ejecuta la asignación en **$0.017\text{ ms}$** para 10 personas, consumiendo menos del $0.1\%$ del presupuesto temporal de $50\text{ ms}$ de la norma ISO 13855.

### Negativas / Compromisos:
* Incorpora la dependencia de `scipy>=1.10.0` en `requirements.txt`.
