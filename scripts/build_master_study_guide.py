#!/usr/bin/env python3
"""
scripts/build_master_study_guide.py
Assembles the complete, comprehensive master study guide PDF for Edge Safety Guard.
Incorporates:
  - Guía Maestra de Estudio & Filosofía (docs/guia-estudio-arquitectura.local.md)
  - Especificación Técnica Industrial (docs/architecture/industrial-edge-ai-specification.md)
  - Directivas de Seguridad ISO 13855 (docs/architecture/safety-directives-iso13855.md)
  - Preguntas y Respuestas de Arquitectura (docs/architecture/preguntas-y-respuestas-arquitectura.md)
  - Pipeline de Datos Sintéticos Pinhole (docs/data/synthetic_generation.md)
  - Benchmarks de Runtimes y Cuantización (docs/benchmarks/*.md)
  - Compendio Íntegro de los 12 ADRs (docs/decisions/adr-*.md)
  - Implementación Real y Snippets de Código
  - Guía de Examen Técnico / Defensa Oral

Features:
  - Vector plots and architectural diagrams
  - Full internal cross-references
  - Clickable Table of Contents
  - Strict pagination and typesetting via Typst (zero text overflow)
"""

import os
import re
import subprocess
from pathlib import Path
import typst

REPO_ROOT = Path("/Users/xander/Projects/edge-safety-guard")
DOCS_DIR = REPO_ROOT / "docs"
TYP_OUTPUT = DOCS_DIR / "guia-estudio-arquitectura.local.typ"
PDF_OUTPUT = DOCS_DIR / "guia-estudio-arquitectura.local.pdf"

def run_pandoc(filepath: Path, shift: int = 0) -> str:
    cmd = ["/opt/homebrew/bin/pandoc", str(filepath), "-t", "typst"]
    if shift != 0:
        cmd.extend([f"--shift-heading-level-by={shift}"])
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    content = res.stdout
    return content

def fix_cross_references(text: str) -> str:
    # Transform file links to internal Typst anchor links
    # Matches #link("...adr-001...") [Text] -> #link(<adr-001>)[Text]
    pattern_adr = re.compile(r'#link\("(?:\.\./)?(?:decisions/)?adr-(0[0-9]{2})[^\"]*"\)\[([^\]]+)\]')
    text = pattern_adr.sub(r'#link(<adr-\1>)[\2]', text)

    # Replace markdown links to other docs
    text = re.sub(r'#link\("[^"]*industrial-edge-ai-specification\.md"\)\[([^\]]+)\]', r'#link(<cap-especificacion>)[\1]', text)
    text = re.sub(r'#link\("[^"]*safety-directives-iso13855\.md"\)\[([^\]]+)\]', r'#link(<cap-iso13855>)[\1]', text)
    text = re.sub(r'#link\("[^"]*preguntas-y-respuestas-arquitectura\.md"\)\[([^\]]+)\]', r'#link(<cap-faq>)[\1]', text)
    text = re.sub(r'#link\("[^"]*synthetic_generation\.md"\)\[([^\]]+)\]', r'#link(<cap-sintetico>)[\1]', text)

    return text

def build_cover() -> str:
    return """
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
      #if title != "" [ *#text(fill: color.darken(25%), title)* \\ ]
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
    #text(fill: rgb("#38BDF8"), size: 24pt, weight: "bold")[EDGE VISION SAFETY GUARD] \
    #v(0.5em)
    #text(fill: rgb("#F8FAFC"), size: 13.5pt, weight: "medium")[Manual Integral de Estudio, Especificaciones y Arquitectura de Sistemas Críticos en Tiempo Real] \
    #v(0.8em)
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
      *Metadatos de Ingeniería y Referencia:* \
      - *Autoría:* Senior Architect & Systems Engineering (GDE & MVP)
      - *Enfoque:* Separación Ortogonal Determinista: Percepción Pura + Geometría + Cinemática + FSM
      - *Runtimes de Ejecución:* ONNX Runtime + CoreML (Apple Silicon ANE/GPU) / INT8 TensorRT (NVIDIA Pascal CC 6.1)
      - *Fecha de Edición:* Septiembre 2026 • Versión 1.0 (Compendio Completo y Autocontenido)
    ]
  ]

  #v(1.5cm)
  #text(fill: rgb("#64748B"), size: 8pt)[
    Documento técnico de estudio local generado automáticamente a partir del repositorio oficial. \
    Incluye la totalidad de las especificaciones, justificaciones matemáticas, benchmarks y el catálogo completo de los 12 ADRs.
  ]
]

#pagebreak()

// ==============================================================================
// TABLA GENERAL DE CONTENIDOS
// ==============================================================================

#outline(title: "Tabla General de Contenidos", indent: auto, depth: 3)

#pagebreak()
"""

def main():
    print("[*] Iniciando construcción del Compendio Maestro de Estudio de Arquitectura...")
    print(f"[*] Directorio docs: {DOCS_DIR}")

    typst_parts = [build_cover()]

    # --------------------------------------------------------------------------
    # CAPÍTULO 1: LA GRAN TESIS Y GUÍA MAESTRA DE ESTUDIO
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 1: Filosofía y Guía Maestra (guia-estudio-arquitectura.local.md)...")
    cap1_path = DOCS_DIR / "guia-estudio-arquitectura.local.md"
    cap1_raw = run_pandoc(cap1_path, shift=0)
    cap1_typ = fix_cross_references(cap1_raw)

    # Inyectar figura de arquitectura tras la sección de arquitectura
    cap1_typ = cap1_typ.replace(
        "== 2. Arquitectura del Sistema: Separación en Cuatro Capas Ortogonales",
        "== 2. Arquitectura del Sistema: Separación en Cuatro Capas Ortogonales\n\n"
        "#figure(image(\"figures/pipeline_flow.png\", width: 95%), caption: [Flujo End-to-End del Pipeline en 4 Capas Desacopladas.]) <fig-pipeline>\n"
    )
    # Inyectar figuras de Schmitt Trigger y Statecharts
    cap1_typ = cap1_typ.replace(
        "=== A. Schmitt Trigger Espacial y Asimetría ENTRY / EXIT",
        "#figure(image(\"figures/schmitt_trigger.png\", width: 75%), caption: [Schmitt Trigger Espacial con Banda de Histéresis (P_danger vs P_release).]) <fig-schmitt>\n\n"
        "=== A. Schmitt Trigger Espacial y Asimetría ENTRY / EXIT"
    )
    cap1_typ = cap1_typ.replace(
        "=== D. MOT Bayesiano y Asignación Combinatoria",
        "#figure(image(\"figures/kalman_mahalanobis.png\", width: 65%), caption: [Compuerta Elipsoidal de Innovación de Mahalanobis.]) <fig-kalman>\n\n"
        "=== D. MOT Bayesiano y Asignación Combinatoria"
    )

    typst_parts.append("\n= 1. La Gran Tesis del Proyecto y Filosofía de Arquitectura <cap-filosofia>\n")
    typst_parts.append(cap1_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 2: ESPECIFICACIÓN TÉCNICA FORMAL DEL SISTEMA EDGE AI
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 2: Especificación Técnica (industrial-edge-ai-specification.md)...")
    cap2_path = DOCS_DIR / "architecture" / "industrial-edge-ai-specification.md"
    cap2_raw = run_pandoc(cap2_path, shift=1)
    cap2_typ = fix_cross_references(cap2_raw)

    typst_parts.append("\n= 2. Especificación Técnica Formal del Sistema Edge AI <cap-especificacion>\n")
    typst_parts.append(cap2_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 3: DIRECTIVAS DE SEGURIDAD Y MODELO MATEMÁTICO ISO 13855:2024
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 3: Directivas ISO 13855 (safety-directives-iso13855.md)...")
    cap3_path = DOCS_DIR / "architecture" / "safety-directives-iso13855.md"
    cap3_raw = run_pandoc(cap3_path, shift=1)
    cap3_typ = fix_cross_references(cap3_raw)

    # Inyectar figura de desglose de latencia
    cap3_typ = cap3_typ.replace(
        "== 2. Presupuesto Temporal de Visión",
        "#figure(image(\"figures/latency_breakdown.png\", width: 85%), caption: [Desglose Cronométrico de Latencias por Etapa del Pipeline.]) <fig-latency>\n\n"
        "== 2. Presupuesto Temporal de Visión"
    )

    typst_parts.append("\n= 3. Directivas de Seguridad y Modelo Matemático ISO 13855:2024 <cap-iso13855>\n")
    typst_parts.append(cap3_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 4: BITÁCORA DE PREGUNTAS Y RESPUESTAS DE ARQUITECTURA
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 4: Preguntas y Respuestas (preguntas-y-respuestas-arquitectura.md)...")
    cap4_path = DOCS_DIR / "architecture" / "preguntas-y-respuestas-arquitectura.md"
    cap4_raw = run_pandoc(cap4_path, shift=1)
    cap4_typ = fix_cross_references(cap4_raw)

    # Inyectar figura de Bbox vs Ankles
    cap4_typ = cap4_typ.replace(
        "== Pregunta 6: ¿Por qué no usar el borde inferior del Bounding Box",
        "#figure(image(\"figures/bbox_vs_ankles.png\", width: 85%), caption: [Comparativa Geométrica: Deformación de Bounding Box ante Torso Inclinado vs Anclaje Invariante en Tobillos.]) <fig-bbox-ankles>\n\n"
        "== Pregunta 6: ¿Por qué no usar el borde inferior del Bounding Box"
    )

    typst_parts.append("\n= 4. Bitácora de Preguntas & Respuestas de Arquitectura <cap-faq>\n")
    typst_parts.append(cap4_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 5: GENERACIÓN DE DATOS SINTÉTICOS Y CIERRE DEL DOMAIN GAP
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 5: Generación Sintética (synthetic_generation.md)...")
    cap5_path = DOCS_DIR / "data" / "synthetic_generation.md"
    cap5_raw = run_pandoc(cap5_path, shift=1)
    cap5_typ = fix_cross_references(cap5_raw)

    # Inyectar curva pinhole
    cap5_typ = cap5_typ.replace(
        "== 2. Arquitectura de Generación Sintética",
        "#figure(image(\"figures/pinhole_scaling.png\", width: 80%), caption: [Curva de Escala Antropométrica Pinhole Estenopeica h(Y).]) <fig-pinhole>\n\n"
        "== 2. Arquitectura de Generación Sintética"
    )

    typst_parts.append("\n= 5. Generación de Datos Sintéticos y Cierre del Domain Gap <cap-sintetico>\n")
    typst_parts.append(cap5_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 6: BENCHMARKS DE RENDIMIENTO Y CUANTIZACIÓN
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 6: Benchmarks...")
    cap6_runtime = run_pandoc(DOCS_DIR / "benchmarks" / "runtime_comparison.md", shift=1)
    cap6_quant = run_pandoc(DOCS_DIR / "benchmarks" / "quantization_comparison.md", shift=1)

    typst_parts.append("\n= 6. Benchmarks Empíricos de Rendimiento y Cuantización <cap-benchmarks>\n")
    typst_parts.append("== Comparativa de Motores de Inferencia (Runtimes)\n")
    typst_parts.append(fix_cross_references(cap6_runtime))
    typst_parts.append("\n== Comparativa de Precisión y Cuantización (FP32 vs FP16 vs INT8)\n")
    typst_parts.append(fix_cross_references(cap6_quant))
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 7: COMPENDIO COMPLETO DE ARCHITECTURE DECISION RECORDS (ADRs)
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 7: Compendio de los 12 ADRs...")
    typst_parts.append("\n= 7. Compendio Completo de Architecture Decision Records (ADRs) <cap-adrs>\n")
    typst_parts.append("""
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
""")

    adr_files = sorted(list((DOCS_DIR / "decisions").glob("adr-*.md")))
    for adr_f in adr_files:
        adr_num_match = re.search(r"adr-(0[0-9]{2})", adr_f.name)
        adr_num = adr_num_match.group(1) if adr_num_match else "000"
        print(f"     - Incorporando ADR-{adr_num}: {adr_f.name}...")
        
        adr_raw = run_pandoc(adr_f, shift=1)
        
        lines = adr_raw.splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("=="):
                clean_heading = re.sub(r'<[^>]+>', '', line).strip()
                lines[idx] = f"{clean_heading} <adr-{adr_num}>"
                if idx + 1 < len(lines) and lines[idx+1].strip().startswith("<") and lines[idx+1].strip().endswith(">"):
                    lines[idx+1] = ""
                break
        adr_typ = "\n".join(lines)
        adr_typ = fix_cross_references(adr_typ)
        
        typst_parts.append(f"\n#line(length: 100%, stroke: 1pt + rgb(\"#0284C7\"))\n")
        typst_parts.append(adr_typ)
        typst_parts.append("\n#v(1.5em)\n")

    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 8: SNIPPETS DE CÓDIGO FUENTE REAL Y ANÁLISIS DE CÓDIGO
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 8: Snippets de Código Fuente Real...")
    code_snippets = """
= 8. Implementación de Referencia y Snippets de Código Crítico <cap-codigo>

En esta sección se exponen las implementaciones reales de los componentes nucleares del sistema extraídas directamente del árbol `src/`. Cada bloque incluye el razonamiento técnico y los contratos que garantizan la integridad temporal y matemática del pipeline.

== 8.1 Cálculo de Condicionamiento y Proyección Vectorizada (`src/core/homography.py`)

#callout(title: "Contrato Numérico y Estabilidad", color: rgb("#0284C7"))[
  El número de condición $kappa(bold(H)) = sigma_"max" / sigma_"min"$ se calcula mediante descomposición en valores singulares (SVD). Si $kappa(bold(H)) >= 10^6$, la calibración se rechaza inmediatamente para evitar errores de amplificación milimétrica en el cálculo de distancias al suelo.
]

```python
# src/core/homography.py
def calculate_condition_number(H: np.ndarray) -> float:
    \"\"\"Calcula el número de condición κ(H) = σ_max / σ_min vía SVD.\"\"\"
    s = np.linalg.svd(H, compute_uv=False)
    if s[-1] < 1e-12:
        return float("inf")
    return float(s[0] / s[-1])

def project_to_world(self, points: np.ndarray) -> np.ndarray:
    \"\"\"Proyección vectorizada en NumPy de píxeles (u, v) a suelo métrico (X, Y) con Zw = 0.\"\"\"
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
    \"\"\"Calcula d_M^2 contra la covarianza de innovación S = H P^- H^T + R.\"\"\"
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
"""
    typst_parts.append(code_snippets)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 9: GUÍA DE DEFENSA TÉCNICA Y PREGUNTAS DE EXAMEN
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 9: Guía de Defensa Oral y Examen Técnico...")
    defense_guide = """
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
"""
    typst_parts.append(defense_guide)

    # --------------------------------------------------------------------------
    # ESCRITURA Y COMPILACIÓN FINAL
    # --------------------------------------------------------------------------
    full_typst_code = "".join(typst_parts)

    print(f"[*] Escribiendo código Typst maestro en {TYP_OUTPUT} ({len(full_typst_code)} caracteres)...")
    with open(TYP_OUTPUT, "w", encoding="utf-8") as f:
        f.write(full_typst_code)

    print(f"[*] Compilando documento maestro con Typst...")
    typst.compile(str(TYP_OUTPUT), output=str(PDF_OUTPUT))

    size_kb = os.path.getsize(PDF_OUTPUT) / 1024.0
    print(f"[✓] ÉXITO TOTAL: Compendio Maestro generado en {PDF_OUTPUT} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
