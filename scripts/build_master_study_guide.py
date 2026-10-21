#!/usr/bin/env python3
"""
scripts/build_master_study_guide.py
Assembles the complete, comprehensive master study guide PDF for Edge Safety Guard.
Incorporates:
  - Guía Maestra de Estudio & Filosofía (docs/guia-estudio-arquitectura.md)
  - Especificación Técnica Industrial (docs/architecture/industrial-edge-ai-specification.md)
  - Directivas de Seguridad ISO 13855 (docs/architecture/safety-directives-iso13855.md)
  - Preguntas y Respuestas de Arquitectura (docs/architecture/preguntas-y-respuestas-arquitectura.md)
  - Pipeline de Datos Sintéticos Pinhole (docs/data/synthetic_generation.md)
  - Benchmarks de Runtimes y Cuantización (docs/benchmarks/*.md)
  - Compendio Íntegro de los 13 ADRs (docs/decisions/adr-*.md)
  - Implementación Real y Snippets de Código
  - Criterios de Diseño y Preguntas Fundamentales de Arquitectura

Features:
  - Vector plots and architectural diagrams
  - Full internal cross-references
  - Clickable Table of Contents without emojis or double numbering
  - Landscape pages for wide benchmark tables
  - Strict pagination and typesetting via Typst (zero text overflow)
"""

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path("/Users/xander/Projects/edge-safety-guard")
DOCS_DIR = REPO_ROOT / "docs"
TYP_OUTPUT = DOCS_DIR / "guia-estudio-arquitectura.typ"
PDF_OUTPUT = DOCS_DIR / "guia-estudio-arquitectura-compendio.pdf"

def run_pandoc(filepath: Path, shift: int = 0) -> str:
    cmd = ["/opt/homebrew/bin/pandoc", str(filepath), "-t", "typst"]
    if shift != 0:
        cmd.extend([f"--shift-heading-level-by={shift}"])
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout

def fix_cross_references(text: str) -> str:
    # Transform file links to internal Typst anchor links
    pattern_adr = re.compile(r'#link\("(?:\.\./)?(?:decisions/)?adr-(0[0-9]{2})[^\"]*"\)\[([^\]]+)\]')
    text = pattern_adr.sub(r'#link(<adr-\1>)[\2]', text)

    # Replace markdown links to other docs
    text = re.sub(r'#link\("[^"]*industrial-edge-ai-specification\.md"\)\[([^\]]+)\]', r'#link(<cap-especificacion>)[\1]', text)
    text = re.sub(r'#link\("[^"]*safety-directives-iso13855\.md"\)\[([^\]]+)\]', r'#link(<cap-iso13855>)[\1]', text)
    text = re.sub(r'#link\("[^"]*preguntas-y-respuestas-arquitectura\.md"\)\[([^\]]+)\]', r'#link(<cap-faq>)[\1]', text)
    text = re.sub(r'#link\("[^"]*synthetic_generation\.md"\)\[([^\]]+)\]', r'#link(<cap-sintetico>)[\1]', text)

    return text

def merge_heading_labels(text: str) -> str:
    """
    Pandoc outputs `<label>` on the line following `= Heading`.
    Merges `<label>` onto the heading line itself (`= Heading <label>`)
    to prevent subsequent `#figure` injections from stealing the heading label.
    """
    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^={1,6}\s+", line):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and re.match(r"^<[^>]+>$", lines[j].strip()):
                label = lines[j].strip()
                result.append(f"{line} {label}")
                lines[j] = ""
                i = j + 1
                continue
        result.append(line)
        i += 1
    return "\n".join(result)

def strip_first_h1(text: str) -> str:
    """
    Strips the first level-1 heading (and its label) from a converted document
    so it does not duplicate the chapter title created by the orchestrator.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("="):
            lines[i] = ""
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and re.match(r"^<[^>]+>$", lines[j].strip()):
                lines[j] = ""
            break
        i += 1
    return "\n".join(lines)

def clean_headings(text: str) -> str:
    """
    Cleans heading lines:
    1. Removes emojis/symbols.
    2. Strips hardcoded leading numbers (e.g. '1. ', '2.1 ', '8.1 ', 'A. ') to let Typst number them.
    3. Removes backticks from headings to prevent rendering white-on-dark code blocks in the outline.
    """
    def strip_heading(match):
        prefix = match.group(1)
        title = match.group(2)
        # Remove emojis
        t = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\ufe0f]", "", title).strip()
        # Remove leading numbers/letters like '1. ', '2.1 ', '8.1 ', 'A. '
        t = re.sub(r"^(?:\d+(?:\.\d+)*\.?\s+|[A-Z]\.\s+)", "", t).strip()
        # Remove backticks from headings
        t = t.replace("`", "")
        return f"{prefix} {t}"

    return re.sub(r"^(={1,6})\s+(.*)$", strip_heading, text, flags=re.MULTILINE)

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
        text(size: 7.5pt, fill: rgb("#64748B"))[Arquitectura de Sistemas Críticos en Tiempo Real (Concepts > Code) • Diseño basado en ISO 13855 / IEC 61496],
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

#show raw.where(block: true): it => block(
  fill: rgb("#0F172A"),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.5pt + rgb("#334155"),
  text(fill: rgb("#E2E8F0"), size: 8pt, font: "Menlo")[#it]
)

#show raw.where(block: false): it => box(
  fill: rgb("#F1F5F9"),
  inset: (x: 3.5pt, y: 0pt),
  outset: (y: 2.5pt),
  radius: 2pt,
  text(fill: rgb("#0F172A"), size: 8pt, font: "Menlo")[#it]
)

#show figure.where(kind: table): set text(size: 8pt)
#set table(
  stroke: 0.5pt + rgb("#CBD5E1"),
  fill: (x, y) => if y == 0 { rgb("#1E293B") } else if calc.even(y) { rgb("#F8FAFC") } else { white }
)
#show table.cell.where(y: 0): set text(fill: white, weight: "bold")

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
    #text(fill: rgb("#94A3B8"), size: 9.5pt)[Diseño Guiado por la Física, Geometría Planar y Criterios de Seguridad Industrial (Basado en ISO 13855 / IEC 61496)]
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
      - *Enfoque Arquitectónico:* Principios Fundamentales (First-Principles) & Concepts > Code
      - *Separación Ortogonal:* Percepción Pura + Geometría + Cinemática + FSM Determinista
      - *Runtimes de Silicio:* Apple Silicon M1 (arm64, desarrollo primario) • PoC NVIDIA Pascal CC 6.1 / GTX 1050 (INT8, proyectada como Trabajo Futuro)
      - *Fecha de Edición:* Octubre 2026 • Versión 1.1 (Compendio Completo y Autocontenido)
    ]
  ]

  #v(1.5cm)
  #text(fill: rgb("#64748B"), size: 8pt)[
    Documento técnico de referencia y estudio generado automáticamente a partir del repositorio oficial. \
    Incluye la totalidad de las especificaciones, justificaciones matemáticas, benchmarks y el catálogo completo de los 13 ADRs.
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
    # CAPÍTULO 1: FILOSOFÍA DEL PROYECTO Y GUÍA MAESTRA DE ESTUDIO
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 1: Filosofía y Guía Maestra (guia-estudio-arquitectura.md)...")
    cap1_path = DOCS_DIR / "guia-estudio-arquitectura.md"
    cap1_raw = run_pandoc(cap1_path, shift=0)
    cap1_typ = merge_heading_labels(cap1_raw)
    cap1_typ = strip_first_h1(cap1_typ)
    cap1_typ = fix_cross_references(cap1_typ)
    cap1_typ = clean_headings(cap1_typ)

    # Inyectar figura de arquitectura tras la sección de arquitectura
    cap1_typ = re.sub(
        r"(==\s*.*?Arquitectura en Capas[^\n]*)",
        r'\1\n\n#figure(image("figures/pipeline_flow.png", width: 95%), caption: [Flujo End-to-End del Pipeline en 4 Capas Desacopladas.]) <fig-pipeline>\n',
        cap1_typ,
        count=1
    )
    # Inyectar figuras de Schmitt Trigger y Statecharts
    cap1_typ = re.sub(
        r"(===\s*.*?Schmitt Trigger[^\n]*)",
        r'#figure(image("figures/schmitt_trigger.png", width: 75%), caption: [Schmitt Trigger Espacial con Banda de Histéresis (P_danger vs P_release).]) <fig-schmitt>\n\n\1',
        cap1_typ,
        count=1
    )
    cap1_typ = re.sub(
        r"(===\s*.*?MOT Bayesiano[^\n]*)",
        r'#figure(image("figures/kalman_mahalanobis.png", width: 65%), caption: [Compuerta Elipsoidal de Innovación de Mahalanobis.]) <fig-kalman>\n\n\1',
        cap1_typ,
        count=1
    )

    typst_parts.append("\n= Filosofía del Proyecto y Guía Maestra de Arquitectura <cap-filosofia>\n")
    typst_parts.append(cap1_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 2: ESPECIFICACIÓN TÉCNICA FORMAL DEL SISTEMA EDGE AI
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 2: Especificación Técnica (industrial-edge-ai-specification.md)...")
    cap2_path = DOCS_DIR / "architecture" / "industrial-edge-ai-specification.md"
    cap2_raw = run_pandoc(cap2_path, shift=0)
    cap2_typ = merge_heading_labels(cap2_raw)
    cap2_typ = strip_first_h1(cap2_typ)
    cap2_typ = fix_cross_references(cap2_typ)
    cap2_typ = clean_headings(cap2_typ)

    typst_parts.append("\n= Especificación Técnica Formal del Sistema Edge AI <cap-especificacion>\n")
    typst_parts.append(cap2_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 3: DIRECTIVAS DE SEGURIDAD Y MODELO MATEMÁTICO ISO 13855:2024
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 3: Directivas ISO 13855 (safety-directives-iso13855.md)...")
    cap3_path = DOCS_DIR / "architecture" / "safety-directives-iso13855.md"
    cap3_raw = run_pandoc(cap3_path, shift=0)
    cap3_typ = merge_heading_labels(cap3_raw)
    cap3_typ = strip_first_h1(cap3_typ)
    cap3_typ = fix_cross_references(cap3_typ)
    cap3_typ = clean_headings(cap3_typ)

    # Inyectar figura de desglose de latencia
    cap3_typ = re.sub(
        r"(==\s*.*?Presupuesto Temporal[^\n]*)",
        r'#figure(image("figures/latency_breakdown.png", width: 85%), caption: [Desglose Cronométrico de Latencias por Etapa del Pipeline.]) <fig-latency>\n\n\1',
        cap3_typ,
        count=1
    )

    typst_parts.append("\n= Directivas de Seguridad y Modelo Matemático ISO 13855 <cap-iso13855>\n")
    typst_parts.append(cap3_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 4: BITÁCORA DE PREGUNTAS Y RESPUESTAS DE ARQUITECTURA
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 4: Preguntas y Respuestas (preguntas-y-respuestas-arquitectura.md)...")
    cap4_path = DOCS_DIR / "architecture" / "preguntas-y-respuestas-arquitectura.md"
    cap4_raw = run_pandoc(cap4_path, shift=0)
    cap4_typ = merge_heading_labels(cap4_raw)
    cap4_typ = strip_first_h1(cap4_typ)
    cap4_typ = fix_cross_references(cap4_typ)
    cap4_typ = clean_headings(cap4_typ)

    # Inyectar figura de Bbox vs Ankles
    cap4_typ = re.sub(
        r"(====\s*.*?P6:[^\n]*)",
        r'#figure(image("figures/bbox_vs_ankles.png", width: 85%), caption: [Comparativa Geométrica: Deformación de Bounding Box ante Torso Inclinado vs Anclaje Invariante en Tobillos.]) <fig-bbox-ankles>\n\n\1',
        cap4_typ,
        count=1
    )

    typst_parts.append("\n= Bitácora de Preguntas y Respuestas de Arquitectura <cap-faq>\n")
    typst_parts.append(cap4_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 5: GENERACIÓN DE DATOS SINTÉTICOS Y CIERRE DEL DOMAIN GAP
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 5: Generación Sintética (synthetic_generation.md)...")
    cap5_path = DOCS_DIR / "data" / "synthetic_generation.md"
    cap5_raw = run_pandoc(cap5_path, shift=0)
    cap5_typ = merge_heading_labels(cap5_raw)
    cap5_typ = strip_first_h1(cap5_typ)
    cap5_typ = fix_cross_references(cap5_typ)
    cap5_typ = clean_headings(cap5_typ)

    # Inyectar curva pinhole
    cap5_typ = re.sub(
        r"(==\s*.*?Arquitectura de Generación[^\n]*)",
        r'#figure(image("figures/pinhole_scaling.png", width: 80%), caption: [Curva de Escala Antropométrica Pinhole Estenopeica h(Y).]) <fig-pinhole>\n\n\1',
        cap5_typ,
        count=1
    )

    typst_parts.append("\n= Generación de Datos Sintéticos y Cierre del Domain Gap <cap-sintetico>\n")
    typst_parts.append(cap5_typ)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 6: BENCHMARKS DE RENDIMIENTO Y CUANTIZACIÓN (EN HOJAS HORIZONTALES)
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 6: Benchmarks...")
    cap6_runtime = run_pandoc(DOCS_DIR / "benchmarks" / "runtime_comparison.md", shift=0)
    cap6_quant = run_pandoc(DOCS_DIR / "benchmarks" / "quantization_comparison.md", shift=0)

    cap6_runtime = merge_heading_labels(cap6_runtime)
    cap6_quant = merge_heading_labels(cap6_quant)

    cap6_runtime = strip_first_h1(cap6_runtime)
    cap6_quant = strip_first_h1(cap6_quant)

    # Adjust table columns for full-width landscape layout
    cap6_runtime = re.sub(r'columns:\s*\([^)]+\)', 'columns: (1.4fr, 1.6fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1.2fr)', cap6_runtime)
    cap6_quant = re.sub(r'columns:\s*\([^)]+\)', 'columns: (1.5fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1.2fr, 1fr, 1fr, 1.1fr, 1.2fr)', cap6_quant)

    cap6_runtime = clean_headings(cap6_runtime)
    cap6_quant = clean_headings(cap6_quant)

    typst_parts.append("\n= Benchmarks Empíricos de Rendimiento y Cuantización <cap-benchmarks>\n")
    typst_parts.append("""
En este capítulo se presentan los resultados empíricos de latencia, varianza temporal, throughput y precisión métrica en el suelo tras la proyección homográfica.
Para garantizar la legibilidad y evitar desbordamientos, las tablas de benchmarks multidimensionales (10 y 11 columnas) se presentan a continuación en orientación apaisada (horizontal).

#pagebreak()
#set page(flipped: true)

""")
    typst_parts.append("== Comparativa de Motores de Inferencia (YOLO11-Pose @ 640x640)\n")
    typst_parts.append(fix_cross_references(cap6_runtime))
    typst_parts.append("\n#v(1.5em)\n")
    typst_parts.append("== Comparativa de Precisión y Cuantización (FP32 vs FP16 vs INT8)\n")
    typst_parts.append(fix_cross_references(cap6_quant))
    typst_parts.append("""
#pagebreak()
#set page(flipped: false)
""")

    # --------------------------------------------------------------------------
    # CAPÍTULO 7: COMPENDIO COMPLETO DE ARCHITECTURE DECISION RECORDS (ADRs)
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 7: Compendio de los 13 ADRs...")
    typst_parts.append("\n= Compendio Completo de Architecture Decision Records (ADRs) <cap-adrs>\n")
    typst_parts.append("""
En este capítulo se recopilan de manera íntegra y exhaustiva las trece decisiones arquitectónicas (ADRs) que gobiernan la totalidad del sistema *Edge Safety Guard*. Cada documento define el contexto, las opciones evaluadas, los trade-offs matemáticos/computacionales, la decisión adoptada y sus consecuencias directas en seguridad industrial.

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
    [#strong[005]], [#link(<adr-005>)[ADR-005]], [Validación preventiva de colinealidad y estabilidad numérica κ(H) < 10^12.],
    [#strong[006]], [#link(<adr-006>)[ADR-006]], [Geometrías preparadas GEOS (C) y bypass dinámico por velocidad vn ≥ 1.6 m/s.],
    [#strong[007]], [#link(<adr-007>)[ADR-007]], [Manejo jerárquico de oclusiones: tobillos duales → individual → bbox.],
    [#strong[008]], [#link(<adr-008>)[ADR-008]], [Epistemología Kalman (OBSERVED/PREDICTED) y bloqueo de desescalada ciega.],
    [#strong[009]], [#link(<adr-009>)[ADR-009]], [Statecharts ortogonales concurrentes: separación ocupación vs dwell time.],
    [#strong[010]], [#link(<adr-010>)[ADR-010]], [Profiling de doble horizonte: hardware (T_system) vs evento físico (T_event).],
    [#strong[011]], [#link(<adr-011>)[ADR-011]], [MOT Bayesiano: Gating Mahalanobis χ² ≤ 9.21, Húngaro y Spatial Birth NMS.],
    [#strong[012]], [#link(<adr-012>)[ADR-012]], [Composición fotorrealista pinhole de identidad única para testing formal.],
    [#strong[013]], [#link(<adr-013>)[ADR-013]], [Inferencia foveada de doble pasada (far_field_roi) y delimitación de pasillo seguro (Yw ≤ 6 m).]
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
        adr_typ = merge_heading_labels(adr_raw)
        
        lines = adr_typ.splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("=="):
                clean_heading = re.sub(r'<[^>]+>', '', line).strip()
                lines[idx] = f"{clean_heading} <adr-{adr_num}>"
                break
        adr_typ = "\n".join(lines)
        adr_typ = clean_headings(adr_typ)
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
= Implementación de Referencia y Snippets de Código Crítico <cap-codigo>

En esta sección se exponen las implementaciones reales de los componentes nucleares del sistema extraídas directamente del árbol src/. Cada bloque incluye el razonamiento técnico y los contratos que garantizan la integridad temporal y matemática del pipeline.

== Cálculo de Condicionamiento y Proyección Vectorizada (src/core/homography.py)

#callout(title: "Contrato Numérico y Estabilidad", color: rgb("#0284C7"))[
  El número de condición $kappa(bold(H)) = sigma_"max" / sigma_"min"$ se calcula mediante descomposición en valores singulares (`np.linalg.cond(H)`). Si $kappa(bold(H)) > 10^12$, la calibración se rechaza inmediatamente para evitar errores de amplificación milimétrica en el cálculo de distancias al suelo.
]

```python
# src/core/homography.py
def compute_homography(self, method: Optional[int] = None) -> np.ndarray:
    H, _ = cv2.findHomography(self._image_points, self._world_points, method=method_flag)
    H = H.astype(np.float64)
    if abs(H[2, 2]) > 1e-12:
        H = H / H[2, 2]
    det = float(np.linalg.det(H))
    if abs(det) < 1e-10:
        raise ValueError(f"Homography matrix is singular or near-singular: det(H) = {det:.2e} < 1e-10.")
    H_inv = np.linalg.inv(H)
    cond = float(np.linalg.cond(H))
    if cond > 1e12 or np.isnan(cond) or np.isinf(cond):
        raise ValueError(f"Homography matrix is ill-conditioned: condition number kappa(H) = {cond:.2e} > 1e12.")
    self._H, self._H_inv, self._is_calibrated = H, H_inv, True
    return self._H

def project_batch(self, points: np.ndarray, to_world: bool = True) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float64)
    M = self._H if to_world else self._H_inv
    pts_h = np.column_stack([pts, np.ones(len(pts), dtype=np.float64)])
    proj = pts_h @ M.T
    w = proj[:, 2:3]
    if np.any(np.abs(w) < 1e-7):
        raise ValueError("One or more points lie on or near the horizon line (|W| < 1e-7).")
    return proj[:, :2] / w
```

== Jerarquía de Anclaje y Orquestación Foveada (src/pipeline/safety_pipeline.py)

#callout(title: "Degradación Controlada y Pasada Foveada", color: rgb("#16A34A"))[
  Cumple con *ADR-007* y *ADR-013*. `extract_ground_anchor` prioriza el punto medio de ambos tobillos (`conf_threshold = 0.5`, confianza media `(left_conf + right_conf) / 2.0`), degrada a tobillo único (`conf * 0.75`) o a base de bounding box (`det_score * 0.40`, también activado si `bbox_h < min_ankle_bbox_height`). En `SafetyPipeline.process_frame`, la inferencia opcional sobre `far_field_roi` se fusiona mediante `deduplicate_detections`.
]

```python
# src/pipeline/safety_pipeline.py
def extract_ground_anchor(
    keypoints: np.ndarray,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    conf_threshold: float = 0.5,
    scale: float = 1.0,
    pad_x: float = 0.0,
    pad_y: float = 0.0,
    allow_bbox_fallback: bool = True,
    det_score: float = 1.0,
    min_ankle_bbox_height: float = 0.0,
) -> Optional[Tuple[Tuple[float, float], AnchorSource, float]]:
    if bbox is not None and min_ankle_bbox_height > 0.0:
        if abs(float(bbox[3]) - float(bbox[1])) < min_ankle_bbox_height:
            if allow_bbox_fallback:
                anchor_pt = unletterbox_point((bbox[0] + bbox[2]) / 2.0, bbox[3], scale, pad_x, pad_y)
                return anchor_pt, AnchorSource.BBOX_BOTTOM, float(det_score) * 0.40
            return None
    left_ankle, right_ankle = keypoints[15], keypoints[16]
    left_valid = float(left_ankle[2]) >= conf_threshold
    right_valid = float(right_ankle[2]) >= conf_threshold
    if left_valid and right_valid:
        mid_x = (float(left_ankle[0]) + float(right_ankle[0])) / 2.0
        mid_y = (float(left_ankle[1]) + float(right_ankle[1])) / 2.0
        avg_conf = (float(left_ankle[2]) + float(right_ankle[2])) / 2.0
        return unletterbox_point(mid_x, mid_y, scale, pad_x, pad_y), AnchorSource.ANKLES_DUAL, float(avg_conf)
    elif left_valid:
        return unletterbox_point(float(left_ankle[0]), float(left_ankle[1]), scale, pad_x, pad_y), AnchorSource.ANKLE_SINGLE, float(left_ankle[2]) * 0.75
    elif right_valid:
        return unletterbox_point(float(right_ankle[0]), float(right_ankle[1]), scale, pad_x, pad_y), AnchorSource.ANKLE_SINGLE, float(right_ankle[2]) * 0.75
    elif allow_bbox_fallback and bbox is not None:
        anchor_pt = unletterbox_point((bbox[0] + bbox[2]) / 2.0, bbox[3], scale, pad_x, pad_y)
        return anchor_pt, AnchorSource.BBOX_BOTTOM, float(det_score) * 0.40
    return None

# Dentro de SafetyPipeline.process_frame(self, frame, capture_timestamp=None):
model_out = self.engine.infer(tensor)
roi_model_out = self.engine.infer(roi_tensor) if roi_bounds is not None else None
detections = self.parse_detections(model_out, scale, pad_x, pad_y, orig_w, orig_h)
if roi_bounds is not None and roi_model_out is not None:
    roi_detections = self.parse_detections(
        roi_model_out, roi_scale, roi_pad_x, roi_pad_y, rx2 - rx1, ry2 - ry1,
        conf_threshold_override=self.far_field_conf_threshold, offset_xy=(float(rx1), float(ry1)),
    )
    detections = deduplicate_detections(detections + roi_detections)
world_positions = self.homography.project_batch(anchors_arr, to_world=True)
active_tracks = self.tracker.update(position_estimates)
safety_output = self.fsm.update(tracks_for_fsm, timestamp=t_start)
```

== Filtro de Kalman Cinemático con Actualización de Joseph (src/core/kalman_filter.py)

```python
# src/core/kalman_filter.py
def mahalanobis_distance(self, measurement: Union[np.ndarray, Tuple[float, float], Sequence[float]], R: Optional[np.ndarray] = None) -> float:
    z = np.asarray(measurement, dtype=np.float64)
    y0, y1 = z[0] - self._x[0], z[1] - self._x[1]
    r_mat = self._R if R is None else np.asarray(R, dtype=np.float64)
    s_inv = np.linalg.inv(self._P[:2, :2] + r_mat)
    d2 = y0 * (s_inv[0, 0] * y0 + s_inv[0, 1] * y1) + y1 * (s_inv[1, 0] * y0 + s_inv[1, 1] * y1)
    return float(max(0.0, d2))

def update(self, measurement: Union[np.ndarray, Tuple[float, float], Sequence[float]], R: Optional[np.ndarray] = None) -> np.ndarray:
    z = np.asarray(measurement, dtype=np.float64)
    r_mat = self._R if R is None else np.asarray(R, dtype=np.float64)
    y = np.array([z[0] - self._x[0], z[1] - self._x[1]], dtype=np.float64)
    s_inv = np.linalg.inv(self._P[:2, :2] + r_mat)
    k_gain = self._P[:, :2] @ s_inv
    self._x = self._x + k_gain @ y
    # Forma estabilizada de Joseph: P = (I - K H) P (I - K H)^T + K R K^T
    a_mat = self._I.copy()
    a_mat[:, :2] -= k_gain
    self._P = a_mat @ self._P @ a_mat.T + k_gain @ r_mat @ k_gain.T
    self._P = 0.5 * (self._P + self._P.T)
    return self._x.copy()
```

== Schmitt Trigger Espacial Vectorizado y Bypass ISO 13855 (src/core/spatial_fsm.py)

```python
# src/core/spatial_fsm.py
def evaluate_containment(self, tracks: List[Track]) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    positions = np.array([trk.position for trk in tracks], dtype=np.float64)
    xs, ys = positions[:, 0], positions[:, 1]
    in_danger = shapely.contains_xy(self._danger_poly, xs, ys)
    in_release = shapely.contains_xy(self._release_poly, xs, ys)
    in_warning = shapely.contains_xy(self._warning_poly, xs, ys) if self._warning_poly is not None else (in_release & ~in_danger)
    return in_danger, in_release, in_warning

# Dentro de SpatialFSM.update(tracks, timestamp):
if in_danger:
    record.clean_count = 0
    if fast_approach or record.fast_approach:
        record.danger_count = max(record.danger_count + 1, self._config.n_confirm)
    else:
        record.danger_count += 1
elif not in_release and obs_status == ObservationStatus.OBSERVED:
    record.clean_count += 1  # Solo desescala con fotones OBSERVED reales
```
"""
    typst_parts.append(code_snippets)
    typst_parts.append("\n#pagebreak()\n")

    # --------------------------------------------------------------------------
    # CAPÍTULO 9: PREGUNTAS FUNDAMENTALES Y CRITERIOS DE DISEÑO ARQUITECTÓNICO
    # --------------------------------------------------------------------------
    print("  -> Procesando Capítulo 9: Preguntas Fundamentales y Criterios de Diseño...")
    defense_guide = """
= Preguntas Fundamentales y Criterios de Diseño Arquitectónico <cap-criterios>

Este capítulo condensa las decisiones fundamentales y criterios técnicos de arquitectura en sistemas de visión artificial en el Edge, junto a las justificaciones fundamentadas en estándares internacionales y física determinista.

== Pregunta 1: ¿Por qué la inferencia de una red neuronal nunca debe tomar la decisión de parada directamente?
#callout(title: "Criterio de Arquitectura", color: rgb("#DC2626"))[
  Las redes neuronales convolucionales o Transformers son estimadores estadísticos no deterministas. Sufren de vulnerabilidades intrínsecas: ataques adversarios, *domain shifts* lumínicos y oclusiones imprevistas. Si se entrena un modelo *end-to-end* para predecir un booleano `trip`, es imposible verificar formalmente los casos de esquina ante directivas inspiradas en IEC 61508 (SIL 2/3) o ISO 13849-1 (PL d/e).
  
  En *Edge Safety Guard*, la IA se restringe estrictamente a percibir coordenadas geométricas en píxeles. Todo el procesamiento posterior —transformación proyectiva euclidiana, estimación cinemática bayesiana y lógica de disparo por polígonos— es puramente determinista, auditable matemáticamente e inmune a las alucinaciones del modelo.
]

== Pregunta 2: ¿Por qué una calibración de exactamente 4 puntos presenta siempre un residuo de reproyección RMSE = 0.00 m?
#callout(title: "Criterio de Arquitectura", color: rgb("#D97706"))[
  La homografía planar proyectiva $3 times 3$ está definida en coordenadas homogéneas hasta un factor de escala no nulo, lo que le otorga exactamente $9 - 1 = 8$ grados de libertad algebraicos. Cada correspondencia de punto $p_i (u, v) <-> P_i (X, Y)$ aporta exactamente 2 ecuaciones independientes tras eliminar la coordenada proyectiva.
  
  Al calibrar con 4 puntos coplanares no colineales, se obtiene un sistema lineal determinado de 8 ecuaciones con 8 incógnitas ($bold(A) bold(h) = 0$). El residuo algebraico es idénticamente nulo porque la transformación encaja exactamente en los 4 pares de puntos sin grados de libertad sobrantes. Para poder medir un residuo empírico o error cuadrático medio de reproyección (RMSE), es estrictamente necesario emplear un sistema sobredeterminado con $N > 4$ marcadores de calibración o puntos de test independientes.
]

== Pregunta 3: ¿Cómo protege el sistema la integridad mecánica de la maquinaria frente a la oscilación de un operario en el borde?
#callout(title: "Criterio de Arquitectura", color: rgb("#2563EB"))[
  Mediante el *Schmitt Trigger Espacial* (*#link(<adr-004>)[ADR-004]*). Si se utilizara un polígono único, el ruido estocástico de detección en los keypoints ($approx plus.minus 15" mm"$) haría conmutar el relé de parada a la frecuencia del pipeline (30 Hz), quemando los contactores mecánicos en pocas horas.
  
  La arquitectura define dos polígonos concéntricos con una banda de histéresis espacial de $Delta d = 200" mm"$:
  1. *Polígono de Peligro ($P_"danger"$):* Determina la activación de alarma.
  2. *Polígono de Liberación ($P_"release"$):* Expandido mediante $P_"release" = P_"danger" ⊕ 0.20" m"$.
  
  Para conmutar a peligro, basta con que el operario ingrese a $P_"danger"$. Pero para retornar a estado seguro, el operario debe caminar completamente fuera de $P_"release"$ durante 5 cuadros consecutivos con condición estricta de fotones `OBSERVED`.
]

== Pregunta 4: ¿Por qué está terminantemente prohibido desescalar la alarma si el filtro de Kalman se encuentra en estado PREDICTED?
#callout(title: "Criterio de Arquitectura", color: rgb("#7C3AED"))[
  Bajo el *#link(<adr-008>)[ADR-008]*, el estado `PREDICTED` representa *dead reckoning*: una extrapolación cinemática matemática ciega ante la pérdida de señal óptica (por oclusión de un pallet o fallo de iluminación).
  
  En seguridad industrial rige el principio inquebrantable de *Fail-Safe*: ante la pérdida de certeza sensorial, el sistema debe asumir la condición más desfavorable (peligro latente). Si se permitiera que una trayectoria extrapolada sin confirmación de fotones reales saliera de la zona y apagara el disparo, un operario que quedara ocluido dentro de la zona de riesgo quedaría desprotegido ante el reinicio intempestivo de la máquina. La salida solo se autoriza con observaciones frescas (`OBSERVED`).
]

== Pregunta 5: ¿Cuál es la distinción fundamental entre latencia de hardware ($T_"system"$) y latencia de evento ($T_"event"$)?
#callout(title: "Criterio de Arquitectura", color: rgb("#059669"))[
  Bajo el *#link(<adr-010>)[ADR-010]*, existen dos horizontes temporales ortogonales:
  - *$T_"system"$ (Latencia por Cuadro):* Tiempo de cómputo que insume el silicio (captura, preproceso, inferencia ONNX, extracción de keypoints, homografía, Kalman y FSM). En nuestro hardware de desarrollo ronda los $18.5 "–" 20.5" ms"$.
  - *$T_"event"$ (Retardo Físico Real de Disparo):* Tiempo transcurrido desde el instante físico en que la extremidad del operario cruza la línea geométrica hasta que la señal `trip = True` abre los contactos del relé. En aproximación normal con debounce de 3 cuadros, $T_"event" approx (3 - 1) times 33.3" ms" + 18.5" ms" = 85.1" ms"$. Sin embargo, si la aproximación es perpendicular y veloz ($v_n >= 1.6" m/s"$), el autómata ejecuta un *bypass dinámico* instantáneo a $N_"confirm" = 1$, reduciendo $T_"event" = T_"system" approx 18.5" ms"$, alineado con las recomendaciones de $t_1 <= 50" ms"$ de ISO 13855:2024.
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

    print(f"[*] Compilando documento maestro con Typst CLI...")
    subprocess.run(["/opt/homebrew/bin/typst", "compile", str(TYP_OUTPUT), str(PDF_OUTPUT)], check=True)

    size_kb = os.path.getsize(PDF_OUTPUT) / 1024.0
    print(f"[✓] ÉXITO TOTAL: Compendio Maestro generado en {PDF_OUTPUT} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
