#!/usr/bin/env python3
"""
scripts/generate_study_pdf.py
Generates the comprehensive Architecture & Engineering Study Guide PDF
for Edge Safety Guard (Vision-Based Restricted Zone Monitoring).

Supports both Spanish (docs/guia-estudio-arquitectura.pdf) and English
(docs/architecture-study-guide.pdf) deliverables.

Design based on ISO 13855:2024, IEC 61496, and ISO 13849-1 principles.
Includes mathematical derivations, architectural diagrams, vector plots,
codebase snippets, and the complete ADR catalog.
"""

import argparse
import os
import sys
import textwrap
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages

DOCS_DIR = Path("/Users/xander/Projects/edge-safety-guard/docs")
OUTPUT_PDF_ES = DOCS_DIR / "guia-estudio-arquitectura.pdf"
OUTPUT_PDF_EN = DOCS_DIR / "architecture-study-guide.pdf"

PAGE_WIDTH = 8.27
PAGE_HEIGHT = 11.69

COLOR_HEADER_BG = "#0F172A"
COLOR_ACCENT_BLUE = "#2563EB"
COLOR_ACCENT_CYAN = "#0EA5E9"
COLOR_DANGER = "#DC2626"
COLOR_WARNING = "#D97706"
COLOR_SUCCESS = "#16A34A"
COLOR_CARD_BG = "#F8FAFC"
COLOR_CARD_BORDER = "#CBD5E1"
COLOR_CODE_BG = "#0F172A"
COLOR_CODE_TEXT = "#E2E8F0"
COLOR_TEXT_MAIN = "#1E293B"
COLOR_TEXT_MUTED = "#64748B"

def create_base_page(page_num: int, total_pages: int, chapter_title: str, lang: str = "es"):
    fig = plt.figure(figsize=(PAGE_WIDTH, PAGE_HEIGHT), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Header Bar
    header_rect = patches.Rectangle((0, 0.94), 1, 0.06, facecolor=COLOR_HEADER_BG, edgecolor="none", zorder=1)
    ax.add_patch(header_rect)

    guide_title = "|  Guía Maestra de Estudio de Arquitectura" if lang == "es" else "|  Master Architecture Study Guide"
    ax.text(0.04, 0.965, "EDGE VISION SAFETY GUARD", fontsize=10, fontweight="bold", color="#38BDF8", va="center")
    ax.text(0.32, 0.965, guide_title, fontsize=9, color="#94A3B8", va="center")
    ax.text(0.96, 0.965, chapter_title.upper(), fontsize=8.5, fontweight="bold", color="#F8FAFC", ha="right", va="center")

    # Footer Bar
    ax.plot([0.04, 0.96], [0.038, 0.038], color=COLOR_CARD_BORDER, lw=0.8)
    if lang == "es":
        footer_left = "Arquitectura de Sistemas Críticos en Tiempo Real (Concepts > Code)  •  Diseño basado en ISO 13855 / IEC 61496"
        footer_right = f"Página {page_num} de {total_pages}"
    else:
        footer_left = "Real-Time Safety-Critical Architecture (Concepts > Code)  •  Design based on ISO 13855 / IEC 61496"
        footer_right = f"Page {page_num} of {total_pages}"

    ax.text(0.04, 0.022, footer_left, fontsize=7.2, color=COLOR_TEXT_MUTED, va="center")
    ax.text(0.96, 0.022, footer_right, fontsize=7.8, fontweight="bold", color=COLOR_TEXT_MAIN, ha="right", va="center")

    return fig, ax

def draw_card(ax, x, y, w, h, title="", bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, border_width=1.0):
    card = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.010,rounding_size=0.012",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=border_width,
        zorder=2
    )
    ax.add_patch(card)
    if title:
        ax.text(x + 0.02, y + h - 0.020, title, fontsize=8.5, fontweight="bold", color=COLOR_HEADER_BG, va="top", zorder=3)
    return card

def draw_code_box(ax, x, y, w, h, code_text: str, filename: str = ""):
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.008,rounding_size=0.008",
        facecolor=COLOR_CODE_BG,
        edgecolor="#334155",
        linewidth=1.0,
        zorder=3
    )
    ax.add_patch(box)

    if filename:
        badge = patches.Rectangle((x, y + h - 0.022), w, 0.022, facecolor="#1E293B", edgecolor="none", zorder=4)
        ax.add_patch(badge)
        ax.text(x + 0.015, y + h - 0.011, f"  SOURCE: {filename}", fontsize=7.0, fontweight="bold", color="#38BDF8", family="monospace", va="center", zorder=5)

    lines = code_text.strip().split("\n")
    line_spacing = (h - 0.030) / max(len(lines), 1)
    for idx, line in enumerate(lines):
        line_y = y + h - 0.030 - (idx * line_spacing)
        ax.text(x + 0.015, line_y, f"{idx+1:2d} ", fontsize=6.4, color="#64748B", family="monospace", va="top", zorder=5)
        ax.text(x + 0.045, line_y, line, fontsize=6.4, color=COLOR_CODE_TEXT, family="monospace", va="top", zorder=5)


# ==============================================================================
# PAGE 1: PORTADA & FILOSOFÍA CENTRAL (LA GRAN TESIS)
# ==============================================================================
def render_page_1(pdf, lang: str = "es"):
    ch_title = "01. Filosofía y Tesis" if lang == "es" else "01. Philosophy & Thesis"
    fig, ax = create_base_page(1, 8, ch_title, lang=lang)

    banner = patches.FancyBboxPatch(
        (0.04, 0.795), 0.92, 0.135,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        facecolor="#0B132B",
        edgecolor="#1C2541",
        linewidth=1.5,
        zorder=2
    )
    ax.add_patch(banner)

    ax.text(0.07, 0.895, "EDGE VISION SAFETY GUARD", fontsize=17, fontweight="bold", color="#F8FAFC", zorder=3)
    sub1 = "Manual de Estudio de Arquitectura de Sistemas Críticos en Tiempo Real" if lang == "es" else "Real-Time Safety-Critical Systems Architecture Manual"
    sub2 = ("Diseño Guiado por la Física, Geometría Planar y Criterios de Seguridad Industrial (Basado en ISO 13855 / IEC 61496)"
            if lang == "es" else
            "Physics-Guided Design, Planar Geometry, and Industrial Safety Principles (Based on ISO 13855 / IEC 61496)")
    ax.text(0.07, 0.860, sub1, fontsize=10.5, color="#38BDF8", zorder=3)
    ax.text(0.07, 0.825, sub2, fontsize=8.0, color="#94A3B8", zorder=3)

    badges = [
        ("ISO 13855:2024", "#DC2626"),
        ("IEC 61496 / 61508", "#2563EB"),
        ("CONCEPTS > CODE", "#D97706"),
        ("FAIL-SAFE ARCHITECTURE", "#059669"),
        ("DLT HOMOGRAPHY 3x3", "#7C3AED"),
    ]
    bx = 0.07
    for text, col in badges:
        bw = len(text) * 0.0068 + 0.018
        bpatch = patches.FancyBboxPatch((bx, 0.765), bw, 0.019, boxstyle="round,pad=0.003,rounding_size=0.005",
                                        facecolor=col, edgecolor="none", zorder=3)
        ax.add_patch(bpatch)
        ax.text(bx + bw/2, 0.774, text, fontsize=6.5, fontweight="bold", color="#FFFFFF", ha="center", va="center", zorder=4)
        bx += bw + 0.010

    c1_title = "1. LA GRAN TESIS DEL PROYECTO (Concepts > Code)" if lang == "es" else "1. CORE ARCHITECTURAL THESIS (Concepts > Code)"
    draw_card(ax, 0.04, 0.510, 0.92, 0.225, c1_title)

    quote_box = patches.Rectangle((0.065, 0.675), 0.87, 0.028, facecolor="#EFF6FF", edgecolor="#3B82F6", linewidth=1.0, zorder=3)
    ax.add_patch(quote_box)
    quote_text = ('"No todos los problemas de un sistema de Inteligencia Artificial se resuelven con más Inteligencia Artificial."'
                  if lang == "es" else
                  '"Not every challenge in Artificial Intelligence should be solved with more Artificial Intelligence."')
    ax.text(0.5, 0.689, quote_text, fontsize=7.8, fontweight="bold", style="italic", color="#1E3A8A", ha="center", va="center", zorder=4)

    if lang == "es":
        t1_text = (
            "En el desarrollo de software contemporáneo existe la tentación de concebir las redes neuronales como 'cajas negras' universales:\n"
            "pretender entrenar modelos para inferir si un operario 'comete una infracción' o 'cuánto tiempo lleva dentro de una zona'.\n"
            "Ese enfoque es estocástico, opaco, computacionalmente ineficiente y no auditable bajo normas de seguridad industrial.\n\n"
            "Este proyecto demuestra un diseño arquitectónico riguroso separando el problema en cuatro capas ortogonales y deterministas:\n"
            "  1. La IA se restringe a Percepción Pura: Detectar únicamente coordenadas de tobillos anatómicos en el espacio de píxeles.\n"
            "  2. La Geometría resuelve el Espacio: Transformación planar proyectiva homográfica 3x3 al plano del suelo (Zw = 0).\n"
            "  3. La Cinemática resuelve la Incertidumbre: Filtro de Kalman 2D continuo con compuertas elipsoidales de Mahalanobis.\n"
            "  4. La Lógica Determinista toma las Decisiones: Statecharts ortogonales concurrentes ejecutados en < 0.05 ms por cuadro."
        )
    else:
        t1_text = (
            "In modern software engineering, there is an omnipresent temptation to treat neural networks as universal black boxes:\n"
            "attempting to train models to infer whether an operator 'is violating a safety zone' or 'how long they have dwelled inside'.\n"
            "That approach is stochastic, opaque, computationally wasteful, and non-auditable under industrial safety directives.\n\n"
            "This project demonstrates a rigorous architectural design by decoupling the problem into four orthogonal, deterministic layers:\n"
            "  1. AI is restricted to Pure Perception: Detecting solely anatomical ankle keypoints in camera pixel space.\n"
            "  2. Geometry resolves Physical Space: 3x3 DLT planar projective homography mapping to the floor plane (Zw = 0).\n"
            "  3. Kinematics resolves Uncertainty: Continuous 2D Kalman Filter with Mahalanobis ellipsoidal validation gating.\n"
            "  4. Deterministic Logic governs Safety Decisions: Concurrent orthogonal statecharts evaluated in < 0.05 ms per frame."
        )
    ax.text(0.065, 0.660, t1_text, fontsize=7.3, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    c2_title = "2. ARQUITECTURA EN CAPAS: EL FLUJO END-TO-END" if lang == "es" else "2. LAYERED ARCHITECTURE: THE END-TO-END PIPELINE"
    draw_card(ax, 0.04, 0.065, 0.92, 0.435, c2_title)

    if lang == "es":
        layers = [
            ("1. PERCEPCIÓN", "#1E293B", "#38BDF8", [
                "Frame RTSP / V4L2",
                "YOLO11-Pose (CoreML)",
                "Keypoints Tobillos (15, 16)",
                "Anchor Fallback Degradado"
            ]),
            ("2. GEOMETRÍA", "#0C4A6E", "#38BDF8", [
                "DLT Homografía H (3x3)",
                "Verificación κ(H) < 10^6",
                "Mapeo Inverso (Zw = 0)",
                "Métrico (X, Y) [metros]"
            ]),
            ("3. ESTIMACIÓN", "#14532D", "#4ADE80", [
                "Kalman Filter 2D (CV)",
                "Gating Mahalanobis χ²_2",
                "Asignación Húngara O(N³)",
                "OBSERVED / PREDICTED"
            ]),
            ("4. DECISIÓN", "#7C2D12", "#FDBA74", [
                "Prepared Geometries GEOS",
                "Schmitt Trigger (200 mm)",
                "Bypass vn ≥ 1.6 m/s",
                "Statecharts (Trip = True)"
            ]),
        ]
    else:
        layers = [
            ("1. PERCEPTION", "#1E293B", "#38BDF8", [
                "RTSP / V4L2 Video Stream",
                "YOLO11-Pose (CoreML)",
                "Ankle Keypoints (15, 16)",
                "Graceful Anchor Fallback"
            ]),
            ("2. GEOMETRY", "#0C4A6E", "#38BDF8", [
                "DLT Homography H (3x3)",
                "Stability Check κ(H) < 10^6",
                "Inverse Mapping (Zw = 0)",
                "Metric (X, Y) [meters]"
            ]),
            ("3. ESTIMATION", "#14532D", "#4ADE80", [
                "2D Kalman Filter (CV)",
                "Mahalanobis Gating χ²_2",
                "Hungarian Matching O(N³)",
                "OBSERVED / PREDICTED"
            ]),
            ("4. DECISION", "#7C2D12", "#FDBA74", [
                "GEOS Prepared Geometries",
                "Schmitt Trigger (200 mm)",
                "Fast Bypass vn ≥ 1.6 m/s",
                "Statecharts (Trip = True)"
            ]),
        ]

    col_w = 0.205
    col_gap = 0.02
    start_x = 0.065
    y_top = 0.455

    for i, (title, header_bg, accent_c, items) in enumerate(layers):
        cx = start_x + i * (col_w + col_gap)
        c_box = patches.FancyBboxPatch((cx, y_top - 0.26), col_w, 0.26, boxstyle="round,pad=0.006,rounding_size=0.008",
                                       facecolor="#F1F5F9", edgecolor="#CBD5E1", lw=1.0, zorder=3)
        ax.add_patch(c_box)

        h_box = patches.FancyBboxPatch((cx, y_top - 0.034), col_w, 0.034, boxstyle="round,pad=0.005,rounding_size=0.006",
                                       facecolor=header_bg, edgecolor="none", zorder=4)
        ax.add_patch(h_box)
        ax.text(cx + col_w/2, y_top - 0.017, title, fontsize=7.8, fontweight="bold", color=accent_c, ha="center", va="center", zorder=5)

        iy = y_top - 0.050
        for item in items:
            ibox = patches.FancyBboxPatch((cx + 0.006, iy - 0.036), col_w - 0.012, 0.036,
                                          boxstyle="round,pad=0.003,rounding_size=0.005",
                                          facecolor="#FFFFFF", edgecolor="#E2E8F0", lw=0.8, zorder=4)
            ax.add_patch(ibox)
            ax.text(cx + col_w/2, iy - 0.018, item, fontsize=6.8, color=COLOR_TEXT_MAIN, ha="center", va="center", zorder=5)
            iy -= 0.046

        if i < 3:
            arrow_x = cx + col_w + 0.003
            ax.annotate("", xy=(arrow_x + col_gap - 0.006, y_top - 0.130), xytext=(arrow_x, y_top - 0.130),
                        arrowprops=dict(arrowstyle="->", color="#64748B", lw=1.8), zorder=6)

    prof_box = patches.FancyBboxPatch((0.065, 0.085), 0.87, 0.075, boxstyle="round,pad=0.008,rounding_size=0.008",
                                     facecolor="#1E293B", edgecolor="#334155", lw=1.0, zorder=3)
    ax.add_patch(prof_box)
    prof_header = ("PERFORMANCE PROFILER & SAFETY INTEGRITY HORIZONS (ORTOGONAL):"
                   if lang == "es" else
                   "PERFORMANCE PROFILER & SAFETY INTEGRITY HORIZONS (ORTHOGONAL):")
    ax.text(0.08, 0.140, prof_header, fontsize=7.8, fontweight="bold", color="#38BDF8", zorder=4)

    if lang == "es":
        line1 = (
            r"• $T_{\mathrm{system}}$ (Hardware / Frame): "
            r"$T_{\mathrm{capture}} + T_{\mathrm{pre}} + T_{\mathrm{infer}} + T_{\mathrm{pose}} + T_{\mathrm{geom}} + T_{\mathrm{track}} + T_{\mathrm{fsm}} \approx 18.5 - 20.5$ ms por cuadro."
        )
        line2 = (
            r"• $T_{\mathrm{event}}$ (Respuesta Física Total): Paso normal con debounce ($N_{\mathrm{confirm}}=3$) $\approx 81.7$ ms  |  "
            r"Aproximación rápida ($v_n \geq 1.6$ m/s) bypass = 19 ms."
        )
    else:
        line1 = (
            r"• $T_{\mathrm{system}}$ (Hardware / Frame): "
            r"$T_{\mathrm{capture}} + T_{\mathrm{pre}} + T_{\mathrm{infer}} + T_{\mathrm{pose}} + T_{\mathrm{geom}} + T_{\mathrm{track}} + T_{\mathrm{fsm}} \approx 18.5 - 20.5$ ms per frame."
        )
        line2 = (
            r"• $T_{\mathrm{event}}$ (Total Physical Response): Nominal approach with debounce ($N_{\mathrm{confirm}}=3$) $\approx 81.7$ ms  |  "
            r"Fast approach ($v_n \geq 1.6$ m/s) dynamic bypass = 19 ms."
        )

    ax.text(0.08, 0.121, line1, fontsize=6.8, color="#E2E8F0", va="top", zorder=4)
    ax.text(0.08, 0.103, line2, fontsize=6.8, color="#E2E8F0", va="top", zorder=4)

    fig.savefig(f"/tmp/deck_{lang}_p1.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 2: GEOMETRÍA PROYECTIVA Y HOMOGRAFÍA PLANAR (Zw = 0)
# ==============================================================================
def render_page_2(pdf, lang: str = "es"):
    ch_title = "02. Geometría y Homografía" if lang == "es" else "02. Geometry & Homography"
    fig, ax = create_base_page(2, 8, ch_title, lang=lang)

    c1_title = "1. EL COLAPSO DE PERSPECTIVA: RESTRICCIÓN PLANAR (Zw = 0)" if lang == "es" else "1. THE PERSPECTIVE COLLAPSE: PLANAR CONSTRAINT (Zw = 0)"
    draw_card(ax, 0.04, 0.695, 0.92, 0.225, c1_title)

    if lang == "es":
        geo_text = (
            "Una cámara monocular 2D pierde intrínsecamente la coordenada de profundidad Z: infinitos puntos a lo largo del rayo proyectan\n"
            "al mismo píxel (u, v). La matriz general de proyección de cámara es de dimension 3x4:\n"
        )
    else:
        geo_text = (
            "A monocular 2D camera inherently loses the depth coordinate Z: infinite 3D points along the projective ray map\n"
            "to the exact same pixel (u, v). The general camera projection matrix has dimension 3x4:\n"
        )
    ax.text(0.065, 0.890, geo_text, fontsize=7.8, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    math_box = patches.Rectangle((0.065, 0.812), 0.87, 0.038, facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=1, zorder=3)
    ax.add_patch(math_box)
    math_eq = (
        r"$s \cdot [u, v, 1]^T = \mathbf{P}_{3 \times 4} [X_w, Y_w, 0, 1]^T = \mathbf{H}_{3 \times 3} [X_w, Y_w, 1]^T "
        r"\quad \Longleftrightarrow \quad [X_w, Y_w, 1]^T = \mathbf{H}^{-1} (s \cdot [u, v, 1]^T)$"
    )
    ax.text(0.5, 0.831, math_eq, fontsize=8.2, color="#0F172A", ha="center", va="center", zorder=4)

    if lang == "es":
        geo_explain = (
            "Al rastrear exclusivamente los tobillos apoyados sobre el suelo, fijamos físicamente Zw = 0. La tercera columna de proyección\n"
            "se anula matemáticamente, colapsando el sistema a una matriz H invertible de 3x3. Esto permite transformar píxeles a metros\n"
            "reales mediante álgebra lineal pura en menos de 0.05 ms, sin recurrir a costosos sensores LiDAR o cámaras estéreo."
        )
    else:
        geo_explain = (
            "By tracking exclusively the operator's ankles resting on the floor, we physically enforce Zw = 0. The third projection column\n"
            "vanishes mathematically, collapsing the system into an invertible 3x3 homography matrix H. This allows transforming pixels into true\n"
            "world meters via pure linear algebra in under 0.05 ms, without requiring expensive LiDAR sensors or stereo cameras."
        )
    ax.text(0.065, 0.792, geo_explain, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    c2_title = "2. ALGORITMO DLT, GRADOS DE LIBERTAD Y CONDICIONAMIENTO" if lang == "es" else "2. DLT ALGORITHM, DEGREES OF FREEDOM & MATRIX CONDITIONING"
    draw_card(ax, 0.04, 0.435, 0.92, 0.245, c2_title)

    if lang == "es":
        dlt_text = (
            "• Grados de Libertad: La matriz H posee 9 coeficientes, pero al estar definida en coordenadas homogéneas proyectivas hasta\n"
            "  un factor de escala arbitrario (H y λH representan la misma transformación), tiene exactamente 9 - 1 = 8 grados de libertad.\n"
            "• Determinación Exacta: Cada correspondencia de punto (u, v) ↔ (X, Y) genera 2 ecuaciones lineales algebraicamente independientes.\n"
            "  Con exactamente 4 puntos coplanares no colineales, se forma un sistema determinado de 8x8 con residuo RMSE = 0.00 m.\n"
            "• Calibración Sobredeterminada (N > 4): Para medir error real de reproyección se requieren N > 4 marcadores o puntos de test.\n"
            "• Verificación de Colinealidad: En N = 4, ningún triplete puede ser colineal (Área(Δ) > ε). En N > 4, se exige rango afín pleno (rank=3)\n"
            "  y la existencia de al menos un cuadrilátero no degenerado para evitar falsos rechazos en perímetros rectangulares."
        )
    else:
        dlt_text = (
            "• Degrees of Freedom: Matrix H contains 9 coefficients, but because it is defined in homogeneous projective coordinates up to\n"
            "  an arbitrary scale factor (H and λH represent the exact same mapping), it possesses exactly 9 - 1 = 8 degrees of freedom.\n"
            "• Exact Determination: Each point correspondence (u, v) ↔ (X, Y) yields 2 algebraically independent linear equations.\n"
            "  Exactly 4 coplanar, non-collinear points form a determined 8x8 system with algebraic residual RMSE = 0.00 m.\n"
            "• Overdetermined Calibration (N > 4): Evaluating empirical reprojection error requires N > 4 markers or test coordinates.\n"
            "• Collinearity Verification: At N = 4, no triplet may be collinear (Area(Δ) > ε). At N > 4, full affine rank (rank = 3)\n"
            "  and at least one non-degenerate quadrilateral are required to prevent false rejections on rectangular perimeters."
        )
    ax.text(0.065, 0.645, dlt_text, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    cond_box = patches.Rectangle((0.065, 0.450), 0.87, 0.040, facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=1, zorder=3)
    ax.add_patch(cond_box)
    stab_label = r"\mathrm{(L\acute{\imath}mite\ de\ Estabilidad)}" if lang == "es" else r"\mathrm{(Stability\ Limit)}"
    cond_math = (
        r"$\kappa(\mathbf{H}) = \frac{\sigma_{\max}(\mathbf{H})}{\sigma_{\min}(\mathbf{H})} < 10^6 \quad " + stab_label +
        r"\qquad \mathrm{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N \|\mathbf{X}_i - \mathbf{H}^{-1}\mathbf{x}_i\|^2} \leq 0.05\mathrm{ m}$"
    )
    ax.text(0.5, 0.470, cond_math, fontsize=8.2, color="#0F172A", ha="center", va="center", zorder=4)

    c3_title = "3. CÓDIGO FUENTE REAL: VALIDACIÓN Y PROYECCIÓN VECTORIZADA" if lang == "es" else "3. PRODUCTION SOURCE CODE: NUMERICAL CONDITIONING & VECTORIZED PROJECTION"
    draw_card(ax, 0.04, 0.065, 0.92, 0.355, c3_title)

    if lang == "es":
        code_homography = """# src/core/homography.py (Implementación de Producción)
def calculate_condition_number(H: np.ndarray) -> float:
    # Calcula el número de condición κ(H) = σ_max / σ_min vía SVD
    s = np.linalg.svd(H, compute_uv=False)
    if s[-1] < 1e-12:
        return float("inf")
    return float(s[0] / s[-1])

def project_to_world(self, points: np.ndarray) -> np.ndarray:
    # Proyección vectorizada de píxeles a metros en suelo (Zw = 0)
    pts = np.atleast_2d(points)
    homogeneous = np.column_stack([pts, np.ones(len(pts))])
    transformed = (self.H @ homogeneous.T).T
    # Normalización por factor de escala proyectivo W
    return transformed[:, :2] / transformed[:, 2:3]"""
    else:
        code_homography = """# src/core/homography.py (Production Implementation)
def calculate_condition_number(H: np.ndarray) -> float:
    # Compute matrix condition number κ(H) = σ_max / σ_min via SVD
    s = np.linalg.svd(H, compute_uv=False)
    if s[-1] < 1e-12:
        return float("inf")
    return float(s[0] / s[-1])

def project_to_world(self, points: np.ndarray) -> np.ndarray:
    # Vectorized projection from pixels to meters on floor (Zw = 0)
    pts = np.atleast_2d(points)
    homogeneous = np.column_stack([pts, np.ones(len(pts))])
    transformed = (self.H @ homogeneous.T).T
    # Normalization by projective scale factor W
    return transformed[:, :2] / transformed[:, 2:3]"""

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.285, code_homography, "src/core/homography.py")

    fig.savefig(f"/tmp/deck_{lang}_p2.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 3: PERCEPCIÓN PURA Y ANCLAJE ANATÓMICO (KEYPOINTS VS BBOX)
# ==============================================================================
def render_page_3(pdf, lang: str = "es"):
    ch_title = "03. Percepción y Anclaje" if lang == "es" else "03. Perception & Ground Anchor"
    fig, ax = create_base_page(3, 8, ch_title, lang=lang)

    c1_title = "1. EL ENGAÑO DEL BOUNDING BOX VS ANCLAJE EN TOBILLOS (ADR-001)" if lang == "es" else "1. THE BOUNDING BOX CENTROID TRAP VS ANKLE GROUND ANCHOR (ADR-001)"
    draw_card(ax, 0.04, 0.690, 0.92, 0.235, c1_title)

    if lang == "es":
        p3_text = (
            "En visión artificial tradicional se utiliza el centroide de la caja delimitadora (bbox centroid) o la base inferior\n"
            "(bbox bottom-center) para posicionar al sujeto. En cámaras elevadas angulares, este método genera fallas críticas:\n\n"
            "• Torsos inclinados y brazos extendidos: Cuando un operario se agacha o extiende herramientas hacia una zona peligrosa\n"
            "  sin cruzar el perímetro con los pies, el bounding box 2D se deforma y proyecta un punto en el suelo a metros de distancia\n"
            "  del cuerpo real, provocando paradas intempestivas falsas que arruinan la productividad industrial.\n"
            "• El Anclaje Anatómico Real: Los tobillos representan el único punto físico en contacto ineludible con el plano Zw = 0.\n"
            "  Al extraer los keypoints 15 (tobillo izquierdo) y 16 (tobillo derecho) del esqueleto COCO de YOLO11-Pose, el anclaje es\n"
            "  invariante ante posturas del torso, vestimenta holgada, agachadas o manipulación de cargas."
        )
    else:
        p3_text = (
            "In traditional computer vision, the bounding box centroid or bottom-center coordinate is commonly used to locate the subject.\n"
            "Under elevated oblique industrial cameras, this approach produces critical failure modes:\n\n"
            "• Leaning Torsos & Extended Tools: When a worker bends over or extends equipment across a hazard perimeter without stepping\n"
            "  inside with their feet, the 2D bounding box widens dramatically. Its projection lands meters into the hazard zone on the floor,\n"
            "  triggering catastrophic false emergency stops that disrupt factory throughput.\n"
            "• True Anatomical Ground Anchor: Ankles represent the sole physical contact point bound to the floor plane Zw = 0.\n"
            "  By extracting keypoints 15 (left ankle) and 16 (right ankle) from YOLO11-Pose, the spatial anchor is fully\n"
            "  invariant to torso bending, loose clothing, crouching, or material handling."
        )
    ax.text(0.065, 0.890, p3_text, fontsize=7.6, color=COLOR_TEXT_MAIN, linespacing=1.30, va="top", zorder=3)

    anchor_box = patches.Rectangle((0.065, 0.702), 0.87, 0.035, facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=1, zorder=3)
    ax.add_patch(anchor_box)
    if_word = r"\mathrm{si\ }" if lang == "es" else r"\mathrm{if\ }"
    eq_anchor = (
        r"$\mathbf{p}_{\mathrm{ground}} = \frac{\mathbf{p}_{\mathrm{ankle\_left}} + \mathbf{p}_{\mathrm{ankle\_right}}}{2} \quad " +
        if_word + r"\min(\mathrm{conf}_L, \mathrm{conf}_R) \geq 0.30$"
    )
    ax.text(0.5, 0.720, eq_anchor, fontsize=8.4, color="#0F172A", ha="center", va="center", zorder=4)

    c2_title = "2. DIAGRAMA COMPARATIVO: DEFORMACIÓN DE BBOX ANTE TORSO INCLINADO" if lang == "es" else "2. COMPARATIVE ANALYSIS: BOUNDING BOX DEFORMATION UNDER LEANING TORSO"
    draw_card(ax, 0.04, 0.380, 0.92, 0.295, c2_title)

    d_ax = ax
    floor_y = 0.445
    d_ax.plot([0.055, 0.44], [floor_y, floor_y], color="#334155", lw=2, zorder=3)
    floor_lbl = "Piso (Zw = 0)" if lang == "es" else "Floor (Zw = 0)"
    d_ax.text(0.055, floor_y + 0.008, floor_lbl, fontsize=6.6, color=COLOR_TEXT_MUTED, va="bottom", zorder=3)

    # Human figure leaning
    d_ax.plot([0.16, 0.18], [floor_y, 0.490], color="#1E293B", lw=3, zorder=4)
    d_ax.plot([0.18, 0.28], [0.490, 0.560], color="#1E293B", lw=3, zorder=4)
    d_ax.plot([0.28, 0.34], [0.560, 0.530], color="#1E293B", lw=2.5, zorder=4)
    d_ax.plot(0.29, 0.580, "o", color="#1E293B", ms=7, zorder=4)

    # Real Ankles
    d_ax.plot(0.16, floor_y, "o", color="#16A34A", ms=8, zorder=6)
    ankles_lbl = "Tobillos (Real)" if lang == "es" else "Ankles (Real)"
    d_ax.text(0.15, floor_y - 0.015, ankles_lbl, fontsize=6.8, fontweight="bold", color="#16A34A", ha="center", va="top", zorder=6)

    # Bbox rectangle
    bbox_rect = patches.Rectangle((0.13, floor_y), 0.22, 0.155, fill=False, edgecolor="#DC2626", ls="--", lw=1.5, zorder=5)
    d_ax.add_patch(bbox_rect)
    bbox_center_x = (0.13 + 0.35) / 2.0
    d_ax.plot(bbox_center_x, floor_y, "x", color="#DC2626", ms=9, mew=2.5, zorder=6)
    bbox_lbl = "Bbox Bottom (Error)" if lang == "es" else "Bbox Bottom (Error)"
    d_ax.text(bbox_center_x, floor_y - 0.036, bbox_lbl, fontsize=6.8, fontweight="bold", color="#DC2626", ha="center", va="top", zorder=6)

    # Danger zone threshold
    d_ax.plot([0.205, 0.205], [0.425, 0.625], color="#EF4444", lw=2, ls=":", zorder=5)
    zone_lbl = "Límite Zona Peligro" if lang == "es" else "Hazard Zone Perimeter"
    d_ax.text(0.210, 0.615, zone_lbl, fontsize=7.2, color="#EF4444", zorder=5)

    if lang == "es":
        comp_text = (
            "ANÁLISIS DE ERROR GEOMÉTRICO:\n"
            "• El operario tiene los pies afuera de la zona (x = 0.16 m).\n"
            "• El Bounding Box se ensancha hacia la derecha por el torso y brazos inclinados.\n"
            "• La base del Bbox calcula x = 0.240 m → DENTRO DE PELIGRO (Falso Positivo).\n"
            "• El Keypoint de tobillos calcula x = 0.160 m → FUERA DE PELIGRO (Correcto).\n"
            "• Resultado: Cero falsas paradas ante posturas corporales o herramientas."
        )
    else:
        comp_text = (
            "GEOMETRIC ERROR ANALYSIS:\n"
            "• The operator's feet remain safely outside the zone (x = 0.16 m).\n"
            "• The bounding box expands rightward due to torso and arms leaning.\n"
            "• Bbox bottom projects to x = 0.240 m → INSIDE HAZARD (False Positive Trip).\n"
            "• Ankle keypoint projects to x = 0.160 m → OUTSIDE HAZARD (Correct Safe State).\n"
            "• Result: Zero false shutdowns caused by body postures or handheld tools."
        )
    d_ax.text(0.48, 0.605, comp_text, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.32, va="top", zorder=4)

    c3_title = "3. CÓDIGO FUENTE: JERARQUÍA DE DEGRADACIÓN DE ANCLAJE (ADR-007)" if lang == "es" else "3. PRODUCTION SOURCE CODE: GRACEFUL ANCHOR DEGRADATION HIERARCHY (ADR-007)"
    draw_card(ax, 0.04, 0.065, 0.92, 0.300, c3_title)

    if lang == "es":
        code_anchor = """# src/pipeline/safety_pipeline.py (Extracción de Anclaje Robusto)
def extract_ground_anchor(kpts: np.ndarray, bbox: tuple) -> Tuple[Tuple[float, float], AnchorSource, float]:
    left_conf, right_conf = float(kpts[15, 2]), float(kpts[16, 2])
    # Nivel 1: Ambos tobillos detectados con alta confianza
    if left_conf >= 0.30 and right_conf >= 0.30:
        midpoint = ((float(kpts[15, 0]) + float(kpts[16, 0])) / 2.0,
                    (float(kpts[15, 1]) + float(kpts[16, 1])) / 2.0)
        return midpoint, AnchorSource.ANKLES_DUAL, min(left_conf, right_conf)
    # Nivel 2: Tobillo individual visible (el otro ocluido)
    if left_conf >= 0.30:
        return (float(kpts[15, 0]), float(kpts[15, 1])), AnchorSource.ANKLE_SINGLE, left_conf
    if right_conf >= 0.30:
        return (float(kpts[16, 0]), float(kpts[16, 1])), AnchorSource.ANKLE_SINGLE, right_conf
    # Nivel 3: Fallback degradado a base de bounding box
    bbox_bottom = ((bbox[0] + bbox[2]) / 2.0, bbox[3])
    return bbox_bottom, AnchorSource.BBOX_BOTTOM, 0.20"""
    else:
        code_anchor = """# src/pipeline/safety_pipeline.py (Robust Ground Anchor Extraction)
def extract_ground_anchor(kpts: np.ndarray, bbox: tuple) -> Tuple[Tuple[float, float], AnchorSource, float]:
    left_conf, right_conf = float(kpts[15, 2]), float(kpts[16, 2])
    # Tier 1: Dual ankles detected with high confidence
    if left_conf >= 0.30 and right_conf >= 0.30:
        midpoint = ((float(kpts[15, 0]) + float(kpts[16, 0])) / 2.0,
                    (float(kpts[15, 1]) + float(kpts[16, 1])) / 2.0)
        return midpoint, AnchorSource.ANKLES_DUAL, min(left_conf, right_conf)
    # Tier 2: Single visible ankle (the other occluded)
    if left_conf >= 0.30:
        return (float(kpts[15, 0]), float(kpts[15, 1])), AnchorSource.ANKLE_SINGLE, left_conf
    if right_conf >= 0.30:
        return (float(kpts[16, 0]), float(kpts[16, 1])), AnchorSource.ANKLE_SINGLE, right_conf
    # Tier 3: Graceful fallback to bounding box bottom-center
    bbox_bottom = ((bbox[0] + bbox[2]) / 2.0, bbox[3])
    return bbox_bottom, AnchorSource.BBOX_BOTTOM, 0.20"""

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_anchor, "src/pipeline/safety_pipeline.py")

    fig.savefig(f"/tmp/deck_{lang}_p3.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 4: CINEMÁTICA BAYESIANA, FILTRO DE KALMAN 2D Y ASOCIACIÓN HÚNGARA
# ==============================================================================
def render_page_4(pdf, lang: str = "es"):
    ch_title = "04. Cinemática y Tracking" if lang == "es" else "04. Kinematics & Tracking"
    fig, ax = create_base_page(4, 8, ch_title, lang=lang)

    c1_title = "1. FILTRO DE KALMAN 2D: VELOCIDAD CONSTANTE Y COVARIANZAS" if lang == "es" else "1. 2D KALMAN FILTER: CONSTANT VELOCITY MODEL & COVARIANCES"
    draw_card(ax, 0.04, 0.690, 0.92, 0.235, c1_title)

    if lang == "es":
        k_text = (
            "El jitter de detección en píxeles produce saltos estocásticos de posición métrica de ±15 mm. El Filtro de Kalman 2D\n"
            "estima el vector de estado cinemático continuo x = [X, Y, vx, vy]^T en coordenadas del mundo real:\n"
        )
    else:
        k_text = (
            "Pixel detection jitter produces stochastic position jumps of ±15 mm. A continuous 2D Kalman Filter\n"
            "estimates the dynamic kinematic state vector x = [X, Y, vx, vy]^T in world coordinates:\n"
        )
    ax.text(0.065, 0.885, k_text, fontsize=7.6, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    math_kalman = (
        r"$\mathbf{x}_k = [X, Y, v_x, v_y]^T, \quad "
        r"\mathbf{x}_k = \mathbf{F}(\Delta t) \mathbf{x}_{k-1} + \mathbf{w}_k, \quad "
        r"\mathbf{z}_k = \mathbf{H}_{\mathrm{obs}} \mathbf{x}_k + \mathbf{v}_k$"
    )
    ax.text(0.5, 0.835, math_kalman, fontsize=8.3, color="#0F172A", ha="center", va="center", zorder=4)

    k_eq2 = (
        r"$\mathbf{P}_k^- = \mathbf{F} \mathbf{P}_{k-1} \mathbf{F}^T + \mathbf{Q}, \quad "
        r"\mathbf{K}_k = \mathbf{P}_k^- \mathbf{H}^T (\mathbf{H} \mathbf{P}_k^- \mathbf{H}^T + \mathbf{R})^{-1}, \quad "
        r"\hat{\mathbf{x}}_k = \hat{\mathbf{x}}_k^- + \mathbf{K}_k (\mathbf{z}_k - \mathbf{H}\hat{\mathbf{x}}_k^-)$"
    )
    ax.text(0.5, 0.785, k_eq2, fontsize=8.0, color="#0F172A", ha="center", va="center", zorder=4)

    if lang == "es":
        k_epist = (
            "• Epistemología de Estados (ADR-008): Cada estimación registra su frescura: OBSERVED (fotón óptico fresco k=0),\n"
            "  PREDICTED (dead reckoning seguro 1 ≤ k ≤ 3, ≤ 100 ms) y STALE (divergencia no segura k ≥ 4, relé bloqueado)."
        )
    else:
        k_epist = (
            "• Epistemic States (ADR-008): Every estimate explicitly tracks data freshness: OBSERVED (fresh optical photon at k=0),\n"
            "  PREDICTED (safe bounded dead reckoning 1 ≤ k ≤ 3, ≤ 100 ms), and STALE (unsafe divergence k ≥ 4, trip locked)."
        )
    ax.text(0.065, 0.740, k_epist, fontsize=7.4, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    c2_title = "2. GATING ELIPSOIDAL DE MAHALANOBIS Y ASIGNACIÓN GLOBAL HÚNGARA (ADR-011)" if lang == "es" else "2. MAHALANOBIS ELLIPSOIDAL GATING & GLOBAL HUNGARIAN MATCHING (ADR-011)"
    draw_card(ax, 0.04, 0.375, 0.92, 0.300, c2_title)

    sub_ax = fig.add_axes([0.110, 0.405, 0.255, 0.205])
    cov_x = 0.4
    cov_y = 0.15
    theta = np.radians(35)
    t = np.linspace(0, 2*np.pi, 100)
    for sig, col, lbl in [(1.0, "#93C5FD", "1σ"), (2.0, "#60A5FA", "2σ"), (3.03, "#EF4444", "χ²=9.21")]:
        xs = sig * cov_x * np.cos(t)
        ys = sig * cov_y * np.sin(t)
        xr = xs * np.cos(theta) - ys * np.sin(theta) + 0.5
        yr = xs * np.sin(theta) + ys * np.cos(theta) + 0.5
        sub_ax.plot(xr, yr, color=col, lw=1.5 if sig > 2.5 else 1.0, label=lbl)

    sub_ax.annotate("", xy=(0.85, 0.75), xytext=(0.5, 0.5),
                    arrowprops=dict(arrowstyle="->", color="#1E293B", lw=2))
    sub_ax.plot(0.5, 0.5, "o", color="#1E293B", ms=5)
    sub_ax.text(0.48, 0.42, "Track (x, y)", fontsize=6.8, fontweight="bold", ha="right")
    sub_ax.text(0.86, 0.77, "Vector v", fontsize=7.0, fontweight="bold", color="#1E293B")
    el_title = "Elipsoide de Innovación Mahalanobis" if lang == "es" else "Mahalanobis Innovation Ellipsoid"
    sub_ax.set_title(el_title, fontsize=7.0, fontweight="bold", pad=2)
    sub_ax.legend(fontsize=6.0, loc="lower right")
    sub_ax.axis("equal")
    sub_ax.grid(True, ls=":", alpha=0.5)
    sub_ax.tick_params(labelsize=6.0, pad=2)

    if lang == "es":
        mot_text = (
            "RESOLUCIÓN DE CRUCES Y FALSOS TRACKS:\n\n"
            "1. Compuerta de Mahalanobis χ²_2(0.99) ≤ 9.210:\n"
            "   La covarianza de innovación S = H P^- H^T + R proyecta\n"
            "   un elipsoide orientado según la dirección del vector de\n"
            "   velocidad v, impidiendo asociar detecciones perpendiculares.\n\n"
            "2. Algoritmo Global Húngaro (Munkres):\n"
            "   Resuelve la asignación biyectiva óptima O(N³) en 0.017 ms,\n"
            "   garantizando permanencia de ID en cruces de operarios.\n\n"
            "3. World-Space Spatial Birth NMS (d_birth ≥ 0.6 m):\n"
            "   Suprime tracks fantasma por propuestas redundantes de YOLO."
        )
    else:
        mot_text = (
            "CROSSING AMBIGUITY & GHOST TRACK RESOLUTION:\n\n"
            "1. Mahalanobis Gating χ²_2(0.99) ≤ 9.210:\n"
            "   Innovation covariance S = H P^- H^T + R projects an\n"
            "   ellipsoid aligned along the velocity vector v,\n"
            "   rejecting orthogonal false detections.\n\n"
            "2. Global Hungarian Algorithm (Munkres):\n"
            "   Solves optimal bipartite assignment O(N³) in 0.017 ms,\n"
            "   preserving consistent track IDs during worker crossings.\n\n"
            "3. World-Space Spatial Birth NMS (d_birth ≥ 0.6 m):\n"
            "   Suppresses duplicate tracks from redundant YOLO proposals."
        )
    ax.text(0.40, 0.630, mot_text, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    c3_title = "3. CÓDIGO FUENTE: PREDICCIÓN, ACTUALIZACIÓN Y GATING DE INNOVACIÓN" if lang == "es" else "3. PRODUCTION SOURCE CODE: PREDICTION, UPDATE & INNOVATION GATING"
    draw_card(ax, 0.04, 0.065, 0.92, 0.295, c3_title)

    if lang == "es":
        code_kalman = """# src/core/kalman_filter.py (Filtro Cinemático y Gating)
def mahalanobis_distance(self, z: np.ndarray) -> float:
    # Calcula la distancia cuadrática d_M² contra la covarianza de innovación S
    y = z - (self._H @ self._x)
    S = self._H @ self._P @ self._H.T + self._R
    return float(y.T @ np.linalg.inv(S) @ y)

def update(self, measurement: Tuple[float, float], confidence: float, source: AnchorSource) -> PositionEstimate:
    z = np.asarray(measurement, dtype=np.float64)
    y = z - (self._H @ self._x)
    S = self._H @ self._P @ self._H.T + self._R
    K = self._P @ self._H.T @ np.linalg.inv(S)
    self._x = self._x + K @ y
    self._P = (self._I - K @ self._H) @ self._P  # Corrección de covarianza
    return PositionEstimate(xy_m=(float(self._x[0]), float(self._x[1])), confidence=confidence, source=source)"""
    else:
        code_kalman = """# src/core/kalman_filter.py (Kinematic Filter & Gating)
def mahalanobis_distance(self, z: np.ndarray) -> float:
    # Compute squared Mahalanobis distance d_M² against innovation covariance S
    y = z - (self._H @ self._x)
    S = self._H @ self._P @ self._H.T + self._R
    return float(y.T @ np.linalg.inv(S) @ y)

def update(self, measurement: Tuple[float, float], confidence: float, source: AnchorSource) -> PositionEstimate:
    z = np.asarray(measurement, dtype=np.float64)
    y = z - (self._H @ self._x)
    S = self._H @ self._P @ self._H.T + self._R
    K = self._P @ self._H.T @ np.linalg.inv(S)
    self._x = self._x + K @ y
    self._P = (self._I - K @ self._H) @ self._P  # Covariance correction
    return PositionEstimate(xy_m=(float(self._x[0]), float(self._x[1])), confidence=confidence, source=source)"""

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_kalman, "src/core/kalman_filter.py")

    fig.savefig(f"/tmp/deck_{lang}_p4.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 5: SCHMITT TRIGGER ESPACIAL Y STATECHARTS ORTOGONALES
# ==============================================================================
def render_page_5(pdf, lang: str = "es"):
    ch_title = "05. FSM y Lógica de Seguridad" if lang == "es" else "05. FSM & Safety Logic"
    fig, ax = create_base_page(5, 8, ch_title, lang=lang)

    c1_title = "1. EL PROBLEMA DEL CHATTERING Y EL SCHMITT TRIGGER ESPACIAL (ADR-004)" if lang == "es" else "1. RELAY CHATTERING & THE SPATIAL SCHMITT TRIGGER (ADR-004)"
    draw_card(ax, 0.04, 0.675, 0.92, 0.250, c1_title)

    if lang == "es":
        fsm_text = (
            "En los límites de una zona de seguridad, un operario trabajando en el borde genera micro-oscilaciones de detección (chattering)\n"
            "debido al ruido de inferencia de keypoints. Conmutar un relé de parada a 30 Hz destruye físicamente los contactores mecánicos\n"
            "de la máquina en cuestión de horas y causa paradas erráticas continuas.\n\n"
            "La Solución Arquitectónica: Schmitt Trigger con Banda de Histéresis Espacial (Δd = 200 mm):\n"
            r"  • Límite de Peligro ($P_{\mathrm{danger}}$): Polígono interior que activa la conmutación a peligro." + "\n"
            r"  • Límite de Liberación ($P_{\mathrm{release}}$): Polígono exterior expandido $P_{\mathrm{release}} = P_{\mathrm{danger}} \oplus 0.20\ \mathrm{m}$. El operario debe cruzar" + "\n"
            "    completamente fuera del buffer de 200 mm para que el sistema considere iniciar la desescalada.\n"
            "  • Asimetría de Seguridad:\n"
            r"    1. ENTRADA RÁPIDA: Debounce normal $N_{\mathrm{confirm}} = 3$ cuadros. Pero si el vector de aproximación perpendicular" + "\n"
            r"       es rápido ($v_n \geq 1.6$ m/s según ISO 13855), se produce un BYPASS DINÁMICO INSTANTÁNEO a $N_{\mathrm{confirm}} = 1$ en 19 ms." + "\n"
            r"    2. SALIDA ESTRICTA: Exige $N_{\mathrm{release}} = 5$ cuadros consecutivos afuera Y condición estricta de OBSERVED." + "\n"
            "       Si hay oclusión y el filtro extrapola en PREDICTED, la desescalada se bloquea y trip permanece en True."
        )
    else:
        fsm_text = (
            "Near zone boundaries, a worker operating on the perimeter induces high-frequency detection jitter (chattering)\n"
            "due to keypoint inference noise. Switching a safety relay at 30 Hz physically destroys mechanical contactors\n"
            "within hours and causes repeated erratic machine shutdowns.\n\n"
            "The Architectural Solution: Spatial Schmitt Trigger with Hysteresis Band (Δd = 200 mm):\n"
            r"  • Danger Boundary ($P_{\mathrm{danger}}$): Inner polygon triggering the safety trip state." + "\n"
            r"  • Release Boundary ($P_{\mathrm{release}}$): Outer expanded polygon $P_{\mathrm{release}} = P_{\mathrm{danger}} \oplus 0.20\ \mathrm{m}$. An operator must step" + "\n"
            "    completely outside the 200 mm buffer before de-escalation may initiate.\n"
            "  • Asymmetric Safety Invariant:\n"
            r"    1. FAST ENTRY: Nominal debounce $N_{\mathrm{confirm}} = 3$ frames. But if the perpendicular approach velocity is fast" + "\n"
            r"       ($v_n \geq 1.6\text{ m/s}$ per ISO 13855), an INSTANT DYNAMIC BYPASS drops $N_{\mathrm{confirm}} = 1$ in 19 ms." + "\n"
            r"    2. STRICT EXIT: Demands $N_{\mathrm{release}} = 5$ consecutive outside frames AND an explicit OBSERVED state." + "\n"
            "       During occlusions where Kalman predicts in dead reckoning, de-escalation is blocked (trip remains True)."
        )
    ax.text(0.065, 0.885, fsm_text, fontsize=7.5, color=COLOR_TEXT_MAIN, linespacing=1.30, va="top", zorder=3)

    c2_title = "2. DIAGRAMA DE STATECHARTS ORTOGONALES CONCURRENTES (ADR-009)" if lang == "es" else "2. CONCURRENT ORTHOGONAL STATECHARTS ARCHITECTURE (ADR-009)"
    draw_card(ax, 0.04, 0.365, 0.92, 0.295, c2_title)

    s_ax = ax
    # Left: Schmitt Trigger Polygons
    rel_patch = patches.FancyBboxPatch((0.08, 0.40), 0.34, 0.19, boxstyle="round,pad=0.01,rounding_size=0.01",
                                       facecolor="#FEF3C7", edgecolor="#D97706", lw=1.5, ls="--", zorder=3)
    s_ax.add_patch(rel_patch)
    dan_patch = patches.FancyBboxPatch((0.13, 0.43), 0.24, 0.13, boxstyle="round,pad=0.01,rounding_size=0.01",
                                       facecolor="#FEE2E2", edgecolor="#DC2626", lw=2.0, zorder=4)
    s_ax.add_patch(dan_patch)
    mac_patch = patches.Rectangle((0.18, 0.465), 0.14, 0.06, facecolor="#94A3B8", edgecolor="#334155", lw=1, zorder=5)
    s_ax.add_patch(mac_patch)
    mac_label = "MÁQUINA" if lang == "es" else "MACHINE"
    s_ax.text(0.25, 0.495, mac_label, fontsize=8, fontweight="bold", color="#0F172A", ha="center", va="center", zorder=6)

    lbl_danger = r"$P_{\mathrm{danger}}$ (Límite Peligro)" if lang == "es" else r"$P_{\mathrm{danger}}$ (Danger Boundary)"
    lbl_release = r"$P_{\mathrm{release}}$ (Banda Histéresis $\Delta d = 200\ \mathrm{mm}$)" if lang == "es" else r"$P_{\mathrm{release}}$ (Hysteresis Band $\Delta d = 200\ \mathrm{mm}$)"
    s_ax.text(0.25, 0.438, lbl_danger, fontsize=7.2, fontweight="bold", color="#DC2626", ha="center", zorder=6)
    s_ax.text(0.25, 0.575, lbl_release, fontsize=7.2, fontweight="bold", color="#D97706", ha="center", zorder=6)

    # Right: Orthogonal FSMs
    fsm1 = patches.FancyBboxPatch((0.47, 0.495), 0.47, 0.085, boxstyle="round,pad=0.006,rounding_size=0.008",
                                  facecolor="#F8FAFC", edgecolor="#2563EB", lw=1.2, zorder=3)
    s_ax.add_patch(fsm1)
    fsm1_h = "1. AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)" if lang == "es" else "1. SPATIAL OCCUPANCY AUTOMATON (OccupancyState)"
    s_ax.text(0.485, 0.562, fsm1_h, fontsize=6.8, fontweight="bold", color="#1E3A8A", zorder=4)
    s_ax.text(0.485, 0.520, "OUTSIDE  ──►  ENTER_PENDING  ──►  INSIDE (Trip=True)  ──►  EXIT_PENDING",
              fontsize=6.1, color=COLOR_TEXT_MAIN, zorder=4)

    fsm2 = patches.FancyBboxPatch((0.47, 0.380), 0.47, 0.085, boxstyle="round,pad=0.006,rounding_size=0.008",
                                  facecolor="#F8FAFC", edgecolor="#059669", lw=1.2, zorder=3)
    s_ax.add_patch(fsm2)
    fsm2_h = "2. CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)" if lang == "es" else "2. TEMPORAL DWELL CLASSIFIER (DwellState)"
    s_ax.text(0.485, 0.448, fsm2_h, fontsize=6.8, fontweight="bold", color="#065F46", zorder=4)
    s_ax.text(0.485, 0.405, "NORMAL (t < 5s)  ──►  WARNING (5s ≤ t < 10s)  ──►  VIOLATION (t ≥ 10s)",
              fontsize=6.1, color=COLOR_TEXT_MAIN, zorder=4)

    s_ax.annotate("", xy=(0.70, 0.470), xytext=(0.70, 0.495),
                  arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.5), zorder=5)
    guard_lbl = "Guardia: INSIDE (Invariante Fail-Safe t=0s)" if lang == "es" else "Guard: INSIDE (Fail-Safe Invariant at t=0s)"
    s_ax.text(0.71, 0.478, guard_lbl, fontsize=6.3, color="#DC2626", zorder=5)

    c3_title = "3. CÓDIGO FUENTE: EVALUACIÓN DE HISTÉRESIS Y BYPASS DE APROXIMACIÓN RÁPIDA" if lang == "es" else "3. PRODUCTION SOURCE CODE: HYSTERESIS EVALUATION & FAST APPROACH BYPASS"
    draw_card(ax, 0.04, 0.065, 0.92, 0.285, c3_title)

    if lang == "es":
        code_fsm = """# src/core/spatial_fsm.py (Lógica Schmitt Trigger y Bypass)
def evaluate_occupant(self, track_id: int, pos: PositionEstimate, velocity: np.ndarray) -> Tuple[bool, OccupancyState]:
    point = Point(pos.xy_m)
    in_danger = self._prepared_danger.contains(point)
    in_release = self._prepared_release.contains(point)
    
    # Bypass dinámico ISO 13855: velocidad normal vn >= 1.6 m/s
    vn = np.dot(velocity, self._approach_normal)
    if in_danger and vn >= self.config.iso_k_speed:
        self._confirm_counts[track_id] = self.config.n_confirm  # Bypass inmediato!
        
    # Salvaguarda asimétrica de desescalada (ADR-008):
    if not in_release and pos.status == ObservationStatus.OBSERVED:
        self._release_counts[track_id] += 1
    else:
        self._release_counts[track_id] = 0  # Oclusión o PREDICTED bloquea la salida!"""
    else:
        code_fsm = """# src/core/spatial_fsm.py (Schmitt Trigger & Bypass Logic)
def evaluate_occupant(self, track_id: int, pos: PositionEstimate, velocity: np.ndarray) -> Tuple[bool, OccupancyState]:
    point = Point(pos.xy_m)
    in_danger = self._prepared_danger.contains(point)
    in_release = self._prepared_release.contains(point)
    
    # ISO 13855 dynamic bypass: normal velocity vn >= 1.6 m/s
    vn = np.dot(velocity, self._approach_normal)
    if in_danger and vn >= self.config.iso_k_speed:
        self._confirm_counts[track_id] = self.config.n_confirm  # Instant bypass!
        
    # Asymmetric de-escalation safeguard (ADR-008):
    if not in_release and pos.status == ObservationStatus.OBSERVED:
        self._release_counts[track_id] += 1
    else:
        self._release_counts[track_id] = 0  # Occlusion or PREDICTED blocks de-escalation!"""

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.225, code_fsm, "src/core/spatial_fsm.py")

    fig.savefig(f"/tmp/deck_{lang}_p5.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 6: PRESUPUESTO TEMPORAL BASADO EN ISO 13855 Y ACELERACIÓN EDGE
# ==============================================================================
def render_page_6(pdf, lang: str = "es"):
    ch_title = "06. ISO 13855 y Latencias" if lang == "es" else "06. ISO 13855 & Latency Budget"
    fig, ax = create_base_page(6, 8, ch_title, lang=lang)

    c1_title = "1. MODELO DE SEPARACIÓN TEÓRICO BASADO EN ISO 13855:2024" if lang == "es" else "1. THEORETICAL SEPARATION MODEL BASED ON ISO 13855:2024"
    draw_card(ax, 0.04, 0.680, 0.92, 0.245, c1_title)

    if lang == "es":
        iso_text = (
            "La formulación matemática de la norma ISO 13855:2024 provee el modelo teórico de referencia para calcular distancias\n"
            "mínimas de seguridad S respecto a la velocidad de aproximación humana. El sistema evalúa su pipeline según esta ecuación:\n"
        )
        iso_math = (
            r"$S = (K \cdot T) + C + C_{\mathrm{dyn}} + Z_{\mathrm{extra}}, \qquad "
            r"T = t_1(\mathrm{visi\acute{o}n}) + t_2(\mathrm{PLC}) + t_3(\mathrm{frenado})$"
        )
        iso_desc = (
            "• Constante K: 1600 mm/s (aproximación transversal estándar) y 2000 mm/s (aproximación directa perpendicular).\n"
            r"• Presupuesto Teórico de Visión ($t_1$): Directiva recomendada $t_1 \leq 50$ ms ($\geq 20$ FPS continuos sin caídas)." + "\n"
            r"• Doble Horizonte Temporal (ADR-010):" + "\n"
            r"  1. Latencia de Hardware por Cuadro ($T_{\mathrm{system}}$): $T_{\mathrm{cap}} + T_{\mathrm{pre}} + T_{\mathrm{infer}} + T_{\mathrm{pose}} + T_{\mathrm{geom}} + T_{\mathrm{track}} + T_{\mathrm{fsm}} \approx 18.5 - 20.5\ \mathrm{ms}$." + "\n"
            r"  2. Latencia de Reacción Física del Evento ($T_{\mathrm{event}} = t_{\mathrm{trip}} - t_{\mathrm{physical\_entry}}$):" + "\n"
            r"     - Aproximación normal con debounce ($N_{\mathrm{confirm}} = 3$): $T_{\mathrm{event}} = (3 - 1) \times 33.3\ \mathrm{ms} + 18.5\ \mathrm{ms} = 85.1\ \mathrm{ms}$." + "\n"
            r"     - Aproximación rápida ($v_n \geq 1.6$ m/s): Bypass automático $N_{\mathrm{confirm}} = 1 \rightarrow T_{\mathrm{event}} = T_{\mathrm{system}} \approx 18.5$ ms."
        )
    else:
        iso_text = (
            "The mathematical formulation of ISO 13855:2024 provides the foundational model for calculating minimum\n"
            "safety distance S relative to human approach speed. The vision pipeline is evaluated against this equation:\n"
        )
        iso_math = (
            r"$S = (K \cdot T) + C + C_{\mathrm{dyn}} + Z_{\mathrm{extra}}, \qquad "
            r"T = t_1(\mathrm{vision}) + t_2(\mathrm{PLC}) + t_3(\mathrm{braking})$"
        )
        iso_desc = (
            "• Approach Constant K: 1600 mm/s (transverse approach) and 2000 mm/s (direct perpendicular approach).\n"
            r"• Theoretical Vision Budget ($t_1$): Recommended directive $t_1 \leq 50$ ms ($\geq 20$ FPS continuous sustained)." + "\n"
            r"• Dual Time Horizon (ADR-010):" + "\n"
            r"  1. Hardware Latency per Frame ($T_{\mathrm{system}}$): $T_{\mathrm{cap}} + T_{\mathrm{pre}} + T_{\mathrm{infer}} + T_{\mathrm{pose}} + T_{\mathrm{geom}} + T_{\mathrm{track}} + T_{\mathrm{fsm}} \approx 18.5 - 20.5\text{ ms}$." + "\n"
            r"  2. Physical Event Reaction Latency ($T_{\mathrm{event}} = t_{\mathrm{trip}} - t_{\mathrm{physical\_entry}}$):" + "\n"
            r"     - Nominal approach with debounce ($N_{\mathrm{confirm}} = 3$): $T_{\mathrm{event}} = (3 - 1) \times 33.3\text{ ms} + 18.5\text{ ms} = 85.1\text{ ms}$." + "\n"
            r"     - Fast approach ($v_n \geq 1.6\text{ m/s}$): Dynamic bypass $N_{\mathrm{confirm}} = 1 \rightarrow T_{\mathrm{event}} = T_{\mathrm{system}} \approx 18.5\text{ ms}$."
        )
    ax.text(0.065, 0.885, iso_text, fontsize=7.6, color=COLOR_TEXT_MAIN, va="top", zorder=3)
    ax.text(0.5, 0.835, iso_math, fontsize=8.5, color="#0F172A", ha="center", va="center", zorder=4)
    ax.text(0.065, 0.790, iso_desc, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    c2_title = "2. DESGLOSE CRONOMÉTRICO DE LATENCIAS POR ETAPA DEL PIPELINE" if lang == "es" else "2. GRANULAR LATENCY BUDGET BREAKDOWN PER PIPELINE STAGE"
    draw_card(ax, 0.04, 0.365, 0.92, 0.300, c2_title)

    l_ax = fig.add_axes([0.09, 0.405, 0.37, 0.20])
    stages = ["Captura", "Preproc", "Inferencia", "Keypoints", "Homog", "Kalman", "FSM"] if lang == "es" else ["Capture", "Preproc", "Inference", "Keypoints", "Homog", "Kalman", "FSM"]
    times = [1.2, 0.8, 12.5, 1.8, 0.08, 0.45, 0.04]
    bar_colors = ["#64748B", "#64748B", "#DC2626", "#F59E0B", "#38BDF8", "#10B981", "#8B5CF6"]

    bars = l_ax.barh(stages, times, color=bar_colors, edgecolor="none", height=0.65)
    x_lbl = "Latencia en Milisegundos (ms)" if lang == "es" else "Latency in Milliseconds (ms)"
    l_ax.set_xlabel(x_lbl, fontsize=6.8)
    l_ax.set_xlim(0, 15)
    l_ax.grid(True, axis="x", ls=":", alpha=0.6)
    l_ax.tick_params(labelsize=6.8)
    for bar in bars:
        w = bar.get_width()
        l_ax.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{w:.2f} ms", fontsize=6.5, va="center")

    if lang == "es":
        silicon_text = (
            "ANÁLISIS DE ACELERACIÓN EN SILICIO HETEROGÉNEO:\n\n"
            "• Apple Silicon M1 (arm64 - Desarrollo):\n"
            "  - ONNX Runtime + CoreMLExecutionProvider.\n"
            "  - 346 de 354 operadores delegados nativamente al\n"
            "    Apple Neural Engine (ANE) y GPU unificada.\n"
            "  - Latencia de inferencia: 12.5 ms (p95: 14.1 ms, >60 FPS).\n\n"
            "• NVIDIA GTX 1050 / Pascal CC 6.1 (PoC - Trabajo Futuro):\n"
            "  - Hardware físico disponible seleccionado para validar\n"
            "    portabilidad multiplataforma fuera de Apple Silicon.\n"
            "  - Silicio sin Tensor Cores (FP16 penalizado a 1:64);\n"
            "    requiere cuantización INT8 vía PTQ con TensorRT.\n"
            "  - La prueba de concepto en este silicio queda planificada\n"
            "    como Trabajo Futuro formal."
        )
    else:
        silicon_text = (
            "HETEROGENEOUS SILICON ACCELERATION ANALYSIS:\n\n"
            "• Apple Silicon M1 (arm64 - Development Baseline):\n"
            "  - ONNX Runtime + CoreMLExecutionProvider.\n"
            "  - 346 of 354 operators natively dispatched to Apple\n"
            "    Neural Engine (ANE) and unified GPU.\n"
            "  - Inference latency: 12.5 ms (p95: 14.1 ms, > 60 FPS).\n\n"
            "• NVIDIA GTX 1050 / Pascal CC 6.1 (PoC - Future Work):\n"
            "  - Physical hardware on hand selected to evaluate\n"
            "    cross-platform portability beyond Apple Silicon.\n"
            "  - Silicon lacking Tensor Cores (FP16 penalized 1:64);\n"
            "    requires INT8 quantization via PTQ with TensorRT.\n"
            "  - Empirical PoC validation on this target is scheduled\n"
            "    as formal Future Work."
        )
    ax.text(0.50, 0.620, silicon_text, fontsize=7.0, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    c3_title = "3. CÓDIGO FUENTE: PROFILING DE ALTA RESOLUCIÓN Y CÓMPUTO DE T_EVENT" if lang == "es" else "3. PRODUCTION SOURCE CODE: HIGH-RESOLUTION PROFILING & T_EVENT COMPUTATION"
    draw_card(ax, 0.04, 0.065, 0.92, 0.285, c3_title)

    if lang == "es":
        code_lat = """# src/pipeline/safety_pipeline.py (Profiling de Doble Horizonte)
t_start = time.perf_counter()
t_cap = (time.perf_counter() - t_start) * 1000.0

# Inferencia acelerada en OnnxEngine
t_inf_0 = time.perf_counter()
outputs = self.engine.forward(tensor)
t_inf = (time.perf_counter() - t_inf_0) * 1000.0

# Evaluación cinemática y de lógica espacial
latencies = StageLatencies(
    capture_ms=t_cap, preprocess_ms=t_pre, inference_ms=t_inf,
    keypoint_extract_ms=t_kpt, projection_ms=t_geom,
    tracking_ms=t_track, fsm_evaluation_ms=t_fsm,
    total_t1_ms=t_total_frame, total_system_ms=t_system
)
# Medición del retardo físico total desde la entrada del operario
event_latency_ms = (time.perf_counter() - first_cross_timestamp) * 1000.0 if safety.trip else None"""
    else:
        code_lat = """# src/pipeline/safety_pipeline.py (Dual-Horizon Profiling)
t_start = time.perf_counter()
t_cap = (time.perf_counter() - t_start) * 1000.0

# Accelerated inference via OnnxEngine
t_inf_0 = time.perf_counter()
outputs = self.engine.forward(tensor)
t_inf = (time.perf_counter() - t_inf_0) * 1000.0

# Kinematic tracking and spatial logic evaluation
latencies = StageLatencies(
    capture_ms=t_cap, preprocess_ms=t_pre, inference_ms=t_inf,
    keypoint_extract_ms=t_kpt, projection_ms=t_geom,
    tracking_ms=t_track, fsm_evaluation_ms=t_fsm,
    total_t1_ms=t_total_frame, total_system_ms=t_system
)
# Measure total physical elapsed time since operator entered zone
event_latency_ms = (time.perf_counter() - first_cross_timestamp) * 1000.0 if safety.trip else None"""

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.225, code_lat, "src/pipeline/safety_pipeline.py")

    fig.savefig(f"/tmp/deck_{lang}_p6.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 7: CIERRE DEL GAP SINTÉTICO Y RENDERIZADO PINHOLE FOTORREALISTA
# ==============================================================================
def render_page_7(pdf, lang: str = "es"):
    ch_title = "07. Datos Sintéticos y Gap" if lang == "es" else "07. Synthetic Data & Domain Gap"
    fig, ax = create_base_page(7, 8, ch_title, lang=lang)

    c1_title = "1. EL DOMAIN GAP EN DATOS SINTÉTICOS Y POR QUÉ FALLA EL DIBUJO GEOMÉTRICO (ADR-012)" if lang == "es" else "1. SYNTHETIC DOMAIN GAP & WHY NAIVE GEOMETRIC SHAPES FAIL (ADR-012)"
    draw_card(ax, 0.04, 0.680, 0.92, 0.245, c1_title)

    if lang == "es":
        syn_text = (
            "Para validar determinísticamente un sistema de seguridad se requieren videos con trayectorias repetibles milimétricas.\n"
            "Sin embargo, dibujar figuras geométricas 2D (círculos y rectángulos con cv2) provoca una tasa de detección del 0% en YOLO.\n"
            "Los modelos convolucionales y Transformers entrenados en COCO buscan gradientes de textura real, bordes biológicos y sombras.\n\n"
            "La Solución de Arquitectura: Generador Fotorrealista Pinhole Desacoplado:\n"
            "  1. Single-Identity Tracklet Canónico: Extracción y normalización de un sujeto humano real en lienzo canónico\n"
            "     (160x320 RGBA) con alpha-feathering de 3 px y sombra de contacto elíptica Gaussiana en el suelo.\n"
            "  2. Ley Antropométrica Pinhole: La altura del sujeto en pantalla decae estrictamente con la distancia en Y:\n"
            "     h(Y) = 480 / (1.0 + 0.165 · Y) px, manteniendo resolución óptima (h ∈ [240, 480] px) sin colapso morfológico.\n"
            "  3. Desacoplamiento de UI y Telemetría: Banners de estado reubicados en franjas neutras (y < 56 px y y > 1040 px),\n"
            "     eliminando artefactos parásitos sobre la red neuronal y logrando un 100% de detección con confianza 0.835 - 0.861."
        )
    else:
        syn_text = (
            "Deterministically validating a safety system requires repeatable, millimetric trajectory test videos.\n"
            "However, rendering 2D geometric shapes (circles and rectangles via cv2) causes a 0.0% recall rate with YOLO.\n"
            "Deep convolutional models and Transformers look for biological texture gradients, clothing edges, and floor shadows.\n\n"
            "The Architectural Solution: Decoupled Photorealistic Pinhole Generator:\n"
            "  1. Canonical Single-Identity Tracklet: Extraction and normalization of an authentic human subject onto a canvas\n"
            "     (160x320 RGBA) with 3 px Gaussian alpha-feathering and an elliptical ground contact shadow.\n"
            "  2. Pinhole Anthropometric Law: Screen height decays strictly with world depth distance Y:\n"
            "     h(Y) = 480 / (1.0 + 0.165 · Y) px, preserving optimal resolution (h ∈ [240, 480] px) without morphological collapse.\n"
            "  3. UI & Telemetry Decoupling: Relocating status banners to neutral bands (y < 56 px and y > 1040 px)\n"
            "     eliminates parasitic edge artifacts, achieving 100% recall with confidence 0.835 - 0.861."
        )
    ax.text(0.065, 0.885, syn_text, fontsize=7.5, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    c2_title = "2. MODELO DE ESCALA PERSPECTIVA ESTENOPEICA Y SOMBRAS GAUSSIANAS" if lang == "es" else "2. PINHOLE PERSPECTIVE SCALING MODEL & GAUSSIAN GROUND SHADOWS"
    draw_card(ax, 0.04, 0.365, 0.92, 0.300, c2_title)

    p_ax = fig.add_axes([0.09, 0.405, 0.37, 0.20])
    Y_m = np.linspace(0.5, 6.0, 100)
    h_px = 480.0 / (1.0 + 0.165 * Y_m)

    lbl_max = "Máx: 480 px (Y=0)" if lang == "es" else "Max: 480 px (Y=0)"
    lbl_min = "Mín: 240 px (Y=6)" if lang == "es" else "Min: 240 px (Y=6)"
    p_ax.plot(Y_m, h_px, color="#2563EB", lw=2.5, label=r"$h(Y) = \frac{480}{1.0 + 0.165 Y}$")
    p_ax.axhline(480, color="#64748B", ls="--", lw=1.0, label=lbl_max)
    p_ax.axhline(240, color="#DC2626", ls="--", lw=1.0, label=lbl_min)
    x_lbl_syn = "Distancia al Suelo Y (metros)" if lang == "es" else "World Distance Y (meters)"
    y_lbl_syn = "Altura del Sujeto h (píxeles)" if lang == "es" else "Subject Height h (pixels)"
    p_ax.set_xlabel(x_lbl_syn, fontsize=6.8)
    p_ax.set_ylabel(y_lbl_syn, fontsize=6.8)
    p_ax.grid(True, ls=":", alpha=0.6)
    p_ax.legend(fontsize=6.5)
    p_ax.tick_params(labelsize=6.8)

    if lang == "es":
        syn_res_text = (
            "MÉTRICAS DE RENDIMIENTO SINTÉTICO (BENCHMARKS):\n\n"
            "• Detección Clásica (Geométrica cv2):\n"
            "  - Recall: 0.0% (YOLO no detecta keypoints humanos).\n"
            "  - Validez para pruebas: Nula.\n\n"
            "• Generador Pinhole con Sombras Gaussianas:\n"
            "  - Recall en 600 fotogramas de test: 100.0%.\n"
            "  - Confianza Media de Detección: 0.835 - 0.861.\n"
            "  - Saltos de Identidad en Tracking: 0 (ID único preservado).\n"
            "  - RMSE de Anclaje de Tobillos: < 0.018 m (18 mm).\n\n"
            "Conclusión: Permite testing formal sin depender de actores\n"
            "humanos en planta durante la fase de validación de FSM."
        )
    else:
        syn_res_text = (
            "SYNTHETIC BENCHMARK PERFORMANCE METRICS:\n\n"
            "• Naive Geometric Rendering (cv2 shapes):\n"
            "  - Recall: 0.0% (Zero keypoints detected by YOLO).\n"
            "  - Test Validity: None.\n\n"
            "• Photorealistic Pinhole Generator with Gaussian Shadows:\n"
            "  - Recall across 600 validation frames: 100.0%.\n"
            "  - Mean Detection Confidence: 0.835 - 0.861.\n"
            "  - Track ID Switches: 0 (Strict identity preservation).\n"
            "  - Ankle Ground Anchor RMSE: < 0.018 m (18 mm).\n\n"
            "Conclusion: Enables fully automated regression testing before\n"
            "human validation on plant floors."
        )
    ax.text(0.50, 0.620, syn_res_text, fontsize=7.0, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    c3_title = "3. CÓDIGO FUENTE: COMPOSICIÓN ALFA Y PROYECCIÓN PINHOLE" if lang == "es" else "3. PRODUCTION SOURCE CODE: ALPHA COMPOSITING & PINHOLE SCALING"
    draw_card(ax, 0.04, 0.065, 0.92, 0.285, c3_title)

    if lang == "es":
        code_syn = """# src/utils/synthetic_generator.py (Renderizado Fotorrealista)
def compute_pinhole_scale(y_world_m: float) -> Tuple[int, int]:
    # Calcula dimensiones antropométricas en función de la distancia métrica
    h_px = int(round(480.0 / (1.0 + 0.165 * max(0.0, y_world_m))))
    w_px = int(round(h_px * (160.0 / 320.0)))  # Relación de aspecto canónica 1:2
    return max(w_px, 80), max(h_px, 160)

def render_sprite_with_shadow(frame: np.ndarray, sprite_rgba: np.ndarray, u_coord: int, v_coord: int, scale: float):
    # Sombra de contacto elíptica Gaussiana en Zw = 0
    shadow_w, shadow_h = int(scale * 120), int(scale * 36)
    cv2.ellipse(frame, (u_coord, v_coord), (shadow_w//2, shadow_h//2), 0, 0, 360, (20, 20, 20), -1)
    # Composición alfa canónica con feathering
    alpha = cv2.GaussianBlur(sprite_rgba[:, :, 3], (5, 5), 1.0) / 255.0
    frame[y1:y2, x1:x2] = alpha[:, :, None] * sprite_rgba[:, :, :3] + (1 - alpha[:, :, None]) * frame[y1:y2, x1:x2]"""
    else:
        code_syn = """# src/utils/synthetic_generator.py (Photorealistic Rendering)
def compute_pinhole_scale(y_world_m: float) -> Tuple[int, int]:
    # Compute anthropometric dimensions from world depth distance
    h_px = int(round(480.0 / (1.0 + 0.165 * max(0.0, y_world_m))))
    w_px = int(round(h_px * (160.0 / 320.0)))  # Canonical 1:2 aspect ratio
    return max(w_px, 80), max(h_px, 160)

def render_sprite_with_shadow(frame: np.ndarray, sprite_rgba: np.ndarray, u_coord: int, v_coord: int, scale: float):
    # Gaussian elliptical contact shadow on floor plane (Zw = 0)
    shadow_w, shadow_h = int(scale * 120), int(scale * 36)
    cv2.ellipse(frame, (u_coord, v_coord), (shadow_w//2, shadow_h//2), 0, 0, 360, (20, 20, 20), -1)
    # Canonical alpha compositing with edge feathering
    alpha = cv2.GaussianBlur(sprite_rgba[:, :, 3], (5, 5), 1.0) / 255.0
    frame[y1:y2, x1:x2] = alpha[:, :, None] * sprite_rgba[:, :, :3] + (1 - alpha[:, :, None]) * frame[y1:y2, x1:x2]"""

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.225, code_syn, "src/utils/synthetic_generator.py")

    fig.savefig(f"/tmp/deck_{lang}_p7.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


# ==============================================================================
# PAGE 8: CATÁLOGO COMPLETO DE ADRS Y CRITERIOS ARQUITECTÓNICOS
# ==============================================================================
def render_page_8(pdf, lang: str = "es"):
    ch_title = "08. ADRs y Criterios" if lang == "es" else "08. ADR Catalog & Criteria"
    fig, ax = create_base_page(8, 8, ch_title, lang=lang)

    c1_title = "1. CATÁLOGO COMPLETO DE ARCHITECTURE DECISION RECORDS (ADRs)" if lang == "es" else "1. COMPLETE ARCHITECTURE DECISION RECORD (ADR) CATALOG"
    draw_card(ax, 0.04, 0.465, 0.92, 0.460, c1_title)

    if lang == "es":
        adrs = [
            ("001", "adr-001-yolo-pose-vs-bbox.md", "Keypoints tobillos para anclaje físico inmune a posturas de torso."),
            ("002", "adr-002-homography-vs-3d.md", "Mapeo planar DLT 3x3 determinista (Zw=0) vs redes 3D pesadas."),
            ("003", "adr-003-onnx-coreml.md", "Inferencia desacoplada de PyTorch vía ONNX Runtime (ANE/GPU/INT8)."),
            ("004", "adr-004-spatial-fsm.md", "Schmitt trigger espacial (P_danger vs P_release) contra chattering."),
            ("005", "adr-005-homography-val.md", "Verificación preventiva colinealidad y estabilidad κ(H) < 10^6."),
            ("006", "adr-006-prepared-geoms.md", "Micro-optimizaciones GEOS (C) y bypass a vn ≥ 1.6 m/s (ISO 13855)."),
            ("007", "adr-007-occlusion-handling.md", "Jerarquía degradación: tobillos duales → individual → bbox → Kalman."),
            ("008", "adr-008-kalman-epistemology.md", "Epistemología (OBSERVED/PREDICTED) y bloqueo desescalada ciega."),
            ("009", "adr-009-decoupled-statecharts.md", "Statecharts ortogonales: separación formal ocupación y dwell time."),
            ("010", "adr-010-dual-latency.md", "Doble horizonte temporal: frame (T_system) vs evento físico (T_event)."),
            ("011", "adr-011-mahalanobis-hungarian.md", "Gating Mahalanobis χ²_2 ≤ 9.21, Húngaro O(N³) y Spatial Birth NMS."),
            ("012", "adr-012-synthetic-yolo.md", "Composición fotorrealista pinhole de identidad única para benchmarks."),
        ]
    else:
        adrs = [
            ("001", "adr-001-yolo-pose-vs-bbox.md", "Ankle keypoints for physical ground anchoring immune to torso posture."),
            ("002", "adr-002-homography-vs-3d.md", "Deterministic 3x3 DLT planar mapping (Zw=0) vs heavy monocular 3D networks."),
            ("003", "adr-003-onnx-coreml.md", "Decoupled PyTorch inference via ONNX Runtime (ANE / GPU / INT8 PTQ)."),
            ("004", "adr-004-spatial-fsm.md", "Spatial Schmitt Trigger (P_danger vs P_release) to eliminate contactor chattering."),
            ("005", "adr-005-homography-val.md", "Collinearity checks and projective numerical stability validation κ(H) < 10^6."),
            ("006", "adr-006-prepared-geoms.md", "GEOS (C) micro-optimizations and instant bypass at vn ≥ 1.6 m/s (ISO 13855)."),
            ("007", "adr-007-occlusion-handling.md", "Graceful degradation hierarchy: dual ankles → single ankle → bbox → Kalman."),
            ("008", "adr-008-kalman-epistemology.md", "Epistemic states (OBSERVED/PREDICTED) and inhibition of blind de-escalation."),
            ("009", "adr-009-decoupled-statecharts.md", "Orthogonal statecharts: formal decoupling of spatial occupancy and dwell time."),
            ("010", "adr-010-dual-latency.md", "Dual time horizons: per-frame hardware latency (T_system) vs physical event (T_event)."),
            ("011", "adr-011-mahalanobis-hungarian.md", "Mahalanobis gating χ²_2 ≤ 9.21, Hungarian matching O(N³), and Spatial Birth NMS."),
            ("012", "adr-012-synthetic-yolo.md", "Photorealistic pinhole single-identity compositing for regression testing."),
        ]

    table_top = 0.885
    row_height = 0.029

    th_box = patches.Rectangle((0.065, table_top - 0.024), 0.87, 0.024, facecolor="#1E293B", edgecolor="none", zorder=3)
    ax.add_patch(th_box)
    ref_col = "REFERENCIA / ARCHIVO" if lang == "es" else "REFERENCE / FILE"
    dec_col = "DECISIÓN ARQUITECTÓNICA & IMPACTO INDUSTRIAL" if lang == "es" else "ARCHITECTURAL DECISION & INDUSTRIAL IMPACT"
    ax.text(0.08, table_top - 0.012, "ADR", fontsize=7.2, fontweight="bold", color="#38BDF8", va="center", zorder=4)
    ax.text(0.145, table_top - 0.012, ref_col, fontsize=7.2, fontweight="bold", color="#38BDF8", va="center", zorder=4)
    ax.text(0.42, table_top - 0.012, dec_col, fontsize=7.2, fontweight="bold", color="#38BDF8", va="center", zorder=4)

    y_cur = table_top - 0.026
    for idx, (num, path, desc) in enumerate(adrs):
        row_bg = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        r_box = patches.Rectangle((0.065, y_cur - row_height), 0.87, row_height, facecolor=row_bg, edgecolor="#E2E8F0", lw=0.5, zorder=3)
        ax.add_patch(r_box)

        ax.text(0.08, y_cur - row_height/2, f"ADR-{num}", fontsize=7.0, fontweight="bold", color="#0F172A", va="center", zorder=4)
        ax.text(0.145, y_cur - row_height/2, path, fontsize=6.2, color="#2563EB", family="monospace", va="center", zorder=4)
        ax.text(0.42, y_cur - row_height/2, desc, fontsize=6.4, color=COLOR_TEXT_MAIN, va="center", zorder=4)
        y_cur -= row_height

    c2_title = "2. PREGUNTAS FUNDAMENTALES Y CRITERIOS DE DISEÑO ARQUITECTÓNICO" if lang == "es" else "2. FUNDAMENTAL ARCHITECTURAL QUESTIONS & DESIGN CRITERIA"
    draw_card(ax, 0.04, 0.065, 0.92, 0.385, c2_title)

    if lang == "es":
        qa_items = [
            (r"¿Por qué homografía planar 3x3 y no un modelo de Deep Learning monocular 3D?",
             r"Al fijar $Z_w = 0$ con tobillos, la geometría euclidiana resuelve el espacio con precisión milimétrica en < 0.05 ms con 8 grados de libertad deterministas, sin consumir VRAM ni sufrir alucinaciones de profundidad."),
            (r"¿Por qué un sistema de 4 puntos de calibración tiene siempre RMSE = 0?",
             r"4 puntos aportan 8 ecuaciones independientes para 8 incógnitas (grados de libertad de $\mathbf{H}$). El sistema es matemáticamente determinado sin grados de libertad sobrantes; para evaluar residuo real se requiere $N > 4$."),
            (r"¿Cómo se evita que un operario trabajando en el borde destruya contactores por chattering?",
             r"Mediante un Schmitt Trigger espacial: se entra al cruzar $P_{\mathrm{danger}}$ pero no se sale hasta cruzar $P_{\mathrm{release}}$ (buffer de 200 mm). Entrada rápida (19 ms a velocidad $v_n\geq1.6$ m/s) y salida que exige 5 cuadros con OBSERVED."),
            (r"¿Por qué está prohibido permitir la desescalada de alarma durante el estado PREDICTED de Kalman?",
             "PREDICTED representa extrapolación matemática ciega por oclusión. Desactivar una parada sin confirmación sensorial física viola el principio Fail-Safe: ante falta de fotones ópticos frescos, el relé permanece en disparo."),
            (r"¿Cuál es la diferencia entre $T_{\mathrm{system}}$ y $T_{\mathrm{event}}$ bajo las directivas de ISO 13855?",
             r"$T_{\mathrm{system}}$ es la latencia de hardware por frame (~19 ms). $T_{\mathrm{event}}$ es el retardo físico real desde que el cuerpo cruza la línea hasta que el relé abre (~85 ms en paso normal con debounce, y ~19 ms en bypass por aproximación rápida).")
        ]
    else:
        qa_items = [
            (r"Why planar 3x3 homography instead of a deep monocular 3D neural network?",
             r"By enforcing $Z_w = 0$ through ankle contact, Euclidean geometry resolves world space with millimetric accuracy in < 0.05 ms using 8 deterministic degrees of freedom—consuming zero VRAM and avoiding depth hallucinations."),
            (r"Why does a 4-point calibration system always produce RMSE = 0?",
             r"4 points yield 8 independent equations for 8 unknowns (the degrees of freedom of $\mathbf{H}$). The system is mathematically determined with no surplus constraints; evaluating true empirical error requires $N > 4$."),
            (r"How do you prevent an operator working on the boundary from destroying contactors via chattering?",
             r"Through a spatial Schmitt Trigger: entry trips at $P_{\mathrm{danger}}$, but de-escalation requires crossing outside $P_{\mathrm{release}}$ (200 mm buffer). Fast entry (19 ms at approach speed $v_n\geq1.6$ m/s); exit requires 5 OBSERVED frames."),
            (r"Why is de-escalation prohibited while the Kalman filter is in the PREDICTED state?",
             "PREDICTED represents blind mathematical dead reckoning during an occlusion. De-escalating safety without sensor confirmation violates the Fail-Safe principle: lacking fresh optical photons, the trip relay remains engaged."),
            (r"What is the difference between $T_{\mathrm{system}}$ and $T_{\mathrm{event}}$ under ISO 13855 directives?",
             r"$T_{\mathrm{system}}$ is the per-frame hardware processing latency (~19 ms). $T_{\mathrm{event}}$ is the total physical elapsed time from when the body crosses the boundary until the relay trips (~85 ms with debounce, ~19 ms under fast approach bypass).")
        ]

    qa_top = 0.405
    for q, a in qa_items:
        ax.text(0.065, qa_top, f"• {q}", fontsize=7.0, fontweight="bold", color="#1E3A8A", va="top", zorder=3)
        wrapped_a = textwrap.fill(a, width=105)
        ans_prefix = "R: " if lang == "es" else "A: "
        ax.text(0.08, qa_top - 0.014, f"{ans_prefix}{wrapped_a}", fontsize=6.3, color=COLOR_TEXT_MAIN, linespacing=1.20, va="top", zorder=3)
        qa_top -= 0.068

    fig.savefig(f"/tmp/deck_{lang}_p8.png", dpi=120)
    pdf.savefig(fig)
    plt.close(fig)


def generate_deck(output_path: Path, lang: str = "es"):
    lang_name = "Español" if lang == "es" else "English"
    print(f"[*] Generando Guía de Estudio de Arquitectura ({lang_name})...")
    print(f"[*] Destino: {output_path}")

    with PdfPages(output_path) as pdf:
        print("  - Renderizando Página 1: Portada, Filosofía y Tesis End-to-End...")
        render_page_1(pdf, lang=lang)
        print("  - Renderizando Página 2: Geometría Proyectiva y Homografía Planar (Zw = 0)...")
        render_page_2(pdf, lang=lang)
        print("  - Renderizando Página 3: Percepción Pura y Anclaje Anatómico en Tobillos...")
        render_page_3(pdf, lang=lang)
        print("  - Renderizando Página 4: Cinemática Bayesiana, Filtro de Kalman y Gating...")
        render_page_4(pdf, lang=lang)
        print("  - Renderizando Página 5: Schmitt Trigger Espacial y Statecharts Ortogonales...")
        render_page_5(pdf, lang=lang)
        print("  - Renderizando Página 6: Presupuesto Temporal ISO 13855 y Aceleración Edge...")
        render_page_6(pdf, lang=lang)
        print("  - Renderizando Página 7: Cierre del Synthetic Domain Gap y Pinhole...")
        render_page_7(pdf, lang=lang)
        print("  - Renderizando Página 8: Catálogo Completo de ADRs y Criterios Arquitectónicos...")
        render_page_8(pdf, lang=lang)

    file_size_kb = os.path.getsize(output_path) / 1024.0
    print(f"[✓] PDF generado con éxito ({lang_name}): {output_path} ({file_size_kb:.1f} KB, 8 páginas)")


def main():
    parser = argparse.ArgumentParser(description="Generate Edge Safety Guard Architecture Study Guides (PDF Carousel)")
    parser.add_argument("--lang", choices=["es", "en", "all"], default="all", help="Language to generate (es, en, all)")
    args = parser.parse_args()

    os.makedirs(DOCS_DIR, exist_ok=True)

    if args.lang in ["es", "all"]:
        generate_deck(OUTPUT_PDF_ES, lang="es")
    if args.lang in ["en", "all"]:
        generate_deck(OUTPUT_PDF_EN, lang="en")


if __name__ == "__main__":
    main()
