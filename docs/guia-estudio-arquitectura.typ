
#set page(
  paper: "a4",
  margin: (top: 2.2cm, bottom: 2.2cm, left: 2.0cm, right: 2.0cm),
  header: context {
    let p = counter(page).get().first()
    if p > 2 [
      #grid(
        columns: (1fr, 1fr),
        align: (left, right),
        text(size: 7.5pt, fill: rgb("#64748B"), weight: "bold")[EDGE VISION SAFETY GUARD | MANUAL DE ESTUDIO],
        text(size: 7.5pt, fill: rgb("#0284C7"), weight: "bold")[SISTEMAS CRÍTICOS EN TIEMPO REAL]
      )
      #v(-0.5em)
      #line(length: 100%, stroke: 0.5pt + rgb("#CBD5E1"))
    ]
  },
  footer: context {
    let p = counter(page).get().first()
    if p > 2 [
      #line(length: 100%, stroke: 0.5pt + rgb("#CBD5E1"))
      #v(-0.3em)
      #grid(
        columns: (1fr, 1fr),
        align: (left, right),
        text(size: 7.5pt, fill: rgb("#64748B"))[Senior Architecture (Concepts > Code) • ISO 13855:2024 / IEC 61496],
        text(size: 7.5pt, fill: rgb("#0F172A"), weight: "bold")[Página #p de #counter(page).final().first()]
      )
    ]
  }
)

#set text(font: "Helvetica", size: 9.5pt, lang: "es")
#set par(justify: true, leading: 0.65em)
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => block(width: 100%, breakable: false)[
  #v(1.4em)
  #rect(fill: rgb("#0F172A"), width: 100%, radius: 4pt, inset: (x: 14pt, y: 12pt))[
    #text(fill: rgb("#38BDF8"), size: 13pt, weight: "bold")[#it.body]
  ]
  #v(0.8em)
]

#show heading.where(level: 2): it => block(width: 100%, breakable: false)[
  #v(1.1em)
  #text(fill: rgb("#1E3A8A"), size: 11.5pt, weight: "bold")[#it]
  #v(0.4em)
]

#show heading.where(level: 3): it => block(width: 100%, breakable: false)[
  #v(0.8em)
  #text(fill: rgb("#0F172A"), size: 10pt, weight: "bold")[#it]
  #v(0.3em)
]

#show raw: it => block(
  fill: rgb("#0F172A"),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.5pt + rgb("#334155"),
  text(fill: rgb("#E2E8F0"), size: 8pt, font: "Menlo")[#it]
)

#let callout(title: "", body, color: rgb("#2563EB")) = {
  block(
    width: 100%,
    fill: color.lighten(92%),
    stroke: (left: 4pt + color),
    radius: (right: 4pt),
    inset: (x: 12pt, y: 10pt),
    outset: 0pt,
    [
      #if title != "" [ *#text(fill: color.darken(25%), title)* \ ]
      #body
    ]
  )
}

// ==============================================================================
// PORTADA DEL COMPENDIO
// ==============================================================================

#align(center)[
  #v(2cm)
  #rect(fill: rgb("#0B132B"), radius: 8pt, width: 100%, inset: (x: 20pt, y: 24pt))[
    #text(fill: rgb("#38BDF8"), size: 24pt, weight: "bold")[EDGE VISION SAFETY GUARD]     #v(0.5em)
    #text(fill: rgb("#F8FAFC"), size: 13.5pt, weight: "medium")[Manual Integral de Estudio, Especificaciones y Arquitectura de Sistemas Críticos en Tiempo Real]     #v(0.8em)
    #text(fill: rgb("#94A3B8"), size: 9.5pt)[Diseño Guiado por la Física, Geometría Planar Proyectiva y Estándares de Seguridad Industrial]
  ]

  #v(1.5cm)

  #grid(
    columns: (auto, auto, auto, auto),
    gutter: 10pt,
    rect(fill: rgb("#DC2626"), radius: 4pt, inset: 6pt)[#text(fill: white, size: 8pt, weight: "bold")[ISO 13855:2024]],
    rect(fill: rgb("#2563EB"), radius: 4pt, inset: 6pt)[#text(fill: white, size: 8pt, weight: "bold")[IEC 61496 / 61508]],
    rect(fill: rgb("#D97706"), radius: 4pt, inset: 6pt)[#text(fill: white, size: 8pt, weight: "bold")[CONCEPTS > CODE]],
    rect(fill: rgb("#059669"), radius: 4pt, inset: 6pt)[#text(fill: white, size: 8pt, weight: "bold")[FAIL-SAFE ARCHITECTURE]]
  )

  #v(2cm)

  #rect(fill: rgb("#F8FAFC"), stroke: 1pt + rgb("#CBD5E1"), radius: 6pt, width: 90%, inset: 14pt)[
    #align(left)[
      *Metadatos de Ingeniería y Referencia:*       - *Autoría:* Senior Architect & Systems Engineering (GDE & MVP)
      - *Enfoque:* Separación Ortogonal Determinista: Percepción Pura + Geometría + Cinemática + FSM
      - *Runtimes de Ejecución:* ONNX Runtime + CoreML (Apple Silicon ANE/GPU) / INT8 TensorRT (NVIDIA Pascal CC 6.1)
      - *Fecha de Edición:* Septiembre 2026 • Versión 1.0 (Compendio Completo y Autocontenido)
    ]
  ]

  #v(1.5cm)
  #text(fill: rgb("#64748B"), size: 8pt)[
    Documento técnico de estudio local generado automáticamente a partir del repositorio oficial.     Incluye la totalidad de las especificaciones, justificaciones matemáticas, benchmarks y el catálogo completo de los 12 ADRs.
  ]
]

#pagebreak()

// ==============================================================================
// TABLA GENERAL DE CONTENIDOS
// ==============================================================================

#outline(title: "Tabla General de Contenidos", indent: auto, depth: 3)

#pagebreak()

= 1. La Gran Tesis del Proyecto y Filosofía de Arquitectura <cap-filosofia>
= 🛡️ Guía Maestra de Estudio y Publicación: Arquitectura de Edge Safety Guard
<guía-maestra-de-estudio-y-publicación-arquitectura-de-edge-safety-guard>
#quote(block: true)[
#strong[Documento de Estudio & Guion Técnico para Publicación] \
#emph[Patrones de Diseño, Física, Filosofía de Ingeniería y Estándares
Industriales (ISO 13855 / IEC 61496).]
]

#divider()

== 💡 1. La Gran Tesis del Proyecto (Filosofía Central)
<la-gran-tesis-del-proyecto-filosofía-central>
#quote(block: true)[
#strong["No todos los problemas de un sistema de Inteligencia Artificial
se resuelven con más Inteligencia Artificial."]
]

En el desarrollo moderno de software y Edge AI, existe la tentación de
usar redes neuronales como una "caja negra" universal: querer entrenar
un modelo para predecir si alguien "está cometiendo una infracción" o
"cuánto tiempo lleva en la zona".

Este proyecto demuestra un enfoque de #strong[Senior Architecture
(Concepts \> Code)]: 1. #strong[La IA se restringe a la Percepción
Pura:] Detectar la ubicación de los tobillos anatómicos en píxeles. 2.
#strong[La Geometría resuelve el Espacio:] Transformación proyectiva
homográfica $3 times 3$ a coordenadas métricas reales ($Z_w = 0$). 3.
#strong[La Cinemática resuelve la Incertidumbre:] Filtro de Kalman 2D
continuo con modelos de covarianza, compuertas de Mahalanobis y estados
epistemológicos de observación. 4. #strong[La Lógica Determinista toma
las Decisiones:] Statecharts ortogonales concurrentes que evalúan
topología espacial y permanencia temporal con $0.05 upright(" ms")$ de
cómputo.

#divider()

== 🏗️ 2. Arquitectura en Capas: El Flujo End-to-End
<arquitectura-en-capas-el-flujo-end-to-end>
```
                    PERCEPTION
                         │
Camera frame ──► Pose inference (YOLO11-Pose ONNX / CoreML)
                         │
                         ▼
                 keypoint extraction (Tobillos 15 y 16)
                         │
                         ▼
                 ground-point estimate (Fallback a Bbox Bottom)
                         │
─────────────────────────┼────────────────────────────────────────
                    GEOMETRY
                         │
                         ▼
                   Homography (DLT 3x3, κ(H) < 10^6)
                         │
                         ▼
                 (X,Y) estimate [metros en piso físico]
                         │
─────────────────────────┼────────────────────────────────────────
                  STATE ESTIMATION
                         │
                         ▼
                Kalman Filter 2D (Velocidad Constante)
                         │
                         ▼
            filtered metric trajectory (OBSERVED / PREDICTED / STALE)
            + Mahalanobis χ² Gating + Hungarian Association
                         │
─────────────────────────┼────────────────────────────────────────
                 DECISION LOGIC
                         │
                         ▼
              Restricted zone test (Shapely Prepared Geometries)
                         │
                         ▼
                  Spatial FSM (OccupancyState: Schmitt Trigger)
                         │
                         ▼
                   Dwell timer (DwellState: t_dwell = ∫ dt)
                         │
─────────────────────────┼────────────────────────────────────────
                     OUTPUT
                         │
            events (JSONL) / overlay (Dual Perspective + BEV) / metrics

          ═══════════════════════════════════════════════════════
          PERFORMANCE PROFILER (Ortogonal)
          • T_capture : Latencia de buffer de hardware (V4L2 / RTSP)
          • T_system  : Latencia de procesamiento por fotograma (T1 ≈ 19ms)
          • T_event   : Latencia física real desde intrusión hasta disparo
          ═══════════════════════════════════════════════════════
```

#divider()

== 🎛️ 3. Mecanismos Clave de Seguridad & Lógica Industrial
<mecanismos-clave-de-seguridad-lógica-industrial>
#figure(image("figures/schmitt_trigger.png", width: 75%), caption: [Schmitt Trigger Espacial con Banda de Histéresis (P_danger vs P_release).]) <fig-schmitt>

=== A. Schmitt Trigger Espacial y Asimetría ENTRY / EXIT (#link(<adr-004>)[ADR-004], #link(<adr-006>)[ADR-006], #link(<adr-008>)[ADR-008])
<a.-schmitt-trigger-espacial-y-asimetría-entry-exit-adr-004-adr-006-adr-008>
```
                      P_release (Límite de Liberación)
                   ┌───────────────────────────────────┐
                   │       Banda de Histéresis         │
                   │       (Δd = 200 mm)               │
                   │    P_danger (Límite de Peligro)   │
                   │   ┌───────────────────────────┐   │
                   │   │                           │   │
                   │   │          MÁQUINA          │   │
                   │   │                           │   │
                   │   └───────────────────────────┘   │
                   │                                   │
                   └───────────────────────────────────┘
```

- #strong[El Problema:] Un operario trabajando en el borde genera
  #emph[chattering] (parpadeo de alarmas que destruye contactores)
  debido al ruido estocástico de detección.
- #strong[La Solución (Schmitt Trigger):] Entrás al cruzar
  $P_(upright("danger"))$, pero no salís hasta cruzar completamente
  $P_(upright("release")) = P_(upright("danger")) xor 0.20 upright(" m")$.
- #strong[Asimetría Industrial:]
  + #strong[ENTRY (Conservative & Fast):]
    - Paso normal ($v_n < 1.6 upright(" m/s")$): Debounce de
      $N_(upright("confirm")) = 3$ cuadros.
    - Aproximación rápida ($v_n gt.eq 1.6 upright(" m/s")$ --- ISO
      13855): #strong[Bypass instantáneo ($N_(upright("confirm")) = 1$)]
      en el cuadro 1 sin esperar.
  + #strong[EXIT (Hysteretic & Strict):]
    - Exige $N_(upright("release")) = 5$ cuadros consecutivos afuera.
    - #strong[Salvaguarda Asimétrica:] Solo se permite desescalar si los
      cuadros son ópticamente verificados (`OBSERVED`). Si hay oclusión
      y el filtro de Kalman extrapola en `PREDICTED`, la salida se
      bloquea y el relé permanece abierto.

#divider()

=== B. Statecharts Ortogonales: Desacoplamiento Espacial y Temporal (#link(<adr-009>)[ADR-009])
<b.-statecharts-ortogonales-desacoplamiento-espacial-y-temporal-adr-009>
El estado del sistema es el producto cartesiano de dos regiones
concurrentes:

$ cal(S)_(upright("global")) = cal(S)_(upright("occupancy")) times cal(S)_(upright("dwell")) $

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)                          │
│    [ OUTSIDE ] ──► [ ENTER_PENDING ] ──► [ INSIDE ] ──► [ EXIT_PENDING ]     │
│                                        (trip=True)                          │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │ (Condición de guardia: INSIDE)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)                        │
│    [ NORMAL ] ──────(t >= Twarn)─────► [ WARNING ] ─────(t >= Tviol)─────► [ VIOLATION ] │
└─────────────────────────────────────────────────────────────────────────────┘
```

- #strong[Invariante Fail-Safe:] `trip = True` se dispara de inmediato
  en $t = 0.0 upright(" s")$ de confirmación en `INSIDE`. El
  #emph[dwell] no demora la parada de emergencia; clasifica la gravedad
  operativa para auditoría.

#divider()

=== C. Doble Horizonte Temporal en Edge AI: $T_(upright("system"))$ vs $T_(upright("event"))$ (#link(<adr-010>)[ADR-010])
<c.-doble-horizonte-temporal-en-edge-ai-t_textsystem-vs-t_textevent-adr-010>
Bajo la norma #strong[ISO 13855:2024] ($S = K dot.op T + C$):

+ #strong[Latencia de Sistema por Cuadro ($T_(upright("system"))$):]
  $ T_(upright("system")) = T_(upright("capture")) + T_(upright("pre")) + T_(upright("infer")) + T_(upright("pose")) + T_(upright("geom")) + T_(upright("track")) + T_(upright("fsm")) $
+ #strong[Latencia de Reacción del Evento Físico
  ($T_(upright("event"))$):]
  $ T_(upright("event")) = t_(upright("trip")) - t_(upright("physical_entry")) $
  - #emph[Aproximación normal:]
    $T_(upright("event")) =\(N_(upright("confirm")) - 1\)dot.op Delta t_(upright("frame")) + T_(upright("system")) approx 81.7 upright(" ms")$
    (a 30 FPS).
  - #emph[Aproximación rápida ($v_n gt.eq 1.6 upright(" m/s")$):]
    $T_(upright("event")) = T_(upright("system")) approx 19 upright(" ms")$.

#divider()

#figure(image("figures/kalman_mahalanobis.png", width: 65%), caption: [Compuerta Elipsoidal de Innovación de Mahalanobis.]) <fig-kalman>

=== D. MOT Bayesiano y Asignación Combinatoria (#link(<adr-011>)[ADR-011])
<d.-mot-bayesiano-y-asignación-combinatoria-adr-011>
Para resolver el cruce de múltiples personas y los falsos nacimientos
(#emph[ghost tracks]): 1. #strong[Compuerta de Mahalanobis
$chi_2^2\(0.99\)lt.eq 9.210$:] Proyección de covarianza de innovación
$S = P + R$ que ensancha el elipsoide de búsqueda a lo largo del vector
de velocidad $arrow(v)$. 2. #strong[Asignación Global Húngara /
Munkres:] Resuelve la asignación biyectiva global en $cal(O)\(N^3\)$ en
$0.017 upright(" ms")$, eliminando permutaciones de ID en cruces. 3.
#strong[World-Space Spatial Birth NMS
($d_(upright("birth_min")) = 0.6 upright(" m")$):] Regla espacial en
metros en el piso que suprime instanciaciones duplicadas causadas por
propuestas redundantes de YOLO.

#divider()

=== E. Cierre del Gap Sintético y Renderizado Fotorrealista Pinhole (#link(<adr-012>)[ADR-012], #link(<cap-sintetico>)[Doc Técnico])
<e.-cierre-del-gap-sintético-y-renderizado-fotorrealista-pinhole-adr-012-doc-técnico>
- #strong[El Problema del Synthetic Domain Gap:] Las figuras geométricas
  2D (`cv2.line`/`cv2.rectangle`) provocan 0% de detección en YOLO
  (COCO) por carecer de gradientes y texturas reales.
- #strong[La Solución Arquitectónica:]
  + #strong[Single-Identity Tracklet & Normalización:] Extracción
    continua de un único sujeto en lienzo canónico
    ($160 times 320 upright(" RGBA")$) con alpha-feathering y sombra de
    contacto Gaussiana (0% saltos de ropa o silueta).
  + #strong[Escala Pinhole Perspectiva:] Altura antropométrica
    $h = frac(480, 1.0 + 0.165 dot.op Y)$ que mantiene al sujeto siempre
    en resolución óptima ($h in\[240\,480\]upright(" px")$).
  + #strong[Desacoplamiento de UI:] HUD de seguridad superior traslúcido
    (56px) y telemetría de simulación inferior
    ($y = 1040 upright(" px")$), logrando #strong[100% de detección] con
    confianza promedio de #strong[0.835 - 0.861].

#divider()

== 📚 4. Catálogo Completo de Architecture Decision Records (ADRs)
<catálogo-completo-de-architecture-decision-records-adrs>
#figure(
  align(center)[#table(
    columns: (33.33%, 33.33%, 33.33%),
    align: (left,left,left,),
    table.header([ADR], [Documento], [Decisión Fundamental],),
    table.hline(),
    [#strong[001]], [#link(<adr-001>)[ADR-001]], [Keypoints
    de tobillos para anclaje físico al suelo inmune a posturas del
    torso.],
    [#strong[002]], [#link(<adr-002>)[ADR-002]], [Mapeo
    proyectivo DLT $3 times 3$ determinista en lugar de redes neuronales
    3D pesadas.],
    [#strong[003]], [#link(<adr-003>)[ADR-003]], [Aceleración
    en silicio heterogéneo (Apple Neural Engine / GPU) desacoplada de
    PyTorch.],
    [#strong[004]], [#link(<adr-004>)[ADR-004]], [Schmitt
    trigger espacial y filtrado cinemático contra el #emph[chattering]
    en actuadores.],
    [#strong[005]], [#link(<adr-005>)[ADR-005]], [Verificación
    matemática preventiva de colinealidad y condicionamiento
    $kappa\(H\)< 10^6$.],
    [#strong[006]], [#link(<adr-006>)[ADR-006]], [Micro-optimizaciones
    GEOS (C) y bypass instantáneo por vector de aproximación
    $v_n gt.eq 1.6 upright(" m/s")$.],
    [#strong[007]], [#link(<adr-007>)[ADR-007]], [Jerarquía
    de degradación ante pies tapados: tobillos $arrow.r$ bbox bottom
    $arrow.r$ coasting Kalman.],
    [#strong[008]], [#link(<adr-008>)[ADR-008]], [Estados
    (`OBSERVED`, `PREDICTED`, `STALE`) y desescalada bloqueada sin
    fotones reales.],
    [#strong[009]], [#link(<adr-009>)[ADR-009]], [Desacoplamiento
    formal entre autómata espacial de ocupación y temporizador de
    permanencia.],
    [#strong[010]], [#link(<adr-010>)[ADR-010]], [Doble
    horizonte temporal: rendimiento de hardware
    ($T_(upright("system"))$) vs respuesta física
    ($T_(upright("event"))$).],
    [#strong[011]], [#link(<adr-011>)[ADR-011]], [Gating
    elipsoidal de Mahalanobis $chi^2$, asignación global Húngara y
    Spatial Birth NMS.],
    [#strong[012]], [#link(<adr-012>)[ADR-012]], [Composición
    fotorrealista pinhole de identidad única y HUD desacoplado para
    benchmarks.],
  )]
  , kind: table
  )

#divider()

== 🎯 5. Guion Maestro para Storytelling y Publicación Técnica
<guion-maestro-para-storytelling-y-publicación-técnica>
+ #strong[El Gancho (The Hook):] #emph[¿Por qué no deberías usar un
  modelo de Deep Learning para decidir cuándo parar una máquina
  industrial?]
+ #strong[El Problema Real:] El ruido estocástico en visión artificial,
  el #emph[chattering] de relés y la falsa sensación de seguridad de
  predecir en píxeles de pantalla.
+ #strong[El Puente Matemático:] La homografía planar ($Z_w = 0$) y por
  qué proyectar al plano métrico del suelo convierte un problema
  incierto de computer vision en un problema clásico de cinemática y
  control lineal.
+ #strong[La Arquitectura Asimétrica:] Explicar el Schmitt trigger
  ($P_(upright("danger"))$ vs $P_(upright("release"))$) y por qué la
  entrada a peligro debe ser instantánea (bypass ISO 13855 a
  $1.6 upright(" m/s")$) pero la salida exige confirmación óptica
  estricta con fotones reales.
+ #strong[El Reto de los Datos Sintéticos (Domain Gap):] Cómo resolvimos
  la validación determinista creando un generador de sprites con
  identidad única, escala pinhole estenopeica y sombras gaussianas que
  elevó la detección de 0% a 100% (confianza 0.86).
+ #strong[La Conclusión:] La mejor arquitectura no es la que satura el
  pipeline de redes neuronales, sino la que sabe exactamente dónde
  termina el rol de la inferencia probabilística y dónde toma el control
  la ingeniería determinista.

#pagebreak()

= 2. Especificación Técnica Formal del Sistema Edge AI <cap-especificacion>
== Diseño Arquitectónico y Especificación Técnica de un MVP de Visión Artificial en el Edge para la Detección de Intrusión y Permanencia en Zonas Industriales Restringidas
<diseño-arquitectónico-y-especificación-técnica-de-un-mvp-de-visión-artificial-en-el-edge-para-la-detección-de-intrusión-y-permanencia-en-zonas-industriales-restringidas>

#divider()

=== 1. Marco Teórico y Razonamiento de Seguridad Industrial (Inspirado en ISO 13855:2024)
<marco-teórico-y-razonamiento-de-seguridad-industrial-inspirado-en-iso-138552024>
#quote(block: true)[
#strong[Definición Formal del Problema:] #emph[Given a video stream from
a fixed monocular camera observing an approximately planar floor,
estimate the ground-plane position of visible workers, determine whether
they enter a configured metric restricted zone, and emit temporally
stable intrusion and dwell events while characterizing end-to-end
processing latency.]
]

#quote(block: true)[
\[!CAUTION\] #strong[Non-goal:] #emph[This prototype is not a certified
safety function and must not be used to stop or control hazardous
machinery.]

#strong[Aviso de Alcance y Seguridad Funcional (Disclaimer):]
#emph[Experimental vision-based intrusion monitoring system inspired by
industrial safety-zone concepts and ISO 13855 safety-distance reasoning.
Not a safety-rated protective device.] Este desarrollo es un prototipo
experimental de investigación aplicada. No constituye un Equipo de
Protección Electrosensible (ESPE) ni un Dispositivo de Protección Basado
en Visión (VBPD) certificado funcionalmente bajo IEC 61496, ISO 13849 o
IEC 61508. Su propósito es servir como banco de estudio para evaluar
latencias de percepción ($t_1$), filtrado métrico planar y dinámicas
temporales en el Edge.
]

La norma internacional #strong[ISO 13855:2024] regula el posicionamiento
y dimensionamiento de salvaguardas con respecto a la velocidad de
aproximación del cuerpo humano hacia un punto de peligro. Si bien los
dispositivos certificados funcionalmente requieren hardware y ciclos de
vida normados, la formulación matemática de ISO 13855 provee un marco
conceptual riguroso para #strong[razonar sobre presupuestos de latencia
(#emph[latency budgets]) y distancias de separación] en sistemas de
visión artificial.

Para una aproximación dinámica con dirección humana desconocida, la
distancia de separación requerida $S$ (medida en milímetros) se calcula
mediante la siguiente formulación estándar:

$ S =\(K times T\)+ C + C_(upright("dyn")) + Z_(upright("extra")) $

En esta ecuación: \* #strong[$K$:] Representa la velocidad de
aproximación del cuerpo o de las extremidades. La norma especifica una
velocidad de $2000 upright(" mm/s")$ para la aproximación de
extremidades superiores y $1600 upright(" mm/s")$ para la velocidad
general de marcha humana. \* #strong[$T$:] El tiempo total de respuesta
del sistema (en segundos), que integra tres componentes temporales:
$ T = t_1 + t_2 + t_3 $ \* $t_1$: Tiempo de respuesta del sistema de
control relativo a la seguridad (latencia total del pipeline de visión
Edge: captura, preprocesamiento, inferencia y lógica de control). \*
$t_2$: Tiempo de respuesta del controlador/PLC de seguridad o relé de
disparo. \* $t_3$: Tiempo de parada mecánica inercial de la máquina
(#emph[stopping performance]). \* #strong[$C$:] Suplementos por
distancia de alcance asociados a la geometría de la zona de protección.
\* #strong[$C_(upright("dyn"))$:] Suplemento dinámico que compensa el
movimiento del punto de peligro durante el proceso de parada:
$ C_(upright("dyn")) = v_(upright("hazard")) times t_3 + 1 / 2 a_(upright("hazard")) times t_3^2 $
Donde $v_(upright("hazard"))$ es la velocidad inicial del peligro y
$a_(upright("hazard"))$ la desaceleración mecánica. \*
#strong[$Z_(upright("extra"))$:] Margen suplementario para absorber
incertidumbres de medición, errores en la calibración
intrínseca/extrínseca de las cámaras, variaciones de reflectancia y
degradación en el par de frenado.

La norma establece que bajo ninguna circunstancia la distancia $S$ puede
ser inferior a un límite absoluto de #strong[$100 upright(" mm")$]. Por
consiguiente, la latencia del software del MVP en el dispositivo Edge
($t_1$) limita de manera directa la distancia física mínima a la que se
debe desplegar la #emph[virtual fence] o barrera digital.

#divider()

=== 2. Arquitectura de Sistema y Pipeline de Procesamiento en Tiempo Real
<arquitectura-de-sistema-y-pipeline-de-procesamiento-en-tiempo-real>
==== 2.1 Cadena de Procesamiento Principal (Scope Freeze del MVP)
<cadena-de-procesamiento-principal-scope-freeze-del-mvp>
Para preservar la viabilidad técnica y evitar la dispersión de
esfuerzos, el alcance del MVP se estructura de forma lineal y
determinista:

```
Recorded Video / Ingestion
        ↓
  Person Pose (YOLO11n-Pose ONNX)
        ↓
  Ground Point (Extracción de tobillos)
        ↓
  Homography (DLT 2D a coordenadas de planta métrica)
        ↓
  Metric Location (Posición X, Y en metros)
        ↓
  Spatial Filtering (Filtro de Kalman 2D CV)
        ↓
  Restricted-Zone State (Spatial FSM con doble histéresis)
        ↓
  Dwell State (Permanencia y acumulación de tiempo en peligro)
        ↓
Visualization + Event Log (Dual View y telemetría JSON)
        ↓
Latency Profiling (Medición T1 de fin a fin según ISO 13855)
```

===== Clasificación de Requerimientos y Priorización de Alcance
<clasificación-de-requerimientos-y-priorización-de-alcance>
+ #strong[MVP Obligatorio (Principal):]
  - Ingestión de video grabado/stream con preprocesamiento letterbox
    $\(640 times 640\)$.
  - Inferencia con YOLO11n-pose en ONNX Runtime desacoplado.
  - Extracción de punto de apoyo en suelo a partir del punto medio de
    tobillos (`left_ankle`, `right_ankle`) con filtrado por confianza.
  - Mapeo perspectiva a coordenadas métricas reales en metros mediante
    homografía planar DLT ($Z_w = 0$).
  - Filtro de suavizado métrico Kalman 2D multiobjeto con estimación de
    velocidad $\(dot(X)\,dot(Y)\)$ y mitigación de oclusiones
    temporales.
  - Máquina de estados espacial (`SpatialFSM`) con histéresis geográfica
    concéntrica ($P_(upright("danger"))$ vs $P_(upright("release"))$) e
    histéresis temporal ($N_(upright("confirm"))$).
  - Control de permanencia (#emph[dwell time]) con alertas de
    aproximación, advertencia y violación.
  - Compositor dual en tiempo real (vista de cámara con overlays + vista
    cenital métrica Top-Down BEV) y registro de eventos JSON.
  - Medición de latencia de reacción $T_1$ por etapas y métricas de
    percentiles (p50, p95, p99).
+ #strong[Secundario (Sólo si sobra tiempo):]
  - Comparación y benchmark de rendimiento PyTorch vs ONNX Runtime.
  - Evaluación granular de rendimiento con CoreML Execution Provider en
    Apple Silicon.
  - Baseline comparativo contra detectores alternativos más compactos.
+ #strong[Fuera de Alcance del MVP (Definitivamente después):]
  - Despliegue optimizado en GPU NVIDIA GTX 1050 (requiere cuantización
    PTQ INT8).
  - Integración nativa con TensorRT y pipelines zero-copy DeepStream.
  - Adaptaciones para hardware embebido heterogéneo (NVIDIA Jetson
    Nano/Orin, Raspberry Pi).
  - Empaquetado en contenedor Docker para distribución industrial.
  - Fusión sensorial con dispositivos físicos (sensores LiDAR, radares
    industriales, cortinas fotoeléctricas).
  - Topología multi-cámara con calibración extrínseca combinada y
    re-identificación de operarios.
  - Re-entrenamiento y fine-tuning de modelos en datasets de seguridad
    específicos.

#divider()

=== 3. Evaluación de Arquitecturas Deep Learning y Plataformas de Cómputo Edge
<evaluación-de-arquitecturas-deep-learning-y-plataformas-de-cómputo-edge>
==== 3.1 Análisis Comparativo de Modelos
<análisis-comparativo-de-modelos>
#figure(
  align(center)[#table(
    columns: (14.29%, 14.29%, 14.29%, 14.29%, 14.29%, 14.29%, 14.29%),
    align: (left,left,left,left,left,left,left,),
    table.header([Modelo], [Parámetros (M)], [FLOPs (G)], [mAP 50-95
      (%)], [Latencia CPU ONNX (ms)], [Latencia TensorRT INT8
      (ms)], [Plataforma Recomendada],),
    table.hline(),
    [#strong[YOLOX-Nano]], [0.91], [1.08], [25.8], [\~18.2], [\~3.1], [Microcontroladores
    \/ Edge Low-Power],
    [#strong[YOLOv8n]], [3.2], [8.7], [37.3], [\~80.4], [\~4.2], [NVIDIA
    Jetson Nano / GTX 1050 (INT8)],
    [#strong[YOLOv11n]], [2.6], [6.5], [39.5], [\~56.1], [\~3.8], [NVIDIA
    Jetson Orin Nano / CPU Edge],
    [#strong[YOLO26n]], [2.4], [5.8], [39.8], [\~38.9], [\~2.9], [Procesadores
    Embebidos NMS-Free],
    [#strong[YOLOv8s]], [11.2], [28.6], [44.9], [\~128.4], [\~7.6], [NVIDIA
    Jetson Orin / GTX 1050 (INT8)],
    [#strong[YOLOv11s]], [9.4], [21.5], [47.0], [\~90.0], [\~6.1], [NVIDIA
    Jetson Orin Nano / Xavier NX],
  )]
  , kind: table
  )

==== 3.2 Consideraciones de Hardware y Trampas de Implementación
<consideraciones-de-hardware-y-trampas-de-implementación>
- #strong[Arquitectura NVIDIA Pascal (ej. GTX 1050, Compute Capability
  6.1):]
  - #emph[Restricción de Silicio:] Aunque Pascal tiene soporte
    #emph[full-rate] para operaciones enteras #strong[INT8], su cómputo
    en #strong[FP16] está penalizado de fábrica (#emph[low-rate], 1:64
    respecto a FP32).
  - #emph[Directriz Obligatoria:] Cualquier despliegue en Pascal
    requiere #strong[cuantización post-entrenamiento (PTQ) a INT8] con
    TensorRT y dataset de calibración. En cambio, arquitecturas Ampere u
    Orin cuentan con Tensor Cores que aceleran FP16 e INT8
    indistintamente.
- #strong[Aceleradores Edge TPU (Google Coral):]
  - #emph[Trampa de Ejecución Mixta:] Si la red incluye operadores no
    soportados nativamente por el compilador de la Edge TPU (atención
    compleja, DFL, NMS custom), se generan transferencias cíclicas de
    tensores por el bus del sistema entre la TPU y la CPU en cada
    fotograma, disparando la latencia de 20-30 ms a 1800-2100 ms y
    destruyendo el determinismo.

#divider()

=== 4. Analytics Espacio-Temporales: Homografía, Pose e Histéresis
<analytics-espacio-temporales-homografía-pose-e-histéresis>
==== 4.1 Corrección de Perspectiva y Mapeo Planar
<corrección-de-perspectiva-y-mapeo-planar>
Se prohíbe el uso del centroide de cajas 2D debido a que la inclinación
angular de la cámara proyecta el torso o la cabeza dentro de la zona
peligrosa cuando los pies están en zona segura. El sistema extrae los
keypoints de los tobillos (`left_ankle: 15`, `right_ankle: 16`) y
calcula su punto medio:

$ p_(upright("ground")) = frac(p_(upright("ankle_left")) + p_(upright("ankle_right")), 2) $

Dicho punto se proyecta al plano métrico mediante la matriz de
homografía $H in bb(R)^(3 times 3)$:

$ mat(delim: "[", X_w; Y_w; 1) tilde.op H mat(delim: "[", u; v; 1) $

La calibración se realiza a partir de 4 o más puntos coplanares con
coordenadas métricas conocidas en planta mediante el algoritmo Solve-PnP
\/ DLT.

==== 4.2 Lógica de Intrusión y Permanencia: Spatial FSM
<lógica-de-intrusión-y-permanencia-spatial-fsm>
Para erradicar el #emph[flickering] en las alarmas, la FSM opera con 6
estados y doble histéresis:

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

- #strong[Histéresis Espacial:]
  $ P_(upright("release")) = P_(upright("danger")) xor Delta d\,quad Delta d in\[150\,300\]upright(" mm") $
- #strong[Histéresis Temporal:] Requiere
  $N_(upright("confirm")) gt.eq 3 upright("–") 5$ fotogramas
  consecutivos de persistencia para conmutar a alarma.
- #strong[Filtro Kalman 2D:] Suavizado de trayectoria métrica
  $\(X_w\,Y_w\,dot(X)_w\,dot(Y)_w\)$ para filtrar vibraciones de
  keypoints ($plus.minus 15 upright(" mm")$).

#divider()

=== 5. Corpus de Datasets Industriales y Data Augmentation
<corpus-de-datasets-industriales-y-data-augmentation>
==== 5.1 Datasets Abiertos
<datasets-abiertos>
- #strong[Roboflow Worker Safety:] \~4,280 imágenes (Person, Helmet,
  Vest). Inspección de EPIs en celdas industriales.
- #strong[Roboflow Construction Site Safety:] 717 a 2,286 imágenes
  (Hardhat, Machinery, Person). Supervisión cerca de maquinaria pesada.
- #strong[Mendeley Industrial Safety PPE:] 2,286 imágenes (Person,
  Safety Shoes, Gloves). Zonas con calzado obligatorio.
- #strong[Roboflow Manufacturing & Forklift:] \~24,000 imágenes
  (Forklift, Worker). Prevención de atropellos en tráfico mixto.
- #strong[MOT17 / MOT20 Benchmark:] 11,235 fotogramas. Calibración y
  benchmarking de rastreo multiobjeto.
- #strong[VIRAT Video Dataset:] \>100 horas de video HD. Pruebas de
  #emph[dwell time] e intrusión perimetral.

==== 5.2 Estrategias de Aumentación de Datos (Albumentations)
<estrategias-de-aumentación-de-datos-albumentations>
+ #strong[Aumentación Fotométrica:] Variaciones drásticas de
  brillo/contraste y ruido gaussiano para simular destellos de soldadura
  y caídas de luz en planta.
+ #strong[CutMix y Oclusión Sintética:] Superposición de fragmentos
  metálicos y barras de maquinaria para entrenar la red ante oclusiones
  corporales parciales.
+ #strong[Aumentación Geométrica de Perspectiva:] Deformaciones
  homográficas aleatorias para inmunizar el modelo frente a diferentes
  ángulos de montaje de cámara.

#divider()

=== 6. Compilación, Inferencia e Integración Industrial
<compilación-inferencia-e-integración-industrial>
+ #strong[Pipeline de Video Zero-Copy (NVIDIA DeepStream / GStreamer):]
  Evita transferencias entre memoria host y device, manteniendo la
  latencia de pre/post-procesamiento por debajo de $5 upright(" ms")$.
+ #strong[Cuantización INT8 (TensorRT PTQ):] Determinación de factores
  de escala $S$ y punto cero $Z$ mediante histogramas de activación con
  imágenes industriales reales.
+ #strong[Salidas Industriales:]
  - #strong[Capa Física (Relé de Seguridad / GPIO):] Disparo directo del
    bucle de paro de emergencia en $< 5 upright(" ms")$.
  - #strong[Automatización (Modbus TCP / OPC UA):] Desaceleración
    controlada y modo colaborativo en PLCs.
  - #strong[Telemetría (MQTT / JSON):] Timestamp, Worker ID, coordenadas
    de intrusión y clips de video para auditoría SCADA/Cloud.

#divider()

=== 7. Referencias
<referencias>
+ #emph[Safety standard EN ISO 13855 for the positioning of safeguards]
  --- Pilz Safety Automation.
+ #emph[Vision-Based Protective Devices] --- IGI Global Research.
+ #emph[Protective devices employing 3D safety zones on machines] ---
  DGUV (IFA).
+ #emph[AIOS in Practice: Setting Up a Virtual Fence for Industrial
  Applications] --- DT Labs.

#pagebreak()

= 3. Directivas de Seguridad y Modelo Matemático ISO 13855:2024 <cap-iso13855>
== Razonamiento de Distancias de Seguridad y Presupuestos Temporales (Marco ISO 13855:2024)
<razonamiento-de-distancias-de-seguridad-y-presupuestos-temporales-marco-iso-138552024>
#quote(block: true)[
\[!CAUTION\] #strong[Aviso de Alcance y Seguridad Funcional
(Disclaimer):] #emph[Experimental vision-based intrusion monitoring
system inspired by industrial safety-zone concepts and ISO 13855
safety-distance reasoning. Not a safety-rated protective device.] Este
documento utiliza las ecuaciones y conceptos de la norma ISO 13855:2024
exclusivamente como #strong[marco analítico para modelar el presupuesto
de latencia ($T_1$) y dimensionar distancias de separación teóricas]. El
software desarrollado es un prototipo experimental y no cuenta con
certificación SIL/PL para gobernar circuitos de parada de emergencia en
maquinaria industrial sin salvaguardas certificadas.
]

#divider()

=== 1. Presupuesto Temporal y Modelo de Separación Teórico
<presupuesto-temporal-y-modelo-de-separación-teórico>
En aplicaciones industriales de zonas de peligro asistidas por visión
artificial, la distancia mínima de separación de seguridad ($S$) entre
el límite de detección y el punto peligroso de la maquinaria está
gobernada por:

$ S =\(K times T\)+ C + C_(upright("dyn")) + Z_(upright("extra")) $

Donde: \* #strong[$K$:] Velocidad de aproximación del cuerpo humano
(típicamente $1600 upright(" mm/s")$ para aproximación transversal o
$2000 upright(" mm/s")$ para aproximación directa). \* #strong[$T$:]
Tiempo total de respuesta de la cadena de seguridad:
$ T = t_1 + t_2 + t_3 $ \* $t_1$: Latencia total del pipeline de visión
por computadora (adquisición + inferencia + homografía + tracking). \*
$t_2$: Tiempo de respuesta del controlador/PLC de seguridad o relé de
disparo. \* $t_3$: Tiempo de parada mecánica (#emph[stopping
performance]) de la máquina/robot. \* #strong[$C$:] Distancia de
penetración intrínseca según resolución y posición del sensor. \*
#strong[$C_(upright("dyn"))$:] Margen adicional por variabilidad
dinámica del movimiento humano. \* #strong[$Z_(upright("extra"))$:]
Factor de incertidumbre de medición métrica y jitter del sensor.

==== Presupuesto para el Pipeline de Visión ($t_1$)
<presupuesto-para-el-pipeline-de-visión-t_1>
- #strong[Límite Normativo:] $t_1 lt.eq 50 upright(" ms")$ (tasa de
  refresco efectiva $gt.eq 20 upright(" FPS")$).
- #strong[Margen en Inferencia (Bloque 2):] Inferencia con YOLO Pose
  ONNX en Apple Silicon CoreML medida a
  $t_(upright("infer")) lt.eq 20.5 upright(" ms")$ ($p_95$).
- #strong[Margen Disponible para Bloque 3:] $approx 29.5 upright(" ms")$
  para captura de frame, proyección DLT, filtrado Kalman y evaluación de
  polígonos.

#divider()

=== 2. Anclaje Espacial Mediante Keypoints de Tobillos
<anclaje-espacial-mediante-keypoints-de-tobillos>
Para anular las falsas alarmas provocadas por la inclinación cenital o
angular de la cámara enfrente de operadores cuyos torsos o cabezas
intersectan la zona pero cuyos pies están fuera: \*
#strong[Prohibición:] Se prohíbe el centroide de la caja delimitadora
(#emph[bounding box centroid]) o la base central de la caja 2D. \*
#strong[Punto de Contacto Real:]
$ p_(upright("ground")) = frac(p_(upright("ankle_left")) + p_(upright("ankle_right")), 2) $
Si un tobillo está ocluido ($c o n f < 0.3$), se adopta el tobillo
visible con mayor confianza. Si ambos están ocluidos temporalmente, el
Filtro Kalman 2D extrapola la trayectoria en espacio métrico.

#divider()

=== 3. Matriz de Homografía Planar ($2 D arrow.r upright("Métrico")$)
<matriz-de-homografía-planar-2d-rightarrow-textmétrico>
Dado que el contacto con el piso ocurre en el plano de planta ($Z = 0$),
la relación entre las coordenadas de la imagen $\(u\,v\)$ y el plano de
trabajo $\(X_w\,Y_w\)$ en metros es biyectiva y lineal en coordenadas
homogéneas:

$ mat(delim: "[", X'_w; Y'_w; W) = H mat(delim: "[", u; v; 1)\,quad X_w = X'_w / W\,quad Y_w = Y'_w / W $

La matriz $H in bb(R)^(3 times 3)$ se calcula con 4 puntos coplanares de
calibración mediante DLT (#emph[Direct Linear Transformation]).

#divider()

=== 4. Control de Estabilidad e Histéresis Espacio-Temporal
<control-de-estabilidad-e-histéresis-espacio-temporal>
Para evitar #emph[chattering] y conmutaciones erráticas en los relés de
seguridad: 1. #strong[Doble Polígono Concéntrico:] \*
$P_(upright("danger"))$: Zona de intrusión crítica que activa la parada
de emergencia. \* $P_(upright("release"))$: Polígono expandido por un
margen $Delta d in\[150\,300\]upright(" mm")$. El sistema no transiciona
de regreso a `OUTSIDE` hasta que los pies del operario no crucen
completamente fuera de $P_(upright("release"))$. 2. #strong[Ventana
Temporal de Confirmación:] \* Requiere
$N_(upright("confirm")) gt.eq 3 upright("–") 5$ fotogramas consecutivos
de persistencia para conmutar estados. 3. #strong[Filtro Kalman 2D:] \*
Suavizado de coordenadas métricas $\(X_w\,Y_w\,dot(X)_w\,dot(Y)_w\)$ que
absorbe el jitter de detección de keypoints
($plus.minus 15 upright(" mm")$).

#divider()

=== 5. Estrategia de Hardware & Cuantización
<estrategia-de-hardware-cuantización>
- #strong[Fase 1 (Desarrollo local - Apple Silicon M1/M2/M3):]
  - Inferencia: ONNX Runtime con `CoreMLExecutionProvider` (346/354 ops
    delegados a ANE/GPU).
  - Fallback: `CPUExecutionProvider` con ARM NEON (4 hilos).
- #strong[Fase 2 (Despliegue Industrial - NVIDIA GTX 1050 Notebook /
  Jetson):]
  - Arquitectura Pascal (Compute Capability 6.1): El silicio de Pascal
    tiene penalización de rendimiento en cómputo FP16 (tasa 1:64 en FP16
    vs FP32).
  - #strong[Estrategia Obligatoria en Pascal:] Cuantización
    #strong[INT8] post-entrenamiento (PTQ) con TensorRT y dataset de
    calibración.

#divider()

=== 6. Salida de Datos: Capa Física vs Telemetría
<salida-de-datos-capa-física-vs-telemetría>
- #strong[Lazo Crítico de Seguridad (Parada de Emergencia):]
  - Salida a relé de seguridad / GPIO físico conectado al circuito de
    parada de la máquina. Latencia $< 5 upright(" ms")$, sin depender de
    stacks de red.
- #strong[Capa Telemática (Monitoreo y Dwell Time):]
  - Protocolos: Modbus TCP / OPC UA para interacción con PLCs de línea;
    MQTT / JSON para eventos de permanencia prolongada (#emph[dwell
    time]) y auditoría en SCADA/Cloud.

#pagebreak()

= 4. Bitácora de Preguntas & Respuestas de Arquitectura <cap-faq>
== Bitácora de Conceptos Clave, Preguntas & Respuestas de Arquitectura
<bitácora-de-conceptos-clave-preguntas-respuestas-de-arquitectura>
Este documento recopila las discusiones técnicas, preguntas
fundamentales y fundamentos de ingeniería analizados a lo largo del
diseño del proyecto #strong[Industrial Edge Safety Guard]. Su propósito
es servir como material de estudio y referencia para comprender el
#emph[por qué] detrás de cada decisión técnica.

#divider()

=== 1. Hardware y Aceleración Edge
<hardware-y-aceleración-edge>
==== P1: ¿Por qué desarrollamos con ONNX Runtime en lugar de TensorRT en la máquina local?
<p1-por-qué-desarrollamos-con-onnx-runtime-en-lugar-de-tensorrt-en-la-máquina-local>
- #strong[Contexto:] La máquina de desarrollo es un Mac con Apple
  Silicon (M1 arm64).
- #strong[Fundamento Técnico:]
  - #strong[Incompatibilidad Física:] TensorRT es software propietario
    de NVIDIA acoplado a la arquitectura CUDA; no existe ni puede
    ejecutarse en Apple Silicon.
  - #strong[Desacoplamiento Arquitectónico:] ONNX (#emph[Open Neural
    Network Exchange]) actúa como capa de abstracción intermedia. Al
    encapsular la inferencia en la clase `OnnxEngine`, la lógica de
    negocio (homografía, FSM, tracking) no sabe ni le importa qué
    hardware corre debajo.
  - #strong[Rendimiento Nativo:] En macOS, ONNX Runtime delega mediante
    `CoreMLExecutionProvider` en el Apple Neural Engine (ANE) y GPU de
    Apple, logrando latencias de inferencia de
    $approx 18 upright("–") 20 upright(" ms")$ ($> 54 upright(" FPS")$).
  - #strong[Portabilidad:] Cuando el código se traslade a un nodo
    industrial con GPU NVIDIA (ej. GTX 1050), solo se cambia el
    Execution Provider a `CUDAExecutionProvider` o TensorRT sin alterar
    una sola línea de código del sistema.

==== P2: ¿Por qué la NVIDIA GTX 1050 (arquitectura Pascal) exige cuantización obligatoria a INT8 y prohíbe FP16?
<p2-por-qué-la-nvidia-gtx-1050-arquitectura-pascal-exige-cuantización-obligatoria-a-int8-y-prohíbe-fp16>
- #strong[Contexto:] Se proyecta desplegar el MVP en una notebook con
  GTX 1050.
- #strong[Fundamento Técnico:]
  - #strong[Restricción de Silicio (Compute Capability 6.1):] Las GPUs
    basadas en Pascal no poseen Tensor Cores dedicados. A nivel de
    silicio, las operaciones en coma flotante de media precisión
    (#strong[FP16]) están penalizadas de fábrica a una tasa de $1 : 64$
    en comparación con precisión simple (#strong[FP32]). Correr en FP16
    en Pascal degrada el rendimiento drásticamente.
  - #strong[Soporte Full-Rate INT8:] Pascal sí soporta instrucciones
    escalares de enteros de 8 bits (#strong[INT8]) a tasa completa
    (#emph[full-rate]).
  - #strong[Conclusión de Ingeniería:] Para lograr alta velocidad en una
    GTX 1050 con TensorRT, es mandatorio realizar #strong[cuantización
    post-entrenamiento (PTQ) a INT8] utilizando un dataset de
    calibración para generar los factores de escala dinámicos.

#divider()

=== 2. Visión por Computadora & Proyección Homográfica
<visión-por-computadora-proyección-homográfica>
==== P3: ¿Por qué no se pueden medir distancias en metros usando una regla de tres directa sobre los píxeles de una cámara inclinada?
<p3-por-qué-no-se-pueden-medir-distancias-en-metros-usando-una-regla-de-tres-directa-sobre-los-píxeles-de-una-cámara-inclinada>
- #strong[Contexto:] Las cámaras de seguridad industrial se instalan en
  posiciones elevadas inclinadas en ángulo hacia el suelo.
- #strong[Fundamento Técnico:]
  - #strong[Deformación Proyectiva y Puntos de Fuga:] La proyección de
    perspectiva en una cámara no conserva distancias euclidianas ni
    paralelismo. Las líneas paralelas en el mundo real convergen hacia
    puntos de fuga en el plano de la imagen.
  - #strong[No linealidad:] Diez píxeles en la parte inferior del
    encuadre (cerca de la cámara) pueden equivaler a $15 upright(" cm")$
    en el suelo, mientras que esos mismos diez píxeles cerca del
    horizonte superior equivalen a $3 upright(" metros")$. Cualquier
    interpolación lineal o regla de tres genera errores métricos
    catastróficos que invalidan el cumplimiento de distancias de
    seguridad.

==== P4: ¿Por qué usamos una Matriz de Homografía 2D ($3 times 3$) y no necesitamos calcular el eje $Z$ (profundidad 3D)?
<p4-por-qué-usamos-una-matriz-de-homografía-2d-3-times-3-y-no-necesitamos-calcular-el-eje-z-profundidad-3d>
- #strong[Contexto:] Tradicionalmente se cree que para conocer la
  posición en el mundo real se necesita una cámara 3D o estimar el eje
  $Z$.
- #strong[Fundamento Técnico (El truco maestro de la arquitectura):]
  - #strong[Pérdida de Dimensión en Cámaras 2D:] Una cámara monocular
    proyecta puntos 3D $\(X\,Y\,Z\)$ a píxeles 2D $\(u\,v\)$, perdiendo
    la profundidad (infinitos puntos a lo largo del rayo proyectan al
    mismo píxel).
  - #strong[La Restricción Planar ($Z_w = 0$):] Como el sistema utiliza
    estimación de pose humana para detectar #strong[los tobillos y pies
    del operario], sabemos físicamente que ese punto está en contacto
    con el suelo. Si definimos nuestro sistema de coordenadas del mundo
    en el plano del piso, fijamos #strong[$Z_w = 0$].
  - #strong[Colapso de la Matriz de Cámara:] En la matriz de proyección
    general de cámara ($3 times 4$):
    $ mat(delim: "[", u; v; 1) tilde.op mat(delim: "[", p_11, p_12, p_13, p_14; p_21, p_22, p_23, p_24; p_31, p_32, p_33, p_34) mat(delim: "[", X_w; Y_w; upright(bold(0)); 1) $
    Al multiplicarse la tercera columna ($p_(i 3)$) por cero, dicha
    columna se anula por completo:
    $ mat(delim: "[", u; v; 1) tilde.op underbrace(mat(delim: "[", p_11, p_12, p_14; p_21, p_22, p_24; p_31, p_32, p_34), H med\(3 times 3\)) mat(delim: "[", X_w; Y_w; 1) $
  - #strong[Biyectividad e Inversión:] La matriz resultante
    $H in bb(R)^(3 times 3)$ es cuadrada, no singular e invertible. Nos
    permite mapear de forma exacta y bidireccional el plano de la imagen
    con el plano del suelo ($X_w\,Y_w = H^(- 1) dot.op\[u\,v\,1\]^T$)
    mediante álgebra lineal pura en $< 0.1 upright(" ms")$, sin
    necesidad de sensores LiDAR ni cámaras estéreo de alto costo.

==== P5: ¿Por qué se necesitan exactamente 4 puntos para calibrar la Homografía?
<p5-por-qué-se-necesitan-exactamente-4-puntos-para-calibrar-la-homografía>
- #strong[Fundamento Técnico:]
  - Una matriz de $3 times 3$ posee 9 coeficientes.
  - Sin embargo, al operar en coordenadas proyectivas homogéneas, la
    matriz está definida salvo un factor de escala arbitrario $lambda$
    ($H$ y $lambda H$ representan la misma transformación geométrica).
    Por lo tanto, tiene
    $9 - 1 = upright(bold(8 upright(" grados de libertad")))$.
  - Cada par de puntos calibrados $\(u_i\,v_i\)arrow.r\(X_i\,Y_i\)$
    aporta dos ecuaciones algebraicas lineales independientes (una para
    la coordenada $X$ y otra para $Y$).
  - Para resolver 8 incógnitas necesitamos 8 ecuaciones:
    $ 4 upright(" puntos") times 2 upright(" ecuaciones/punto") = 8 upright(" ecuaciones") $
  - Con #strong[4 puntos de referencia coplanares (no colineales)]
    marcados en el suelo, el algoritmo DLT (#emph[Direct Linear
    Transformation]) calcula la matriz de forma unívoca y exacta.

==== P6: ¿Por qué no usamos el borde inferior de una Bounding Box (Bottom-Center) y qué costos acarrea Pose?
<p6-por-qué-no-usamos-el-borde-inferior-de-una-bounding-box-bottom-center-y-qué-costos-acarrea-pose>
- #strong[Fundamento Técnico y Trade-Off:]
  - #strong[El Baseline de Detección:] El enfoque tradicional de bajo
    costo no es el centroide 2D (que proyecta el torso), sino la base
    central de la caja delimitadora:
    $ p_(upright("ground_bbox")) = (frac(x_min + x_max, 2) \, thin y_max) $
  - #strong[Por qué Pose ofrece mejor semántica:] En cámaras con ángulo
    cenital, el punto medio de los tobillos detecta exactamente el apoyo
    físico de las extremidades inferiores en el piso ($Z_w = 0$). Si el
    operario se inclina, estira un brazo o manipula una herramienta
    larga, el bounding box crece lateralmente o hacia abajo de forma
    artificial, mientras que los tobillos permanecen anclados al suelo
    real.
  - #strong[El Costo y los Riesgos Ocultos de Pose:]
    + #emph[Costo Computacional:] Un modelo de Pose tiene mayor número
      de capas/canales de salida, requiriendo más cómputo y memoria que
      un detector simple de cajas.
    + #emph[Oclusiones Frecuentes:] En un entorno industrial, los
      tobillos sufren oclusiones constantes por maquinaria baja,
      pallets, carretillas o ropa de trabajo holgada.
    + #emph[Borde del Encuadre:] Si el operario camina cerca del borde
      inferior de la cámara, los pies pueden quedar fuera de la imagen
      mientras el torso sigue dentro.
    + #emph[Degradación de Confianza:] Cuando la confianza del keypoint
      decae, el sistema debe degradar a modo #emph[coasting] (Kalman) o
      apoyarse en el tobillo visible.
  - #strong[Hipótesis Experimental:] Pose se adopta como hipótesis
    primaria por su valor anatómico, pero se mantiene la comparación
    contra Bbox Bottom-Center como experimento abierto para medir si la
    ganancia en fidelidad geométrica compensa la tasa de oclusión y la
    sobrecarga computacional.

==== P8: ¿Por qué con exactamente $N = 4$ puntos el error de reproyección es siempre 0 y cómo se mide un error real?
<p8-por-qué-con-exactamente-n4-puntos-el-error-de-reproyección-es-siempre-0-y-cómo-se-mide-un-error-real>
- #strong[Fundamento Técnico:]
  - En geometría proyectiva, 4 pares de puntos no colineales en el plano
    aportan exactamente 8 ecuaciones lineales independientes para 8
    grados de libertad.
  - El sistema lineal no homogéneo resultante es determinado
    ($8 times 8$), por lo que existe una solución única exacta con
    residuo algebraico nulo.
  - Si se introducen pequeños errores o ruido a cualquiera de los 4
    puntos, el algoritmo DLT simplemente calcula la matriz $H$ que mapea
    con exactitud esos puntos ruidosos (residuo $upright("RMSE") = 0$).
  - Para medir y auditar el error de reproyección real
    ($upright("RMSE") > 0$) de una cámara en planta, el sistema de
    calibración debe ser #strong[sobredeterminado ($N > 4$)] o
    contrastarse contra puntos de verificación independientes
    (#emph[ground-truth] no usados en el ajuste).

==== P9: ¿Cómo se detecta degeneración geométrica en $N > 4$ puntos sin rechazar marcadores en líneas rectas?
<p9-cómo-se-detecta-degeneración-geométrica-en-n-4-puntos-sin-rechazar-marcadores-en-líneas-rectas>
- #strong[Fundamento Técnico:]
  - En un cuadrilátero ($N = 4$), si cualquier triplete de puntos es
    colineal ($upright("Area") approx 0$), el polígono colapsa en un
    triángulo o línea y la matriz $H$ es singular.
  - Sin embargo, si en planta se calibran $N = 8$ puntos a lo largo del
    perímetro de un rectángulo (ej. 3 puntos en el borde inferior), esos
    3 puntos #emph[son] colineales entre sí. Rechazar la calibración por
    tener un triplete colineal sería un error de diseño (falso rechazo).
  - #strong[Regla Arquitectónica:] Para $N = 4$, ningún triplete puede
    ser colineal. Para $N > 4$, la condición necesaria y suficiente es
    que el rango afín sea pleno ($upright("rank") = 3$) y que
    #strong[exista al menos un subconjunto de 4 puntos en posición
    general] (ningún triplete colineal en ese cuadrilátero).

#divider()

=== 3. Dinámica Temporal & Seguridad Funcional
<dinámica-temporal-seguridad-funcional>
==== P7: ¿Cómo se previene el "chattering" o conmutación errática en los relés de seguridad?
<p7-cómo-se-previene-el-chattering-o-conmutación-errática-en-los-relés-de-seguridad>
- #strong[Fundamento Técnico:]
  - Si un operario trabaja o camina justo sobre el límite de la zona
    restringida, el ruido estocástico de detección
    ($plus.minus 15 upright(" mm")$) haría que un algoritmo simple
    conmute de alarma a seguro frame a frame (destruyendo contactores
    físicos y generando alarmas inútiles).
  - #strong[Solución de Tres Niveles:]
    + #strong[Filtro de Kalman 2D:] Suaviza la trayectoria
      $\(X_w\,Y_w\,dot(X)_w\,dot(Y)_w\)$ en el plano métrico,
      absorbiendo las vibraciones de los keypoints.
    + #strong[Histéresis Espacial:] Se configuran dos polígonos
      concéntricos: $P_(upright("danger"))$ (activa intrusión) y
      $P_(upright("release"))$ (libera intrusión), distanciados por un
      margen $Delta d in\[150\,300\]upright(" mm")$.
    + #strong[Histéresis Temporal:] Se exige una persistencia mínima de
      $N_(upright("confirm")) gt.eq 3 upright("–") 5$ fotogramas
      consecutivos antes de cambiar el estado de la Máquina de Estados
      Finitos (`Spatial FSM`).

==== P10: ¿Por qué usamos un Filtro de Kalman 2D para estimar velocidad y no una resta numérica $Delta x\/Delta t$?
<p10-por-qué-usamos-un-filtro-de-kalman-2d-para-estimar-velocidad-y-no-una-resta-numérica-delta-x-delta-t>
- #strong[Fundamento Técnico:]
  - #strong[Explosión del Ruido por Derivación:] La cámara solo entrega
    coordenadas instantáneas. Si deriváramos numéricamente
    $v =\(x_t - x_(t - 1)\)\/Delta t$, a 30 FPS
    ($Delta t approx 0.033 upright(" s")$) un temblor estocástico de
    apenas $2 upright(" cm")$ en la detección del tobillo genera un pico
    ficticio de $0.6 upright(" m/s")$ ($2.16 upright(" km/h")$). Esto
    dispararía paradas de emergencia espurias.
  - #strong[Estimación de Estado Oculto:] Kalman mantiene un vector de
    estado continuo $upright(bold(x)) =\[X\,Y\,dot(X)\,dot(Y)\]^T$ con
    un modelo cinemático de velocidad constante (CV). La Ganancia de
    Kalman equilibra estadísticamente la predicción física con la
    medición ruidosa, entregando velocidad y trayectoria óptimas.
  - #strong[Ventajas en Seguridad (ISO 13855):]
    + #emph[Vector Direccional:] Permite saber si el operario se
      desplaza hacia la zona de peligro o en paralelo a ella (evitando
      detener la máquina si camina tangencialmente).
    + #emph[Coast Mode (Oclusión):] Si un pie queda ocluido durante 2-3
      frames por maquinaria o pallets, el paso de predicción mantiene el
      seguimiento activo sin perder la continuidad ni el estado de
      seguridad.

==== P11: ¿Por qué una arquitectura de Visualización Dual (Vista de Cámara vs Vista Cenital Top-Down BEV)?
<p11-por-qué-una-arquitectura-de-visualización-dual-vista-de-cámara-vs-vista-cenital-top-down-bev>
- #strong[Fundamento Técnico:]
  - #strong[Vista 1: Perspectiva de Cámara con Realidad Aumentada
    (Overlay $H^(- 1)$):]
    - #emph[Propósito Operativo:] Muestra el video RGB en tiempo real
      con las zonas $P_(upright("danger"))$ y $P_(upright("release"))$
      reproyectadas mediante la homografía inversa $H^(- 1)$, junto con
      las cajas delimitadoras y esqueletos.
    - #emph[Valor de Ingeniería:] Permite al supervisor en planta
      validar visualmente qué "ve" el lente: corroborar que se detectan
      personas y no sombras, verificar la ausencia de oclusiones físicas
      en el lente (suciedad, cables sueltos) y monitorear la salud del
      sensor en el espacio de la imagen.
  - #strong[Vista 2: Vista Cenital Métrica Top-Down (Bird's-Eye View -
    BEV):]
    - #emph[Propósito Metrológico:] Genera un lienzo 2D ortogonal del
      suelo en metros (escala lineal constante
      $1 upright(" m") = N upright(" px")$). Dibuja la máquina, las
      zonas concéntricas, los operarios rastreados y sus vectores de
      velocidad $\[dot(X)\,dot(Y)\]$.
    - #emph[Valor Normativo (ISO 13855):] La distancia de seguridad
      $S = K times T + C$ es estrictamente métrica y no puede auditarse
      en píxeles debido a la distorsión proyectiva. La vista BEV permite
      medir distancias euclidianas reales y verificar la dirección
      exacta de aproximación hacia el peligro, además de integrarse
      directamente en gemelos digitales o pantallas HMI/SCADA
      industriales.

==== P12: ¿Por qué aplicamos un congelamiento de alcance (Scope Freeze) separando funcionalidades en Principal, Secundario y Futuro?
<p12-por-qué-aplicamos-un-congelamiento-de-alcance-scope-freeze-separando-funcionalidades-en-principal-secundario-y-futuro>
- #strong[Fundamento de Ingeniería:]
  - #strong[Ley de Rendimientos Decrecientes:] En sistemas de seguridad
    y visión artificial, agregar características complejas antes de
    validar la cadena causal primaria introduce vectores de fallo y
    acoplamientos innecesarios.
  - #strong[La Cadena Causal del MVP:]
    $ upright("Frame") arrow.r upright("Pose") arrow.r upright("Tobillos") arrow.r upright("Homografía") arrow.r upright("Ubicación Métrica") arrow.r upright("Kalman 2D") arrow.r upright("FSM") arrow.r upright("Dwell") arrow.r upright("Visualización Dual") arrow.r upright("Profiling") $
    Cada eslabón responde directamente a la hipótesis central de
    seguridad física bajo la norma ISO 13855:2024. Si este núcleo no es
    determinista y no cumple el presupuesto de tiempo $T_1$, cualquier
    adición periférica carece de valor.
  - #strong[Criterio de Segregación:]
    + #emph[Principal (Obligatorio):] Lo necesario para ingerir video,
      calcular distancias métricas, transicionar estados de seguridad y
      auditar latencias.
    + #emph[Secundario (Solo si sobra tiempo):] Benchmarks comparativos
      (PyTorch vs ONNX, CoreML granular, detectores alternativos) que
      aportan métricas de análisis pero no cambian la lógica de
      seguridad.
    + #emph[Futuro (Fuera de alcance):] Hardware específico (GTX 1050 /
      Jetson), optimizaciones propietarias (TensorRT), orquestación
      (Docker), multi-cámara o re-entrenamiento. Evitan inflar la
      complejidad del MVP antes de contar con un prototipo funcional
      cerrado.

==== P13: ¿Por qué este prototipo se presenta como "inspirado en el razonamiento de ISO 13855" y NUNCA como un "sistema que cumple ISO 13855"?
<p13-por-qué-este-prototipo-se-presenta-como-inspirado-en-el-razonamiento-de-iso-13855-y-nunca-como-un-sistema-que-cumple-iso-13855>
- #strong[Fundamento de Ingeniería y Seguridad Funcional (Diferencia
  Conceptual Crítica):]
  - #strong[Alcance Estricto de ISO 13855:] La norma ISO 13855 regula el
    cálculo de distancias de separación ($S = K dot.op T + C$) para
    salvaguardas mecánicas y dispositivos electrosensibles de protección
    (ESPE / VBPD) certificados. No aplica de manera directa a sistemas
    que operan exclusivamente como sensores de presencia (#emph[presence
    sensing]) sin arquitectura fail-safe tolerante a fallos de hardware.
  - #strong[Certificación vs Razonamiento:] Afirmar que un software en
    Python/ONNX "cumple ISO 13855" es un error conceptual grave. Una
    certificación de seguridad funcional exige redundancia de canal
    (categorías ISO 13849 PL d/e o IEC 61508 SIL 2/3), hardware
    calificado, análisis de modos de fallo (FMEA) y validación ante
    fallas sistemáticas.
  - #strong[La Postura Técnica Correcta:] Presentar el proyecto como: \>
    #emph[Experimental vision-based intrusion monitoring system inspired
    by industrial safety-zone concepts and ISO 13855 safety-distance
    reasoning. Not a safety-rated protective device.] \#\#\# P14: ¿Qué
    significa exactamente que el sistema reporte que una persona está a
    0.93 m del peligro?
- #strong[Fundamento de Metrología y Visión Computacional:]
  - #strong[La Falsa Precisión:] En una entrevista técnica o auditoría,
    responder "la homografía calculó que está a exactamente 93
    centímetros" denota inmadurez en visión por computadora.
  - #strong[El Modelo de Incertidumbre Compuesta:] La coordenada en
    metros es una función estimada
    $hat(P)_(upright("world")) = H\(hat(p)_(upright("feet"))\)$, donde
    se acumulan cinco fuentes de error independientes:
    + #emph[Pose estimation error:] Jitter e incertidumbre en la
      predicción de keypoints de tobillos.
    + #emph[Pixel quantization:] Resolución finita y discretización de
      la cuadrícula del sensor de cámara.
    + #emph[Camera calibration error:] Incertidumbre de medición en los
      puntos coplanares de referencia ground-truth.
    + #emph[Ground-plane assumption:] Pequeñas desviaciones o desniveles
      del piso respecto a la hipótesis plana ideal $Z_w = 0$.
    + #emph[Homography numerical error:] Amplificación de perturbaciones
      gobernada por el número de condición matricial $kappa\(H\)$,
      especialmente en zonas con ángulos rasantes. \#\#\# P15: ¿Qué hace
      el sistema cuando los pies del trabajador no se ven (oclusión por
      maquinaria) y qué es la propagación de confianza?
- #strong[Fundamento de Arquitectura y Modos de Fallo:]
  - #strong[El Escenario Crítico:] En una planta industrial, es habitual
    que una máquina baja o un pallet oculte los pies de un trabajador
    mientras su torso se aproxima al peligro. Si el estimador de pose
    reporta `conf(left_ankle) = 0.12` y `conf(right_ankle) = 0.08`, ¿qué
    se hace?

  - #strong[Las Cinco Opciones de Diseño:]

    - #emph[A) Rechazar la observación:] Descartar el dato en silencio
      genera un #strong[peligro ciego]: el trabajador sigue avanzando
      pero el sistema actúa como si no existiera nadie.
    - #emph[B) Usar un solo tobillo:] Si un tobillo supera el umbral
      ($c o n f gt.eq 0.5$), usarlo como anclaje. Válido, aunque
      introduce un sesgo lateral de hasta
      $25 upright("–") 30 upright(" cm")$.
    - #emph[C) Fallback a Bbox Bottom-Center:] Usar la base de la caja
      delimitadora. Mantiene la presencia pero puede tener sesgo si la
      base de la caja apoya sobre el obstáculo y no sobre el piso.
    - #emph[D) Predicción vía Tracker (Coasting):] El filtro de Kalman
      proyecta la trayectoria previa usando su modelo cinemático
      $\[dot(X)\,dot(Y)\]$ durante una ventana temporal acotada
      ($N_(upright("missed")) lt.eq 5$ frames
      $approx 160 upright(" ms")$).
    - #emph[E) Declarar Incertidumbre Explícita (Confidence
      Propagation):] Asociar una etiqueta de origen y confianza a cada
      coordenada.

  - #strong[La Política Implementada (Graceful Degradation):] El
    pipeline combina B, D y E en una jerarquía tipada:

    + Si ambos tobillos son válidos $arrow.r$ `ANKLES_DUAL` (confianza
      máxima).
    + Si uno es válido $arrow.r$ `ANKLE_SINGLE` (confianza media).
    + Si ambos están ocluidos $arrow.r$ Kalman retiene el track en modo
      `COASTING` extrapolando velocidad (`TRACKER_PREDICTED`).
    + Si la oclusión persiste $> 160 upright(" ms")$, se evalúa fallback
      a bbox o eliminación segura.

  - #strong[Propagación de Confianza:] El sistema no emite simples
    tuplas `(x, y)`\; conceptualmente emite:

    ```python
    PositionEstimate(xy_m, confidence, source="ankles | bbox | predicted", status="OBSERVED | PREDICTED | STALE", missed_count=k)
    ```

    Esto permite que la FSM distinga entre una alarma con certeza física
    directa y una alarma sostenida por inercia cinemática.

==== P16: ¿Por qué la predicción de Kalman NO es verdad física y cómo se calculan los horizontes de divergencia cinemática?
<p16-por-qué-la-predicción-de-kalman-no-es-verdad-física-y-cómo-se-calculan-los-horizontes-de-divergencia-cinemática>
- #strong[Contexto Normativo y Epistemológico:] En dispositivos de
  protección basados en visión (VBPD / ISO 13855:2024), cuando un
  operario sufre una oclusión momentánea (pies pasando tras un pallet o
  soporte), el Filtro de Kalman continúa proyectando su movimiento a
  lazo abierto (#emph[dead reckoning]).
- #strong[Fundamento Físico-Matemático:]
  - #strong["Predicción no es Verdad":] La predicción matemática
    $hat(upright(bold(x)))_k = F hat(upright(bold(x)))_(k - 1)$ asume
    velocidad constante. El operario real es libre de acelerar, frenar,
    tropezar o girar. Sin fotones del sensor, la certidumbre física se
    degrada progresivamente.
  - #strong[Fallo de la Derivada Discreta ($Delta x\/Delta t$):] El
    jitter de keypoints ($sigma approx 15 upright(" mm")$) amplificado a
    30 FPS ($Delta t = 0.0333 upright(" s")$) produce una dispersión de
    velocidad ficticia
    $sigma_v = frac(sqrt(2) sigma, Delta t) approx 0.64 upright(" m/s")$.
    El límite $3 sigma approx 1.91 upright(" m/s")$ superaría
    permanentemente el umbral industrial ISO 13855
    ($K = 1.6 upright(" m/s")$) incluso en trabajadores quietos.
  - #strong[Justificación de Velocidad Constante (CV) frente a
    Aceleración Constante (CA):]
    - La aceleración humana biomecánica máxima es
      $a_max approx 3.5 upright(" m/s")^2$ ($mu lt.eq 0.7$).
    - En un solo cuadro a 30 FPS, el desplazamiento por aceleración es
      $Delta x_(upright("acc")) = 1 / 2 a Delta t^2 approx 1.94 upright(" mm")$,
      casi un orden de magnitud menor al piso de ruido de los keypoints
      ($15 upright(" mm")$). Es físicamente inobservable en un único
      cuadro.
    - Estimar aceleración con un modelo CA exige la segunda diferencia
      discreta, cuya varianza
      $upright("Var")\(hat(a)\)= frac(6, Delta t^4) sigma_(upright("pos"))^2$
      arroja un error estándar
      $sigma_a approx 33.1 upright(" m/s")^2 med\(> 3.3 upright(" g")\)$,
      desestabilizando el filtro. Por ello, el modelo CV es el óptimo.
  - #strong[Envolvente Cuadrática de Divergencia vs Colchón de
    Histéresis ($Delta d = 200 upright(" mm")$):] Durante el
    #emph[coasting], la cota máxima de divergencia física obedece a
    $parallel Delta upright(bold(p))\(t\)parallel lt.eq 1 / 2 a_max t^2 + v_0 t\(1 - cos theta\)$.
    - $k = 0$ ($t = 0 upright(" ms")$):
      $upright(bold(0 upright(" mm")))$ $arrow.r$ #strong[`OBSERVED`]
      (Hecho empírico).
    - $1 lt.eq k lt.eq 3$ ($t lt.eq 100 upright(" ms")$): Divergencia
      $lt.eq 175 upright(" mm") < Delta d$ ($200 upright(" mm")$)
      $arrow.r$ #strong[`PREDICTED`] (Seguro para tracking y disparo).
    - $4 lt.eq k lt.eq 5$
      ($133 upright(" ms") lt.eq t lt.eq 167 upright(" ms")$):
      Divergencia $240 upright(" mm") - 308 upright(" mm") > Delta d$
      $arrow.r$ #strong[`STALE`] (Buffer superado, puramente
      especulativo).
    - $k > 5$ ($t > 167 upright(" ms")$): Pista eliminada (`EXPIRED`).
  - #strong[Detalle Completo:] Ver
    #link(<adr-008>)[ADR-008].

==== P17: ¿Por qué la desescalada de seguridad es asimétrica y qué ocurre cuando un intruso desaparece dentro de la zona de peligro?
<p17-por-qué-la-desescalada-de-seguridad-es-asimétrica-y-qué-ocurre-cuando-un-intruso-desaparece-dentro-de-la-zona-de-peligro>
- #strong[Contexto de Seguridad Funcional (ISO 13849-1 / IEC 61508):]
  Los modos de fallo ante la vida humana son inherentemente asimétricos:
  una falsa alarma detiene la producción (costo económico), pero un
  falso silenciamiento de alarma reinicia la máquina con un operario en
  peligro (riesgo vital o fatalidad).
- #strong[Los Cuatro Invariantes de Seguridad Asimétrica:]
  + #strong[Invariante I (Escalada Proactiva Fail-Safe):] La incursión
    en la zona de peligro $P_(upright("danger"))$ puede y debe disparar
    la parada de emergencia (`trip = True`) ante cualquier estado
    (`OBSERVED`, `PREDICTED` o `STALE`). Ante la duda cinemática, se
    preserva la vida.
  + #strong[Invariante II (Desescalada Estrictamente Verificada por
    Fotones):] Un intruso que sale fuera de $P_(upright("release"))$ NO
    puede desescalar la alarma mediante extrapolaciones cinemáticas
    (`PREDICTED` / `STALE`). Requiere estrictamente
    $N_(upright("release")) = 5$ cuadros consecutivos con estatus
    #strong[`OBSERVED`] comprobado para confirmar visualmente que el
    operario ya no está dentro de la zona peligrosa.
  + #strong[Invariante III (Enclavamiento por Desaparición en Peligro -
    Missing Target Lockout):] Si un intruso en zona de peligro deja de
    detectarse (se poda al superar $k > 5$ cuadros sin verse), el
    sistema jamás debe asumir que "se evaporó" y apagar la alarma.
    Automáticamente enclava la FSM en #strong[`LOCKOUT`]
    (`trip = True`), exigiendo inspección física de la celda y un
    reinicio manual autorizado (`SpatialFSM.reset()`).
  + #strong[Invariante IV (Congelamiento de Dwell Time):] El tiempo de
    permanencia en la zona de advertencia mide exposición acumulada al
    riesgo. Durante oclusiones (`PREDICTED` o `STALE`), el contador de
    dwell time se #strong[congela] en el último valor observado
    empíricamente y no suma tiempo fantasma mientras la persona no sea
    visible.
- #strong[Detalle Completo:] Ver
  #link(<adr-008>)[ADR-008].

#pagebreak()

= 5. Generación de Datos Sintéticos y Cierre del Domain Gap <cap-sintetico>
== Synthetic Benchmark Video Generation Architecture
<synthetic-benchmark-video-generation-architecture>
=== Overview
<overview>
The #strong[Industrial Vision Safety Guard] incorporates a
deterministic, high-fidelity synthetic benchmark video generator
(`src/utils/synthetic_generator.py`). It produces perspective-calibrated
test streams with exact metric ground-truth kinematics, soft contact
shadows, depth-ordered physical occlusions, single-identity walking gait
cycles, and ISO 13855 safety zones.

#divider()

=== Technical Evolution: Before vs.~After (Storytelling)
<technical-evolution-before-vs.-after-storytelling>
#figure(
  align(center)[#table(
    columns: (20%, 20%, 20%, 20%, 20%),
    align: (left,left,left,left,left,),
    table.header([Metric / Aspect], [Before (Vector
      Primitives)], [Intermediate (Mixed Candidates)], [Final
      (Single-Identity Pinhole Compositing)], [Impact],),
    table.hline(),
    [#strong[Actor Representation]], [Flat 2D vector shapes (`cv2.line`,
    `cv2.rectangle`)], [Multi-subject segmented crops (variable
    clothing)], [#strong[Single-Identity Tracklet] normalized on
    $160 times 320 upright(" RGBA")$ canonical canvas], [100% appearance
    & texture stability (no clothing jumps)],
    [#strong[Perspective Scaling]], [Linear depth delta
    ($h in\[90\,300\]upright(" px")$)], [Pinhole scale
    ($h in\[240\,480\]upright(" px")$)], [#strong[Calibrated Pinhole
    Scale] ($h = frac(480, 1.0 + 0.165 dot.op Y)$)], [Preserves
    anthropomorphic scale across all $Y in\[0.5\,5.5\]upright(" m")$],
    [#strong[Ground Contact Realism]], [Flat solid
    ellipse], [Directional blurred shadow], [#strong[Gaussian Soft
    Shadow] + Bottom-aligned baseline], [Natural grounding without edge
    halos or vertical jitter],
    [#strong[YOLO Detection Rate (Seq A)]], [#strong[0.0%] (0 / 180
    frames)], [100.0% (180 / 180 frames)], [#strong[100.0%] (180 / 180
    frames)], [Complete stream detection coverage],
    [#strong[YOLO Mean
    Confidence]], [#strong[0.00]], [0.816], [#strong[0.835] (Seq A) /
    #strong[0.820] (Seq B) / #strong[0.861] (Seq C)], [Maximum spatial
    feature activation & tracking stability],
    [#strong[UI HUD & Text Overlays]], [Overlapping at
    $y = 50 upright(" px")$], [Overlapping top
    banner], [#strong[Decoupled HUD]: Top Safety Banner (56px) + Bottom
    Simulation Badge], [Ultra-crisp, high-contrast, zero-overlap
    readability],
    [#strong[Occlusion Tracking (Seq B)]], [N/A (undetected)], [100.0%
    tracked], [#strong[100.0%] (180 / 180 frames tracked)], [Lower-limb
    coasting validation under pallet barrier],
    [#strong[Dwell Violation Trip (Seq C)]], [N/A (undetected)], [100.0%
    tracked], [#strong[100.0%] (300 / 300 frames tracked)], [Strict ISO
    13855 dwell violation trip at $t gt.eq 5.0 upright("s")$],
  )]
  , kind: table
  )

#divider()

=== Key Architectural Solutions
<key-architectural-solutions>
==== 1. Single-Identity Tracklet Extraction & Normalization
<single-identity-tracklet-extraction-normalization>
To prevent visual flickering or clothing variations during gait cycling,
#link("../../scripts/prepare_sprites.py")[`scripts/prepare_sprites.py`]
tracks a single continuous individual across 35 frames: 1.
#strong[Continuous Spatial Tracking:] IoU-based single-target tracking
isolates one pedestrian. 2. #strong[Instance Segmentation:] Extracts
4-channel RGBA cutout with morphological alpha feathering. 3.
#strong[Canonical Canvas Normalization
($160 times 320 upright(" px")$):] Rescales the isolated worker to a
standardized height and anchors the lowest contact foot to the bottom
center of the canvas $\(80\,316\)$, eliminating bounding box wobble and
vertical jitter.

==== 2. Pinhole Vertical Height Scaling
<pinhole-vertical-height-scaling>
For a standing human of height $H_(o b j) = 1.75 upright(" m")$, the
visual height in screen pixels $h_(p x)\(Y\)$ at ground depth
$Y in\[0.0\,6.0\]upright(" m")$ is computed via the calibrated
perspective scale:

$ h_(p x)\(Y\)= frac(480.0, 1.0 + 0.165 dot.op Y) $

- At near boundary ($Y = 0.5 upright(" m")$):
  $h_(p x) approx 443 upright(" px")$.
- At center zone ($Y = 3.0 upright(" m")$):
  $h_(p x) approx 321 upright(" px")$.
- At far boundary ($Y = 5.5 upright(" m")$):
  $h_(p x) approx 251 upright(" px")$.

==== 3. Decoupled UI & High-Contrast HUD Architecture
<decoupled-ui-high-contrast-hud-architecture>
- #strong[Top HUD Banner (Safety Pipeline):] 56px height, dark acrylic
  background, containing solid-color status pill badges
  (`CRITICAL TRIP: LOCKOUT`, `WARNING`, `SYSTEM NORMAL`) and isolated
  telemetry capsules (`T1 Latency`, `FPS`, `Tracks`, `Dwell`).
- #strong[Bottom Telemetry Badge (Simulation Metadata):] Positioned at
  $y = 1040 upright(" px")$ in the camera view to avoid any collision
  with the top safety overlay.
- #strong[Ground & BEV Anchors:] Text tags rendered with contrasting
  dark pill backgrounds for 100% legibility on any background.

#divider()

=== Benchmark Sequences
<benchmark-sequences>
+ #strong[Sequence A (`sequence_a_clean_incursion.mp4`)]:
  - #emph[Scenario]: Straight pedestrian crossing across the factory
    floor from $\(2.0\,0.5\)upright(" m")$ to
    $\(2.0\,5.5\)upright(" m")$.
  - #emph[Expected Safety Transitions]: `SAFE` $arrow.r$
    `WARNING_APPROACH` $arrow.r$ `DANGER_INTRUSION` $arrow.r$ `LOCKOUT`.
+ #strong[Sequence B (`sequence_b_occlusion_coasting.mp4`)]:
  - #emph[Scenario]: Worker walks along $Y = 2.8 upright(" m")$ passing
    behind a wooden crate barrier at $Y = 2.4 upright(" m")$.
  - #emph[Expected Behavior]: Lower-limb keypoint loss triggers Kalman
    Filter occlusion coasting while maintaining confirmed track ID.
+ #strong[Sequence C (`sequence_c_dwell_loitering.mp4`)]:
  - #emph[Scenario]: Worker enters danger zone
    $\(2.0\,3.0\)upright(" m")$, remains stationary for 6.0 seconds,
    then departs.
  - #emph[Expected Behavior]: Spatial FSM accumulates dwell time,
    triggers `DWELLING` alert at $t > 0.0 upright("s")$, and asserts
    `DWELL_VIOLATION` at $t gt.eq 5.0 upright("s")$.

#divider()

=== CLI Execution
<cli-execution>
```bash
# 1. Extract and normalize single-identity sprite walking cycle
python scripts/prepare_sprites.py

# 2. Generate all 3 synthetic benchmark videos
python scripts/generate_samples.py --sequence all --fps 30

# 3. Run interactive demo with dual-stream visualizer
python scripts/run_demo.py --source data/samples/sequence_a_clean_incursion.mp4 --realtime
python scripts/run_demo.py --source data/samples/sequence_b_occlusion_coasting.mp4 --realtime
python scripts/run_demo.py --source data/samples/sequence_c_dwell_loitering.mp4 --realtime

# 4. Execute batch evaluation and verify safety invariants
python scripts/run_dataset_test.py --dataset sequence_a_clean_incursion --verify-invariants --no-display
python scripts/run_dataset_test.py --dataset sequence_b_occlusion_coasting --verify-invariants --no-display
python scripts/run_dataset_test.py --dataset sequence_c_dwell_loitering --verify-invariants --no-display

# 5. Run automated integrity and invariant verifier
python scripts/verify_synthetic_results.py
```

#pagebreak()

= 6. Benchmarks Empíricos de Rendimiento y Cuantización <cap-benchmarks>
== Comparativa de Motores de Inferencia (Runtimes)
=== 📊 Comparative Runtime Engine Benchmark (YOLO11-Pose)
<comparative-runtime-engine-benchmark-yolo11-pose>
#figure(
  align(center)[#table(
    columns: (8.33%, 8.33%, 10.42%, 10.42%, 10.42%, 10.42%, 10.42%, 10.42%, 10.42%, 10.42%),
    align: (left,left,center,center,center,center,center,center,center,center,),
    table.header([Runtime Engine], [Backend / Device], [Mean (ms)], [p50
      (ms)], [p95 (ms)], [p99 (ms)], [Jitter $sigma$ (ms)], [Throughput
      (FPS)], [Speedup vs CPU], [ISO 13855 ($lt.eq 30 upright("ms")$)],),
    table.hline(),
    [#strong[PyTorch Eager
    (CPU)]], [`PyTorch_CPU`], [70.80], [69.86], [75.11], [75.91], [±1.96], [14.1
    FPS], [1.00x], [❌ FAIL],
    [#strong[PyTorch Eager
    (MPS)]], [`PyTorch_MPS`], [17.63], [17.00], [20.82], [22.75], [±1.67], [56.7
    FPS], [#strong[4.02x]], [✅ PASS],
    [#strong[ONNX Runtime
    (CPU)]], [`CPUExecutionProvider`], [40.54], [39.92], [44.72], [48.18], [±2.04], [24.7
    FPS], [#strong[1.75x]], [❌ FAIL],
    [#strong[ONNX Runtime
    (CoreML/ANE)]], [`CoreMLExecutionProvider`], [15.81], [15.88], [19.02], [20.88], [±1.79], [63.3
    FPS], [#strong[4.48x]], [✅ PASS],
  )]
  , kind: table
  )

== Comparativa de Precisión y Cuantización (FP32 vs FP16 vs INT8)
=== 📊 Comparative Quantization & Metric Precision Benchmark (YOLO11-Pose)
<comparative-quantization-metric-precision-benchmark-yolo11-pose>
#figure(
  align(center)[#table(
    columns: (9.09%, 11.36%, 11.36%, 11.36%, 11.36%, 11.36%, 11.36%, 11.36%, 11.36%),
    align: (left,center,center,center,center,center,center,center,center,),
    table.header([Precision Mode], [Model Size], [Size Reduction], [Mean
      Latency], [Throughput], [Pixel RMSE], [Metric Ground RMSE], [Max
      Drift], [ISO 13855 Status],),
    table.hline(),
    [#strong[FP32 (Single Precision)]], [11.30 MB], [0.0%], [17.68
    ms], [56.6 FPS], [0.00 px], [0.00 cm], [0.00 cm], [✅ PASS],
    [#strong[FP16 (Half Precision)]], [5.69 MB], [49.6%], [42.40
    ms], [23.6 FPS], [0.31 px], [1.37 cm], [34.88 cm], [✅ PASS],
    [#strong[INT8 (Dynamic Quant)]], [3.27 MB], [71.1%], [97.85
    ms], [10.2 FPS], [23.84 px], [156.70 cm], [2179.88 cm], [❌ FAIL],
  )]
  , kind: table
  )

#pagebreak()

= 7. Compendio Completo de Architecture Decision Records (ADRs) <cap-adrs>

En este capítulo se recopilan de manera íntegra y exhaustiva las doce decisiones arquitectónicas (ADRs) que gobiernan la totalidad del sistema *Edge Safety Guard*. Cada documento define el contexto, las opciones evaluadas, los trade-offs matemáticos/computacionales, la decisión adoptada y sus consecuencias directas en seguridad industrial.

#align(center)[
  #table(
    columns: (auto, auto, 1fr),
    fill: (x, y) => if y == 0 { rgb("#1E293B") } else if calc.even(y) { rgb("#F8FAFC") } else { white },
    stroke: 0.5pt + rgb("#CBD5E1"),
    inset: 7pt,
    [*ADR*], [*Referencia*], [*Decisión Arquitectónica & Impacto Industrial*],
    [#strong[001]], [#link(<adr-001>)[ADR-001]], [Anclaje físico anatómico en tobillos (YOLO-Pose) vs Bounding Box.],
    [#strong[002]], [#link(<adr-002>)[ADR-002]], [Mapeo planar DLT 3x3 determinista (Zw = 0) vs estimación monocular 3D.],
    [#strong[003]], [#link(<adr-003>)[ADR-003]], [Inferencia desacoplada de PyTorch vía ONNX Runtime (CoreML / INT8).],
    [#strong[004]], [#link(<adr-004>)[ADR-004]], [Schmitt trigger espacial con banda de 200 mm contra el chattering.],
    [#strong[005]], [#link(<adr-005>)[ADR-005]], [Validación preventiva de colinealidad y estabilidad numérica κ(H) < 10^6.],
    [#strong[006]], [#link(<adr-006>)[ADR-006]], [Geometrías preparadas GEOS (C) y bypass dinámico por velocidad vn ≥ 1.6 m/s.],
    [#strong[007]], [#link(<adr-007>)[ADR-007]], [Manejo jerárquico de oclusiones: tobillos duales → individual → bbox.],
    [#strong[008]], [#link(<adr-008>)[ADR-008]], [Epistemología Kalman (OBSERVED/PREDICTED) y bloqueo de desescalada ciega.],
    [#strong[009]], [#link(<adr-009>)[ADR-009]], [Statecharts ortogonales concurrentes: separación ocupación vs dwell time.],
    [#strong[010]], [#link(<adr-010>)[ADR-010]], [Profiling de doble horizonte: hardware (T_system) vs evento físico (T_event).],
    [#strong[011]], [#link(<adr-011>)[ADR-011]], [MOT Bayesiano: Gating Mahalanobis χ² ≤ 9.21, Húngaro y Spatial Birth NMS.],
    [#strong[012]], [#link(<adr-012>)[ADR-012]], [Composición fotorrealista pinhole de identidad única para testing formal.]
  )
]

#v(1em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-001: Estimación de Contacto con el Suelo: Ankle Keypoints (YOLO-Pose) vs Bounding Box Bottom-Center <adr-001>

- #strong[Estatus:] Aceptado (Hipótesis Primaria sujeta a Benchmark
  Experimental)
- #strong[Fecha:] 2026-08-29 (Revisado: 2026-08-30)
- #strong[Módulo Asociado:] `src/pipeline/safety_pipeline.py`
  (`safety-pipeline`)

=== Contexto
<contexto>
Para proyectar la posición métrica de un operario mediante homografía
planar ($Z_w = 0$), el sistema necesita estimar el punto de contacto
físico entre la persona y el suelo ($hat(p)_(upright("ground"))$).

El baseline razonable en visión computacional #strong[no es el centroide
2D de la caja], sino el #strong[borde inferior central
(#emph[bottom-center])]:
$ p_(upright("ground_bbox")) = (frac(x_min + x_max, 2) \, thin y_max) $

Frente a esto, un modelo de estimación de pose infiere keypoints
anatómicos y calcula:
$ p_(upright("ground_pose")) = upright("mean") (upright("valid_ankles") \( k_15 \, k_16 \)) $

Ambos enfoques intentan resolver exactamente el mismo problema
geométrico: estimar el punto de apoyo en el suelo. La pregunta de
arquitectura no es si Pose es "superior", sino: #strong[¿justifican los
keypoints de tobillo el costo computacional adicional frente a usar el
borde inferior de una bounding box?]

=== Opciones Consideradas y Trade-Offs
<opciones-consideradas-y-trade-offs>
+ #strong[Detector Estándar (Bounding Box Bottom-Center):]
  - #emph[Mecanismo:] Inferencia de detección estándar (ej. YOLOv8n /
    YOLO11n). Punto en $\(\(x_min + x_max\)\/2\,y_max\)$.
  - #emph[Ventajas:] Menor costo computacional
    ($approx 30 upright("–") 40 %$ menos FLOPs y menor latencia),
    topología de red más simple y menor consumo de memoria. Inmune a la
    oclusión específica de pies (mientras detecte el cuerpo, infiere la
    base).
  - #emph[Desventajas:] Si el operario se agacha, salta, se sienta, o
    sus pies no están alineados con la base del bbox, $y_max$ introduce
    un sesgo proyectivo sistemático.
  - #emph[Hipótesis:] Mayor velocidad, pero potencial ruido en posturas
    no bípedas.
+ #strong[Estimador de Pose (Ankle Keypoints):]
  - #emph[Mecanismo:] Inferencia de Pose (ej. YOLO11n-pose). Punto medio
    entre tobillo izquierdo (`idx 15`) y tobillo derecho (`idx 16`)
    condicionado por umbral de confianza ($c o n f gt.eq 0.5$).
  - #emph[Ventajas:] Semántica anatómica real: mide dónde tocan
    efectivamente los pies el suelo, independientemente de que el
    operario esté inclinado hacia adelante o levantando un brazo.
  - #emph[Desventajas:] Mayor latencia de inferencia y
    post-procesamiento. Vulnerable a oclusiones frecuentes en planta
    (pallets, maquinaria baja, indumentaria holgada o calzado cubierto)
    y a pérdida de confianza cuando los pies quedan en el borde inferior
    del encuadre.

=== Decisión Tomada
<decisión-tomada>
Se adopta #strong[YOLO-Pose (Ankle Keypoints)] como #strong[hipótesis
arquitectónica primaria], implementando una política de degradación
controlada (#emph[fallback]): 1. Si ambos tobillos son válidos
($c o n f gt.eq 0.5$): promedio de tobillos. 2. Si un solo tobillo es
visible: anclaje en el tobillo visible. 3. Si ambos tobillos están
ocluidos: el filtro de Kalman cinemático 2D extrapola la trayectoria en
espacio métrico (#emph[coasting]).

Asimismo, se formula la comparación empírica #strong[YOLO-Pose vs Bbox
Bottom-Center] como un estudio experimental prioritario en el roadmap
secundario.

=== Consecuencias y Pregunta Experimental
<consecuencias-y-pregunta-experimental>
- #strong[Trade-Off Crítico:] Se asume un incremento de latencia a
  cambio de fidelidad anatómica en el punto de contacto.
- #strong[Validación Experimental Pendiente:] Contrastar si la ganancia
  en estabilidad espacial de los tobillos compensa la pérdida de
  rendimiento frente al detector de cajas estándar bajo oclusiones
  industriales reales.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-002: Proyección Homográfica 2D a Plano Métrico vs Estimación 3D Monocular <adr-002>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-29
- #strong[Módulo Asociado:] `src/core/homography.py`
  (`calibration-homography`)

=== Contexto
<contexto>
Para auditar distancias de aproximación y zonificación en planta, los
sistemas convencionales definen regiones de interés (#emph[ROIs]) en el
espacio de la imagen como polígonos de píxeles:

```
pixel ROI: [(327, 412), (598, 390), (620, 580), (280, 560)] px
```

Este enfoque sufre de distorsión proyectiva severa inducida por la
inclinación de la cámara (ángulos picados/cenitales): la escala de píxel
a metro no es lineal (10 px en primer plano $eq.not$ 10 px cerca del
horizonte), lo que impide calcular distancias euclidianas reales,
velocidades cinemáticas o distancias a máquinas.

Se requería una solución para traducir las observaciones de la cámara a
un marco físicamente interpretable.

=== Opciones Consideradas
<opciones-consideradas>
+ #strong[Estimación de Pose 3D Monocular / Redes de Profundidad (ej.
  Depth-Anything, Monodepth):]
  - #emph[Pros:] No requiere asumir que la escena es estrictamente
    planar; infiere coordenadas en volumen tridimensional.
  - #emph[Contras:] Computacionalmente pesado en hardware Edge, escala
    métrica indeterminada o ruidosa (requiere calibración métrica
    compleja), latencia no determinista ($> 60 upright(" ms")$) y
    consumo excesivo de memoria.
+ #strong[Proyección Homográfica Planar 2D (Direct Linear Transformation
  \- DLT):]
  - #emph[Pros:] Operación matricial $3 times 3$ ultraligera
    ($< 0.1 upright(" ms")$ por punto proyectado), determinista, y
    matemáticamente exacta para puntos en contacto con el suelo
    ($Z_w = 0$).

  - #emph[Transformación Conceptual:] Convierte un polígono arbitrario
    en píxeles en una zona métrica real:

    ```
    camera image -> pixel coordinates (u, v) -> [ H ] -> ground coordinates (X, Y) [m]
    ```

    Permite definir la zona peligrosa como
    $X in\[1.0\,2.5\]upright(" m")\,Y in\[0.5\,2.0\]upright(" m")$,
    habilitando el cálculo de distancias reales a máquinas, velocidad
    cinemática $\[dot(X)\,dot(Y)\]$, dwell distance y zonas
    concéntricas.

  - #emph[Contras:] Asume que el piso es aproximadamente planar
    ($Z = 0$); requiere al menos 4 puntos de calibración en planta.

=== Decisión Tomada
<decisión-tomada>
Se selecciona la #strong[Transformación Homográfica Planar
($H in bb(R)^(3 times 3)$)] mediante el algoritmo DLT con anclaje en el
punto medio de los tobillos del operario.

Dado que el contacto del operario con el piso ocurre en $Z = 0$, la
matriz de proyección de cámara colapsa a una transformación proyectiva
biyectiva invertible $H$:
$ hat(P)_(upright("world")) = H\(hat(p)_(upright("feet"))\) $

==== Cadena de Propagación de Errores e Incertidumbre
<cadena-de-propagación-de-errores-e-incertidumbre>
Una coordenada estimada en metros $hat(P)_(upright("world"))$ no implica
conocimiento exacto de la posición real. En ella convergen cinco fuentes
de incertidumbre:

```
pose estimation error (detección de keypoints de tobillos)
        +
pixel quantization (discretización del sensor)
        +
camera calibration error (incertidumbre en puntos DLT ground-truth)
        +
ground-plane assumption (desniveles del suelo Z ≠ 0)
        +
homography numerical error (número de condición matricial κ(H))
```

Por ende, reportar que un trabajador se encuentra a
"$0.93 upright(" m")$ del peligro" representa una estimación sobre el
plano del suelo con tolerancia finita ($plus.minus epsilon.alt$). No
debe asumirse precisión centimétrica sin una calibración geométrica
rigurosa y un análisis de condicionamiento $kappa\(H\)$.

=== Consecuencias
<consecuencias>
- #strong[Físicamente Interpretable:] Las zonas y distancias se expresan
  en metros reales del taller, posibilitando telemetría industrial y
  auditoría de velocidades.
- #strong[Latencia Mínima:] La proyección métrica toma
  $< 0.05 upright(" ms")$ en CPU, preservando el presupuesto de latencia
  ($T_1$).
- #strong[Determinismo Matemático:] Álgebra lineal sin fluctuaciones
  estocásticas de profundidad generadas por redes neuronales.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-003: Runtime de Inferencia: ONNX Runtime (CoreML / CPU) vs PyTorch Nativo <adr-003>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-29

=== Contexto
<contexto>
El modelo base de pose (`yolo11n-pose`) debe ejecutarse con latencia
determinista en dispositivos de borde locales (Apple Silicon M1/M2/M3) y
permitir una migración transparente hacia nodos industriales con GPU
dedicada (NVIDIA GTX 1050 / Jetson).

=== Opciones Consideradas
<opciones-consideradas>
+ #strong[Inferencia PyTorch Nativa (`torch.jit` / Python Runtime):]
  - #emph[Pros:] Integración directa sin fase de exportación previa.
  - #emph[Contras:] Elevado consumo de memoria RAM/VRAM, runtime pesado
    (\~1.5 GB en disco), sin optimizaciones específicas de grafo ni
    fusión de capas para silicio local.
+ #strong[ONNX Runtime con Negociación de Execution Providers:]
  - #emph[Pros:] Formato abierto e interoperable; en macOS delega en
    `CoreMLExecutionProvider` (Apple Neural Engine / GPU Apple) con
    fallback a `CPUExecutionProvider` (ARM NEON con multi-threading).
    Desacopla la lógica de negocio de la aceleración física.
  - #emph[Contras:] Requiere paso previo de exportación y validación
    estática de grafos (`imgsz=640`, opset 17).
+ #strong[TensorRT Nativo Directo:]
  - #emph[Pros:] Máximo rendimiento en silicio NVIDIA.
  - #emph[Contras:] Propietario e incompatible con macOS (Apple
    Silicon). En GPUs Pascal (GTX 1050 - sm\_61) requiere cuantización
    obligatoria a INT8 debido a la penalización de hardware de FP16.

=== Decisión Tomada
<decisión-tomada>
Se adopta #strong[ONNX Runtime] como motor de ejecución desacoplado con
la clase `OnnxEngine`. Para desarrollo y demo local se opera con
`CoreMLExecutionProvider` / `CPUExecutionProvider` (4 hilos). Para la
posterior etapa de despliegue en NVIDIA GTX 1050, se mantendrá la misma
interfaz invocando `CUDAExecutionProvider` o TensorRT cuantizado en
INT8.

=== Consecuencias
<consecuencias>
- #strong[Rendimiento Comprobado:] Inferencia verificada a
  $p_95 = 20.26 upright(" ms")$ (54.55 FPS) en Apple Silicon.
- #strong[Portabilidad:] Se cumple el presupuesto temporal de seguridad
  ISO 13855 ($t_(upright("infer")) lt.eq 30 upright(" ms")$) sin acoplar
  el código a ningún silicio específico.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-004: Gestión de Oscilaciones Espaciales mediante Spatial FSM + Filtro Kalman <adr-004>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-29

=== Contexto
<contexto>
En aplicaciones de seguridad industrial, la activación de paradas de
emergencia o alarmas sonoras no puede tolerar oscilaciones rápidas
(#emph[flickering] o #emph[chattering]) cuando un operario camina o
trabaja en el borde exacto de una zona restringida.

=== Opciones Consideradas
<opciones-consideradas>
+ #strong[Evaluación Booleana Instantánea por Frame (Point-in-Polygon):]
  - #emph[Pros:] Implementación trivial (`polygon.contains(point)`).
  - #emph[Contras:] Ruido en la detección de keypoints
    ($plus.minus 10 upright("–") 30 upright(" mm")$) hace que el estado
    de alarma conmute erráticamente de un fotograma a otro en los
    bordes, destruyendo contactores físicos o disparando falsos
    positivos.
+ #strong[Doble Histéresis: Espacial (Doble Polígono) + Temporal
  (Ventana de Frames) + Filtro Kalman:]
  - #emph[Pros:]
    - #strong[Filtro Kalman 2D:] Suaviza la trayectoria del trabajador
      en el plano métrico, absorbiendo vibraciones de keypoints y
      oclusiones instantáneas.
    - #strong[Histéresis Espacial:] Define dos polígonos concéntricos:
      $P_(upright("danger"))$ (incursión) y $P_(upright("release"))$
      (despeje) con una separación
      $Delta d in\[150\,300\]upright(" mm")$.
    - #strong[Histéresis Temporal:] Requiere
      $N_(upright("confirm")) gt.eq 3 upright("–") 5$ fotogramas
      consecutivos de persistencia para cambiar de estado (`OUTSIDE`
      $arrow.r$ `INTRUSION_ACTIVE`).
  - #emph[Contras:] Introduce un pequeño retardo determinista temporal
    equivalente a
    $N_(upright("confirm")) times Delta t_(upright("frame"))$ (aprox.
    $60 upright("–") 90 upright(" ms")$), el cual se compensa
    formalmente en el cálculo de distancia de seguridad $S$.

=== Decisión Tomada
<decisión-tomada>
Se selecciona la #strong[Máquina de Estados Finitos Espacial (Spatial
FSM)] combinada con #strong[Filtro Kalman 2D] y doble polígono
concéntrico con histéresis espacial y temporal asimétrica.

```
════════════════════════════════════════════════════════════════════════════════
              SCHMITT TRIGGER ESPACIAL Y ASIMETRÍA ENTRY / EXIT
════════════════════════════════════════════════════════════════════════════════

                      P_release (Límite de Liberación)
                   ┌───────────────────────────────────┐
                   │       Banda de Histéresis         │
                   │       (Δd = 200 mm)               │
                   │    P_danger (Límite de Peligro)   │
                   │   ┌───────────────────────────┐   │
                   │   │                           │   │
                   │   │          MÁQUINA          │   │
                   │   │                           │   │
                   │   └───────────────────────────┘   │
                   │                                   │
                   └───────────────────────────────────┘

1. ENTRY POLICY: CONSERVATIVE & FAST
   • Aproximación normal (vn < 1.6 m/s) : Debounce de N_confirm = 3 cuadros.
   • Aproximación rápida (vn >= 1.6 m/s): Bypass instantáneo (N_confirm = 1) en cuadro 1 (ISO 13855).

2. EXIT POLICY: HYSTERETIC & STRICT
   • Debounce de salida: Exige N_release = 5 cuadros consecutivos fuera de P_release.
   • Salvaguarda asimétrica (ADR-008): Desescalada permitida estrictamente con fotones reales (OBSERVED).
     Si el objetivo queda ocluido (PREDICTED / STALE), la salida se bloquea y el relé permanece abierto.
════════════════════════════════════════════════════════════════════════════════
```

=== Consecuencias
<consecuencias>
- #strong[Determinismo y Estabilidad:] Supresión total del chattering en
  actuadores de relés de seguridad.
- #strong[Seguridad Fail-Safe:] Eliminación de demoras peligrosas en la
  entrada ante velocidades críticas, manteniendo máxima robustez en la
  salida.
- #strong[Trazabilidad:] Posibilidad de registrar tiempos de permanencia
  (#emph[dwell time]) para advertencias graduadas antes de la parada
  crítica.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-005: Validación Geométrica Preventiva y Proyección Vectorizada en Homografía Planar <adr-005>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-29
- #strong[Módulo Asociado:] `src/core/homography.py`
  (`calibration-homography`)

=== Contexto
<contexto>
En sistemas de visión computacional de seguridad industrial (ISO
13855:2024), el motor de homografía se ubica directamente en el camino
crítico entre la inferencia de keypoints y la evaluación espacial de
incursión.

Se identificaron dos riesgos arquitectónicos de alto impacto: 1.
#strong[Fallas Silenciosas por Puntos Degenerados:] Si los puntos de
calibración en planta presentan colinealidad (3 o 4 puntos en la misma
línea), puntos duplicados o configuración degenerada, la matriz de
homografía $H$ resultante se vuelve singular o mal condicionada
($det\(H\)approx 0$, número de condición $kappa\(H\)gt.double 10^12$).
Esto provocaría distorsiones métricas masivas que desvirtuarían las
distancias de seguridad sin alertar al operador. 2. #strong[Cuello de
Botella por Proyección Punto a Punto:] En escenas con múltiples
operarios simultáneos (hasta 10-15 personas $times$ 2 tobillos = 30
puntos por frame), proyectar punto por punto en bucles nativos de Python
añade latencia innecesaria ($approx 1 upright("–") 3 upright(" ms")$).

=== Opciones Consideradas
<opciones-consideradas>
+ #strong[Proyección Estándar con Bucles Python y Validación Reactiva:]
  - Invocar `cv2.perspectiveTransform` o multiplicar punto a punto en
    bucles `for` en cada frame.
  - Confiar en que OpenCV maneje los errores o atrapar excepciones de
    división por cero en tiempo de ejecución.
  - #emph[Desventajas:] Latencia de inferencia no determinista; fallas
    en tiempo de ejecución en lugar de en el arranque.
+ #strong[Validación Geométrica Preventiva (Pre-flight) + Caching
  In-Memory + Vectorización NumPy:]
  - #strong[Validación Preventiva en Comisionamiento:] Validar antes de
    calcular $H$ que no existan duplicados, que el rango afín sea pleno
    ($upright("rank") = 3$), que ningún subconjunto de 3 puntos en un
    cuadrilátero sea colineal (área de triángulo
    $upright("Area") > 10^(- 4)$), y que el error de reproyección cumpla
    $upright("RMSE") lt.eq 0.05 upright(" m")$.
  - #strong[Precomputación y Caching:] Calcular $H$ y su inversa
    $H^(- 1)$ una única vez durante la inicialización.
  - #strong[Proyección Matricial Vectorizada:] Proyectar arreglos
    completos de forma $\(N\,2\)$ mediante multiplicación matricial
    homogénea en NumPy: $\(N\,3\)@ M^T$.
  - #emph[Ventajas:] Falla de forma temprana e inequívoca durante el
    inicio si la calibración es defectuosa. Reduce el tiempo de
    proyección a $< 0.05 upright(" ms")$ para decenas de keypoints.

=== Decisión Tomada
<decisión-tomada>
Se implementa la #strong[Opción 2] en la clase
#link("file:///Users/xander/Projects/edge-safety-guard/src/core/homography.py")[`HomographyManager`]:
\- Validación geométrica preventiva estricta en el método
`validate_points()`. - Caching en memoria de matrices $H$ y $H^(- 1)$
con verificación de estabilidad numérica ($\|det\(H\)\|> 10^(- 10)$,
$kappa\(H\)< 10^12$). - Proyección vectorizada en `project_batch()` con
guarda explícita contra puntos en la línea del horizonte
($\|W\|< 10^(- 7)$).

=== Consecuencias
<consecuencias>
- #strong[Determinismo y Seguridad Funcional:] Es imposible instanciar
  un sistema de seguridad con puntos de calibración colineales o
  degenerados.
- #strong[Rendimiento Ultrarrápido:] La proyección métrica por lotes
  toma menos de $0.05 upright(" ms")$, consumiendo solo el $0.1 %$ del
  presupuesto total de $50 upright(" ms")$ estipulado por la norma ISO
  \13855.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-006: Geometrías Preparadas y Bypass Dinámico de Debounce en FSM de Seguridad (ISO 13855) <adr-006>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-30
- #strong[Módulo Asociado:] `src/core/spatial_fsm.py`
  (`kalman-spatial-fsm`)

=== Contexto
<contexto>
En sistemas de seguridad funcional de maquinaria industrial (ISO
13855:2024 / IEC 61508), la máquina de estados espacial (`SpatialFSM`)
debe garantizar dos propiedades críticas aparentemente contradictorias:
\1. #strong[Inmunidad al Ruido (Anti-Chattering):] Exigir una ventana de
confirmación temporal ($N_(upright("confirm")) gt.eq 3$ frames
$approx 100 upright(" ms")$) para no detener la producción por falsas
detecciones transitorias. 2. #strong[Respuesta Inmediata ante Amenazas
Críticas:] Si un operario corre o cae a alta velocidad hacia la zona de
peligro (velocidad de aproximación humana $K = 1600 upright(" mm/s")$ o
$2000 upright(" mm/s")$), esperar $100 upright(" ms")$ de confirmación
podría permitirle recorrer entre $160 upright(" mm")$ y
$200 upright(" mm")$ adicionales dentro del perímetro de peligro antes
de que el relé abra el circuito.

Asimismo, la evaluación de pertenencia geográfica
(#emph[Point-in-Polygon]) para múltiples operarios simultáneos no debe
superar el presupuesto temporal ($< 0.1 upright(" ms")$).

=== Opciones Consideradas
<opciones-consideradas>
+ #strong[Debounce Temporal Rígido sin Consideración Cinemática:]
  - La FSM siempre exige $N_(upright("confirm")) gt.eq 3$ frames
    independientemente de la velocidad del operario.
  - #emph[Riesgo de Seguridad:] Un operario en carrera rápida
    ($v gt.eq 2.0 upright(" m/s")$) penetra la zona de peligro durante
    la ventana de confirmación sin que el sistema active el relé de
    inmediato.
+ #strong[Evaluación Instantánea sin Debounce:]
  - Elimina la ventana temporal y dispara en el fotograma 1.
  - #emph[Riesgo Operativo:] Retorna a los problemas de
    #emph[chattering] y falsas paradas por ruido estocástico de
    keypoints.
+ #strong[Bypass Dinámico de Debounce basado en el Vector Normal de
  Aproximación + Geometrías Preparadas:]
  - #strong[Bypass Cinemático:] La FSM evalúa la componente de velocidad
    normal orientada hacia el interior del polígono:
    $ v_n = arrow(v) dot.op hat(n)_(upright("inward")) $ Si
    $v_n gt.eq K_(upright("approach"))$ ($1.6 upright(" m/s")$ según ISO
    13855), la FSM considera la intrusión confirmada en el
    #strong[primer fotograma] ($N_(upright("confirm")) = 1$), puenteando
    el debounce.
  - Si la velocidad normal es baja o tangencial
    ($v_n < 1.6 upright(" m/s")$), se mantiene el debounce estricto
    ($N_(upright("confirm")) gt.eq 3$) para filtrar ruidos.
  - #strong[Geometrías Preparadas (Shapely `prep`):] Los polígonos
    $P_(upright("danger"))$ y $P_(upright("release"))$ se compilan a
    estructuras C optimizadas durante la inicialización, reduciendo las
    consultas `contains_xy()` a menos de $5 mu upright("s")$ por
    objetivo.

=== Decisión Tomada
<decisión-tomada>
Se adopta la #strong[Opción 3] implementada en
#link("file:///Users/xander/Projects/edge-safety-guard/src/core/spatial_fsm.py")[`SpatialFSM`]:
\- Geometrías $P_(upright("danger"))$ y $P_(upright("release"))$
precomputadas y compiladas con `shapely.prepared.prep()`. - Bypass de
debounce activado cuando $v_n gt.eq 1.6 upright(" m/s")$ hacia el
interior del perímetro. - Salida fail-safe por defecto: `trip = True` en
el arranque, ante fallos (`FAULT`), bloqueo manual (`LOCKOUT`) o
intrusiones confirmadas.

=== Consecuencias
<consecuencias>
- #strong[Alineación con el razonamiento ISO 13855:2024:] Respuesta sin
  retardo ($N_(upright("confirm")) = 1$) ante aproximaciones que superan
  la velocidad de aproximación humana típica ($1.6 upright(" m/s")$),
  manteniendo el filtro de falsos positivos en operarios trabajando a
  paso normal.
- #strong[Rendimiento Edge Ultraligero:] La evaluación espacial de 10
  trabajadores toma menos de $0.05 upright(" ms")$.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-007: Gestión de Oclusiones en Extremidades Inferiores y Propagación de Confianza <adr-007>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-30
- #strong[Módulo Asociado:] `src/pipeline/safety_pipeline.py`,
  `src/core/kalman_filter.py`

=== Contexto
<contexto>
En un entorno industrial, la oclusión de las extremidades inferiores es
el modo de fallo primario más común: maquinaria baja, pallets,
carretillas elevadoras, herramientas o el propio borde inferior del
sensor ocultan los pies de un trabajador cuyo torso permanece
perfectamente visible:

```
camera
   ↓
┌──────────── frame
│
│   O
│  /|\
│  / \
│
│──────── maquinaria / obstáculo (oclusión)
│
└────────────
```

Bajo este escenario, el estimador de pose reporta baja confianza o
ausencia total de keypoints en tobillos: `conf(left_ankle) = 0.12`,
`conf(right_ankle) = 0.08` frente a un umbral
$T_(upright("conf")) = 0.5$.

Una arquitectura ingenua tiene dos extremos peligrosos: 1.
#strong[Descartar la observación en silencio:] Deja de monitorear al
trabajador mientras penetra la zona de peligro. 2. #strong[Usar puntos
de baja confianza:] Proyecta ruido estocástico masivo en el plano
métrico, provocando falsas alarmas o cálculos cinemáticos disparatados.

=== Análisis de Alternativas ante Oclusión
<análisis-de-alternativas-ante-oclusión>
#figure(
  align(center)[#table(
    columns: (25%, 25%, 25%, 25%),
    align: (left,left,left,left,),
    table.header([Alternativa], [Descripción], [Ventajas], [Desventajas],),
    table.hline(),
    [#strong[A) Rechazar observación]], [Ignorar al trabajador si no hay
    tobillos válidos], [Cero mediciones ruidosas en
    homografía], [Peligro ciego: el trabajador existe pero el sistema no
    lo monitorea],
    [#strong[B) Anclaje en un solo tobillo]], [Si un tobillo tiene
    $c o n f gt.eq 0.5$, usarlo], [No requiere cajas ni modelos
    externos], [Sesgo lateral de hasta $30 upright(" cm")$ según la
    apertura de piernas],
    [#strong[C) Fallback a Bbox Bottom-Center]], [Proyectar
    $\(\(x_min + x_max\)\/2\,y_max\)$ de la caja], [Preserva presencia
    continua aunque los pies no se vean], [Asume que la base del
    obstáculo coincide con el suelo],
    [#strong[D) Predicción vía Tracker (Coasting)]], [El Filtro Kalman
    proyecta la trayectoria cinemática previa], [Suave, determinista,
    sin saltos espaciales espurios], [Válido solo por ventana corta
    ($N_(upright("missed")) lt.eq 5$ frames
    $approx 160 upright(" ms")$)],
    [#strong[E) Declarar Incertidumbre Explícita]], [Etiquetar la
    estimación con fuente y confianza], [La FSM y el visualizador
    conocen la calidad del dato], [Requiere propagación de contratos
    tipados en todo el pipeline],
  )]
  , kind: table
  )

=== Decisión Tomada
<decisión-tomada>
Se adopta una #strong[política de degradación escalonada (Graceful
Degradation Hierarchy)] combinada con el concepto de #strong[Propagación
de Confianza (Confidence Propagation)]:

==== 1. Jerarquía de Degradación Escalonada
<jerarquía-de-degradación-escalonada>
+ #strong[Nivel 1 (Fidelidad Plena - Dual Ankles):] Si ambos tobillos
  tienen $c o n f gt.eq 0.5$, se proyecta su punto medio. Fuente:
  `SourceType.ANKLES_DUAL`.
+ #strong[Nivel 2 (Fidelidad Monocular - Single Ankle):] Si un solo
  tobillo supera el umbral, se utiliza dicho tobillo como anclaje
  físico. Fuente: `SourceType.ANKLE_SINGLE`.
+ #strong[Nivel 3 (Filtro Cinemático - Coasting):] Si ambos tobillos
  caen por debajo del umbral, el pipeline no proyecta un punto nuevo a
  homografía; en su lugar, el #strong[MultiTargetKalmanTracker] retiene
  el track en modo `COASTING` extrapolando su velocidad
  $\[dot(X)\,dot(Y)\]$ durante un máximo de $N_(upright("missed")) = 5$
  fotogramas. Fuente: `SourceType.TRACKER_PREDICTED`.
+ #strong[Nivel 4 (Pérdida Crítica / Fallback):] Si la oclusión persiste
  más de $N_(upright("missed"))$ fotogramas o se trata de una pista no
  confirmada, se habilita el fallback a `BBOX_BOTTOM_CENTER` con
  penalización de confianza, o se marca el track como `DELETED`.

==== 2. Contrato de Estimación Métrica (Confidence Propagation)
<contrato-de-estimación-métrica-confidence-propagation>
Las coordenadas en metros no deben tratarse como valores escalares
idénticos. Representan el tipo conceptual:

```python
@dataclass(frozen=True)
class PositionEstimate:
    xy_m: Tuple[float, float]
    confidence: float
    source: str  # "ankles_dual" | "ankle_single" | "bbox_bottom" | "tracker_predicted"
    covariance: Optional[np.ndarray] = None
```

=== Consecuencias
<consecuencias>
- #strong[Sin Puntos Ciegos:] Si un operario camina detrás de un pallet
  o máquina, el sistema mantiene el seguimiento métrico y el cálculo de
  intrusión mediante #emph[coasting] sin perder su historial de
  permanencia (#emph[dwell time]).
- #strong[Semántica Clara en Auditoría:] Un evento de alarma disparado
  con `source="ankles_dual"` tiene alta certeza geométrica; uno
  disparado con `source="tracker_predicted"` indica que el trabajador ya
  venía en trayectoria de incursión antes de ocluirse.
- #strong[Fail-Safe Temporal:] La ventana de coasting está acotada
  ($160 upright(" ms")$); no se extrapola indefinidamente para evitar
  derivas cinemáticas.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-008: Epistemología de Estados de Observación Kalman, Descomposición Espectral de Ruido y Desescalada Asimétrica de Seguridad <adr-008>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-30
- #strong[Módulos Asociados:] `src/core/kalman_filter.py`,
  `src/core/spatial_fsm.py`, `src/pipeline/safety_pipeline.py`
- #strong[Estándares Aplicables:] ISO 13855:2024, ISO 13849-1 (PL d/e),
  IEC 61508 (SIL 2/3)

#divider()

=== 1. Contexto y Planteamiento del Defecto Epistemológico
<contexto-y-planteamiento-del-defecto-epistemológico>
En sistemas de protección basados en visión artificial industrial (VBPD
\- #emph[Vision-Based Protective Devices] según ISO 13855 e ISO
13849-1), el sistema de percepción determina de forma autónoma cuándo
abrir o cerrar los contactores de parada de emergencia de maquinaria
peligrosa (ej. celdas robóticas, prensas, transportadores).

Para mitigar el ruido estocástico de detección y suavizar trayectorias
métricas en el plano del suelo ($Z_w = 0$), se utiliza un Filtro de
Kalman métrico 2D. Sin embargo, en arquitecturas tradicionales de
tracking surge un grave defecto de #strong[conflación epistemológica]:

\$\$\\text{\\bf \"La predicción de Kalman es una hipótesis matemática a lazo abierto; la medición óptica es un hecho empírico.\"}\$\$

Cuando la visión se interrumpe por oclusiones (pies pasando tras
estructuras, pallets o maquinaria), el filtro opera en modo
#emph[coasting] (estimación a lazo abierto):
$ hat(upright(bold(x)))_k = F hat(upright(bold(x)))_(k - 1) $

Esta extrapolación asume que el trabajador continúa indefinidamente a
velocidad constante. En la realidad física, un ser humano no observado
es libre de acelerar, frenar, tropezar, arrodillarse o cambiar de
dirección abruptamente. A medida que transcurre el tiempo sin fotones,
el volumen de incertidumbre de la posición física real crece de forma
cuadrática y cúbica.

Tratar una predicción cinemática sin fotones con idéntica autoridad que
una medición respaldada por sensores ópticos constituye una
vulnerabilidad crítica de seguridad industrial: \* #strong[Escalada
hacia el peligro (Fail-Safe):] Si una predicción cinemática entra en la
zona de peligro $P_(upright("danger"))$, disparar la parada es
conservador y seguro (evita accidentes incluso si fue una
sobre-estimación). \* #strong[Desescalada hacia la seguridad
(Peligrosa):] Si un track que violó $P_(upright("danger"))$ proyecta
cinemáticamente que ha salido hacia la zona segura
$P_(upright("release"))$ sin confirmación sensorial, liberar el relé de
parada puede ser mortal si el trabajador en realidad tropezó y yace
inmóvil dentro del radio de alcance del robot.

#divider()

=== 2. Descomposición Espectral del Ruido de Medición
<descomposición-espectral-del-ruido-de-medición>
Las coordenadas métricas $\(X_w\,Y_w\)$ en el piso están corrompidas por
tres procesos estocásticos aditivos superpuestos:

$ tilde(upright(bold(z)))_k = upright(bold(z))_k + bold(eta)_(upright("jitter")) + bold(eta)_(upright("quant")) + bold(eta)_(upright("parallax")) $

+ #strong[Jitter de Keypoints ($bold(eta)_(upright("jitter"))$):]
  Fluctuaciones espaciales de alta frecuencia (10 a 30 Hz, magnitud
  típica
  $sigma approx 0.015 upright(" m") = plus.minus 15 upright(" mm")$),
  debidas a regresión subpíxel de mapas de calor en redes neuronales,
  ondulación de prendas de vestir e interpolación de bordes.
+ #strong[Cuantización de Píxeles ($bold(eta)_(upright("quant"))$):]
  Discretización espacial por la resolución finita del sensor
  ($640 times 640$). Bajo la matriz de homografía $H$, cada píxel
  representa una celda métrica con dispersión
  $sigma_(upright("quant")) approx plus.minus 10 upright(" a ") 40 upright(" mm")$.
+ #strong[Paralaje de Bounding Box ($bold(eta)_(upright("parallax"))$):]
  Desplazamiento estructural de frecuencia media
  ($plus.minus 50 upright(" a ") 250 upright(" mm")$, media
  $approx plus.minus 100 upright(" mm")$) al degradar a la base de la
  caja (`BBOX_BOTTOM`), donde la postura corporal y la perspectiva
  proyectiva alejan la base del punto real de contacto anatómico.

==== Demostración Matemática: Explosión de Ruido en Diferenciación Numérica ($Delta x\/Delta t$)
<demostración-matemática-explosión-de-ruido-en-diferenciación-numérica-delta-x-delta-t>
Si se intenta calcular la velocidad de aproximación mediante diferencias
finitas hacia atrás
$hat(v)_k = frac(tilde(z)_k - tilde(z)_(k - 1), Delta t)$ a 30 FPS
($Delta t = 0.0333 upright(" s")$):

$ sigma_v = frac(sqrt(2) sigma_(upright("pos")), Delta t) = frac(sqrt(2) times 0.015 upright(" m"), 0.0333 upright(" s")) approx 0.637 upright(" m/s") quad\(2.29 upright(" km/h")\) $

Una cota estándar de $3 sigma_v$ genera picos espurios continuos de
velocidad de: $ 3 sigma_v approx 1.91 upright(" m/s") $

Dado que la norma ISO 13855 define la velocidad humana industrial de
aproximación como $K = 1.6 upright(" m/s")$, #strong[la diferenciación
numérica simple dispara continuamente el bypass de emergencia en
trabajadores estacionarios o en ligero balanceo postural.] El uso de un
filtro estocástico estructurado (Kalman) es una exigencia
físico-matemática.

#divider()

=== 3. Justificación Cinemática: Velocidad Constante (CV) vs Aceleración Constante (CA)
<justificación-cinemática-velocidad-constante-cv-vs-aceleración-constante-ca>
Se evaluó si modelar el movimiento humano como Velocidad Constante (CV,
estado 4D: $\[X\,Y\,v_x\,v_y\]^T$) o Aceleración Constante (CA, estado
6D: $\[X\,Y\,v_x\,v_y\,a_x\,a_y\]^T$).

==== 3.1 Cota Biomecánica de Aceleración Humana
<cota-biomecánica-de-aceleración-humana>
La aceleración máxima en marcha humana durante arranque en sprint o
frenada brusca está acotada por el coeficiente de fricción piso-calzado
($mu approx 0.7$):
$ a_max approx 2.5 upright(" a ") 3.5 upright(" m/s")^2 $

En un único intervalo de cuadro a 30 FPS
($Delta t = 0.0333 upright(" s")$): \* Cambio de velocidad por cuadro:
$Delta v = a_max Delta t lt.eq 3.5 times 0.0333 approx 0.117 upright(" m/s")$.
\* Desplazamiento posicional atribuible a la aceleración:
$ Delta x_(upright("acc")) = 1 / 2 a_max\(Delta t\)^2 lt.eq 1 / 2\(3.5\)\(0.0333\)^2 approx 0.00194 upright(" m") = upright(bold(1.94 upright(" mm"))) $

==== 3.2 Relación Ruido-Señal
<relación-ruido-señal>
Comparando el desplazamiento físico real frente al piso de ruido del
sensor: \* Desplazamiento por aceleración:
$upright(bold(1.94 upright(" mm")))$ \* Piso de ruido por jitter:
$upright(bold(15.00 upright(" mm")))$ \* Relación Ruido-a-Señal:
$ frac(sigma_(upright("jitter")), Delta x_(upright("acc"))) = frac(15.0 upright(" mm"), 1.94 upright(" mm")) approx upright(bold(7.73)) $

La aceleración física en un solo fotograma es un orden de magnitud
inferior al ruido de medición. Es físicamente inobservable a 30 FPS.

==== 3.3 Explosión de Varianza en la Segunda Derivada (Modelos CA)
<explosión-de-varianza-en-la-segunda-derivada-modelos-ca>
En un modelo CA, la aceleración debe inferirse a partir de la segunda
diferencia discreta:
$ hat(a)_k approx frac(tilde(z)_k - 2 tilde(z)_(k - 1) + tilde(z)_(k - 2), Delta t^2) arrow.r.double.long upright("Var")\(hat(a)\)= frac(6, Delta t^4) sigma_(upright("pos"))^2 $

Evaluando con $Delta t = 0.0333 upright(" s")$
($Delta t^4 approx 1.23 times 10^(- 6) upright(" s")^4$) y
$sigma_(upright("pos")) = 0.015 upright(" m")$:
$ upright("Var")\(hat(a)\)approx 1097 upright(" m")^2\/upright("s")^4 arrow.r.double.long sigma_a approx upright(bold(33.1 upright(" m/s")^2 med\(> 3.3 upright(" g")\))) $

Un error de estimación de aceleración con desviación típica de
$3.3 upright(" g")$ provoca oscilaciones violentas, sobredisparos
numéricos y falsas alarmas inaceptables. Por tanto, el modelo de
#strong[Velocidad Constante (CV) con ruido de proceso $Q$ que absorbe
las maniobras humanas es la formulación matemáticamente óptima].

#divider()

=== 4. Envolvente de Divergencia Cuadrática y Estados de Observación
<envolvente-de-divergencia-cuadrática-y-estados-de-observación>
Durante oclusión, la posición real del operario diverge de la predicción
de Kalman a lazo abierto según:

$ parallel Delta upright(bold(p))\(t\)parallel lt.eq 1 / 2 a_max t^2 + v_0 t\(1 - cos theta\) $

Evaluando cuadro a cuadro a 30 FPS ($v_0 = 1.6 upright(" m/s")$,
$a_max = 3.0 upright(" m/s")^2$):

#figure(
  align(center)[#table(
    columns: (14.29%, 14.29%, 14.29%, 14.29%, 14.29%, 14.29%, 14.29%),
    align: (center,center,center,center,center,center,center,),
    table.header([Cuadros Perdidos ($k$)], [Tiempo Transcurrido
      ($t$)], [Sobrepaso Lineal ($v_0 t$)], [Divergencia Maniobra
      ($1 / 2 a t^2$)], [Divergencia Máxima], [% Buffer Histeresis
      ($Delta d = 200 upright(" mm")$)], [Estado Epistémico],),
    table.hline(),
    [#strong[0
    cuadros]], [$0.0 upright(" ms")$], [$0 upright(" mm")$], [$0.0 upright(" mm")$], [$upright(bold(0.0 upright(" mm")))$], [$0.0 %$], [#strong[`OBSERVED`]],
    [#strong[1
    cuadro]], [$33.3 upright(" ms")$], [$53 upright(" mm")$], [$1.7 upright(" mm")$], [$approx upright(bold(55 upright(" mm")))$], [$27.5 %$], [#strong[`PREDICTED`]],
    [#strong[2
    cuadros]], [$66.7 upright(" ms")$], [$107 upright(" mm")$], [$6.7 upright(" mm")$], [$approx upright(bold(113 upright(" mm")))$], [$56.5 %$], [#strong[`PREDICTED`]],
    [#strong[3
    cuadros]], [$100.0 upright(" ms")$], [$160 upright(" mm")$], [$15.0 upright(" mm")$], [$approx upright(bold(175 upright(" mm")))$], [$87.5 %$], [#strong[`PREDICTED`]
    (Límite Seguro)],
    [#strong[4
    cuadros]], [$133.3 upright(" ms")$], [$213 upright(" mm")$], [$26.7 upright(" mm")$], [$approx upright(bold(240 upright(" mm")))$], [$120.0 %$], [#strong[`STALE`]
    (Buffer Violado)],
    [#strong[5
    cuadros]], [$166.7 upright(" ms")$], [$267 upright(" mm")$], [$41.7 upright(" mm")$], [$approx upright(bold(308 upright(" mm")))$], [$154.0 %$], [#strong[`STALE`]
    (Crítico)],
    [#strong[\> 5
    cuadros]], [$> 166.7 upright(" ms")$], [$> 320 upright(" mm")$], [$> 60.0 upright(" mm")$], [$> upright(bold(380 upright(" mm")))$], [$> 190.0 %$], [#strong[`EXPIRED`
    \/ `DELETED`]],
  )]
  , kind: table
  )

#divider()

=== 5. Decisión de Diseño
<decisión-de-diseño>
Se establecen los siguientes principios e implementaciones
arquitectónicas:

+ #strong[Modelo Epistémico de Tres Estados (`ObservationStatus`):]
  - `OBSERVED` ($k = 0$): Respaldo directo por fotones del sensor óptico
    en el fotograma actual. Plena autoridad de control.
  - `PREDICTED` ($1 lt.eq k lt.eq 3$): Extrapolación cinemática acotada
    estrictamente dentro del margen de histéresis espacial
    ($lt.eq 175 upright(" mm") < 200 upright(" mm")$).
  - `STALE` ($4 lt.eq k lt.eq 5$): Extrapolación especulativa cuya
    divergencia excede el margen físico de seguridad
    ($> 200 upright(" mm")$).
+ #strong[Invariante de Salvaguarda Asimétrica:]
  - #strong[Invariante I (Escalada Fail-Safe):] La incursión en
    $P_(upright("danger"))$ y escalada a `DANGER_INTRUSION` puede
    activarse mediante estados `OBSERVED`, `PREDICTED` o `STALE`.
  - #strong[Invariante II (Desescalada Gated en Evidencia Óptica):] El
    incremento de `clean_count` y la liberación de la violación requiere
    estrictamente $N_(upright("release"))$ cuadros consecutivos con
    estado `OBSERVED` fuera de $P_(upright("release"))$. Pistas en
    `PREDICTED` o `STALE` tienen terminantemente prohibido desescalar la
    seguridad.
  - #strong[Invariante III (Enclavamiento por Desaparición de Intruso):]
    Si una pista violadora que disparó `DANGER_INTRUSION` desaparece del
    rastreo (se poda al exceder `max_missed` sin salida óptica
    verificada), el sistema enclava en estado `LOCKOUT` con relé abierto
    (`trip = True`). Solo puede restablecerse mediante reset explícito
    autorizado (`fsm.reset()`).
  - #strong[Invariante IV (Congelamiento de Dwell Time):] El tiempo de
    permanencia en zona de advertencia representa exposición física
    acumulada a riesgo. Durante oclusión (`PREDICTED` / `STALE`), el
    contador `dwell_time_s` se congela en el último valor empíricamente
    verificado.

#divider()

=== 6. Consecuencias y Cumplimiento Normativo
<consecuencias-y-cumplimiento-normativo>
- #strong[Seguridad Funcional (ISO 13849-1 Categoría 3/4, PL d/e):] Se
  elimina el modo de fallo catastrófico donde un operario caído u oculto
  en zona de peligro permite que la máquina arranque debido a una
  predicción de salida matemática no confirmada.
- #strong[Eliminación de Paradas Falsas por Dwell:] Se evita que un
  trabajador oculto tras un obstáculo acumule tiempo ficticio de
  permanencia que dispare falsas alarmas en planta.
- #strong[Sobrecarga Computacional Despreciable:] La evaluación del
  estado de observación y el congelamiento de dwell demandan menos de
  $5 thin mu upright("s")$ por cuadro, manteniendo el presupuesto de
  latencia de percepción ($T_1 lt.eq 50 upright(" ms")$) holgadamente
  satisfecho.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-009: Desacoplamiento de Autómata Espacial y Clasificación Temporal de Dwell en Regiones Ortogonales (Statecharts) <adr-009>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-31
- #strong[Módulos Asociados:] `src/core/spatial_fsm.py`,
  `src/pipeline/safety_pipeline.py`, `src/utils/visualizer.py`
- #strong[Estándares Aplicables:] ISO 13855:2024, ISO 13849-1 (PL d/e),
  IEC 61508 (SIL 2/3), Harel Statecharts (ISO/IEC 19501)

#divider()

=== 1. Contexto y Planteamiento del Defecto
<contexto-y-planteamiento-del-defecto>
En sistemas industriales de salvaguarda basados en visión por computador
(VBPD - #emph[Vision-Based Protective Devices]), la lógica de control
debe responder simultáneamente a dos preguntas físicas fundamentales:

+ #strong[Ocupación Espacial:] #emph[¿Dónde se encuentra físicamente el
  trabajador respecto a los límites de la zona de peligro
  ($P_(upright("danger"))$), la banda de histéresis ($Delta d$) y su
  vector cinemático ($arrow(v)$)?]
+ #strong[Permanencia Temporal (#emph[Dwell Time]):] #emph[¿Cuánto
  tiempo lleva el trabajador presente de forma ininterrumpida dentro de
  la zona restringida?]

==== El Antipatrón: Conflación de Estados en una FSM Plana
<el-antipatrón-conflación-de-estados-en-una-fsm-plana>
En implementaciones iniciales, estos dos dominios ortogonales se
aplanaron en un único enum lineal:

```
OUTSIDE ──► ENTER_PENDING ──► INTRUSION_ACTIVE ──► DWELL_WARNING ──► DWELL_VIOLATION ──► EXIT_PENDING
```

Este diseño genera tres defectos arquitectónicos graves:

+ #strong[Conflación de Disparadores (Triggers):]
  - Las transiciones espaciales son disparadas por observaciones
    métricas $\(X_w\,Y_w\)in bb(R)^2$ y debounce discreto
    ($N_(upright("confirm"))\,N_(upright("release"))$).
  - Las transiciones de #emph[dwell] son disparadas por integración de
    tiempo continuo $t_(upright("dwell")) = integral d t$ condicionada a
    la presencia dentro de la zona.
+ #strong[Ambigüedad en el Lazo de Seguridad:]
  - Un operario en `DWELL_WARNING` sigue estando físicamente en
    intrusión dentro de $P_(upright("danger"))$. Tratar `DWELL_WARNING`
    como un estado mutuamente excluyente de `INTRUSION_ACTIVE` confunde
    la semántica del relé de parada.
+ #strong[Acoplamiento Rígido de Políticas:]
  - Modificar los umbrales de permanencia
    ($T_(upright("warn"))\,T_(upright("violation"))$) o incorporar
    políticas de merodeo (#emph[loitering]) multinivel forzaba a
    reescribir y re-validar la histéresis espacial y los contadores de
    debounce.

#divider()

=== 2. Decisión Arquitectónica: Descomposición en Regiones Ortogonales (Statecharts)
<decisión-arquitectónica-descomposición-en-regiones-ortogonales-statecharts>
Se adopta el formalismo de #strong[Statecharts de Harel] (regiones
concurrentes ortogonales), donde el estado global del sistema es el
producto cartesiano de dos autómatas desacoplados:

$ cal(S)_(upright("global")) = cal(S)_(upright("occupancy")) times cal(S)_(upright("dwell")) $

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ REGION 1: AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)                   │
│                                                                             │
│               [ OUTSIDE ] ◄─────────────────┐                               │
│                    │                        │                               │
│     (Punto dentro) │                        │ (N_release cuadros OBSERVED   │
│                    ▼                        │  fuera de P_release)          │
│            [ ENTER_PENDING ]                │                               │
│                    │                        │                               │
│ (N_confirm cuadros │                        │                               │
│  o vn >= 1.6 m/s)  ▼                        │                               │
│               [ INSIDE ] ──────────► [ EXIT_PENDING ]                       │
│              (trip=True)    (Punto fuera    │                               │
│                              de P_danger)   │                               │
└────────────────────┬────────────────────────┴───────────────────────────────┘
                     │ (Condición de guardia: Occupancy == INSIDE)
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ REGION 2: CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)                 │
│                                                                             │
│    (Occupancy != INSIDE) ──► [ NONE ] (Timer inactivo / reset a 0.0s)        │
│                                                                             │
│    [ NORMAL ] ──(t >= T_warn)──► [ WARNING ] ──(t >= T_violation)──► [ VIOLATION ] │
│   (0 <= t < T_warn)            (T_warn <= t < T_viol)           (t >= T_viol)│
└─────────────────────────────────────────────────────────────────────────────┘
```

#divider()

=== 3. Dinámica de Transición y Tablas de Verdad
<dinámica-de-transición-y-tablas-de-verdad>
==== 3.1. Región 1: Estados de Ocupación Espacial (`OccupancyState`)
<región-1-estados-de-ocupación-espacial-occupancystate>
- #strong[`OUTSIDE`:] Ningún track confirmado dentro de
  $P_(upright("danger"))$ ni en banda de histéresis
  $P_(upright("release"))$.
- #strong[`ENTER_PENDING`:] Track detectado dentro de
  $P_(upright("danger"))$ con contador de confirmación
  $0 < n < N_(upright("confirm"))$ y velocidad normal
  $v_n < 1.6 upright(" m/s")$.
- #strong[`INSIDE`:] Incursión confirmada
  ($n gt.eq N_(upright("confirm"))$ o #emph[bypass] cinemático por
  $v_n gt.eq 1.6 upright(" m/s")$). #strong[Abre contactores de
  seguridad (`trip=True`) inmediatamente ($t = 0 upright(" s")$).]
- #strong[`EXIT_PENDING`:] Track previamente `INSIDE` que sale de
  $P_(upright("danger"))$ pero aún no completa $N_(upright("release"))$
  cuadros estrictamente `OBSERVED` fuera de $P_(upright("release"))$.

==== 3.2. Región 2: Estados de Permanencia Temporal (`DwellState`)
<región-2-estados-de-permanencia-temporal-dwellstate>
- #strong[`NONE`:] Inactivo cuando `OccupancyState != INSIDE`.
- #strong[`NORMAL`:]
  $0.0 upright(" s") lt.eq t_(upright("dwell")) < T_(upright("warn"))$
  (presencia dentro del tiempo de ciclo permitido).
- #strong[`WARNING`:]
  $T_(upright("warn")) lt.eq t_(upright("dwell")) < T_(upright("violation"))$
  (alerta de permanencia excesiva).
- #strong[`VIOLATION`:]
  $t_(upright("dwell")) gt.eq T_(upright("violation"))$ (violación
  crítica de tiempo de permanencia).

#divider()

=== 4. Invariante de Seguridad Funcional (Fail-Safe Invariant)
<invariante-de-seguridad-funcional-fail-safe-invariant>
$ upright("trip") =\(upright("OccupancyState") = = upright("INSIDE")\)or upright("FAULT") or upright("LOCKOUT") $

La parada de emergencia (`trip = True`) #strong[NO espera a que el dwell
timer alcance `WARNING` o `VIOLATION`]. El disparo ocurre en el instante
$t = 0.0 upright(" s")$ de la confirmación espacial de `INSIDE`. El
estado de #emph[dwell] actúa como un clasificador semántico y de
diagnóstico operacional.

#divider()

=== 5. Consecuencias
<consecuencias>
- #strong[Positivas:]
  - Separación total de responsabilidades entre geometría/cinemática y
    temporizadores.
  - Facilidad para reconfigurar tiempos de advertencia
    ($T_(upright("warn"))$) sin alterar el comportamiento de debounce
    espacial.
  - Claridad total en telemetría, visualización y auditoría funcional.
- #strong[Neutras:]
  - Los consumidores de la API reciben `occupancy_state` y `dwell_state`
    en lugar de un único string.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-010: Doble Horizonte Temporal de Latencia en Edge AI Industrial (ISO 13855 / IEC 61496) <adr-010>

- #strong[Estatus:] Aceptado
- #strong[Fecha:] 2026-08-31
- #strong[Módulos Asociados:] `src/pipeline/safety_pipeline.py`,
  `src/core/spatial_fsm.py`, `scripts/run_demo.py`,
  `scripts/benchmark.py`
- #strong[Estándares Aplicables:] ISO 13855:2024 (Safety Distances &
  Overall Stopping Performance), IEC 61496 (VBPDs), IEC 61508 (SIL 2/3)

#divider()

=== 1. Contexto y Planteamiento del Problema
<contexto-y-planteamiento-del-problema>
En aplicaciones de visión por computador para seguridad industrial y
Edge AI, la métrica de rendimiento típicamente reportada en la
literatura es la latencia de inferencia de la red neuronal
($T_(upright("infer"))$) o la tasa de cuadros por segundo
($upright("FPS")$).

Sin embargo, en sistemas de protección funcional certificados bajo
#strong[ISO 13855:2024], la distancia de separación de seguridad
requerida se rige por la ecuación:

$ S = K dot.op T + C = K dot.op\(t_1 + t_2 + t_3\)+ C $

Donde $t_1$ representa el tiempo de respuesta total del dispositivo
sensor (VBPD).

==== El Antipatrón: Conflación entre Throughput de Pipeline y Reacción del Evento Físico
<el-antipatrón-conflación-entre-throughput-de-pipeline-y-reacción-del-evento-físico>
Medir únicamente la latencia del fotograma dentro del pipeline
($T_(upright("system"))$) introduce dos errores de metrología críticos
en planta:

+ #strong[Omisión de la Latencia de Ingestión y Buffer
  ($T_(upright("capture"))$):] Los fotogramas capturados por sensores
  V4L2, MIPI-CSI o RTSP GStreamer pueden acumular retraso en colas del
  kernel del sistema operativo (#emph[buffer bloat]), distorsionando el
  tiempo real de llegada de la imagen.
+ #strong[Conflación de $T_(upright("pipeline"))$ con la Reacción del
  Evento ($T_(upright("event"))$):] Un pipeline que procesa a
  $15 upright(" ms")$ ($66 upright(" FPS")$) no detiene la máquina en
  $15 upright(" ms")$ si implementa filtros de debounce temporal
  ($N_(upright("confirm")) = 3$ cuadros). A 30 FPS, la persona debe
  permanecer físicamente dentro de la zona durante 2 intervalos de
  cuadro adicionales ($approx 66.7 upright(" ms")$), haciendo que la
  latencia real del evento sea de $approx 81.7 upright(" ms")$.

#divider()

=== 2. Decisión Arquitectónica: Modelo de Doble Horizonte Temporal
<decisión-arquitectónica-modelo-de-doble-horizonte-temporal>
Se implementa una arquitectura desacoplada de doble horizonte temporal
para el perfilado de rendimiento en Edge AI:

```
════════════════════════════════════════════════════════════════════════════════
                        MODELO DE DOBLE HORIZONTE
════════════════════════════════════════════════════════════════════════════════

HORIZONTE 1: LATENCIA DE SISTEMA POR CUADRO (T_system)
┌───────────┐   ┌─────────────────────────────────────────────────────────┐
│ T_capture │ + │ T_pre + T_infer + T_pose + T_geom + T_track + T_fsm     │ = T_system
└───────────┘   └─────────────────────────────────────────────────────────┘
  (Buffer lag)                          (Pipeline T1)

HORIZONTE 2: LATENCIA DE REACCIÓN DEL EVENTO FÍSICO (T_event)
Entrada física en P_danger
(t = t_entry)
      │
      ▼
┌──────────────┐     ┌──────────────┐     ┌───────────────────┐
│ Frame 1      │ ──► │ Frame 2      │ ──► │ Frame N_confirm   │ ──► RELÉ ABIERTO (TRIP)
│ (t_entry)    │     │              │     │ (t_trip)          │     (t = t_trip)
└──────────────┘     └──────────────┘     └───────────────────┘
      │                                             ▲
      └────────────────── T_event ──────────────────┘
                 (t_trip - t_entry)
════════════════════════════════════════════════════════════════════════════════
```

==== 1. Latencia de Sistema por Cuadro ($T_(upright("system"))$)
<latencia-de-sistema-por-cuadro-t_textsystem>
Mide la duración determinista de procesamiento de cada fotograma
individual:
$ T_(upright("system")) = T_(upright("capture")) + T_(upright("pre")) + T_(upright("infer")) + T_(upright("pose")) + T_(upright("geom")) + T_(upright("track")) + T_(upright("fsm")) $

==== 2. Latencia de Reacción del Evento ($T_(upright("event"))$)
<latencia-de-reacción-del-evento-t_textevent>
Mide el delta de tiempo físico continuo transcurrido desde el instante
de la primera intrusión detectada en $P_(upright("danger"))$
($t_(upright("entry"))$) hasta la confirmación y apertura del relé de
parada (`trip = True` en $t_(upright("trip"))$):

$ T_(upright("event")) = t_(upright("trip")) - t_(upright("entry")) $

- #strong[En Aproximación Normal ($v_n < 1.6 upright(" m/s")$):]
  $ T_(upright("event")) =\(N_(upright("confirm")) - 1\)dot.op Delta t_(upright("frame")) + T_(upright("system")) $
- #strong[En Aproximación Rápida ($v_n gt.eq 1.6 upright(" m/s")$ ---
  Bypass ISO 13855):]
  $ T_(upright("event")) = 0 dot.op Delta t_(upright("frame")) + T_(upright("system")) = T_(upright("system")) $

#divider()

=== 3. Consecuencias y Beneficios
<consecuencias-y-beneficios>
- #strong[Cumplimiento Normativo Riguroso:] Proporciona los valores
  empíricos $t_1$ exactos requeridos por ISO 13855:2024 para el cálculo
  de distancias mínimas $S$.
- #strong[Auditoría de Ingestión Edge AI:] Detecta saturación de buffer
  y pérdida de sincronismo en tiempo real.
- #strong[Transparencia en Telemetría:] Cada evento de intrusión emitido
  en el stream JSONL incluye su `event_latency_ms` individual.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-011: Bayesian Validation Gating (Mahalanobis $chi^2$), Asignación Global Húngara y World-Space Spatial Birth NMS <adr-011>

=== Estado
<estado>
#strong[Aceptado y Aplicado] (2026-09-01)

=== Contexto
<contexto>
En el seguimiento multi-objetivo (#emph[Multi-Object Tracking - MOT])
para zonas de seguridad industrial bajo la norma ISO 13855, el sistema
inicial utilizaba una compuerta espacial euclidiana fija
($d_(upright("gate")) lt.eq 1.0 upright(" m")$) combinada con una
asignación codiciosa (#emph[greedy nearest-neighbor]).

Durante la evaluación empírica con datasets de alta densidad peatonal y
oclusiones dinámicas complejas (`pets2009_s2_l1` y `openvino_people`),
se manifestaron cuatro fallos arquitectónicos:

+ #strong[Falacia de Incertidumbre Isotrópica:] Tratar la compuerta de
  asociación como un círculo euclidiano ignora la cinemática del
  operario. La incertidumbre real no es esférica, sino una
  #strong[elipse anisótropa] orientada según el vector de velocidad
  $arrow(v) =\[v_x\,v_y\]$ y la covarianza de estado $P$.
+ #strong[Rigidez durante Oclusión (#emph[Coasting]):] Cuando un
  operario pasa varios cuadros sin detección, la matriz de covarianza
  $P$ crece por la propagación $F P F^T + Q$. Mantener un radio de
  búsqueda rígido de $1.0 upright(" m")$ provoca pérdidas de track y
  fragmentación de identidades (#emph[ID Switching]) al momento de la
  reaparición.
+ #strong[Asignación Subóptima Local (#emph[Greedy Bias]):] Ordenar los
  pares por distancia euclidiana de forma codiciosa permite que un falso
  positivo cercano robe el track de un operario legítimo, forzando a la
  detección real a ser descartada o asignada a otro track.
+ #strong[Proliferación de Tracks Fantasma (#emph[Ghost Tracks]):]
  Cuando el detector YOLO entrega dos propuestas cercanas sobre el mismo
  cuerpo (por ejemplo, tobillos separados o propuestas dobles de NMS
  2D), la propuesta huérfana inicializa un segundo track duplicado en
  paralelo.

#divider()

=== Decisión
<decisión>
==== 1. Compuerta de Validación Bayesiana de Mahalanobis ($chi^2$ Gating)
<compuerta-de-validación-bayesiana-de-mahalanobis-chi2-gating>
Se reemplaza la distancia euclidiana por la distancia cuadrática de
Mahalanobis normalizada por la matriz de covarianza de innovación
$S_i in bb(R)^(2 times 2)$:

$ S_i = H P_(i\|k - 1) H^T + R = P_(i\[: 2\,: 2\]) + R $

$ d_M^2\(i\,j\)=\(upright(bold(z))_j - hat(upright(bold(x)))_(i\,p o s)\)^T S_i^(- 1)\(upright(bold(z))_j - hat(upright(bold(x)))_(i\,p o s)\) $

- #strong[Inversión Analítica $2 times 2$:] Se utiliza la regla de
  Cramer para calcular $S_i^(- 1)$ en $< 30 upright(" ns")$ con piso de
  no-singularidad:
  $ S^(- 1) = frac(1, s_00 s_11 - s_01 s_10) mat(delim: "[", s_11, - s_01; - s_10, s_00) $
- #strong[Criterio Estadístico $chi^2$ (2 Grados de Libertad):] Como la
  medición es bidimensional ($upright(bold(z)) in bb(R)^2$), $d_M^2$
  sigue una distribución Chi-cuadrado $chi_2^2$. Se establece la
  compuerta en $gamma = 9.210$ (intervalo de confianza del $99 %$). Toda
  detección con $d_M^2 > 9.210$ es rechazada estadísticamente antes de
  la asignación.
- #strong[Vectorización Tensorial Einstein:] Se calcula el tensor
  completo $N times M$ mediante
  `np.einsum("nab,nmb->nma", S_inv_arr, Y)` en $0.017 upright(" ms")$
  para $10 times 10$ objetivos.

==== 2. Asignación Global Bipartita (Algoritmo Húngaro / Munkres)
<asignación-global-bipartita-algoritmo-húngaro-munkres>
Se construye la matriz de costos global $C in bb(R)^(N times M)$:

$ C_(i\,j) = cases(delim: "{", d_M^2\(i\,j\) & upright("si ") d_M^2\(i\,j\)lt.eq 9.210, 10^5 & upright("si ") d_M^2\(i\,j\)> 9.210 quad\(upright("rechazo por gating")\)) $

Se resuelve la asignación biunívoca global mínima mediante
`scipy.optimize.linear_sum_assignment(C)` en complejidad
$cal(O)\(N^3\)$, eliminando el sesgo codicioso.

==== 3. World-Space Spatial Birth Non-Maximum Suppression (NMS)
<world-space-spatial-birth-non-maximum-suppression-nms>
Se introduce una regla de no-nacimiento en el espacio métrico del piso:
\* Ninguna detección no asignada $upright(bold(z))_j$ puede instanciar
un nuevo track tentativo si su distancia euclidiana al plano de suelo
respecto a cualquier track activo/confirmado es menor a
$d_(upright("birth_min")) = 0.6 upright(" m")$ (radio del cuerpo humano
según ISO 13855). \* Se suprimen también propuestas concurrentes
huérfanas en el mismo cuadro separadas por menos de $0.6 upright(" m")$.

#divider()

=== Consecuencias
<consecuencias>
==== Positivas:
<positivas>
- #strong[Invariancia a Cruces de Trayectorias:] En cruces densos de
  peatones, la asignación global mantiene la trayectoria inercial de
  cada sujeto sin intercambios de identificadores ni cambios erráticos
  de color en BEV.
- #strong[Adaptación Dinámica durante Coasting:] A mayor tiempo en
  oclusión, la compuerta se ensancha automáticamente a lo largo del
  vector de velocidad, facilitando la reasociación natural del operario
  al salir de detrás de un obstáculo.
- #strong[Eliminación Total de Ghost Tracks:] Se suprimen los vectores
  dobles sobre una misma persona causados por propuestas redundantes de
  YOLO.
- #strong[Latencia Despreciable:] La combinación de inversión analítica
  y vectorización `einsum` ejecuta la asignación en
  #strong[$0.017 upright(" ms")$] para 10 personas, consumiendo menos
  del $0.1 %$ del presupuesto temporal de $50 upright(" ms")$ de la
  norma ISO 13855.

==== Negativas / Compromisos:
<negativas-compromisos>
- Incorpora la dependencia de `scipy>=1.10.0` en `requirements.txt`.
#v(1.5em)

#line(length: 100%, stroke: 1pt + rgb("#0284C7"))
== ADR-012: Generación de Videos Sintéticos Fotorrealistas con Escala Pinhole e Identidad Única <adr-012>

=== Estado
<estado>
Aceptado

=== Contexto
<contexto>
Para validar de forma determinista y reproducible el pipeline de
seguridad industrial (incursión limpia, oclusión de extremidades
inferiores y tiempo de permanencia / #emph[dwell time]), se diseñó un
generador sintético de video (`src/utils/synthetic_generator.py`).

Sin embargo, las implementaciones iniciales sufrieron dos problemas
fundamentales: 1. #strong[Falta de Detección en YOLO (Synthetic Domain
Gap):] Los humanoides dibujados con primitivas geométricas vectoriales
planas (`cv2.line`, `cv2.rectangle`) carecían de los gradientes,
texturas fotográficas y anatomía orgánica que activan los feature maps
convolucionales de los modelos YOLO pre-entrenados en COCO
($c o n f = 0.00$, 0% detección). 2. #strong[Inconsistencia de Identidad
y Escala (#emph[Identity Flickering & Underscaling]):] - El muestreo
discontinuo de candidatos causaba que el operario cambiara de vestimenta
y silueta cada 3 fotogramas. - El escalado de altura por delta local
sub-escalaba al sujeto en el fondo ($Y gt.eq 4.0 upright(" m")$) a menos
de 90 píxeles, provocando pérdida de detección por tamaño diminuto. -
Los textos del generador colisionaban en la coordenada
$y = 50 upright(" px")$ con el banner del HUD de seguridad.

=== Decisión
<decisión>
Se decide implementar una arquitectura de renderizado sintético 2.5D
basada en: 1. #strong[Extracción y Normalización de Tracklet de
Identidad Única:] - Un único sujeto continuo trackeado en video real
mediante IoU es segmentado con `yolo11n-seg` y normalizado en un lienzo
canónico de $160 times 320 upright(" RGBA")$ con alpha-feathering suave
y anclaje de pies en el borde inferior. 2. #strong[Escalado Perspectivo
Pinhole Calibrado:] - La altura en píxeles del actor a cualquier
profundidad métrica $Y in\[0.0\,6.0\]upright(" m")$ sigue estrictamente
la proyección de cámara estenopeica (#emph[pinhole]):
$ h_(p x)\(Y\)= frac(480.0, 1.0 + 0.165 dot.op Y) $ Garantizando
$h in\[240\,480\]upright(" px")$ y manteniendo al sujeto siempre dentro
del rango óptimo de detección de YOLO. 3. #strong[Sombra de Contacto
Direccional Gaussiana:] - Proyección de elipse difusa con desenfoque
Gaussiano bajo los pies del actor para integración visual sobre el piso
industrial. 4. #strong[Desacoplamiento Estricto de Capas de UI:] - El
HUD del pipeline de seguridad se confina al banner superior (56px) con
pastillas de alto contraste, mientras que la metadata de simulación se
dibuja en un badge inferior ($y = 1040 upright(" px")$), evitando
cualquier colisión textual.

=== Consecuencias
<consecuencias>
==== Positivas
<positivas>
- #strong[100% de Tasa de Detección:] Cobertura total en las 3
  secuencias de prueba (`sequence_a`, `sequence_b`, `sequence_c`).
- #strong[Alta Confianza:] Confianza promedio de YOLO elevada a
  #strong[0.835 - 0.861].
- #strong[Continuidad Temporal:] Cero saltos de vestimenta o silueta; el
  filtro de Kalman trackea un único sujeto continuo.
- #strong[Legibilidad Industrial:] UI ultra-nítida con pastillas de
  contraste y badges de telemetría desacoplados.

==== Negativas / Mitigaciones
<negativas-mitigaciones>
- Requiere empaquetar una biblioteca liviana de sprites RGBA curados en
  `data/assets/sprites/worker/` (\~200 KB).
#v(1.5em)

#pagebreak()

= 8. Implementación de Referencia y Snippets de Código Crítico <cap-codigo>

En esta sección se exponen las implementaciones reales de los componentes nucleares del sistema extraídas directamente del árbol `src/`. Cada bloque incluye el razonamiento técnico y los contratos que garantizan la integridad temporal y matemática del pipeline.

== 8.1 Cálculo de Condicionamiento y Proyección Vectorizada (`src/core/homography.py`)

#callout(title: "Contrato Numérico y Estabilidad", color: rgb("#0284C7"))[
  El número de condición $kappa(bold(H)) = sigma_"max" / sigma_"min"$ se calcula mediante descomposición en valores singulares (SVD). Si $kappa(bold(H)) >= 10^6$, la calibración se rechaza inmediatamente para evitar errores de amplificación milimétrica en el cálculo de distancias al suelo.
]

```python
# src/core/homography.py
def calculate_condition_number(H: np.ndarray) -> float:
    """Calcula el número de condición κ(H) = σ_max / σ_min vía SVD."""
    s = np.linalg.svd(H, compute_uv=False)
    if s[-1] < 1e-12:
        return float("inf")
    return float(s[0] / s[-1])

def project_to_world(self, points: np.ndarray) -> np.ndarray:
    """Proyección vectorizada en NumPy de píxeles (u, v) a suelo métrico (X, Y) con Zw = 0."""
    pts = np.atleast_2d(points)
    homogeneous = np.column_stack([pts, np.ones(len(pts))])
    transformed = (self.H @ homogeneous.T).T
    # Normalización proyectiva por coordenada homogénea W
    return transformed[:, :2] / transformed[:, 2:3]
```

== 8.2 Jerarquía de Anclaje de Tobillos (`src/pipeline/safety_pipeline.py`)

#callout(title: "Degradación Controlada", color: rgb("#16A34A"))[
  Cumple con el *ADR-007*. La estimación anatómica prioriza la bisección de tobillos con confianza superior a 0.30. Si ambos están ocluidos, conmuta a la base de la caja delimitadora con penalización de confianza a 0.20 para informar al filtro de Kalman.
]

```python
# src/pipeline/safety_pipeline.py
def extract_ground_anchor(kpts: np.ndarray, bbox: Tuple[float, ...]) -> Tuple[Tuple[float, float], AnchorSource, float]:
    left_conf, right_conf = float(kpts[15, 2]), float(kpts[16, 2])
    # Nivel 1: Ambos tobillos visibles con confianza plena
    if left_conf >= 0.30 and right_conf >= 0.30:
        midpoint = ((float(kpts[15, 0]) + float(kpts[16, 0])) / 2.0,
                    (float(kpts[15, 1]) + float(kpts[16, 1])) / 2.0)
        return midpoint, AnchorSource.ANKLES_DUAL, min(left_conf, right_conf)
    # Nivel 2: Tobillo individual (el otro tapado por maquinaria)
    if left_conf >= 0.30:
        return (float(kpts[15, 0]), float(kpts[15, 1])), AnchorSource.ANKLE_SINGLE, left_conf
    if right_conf >= 0.30:
        return (float(kpts[16, 0]), float(kpts[16, 1])), AnchorSource.ANKLE_SINGLE, right_conf
    # Nivel 3: Base de Bounding Box (degradado)
    bbox_bottom = ((bbox[0] + bbox[2]) / 2.0, bbox[3])
    return bbox_bottom, AnchorSource.BBOX_BOTTOM, 0.20
```

== 8.3 Filtro de Kalman Cinemático y Gating de Mahalanobis (`src/core/kalman_filter.py`)

```python
# src/core/kalman_filter.py
def mahalanobis_distance(self, z: np.ndarray) -> float:
    """Calcula d_M^2 contra la covarianza de innovación S = H P^- H^T + R."""
    y = z - (self._H @ self._x)
    S = self._H @ self._P @ self._H.T + self._R
    return float(y.T @ np.linalg.inv(S) @ y)

def update(self, measurement: Tuple[float, float], confidence: float, source: AnchorSource) -> PositionEstimate:
    z = np.asarray(measurement, dtype=np.float64)
    y = z - (self._H @ self._x)
    S = self._H @ self._P @ self._H.T + self._R
    K = self._P @ self._H.T @ np.linalg.inv(S)
    self._x = self._x + K @ y
    self._P = (self._I - K @ self._H) @ self._P
    return PositionEstimate(xy_m=(float(self._x[0]), float(self._x[1])), confidence=confidence, source=source)
```

== 8.4 Schmitt Trigger Espacial y Bypass por Velocidad ISO 13855 (`src/core/spatial_fsm.py`)

```python
# src/core/spatial_fsm.py
def evaluate_occupant(self, track_id: int, pos: PositionEstimate, velocity: np.ndarray) -> Tuple[bool, OccupancyState]:
    point = Point(pos.xy_m)
    in_danger = self._prepared_danger.contains(point)
    in_release = self._prepared_release.contains(point)
    
    # Bypass dinámico de confirmación si la velocidad hacia el peligro es alta (ISO 13855)
    vn = np.dot(velocity, self._approach_normal)
    if in_danger and vn >= self.config.iso_k_speed:
        self._confirm_counts[track_id] = self.config.n_confirm  # Disparo instantáneo en 1 frame
        
    # Desescalada asimétrica condicionada estrictamente a fotones OBSERVED (ADR-008)
    if not in_release and pos.status == ObservationStatus.OBSERVED:
        self._release_counts[track_id] += 1
    else:
        self._release_counts[track_id] = 0  # Si está en PREDICTED o STALE, no desescala jamás!
```

#pagebreak()

= 9. Guía de Examen Técnico y Defensa Oral (Senior Architect) <cap-defensa>

Este capítulo condensa las preguntas más rigurosas que un arquitecto de software o comité de seguridad industrial formula al auditar una solución de visión artificial en el Edge, junto a las respuestas modelo fundamentadas en estándares internacionales y física determinista.

== Pregunta 1: ¿Por qué la inferencia de una red neuronal nunca debe tomar la decisión de parada directamente?
#callout(title: "Respuesta de Senior Architect", color: rgb("#DC2626"))[
  Las redes neuronales convolucionales o Transformers son estimadores estadísticos no deterministas. Sufren de vulnerabilidades intrínsecas: ataques adversarios, *domain shifts* lumínicos y oclusiones imprevistas. Si se entrena un modelo *end-to-end* para predecir un booleano `trip`, es imposible verificar formalmente los casos de esquina ante normas como IEC 61508 (SIL 2/3) o ISO 13849-1 (PL d/e).
  
  En *Edge Safety Guard*, la IA se restringe estrictamente a percibir coordenadas geométricas en píxeles. Todo el procesamiento posterior —transformación proyectiva euclidiana, estimación cinemática bayesiana y lógica de disparo por polígonos— es puramente determinista, auditable matemáticamente e inmune a las alucinaciones del modelo.
]

== Pregunta 2: ¿Por qué una calibración de exactamente 4 puntos presenta siempre un residuo de reproyección RMSE = 0.00 m?
#callout(title: "Respuesta de Senior Architect", color: rgb("#D97706"))[
  La homografía planar proyectiva $3 times 3$ está definida en coordenadas homogéneas hasta un factor de escala no nulo, lo que le otorga exactamente $9 - 1 = 8$ grados de libertad algebraicos. Cada correspondencia de punto $p_i (u, v) <-> P_i (X, Y)$ aporta exactamente 2 ecuaciones independientes tras eliminar la coordenada proyectiva.
  
  Al calibrar con 4 puntos coplanares no colineales, se obtiene un sistema lineal determinado de 8 ecuaciones con 8 incógnitas ($bold(A) bold(h) = 0$). El residuo algebraico es idénticamente nulo porque la transformación encaja exactamente en los 4 pares de puntos sin grados de libertad sobrantes. Para poder medir un residuo empírico o error cuadrático medio de reproyección (RMSE), es estrictamente necesario emplear un sistema sobredeterminado con $N > 4$ marcadores de calibración o puntos de test independientes.
]

== Pregunta 3: ¿Cómo protege el sistema la integridad mecánica de la maquinaria frente a la oscilación de un operario en el borde?
#callout(title: "Respuesta de Senior Architect", color: rgb("#2563EB"))[
  Mediante el *Schmitt Trigger Espacial* (*#link(<adr-004>)[ADR-004]*). Si se utilizara un polígono único, el ruido estocástico de detección en los keypoints ($approx plus.minus 15" mm"$) haría conmutar el relé de parada a la frecuencia del pipeline (30 Hz), quemando los contactores mecánicos en pocas horas.
  
  La arquitectura define dos polígonos concéntricos con una banda de histéresis espacial de $Delta d = 200" mm"$:
  1. *Polígono de Peligro ($P_"danger"$):* Determina la activación de alarma.
  2. *Polígono de Liberación ($P_"release"$):* Expandido mediante $P_"release" = P_"danger" ⊕ 0.20" m"$.
  
  Para conmutar a peligro, basta con que el operario ingrese a $P_"danger"$. Pero para retornar a estado seguro, el operario debe caminar completamente fuera de $P_"release"$ durante 5 cuadros consecutivos con condición estricta de fotones `OBSERVED`.
]

== Pregunta 4: ¿Por qué está terminantemente prohibido desescalar la alarma si el filtro de Kalman se encuentra en estado PREDICTED?
#callout(title: "Respuesta de Senior Architect", color: rgb("#7C3AED"))[
  Bajo el *#link(<adr-008>)[ADR-008]*, el estado `PREDICTED` representa *dead reckoning*: una extrapolación cinemática matemática ciega ante la pérdida de señal óptica (por oclusión de un pallet o fallo de iluminación).
  
  En seguridad industrial rige el principio inquebrantable de *Fail-Safe*: ante la pérdida de certeza sensorial, el sistema debe asumir la condición más desfavorable (peligro latente). Si se permitiera que una trayectoria extrapolada sin confirmación de fotones reales saliera de la zona y apagara el disparo, un operario que quedara ocluido dentro de la zona de riesgo quedaría desprotegido ante el reinicio intempestivo de la máquina. La salida solo se autoriza con observaciones frescas (`OBSERVED`).
]

== Pregunta 5: ¿Cuál es la distinción fundamental entre latencia de hardware ($T_"system"$) y latencia de evento ($T_"event"$)?
#callout(title: "Respuesta de Senior Architect", color: rgb("#059669"))[
  Bajo el *#link(<adr-010>)[ADR-010]*, existen dos horizontes temporales ortogonales:
  - *$T_"system"$ (Latencia por Cuadro):* Tiempo de cómputo que insume el silicio (captura, preproceso, inferencia ONNX, extracción de keypoints, homografía, Kalman y FSM). En nuestro hardware de desarrollo ronda los $18.5 "–" 20.5" ms"$.
  - *$T_"event"$ (Retardo Físico Real de Disparo):* Tiempo transcurrido desde el instante físico en que la extremidad del operario cruza la línea geométrica hasta que la señal `trip = True` abre los contactos del relé. En aproximación normal con debounce de 3 cuadros, $T_"event" approx (3 - 1) times 33.3" ms" + 18.5" ms" = 85.1" ms"$. Sin embargo, si la aproximación es perpendicular y veloz ($v_n >= 1.6" m/s"$), el autómata ejecuta un *bypass dinámico* instantáneo a $N_"confirm" = 1$, reduciendo $T_"event" = T_"system" approx 18.5" ms"$, cumpliendo con creces el límite $t_1 <= 50" ms"$ fijado por ISO 13855:2024.
]
