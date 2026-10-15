#!/usr/bin/env python3
"""
scripts/generate_study_pdf.py
Generates the comprehensive Architecture & Engineering Study Guide PDF
for Edge Safety Guard (Vision-Based Restricted Zone Monitoring).

Complies with ISO 13855:2024, IEC 61496, ISO 13849-1 standards.
Includes mathematical derivations, architectural diagrams, vector plots,
real codebase snippets, and the complete ADR catalog.
"""

import os
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages

DOCS_DIR = Path("/Users/xander/Projects/edge-safety-guard/docs")
OUTPUT_PDF = DOCS_DIR / "guia-estudio-arquitectura.local.pdf"

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

def create_base_page(page_num: int, total_pages: int, chapter_title: str):
    fig = plt.figure(figsize=(PAGE_WIDTH, PAGE_HEIGHT), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Header Bar
    header_rect = patches.Rectangle((0, 0.94), 1, 0.06, facecolor=COLOR_HEADER_BG, edgecolor="none", zorder=1)
    ax.add_patch(header_rect)

    ax.text(0.04, 0.965, "EDGE VISION SAFETY GUARD", fontsize=10, fontweight="bold", color="#38BDF8", va="center")
    ax.text(0.32, 0.965, "|  Guía Maestra de Estudio de Arquitectura", fontsize=9, color="#94A3B8", va="center")
    ax.text(0.96, 0.965, chapter_title.upper(), fontsize=8.5, fontweight="bold", color="#F8FAFC", ha="right", va="center")

    # Footer Bar
    ax.plot([0.04, 0.96], [0.038, 0.038], color=COLOR_CARD_BORDER, lw=0.8)
    ax.text(0.04, 0.022, "Senior Architecture & Systems Engineering (Concepts > Code)  •  ISO 13855:2024 / IEC 61496",
            fontsize=7.2, color=COLOR_TEXT_MUTED, va="center")
    ax.text(0.96, 0.022, f"Página {page_num} de {total_pages}", fontsize=7.8, fontweight="bold", color=COLOR_TEXT_MAIN, ha="right", va="center")

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
        ax.text(x + 0.02, y + h - 0.022, title, fontsize=8.5, fontweight="bold", color=COLOR_HEADER_BG, va="top", zorder=3)
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
def render_page_1(pdf):
    fig, ax = create_base_page(1, 8, "01. Filosofía y Tesis")

    banner = patches.FancyBboxPatch(
        (0.04, 0.775), 0.92, 0.145,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        facecolor="#0B132B",
        edgecolor="#1C2541",
        linewidth=1.5,
        zorder=2
    )
    ax.add_patch(banner)

    ax.text(0.07, 0.88, "EDGE VISION SAFETY GUARD", fontsize=17, fontweight="bold", color="#F8FAFC", zorder=3)
    ax.text(0.07, 0.845, "Manual de Estudio de Arquitectura de Sistemas Críticos en Tiempo Real", fontsize=10.5, color="#38BDF8", zorder=3)
    ax.text(0.07, 0.81, "Diseño Guiado por la Física, Geometría Planar y Estándares de Seguridad Industrial (ISO 13855 / IEC 61496)",
            fontsize=8.0, color="#94A3B8", zorder=3)

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
        bpatch = patches.FancyBboxPatch((bx, 0.745), bw, 0.020, boxstyle="round,pad=0.003,rounding_size=0.005",
                                        facecolor=col, edgecolor="none", zorder=3)
        ax.add_patch(bpatch)
        ax.text(bx + bw/2, 0.755, text, fontsize=6.5, fontweight="bold", color="#FFFFFF", ha="center", va="center", zorder=4)
        bx += bw + 0.010

    draw_card(ax, 0.04, 0.525, 0.92, 0.205, "1. LA GRAN TESIS DEL PROYECTO (Senior Architecture: Concepts > Code)")

    quote_box = patches.Rectangle((0.065, 0.655), 0.87, 0.030, facecolor="#EFF6FF", edgecolor="#3B82F6", linewidth=1.0, zorder=3)
    ax.add_patch(quote_box)
    ax.text(0.5, 0.670, '"No todos los problemas de un sistema de Inteligencia Artificial se resuelven con más Inteligencia Artificial."',
            fontsize=7.8, fontweight="bold", style="italic", color="#1E3A8A", ha="center", va="center", zorder=4)

    t1_text = (
        "En el desarrollo de software actual existe la tentación de concebir las redes neuronales como 'cajas negras' universales:\n"
        "pretender entrenar modelos para inferir si un operario 'comete una infracción' o 'cuánto tiempo lleva dentro de una zona'.\n"
        "Ese enfoque es estocástico, opaco, computacionalmente ineficiente y no auditable bajo normas de seguridad funcional.\n\n"
        "Este proyecto demuestra un diseño de Senior Architect separando el problema en cuatro capas ortogonales y deterministas:\n"
        "  1. La IA se restringe a Percepción Pura: Detectar únicamente coordenadas de tobillos anatómicos en el espacio de píxeles.\n"
        "  2. La Geometría resuelve el Espacio: Transformación planar proyectiva homográfica 3x3 al plano del suelo (Zw = 0).\n"
        "  3. La Cinemática resuelve la Incertidumbre: Filtro de Kalman 2D continuo con compuertas elipsoidales de Mahalanobis.\n"
        "  4. La Lógica Determinista toma las Decisiones: Statecharts ortogonales concurrentes ejecutados en < 0.05 ms por cuadro."
    )
    ax.text(0.065, 0.640, t1_text, fontsize=7.3, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    draw_card(ax, 0.04, 0.065, 0.92, 0.445, "2. ARQUITECTURA EN CAPAS: EL FLUJO END-TO-END")

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

    col_w = 0.205
    col_gap = 0.02
    start_x = 0.065
    y_top = 0.465

    for i, (title, header_bg, accent_c, items) in enumerate(layers):
        cx = start_x + i * (col_w + col_gap)
        c_box = patches.FancyBboxPatch((cx, y_top - 0.27), col_w, 0.27, boxstyle="round,pad=0.006,rounding_size=0.008",
                                       facecolor="#F1F5F9", edgecolor="#CBD5E1", lw=1.0, zorder=3)
        ax.add_patch(c_box)

        h_box = patches.FancyBboxPatch((cx, y_top - 0.034), col_w, 0.034, boxstyle="round,pad=0.005,rounding_size=0.006",
                                       facecolor=header_bg, edgecolor="none", zorder=4)
        ax.add_patch(h_box)
        ax.text(cx + col_w/2, y_top - 0.017, title, fontsize=7.8, fontweight="bold", color=accent_c, ha="center", va="center", zorder=5)

        iy = y_top - 0.052
        for item in items:
            ibox = patches.FancyBboxPatch((cx + 0.006, iy - 0.038), col_w - 0.012, 0.038,
                                          boxstyle="round,pad=0.003,rounding_size=0.005",
                                          facecolor="#FFFFFF", edgecolor="#E2E8F0", lw=0.8, zorder=4)
            ax.add_patch(ibox)
            ax.text(cx + col_w/2, iy - 0.019, item, fontsize=6.8, color=COLOR_TEXT_MAIN, ha="center", va="center", zorder=5)
            iy -= 0.048

        if i < 3:
            arrow_x = cx + col_w + 0.003
            ax.annotate("", xy=(arrow_x + col_gap - 0.006, y_top - 0.135), xytext=(arrow_x, y_top - 0.135),
                        arrowprops=dict(arrowstyle="->", color="#64748B", lw=1.8), zorder=6)

    prof_box = patches.FancyBboxPatch((0.065, 0.09), 0.87, 0.075, boxstyle="round,pad=0.008,rounding_size=0.008",
                                     facecolor="#1E293B", edgecolor="#334155", lw=1.0, zorder=3)
    ax.add_patch(prof_box)
    ax.text(0.08, 0.145, "PERFORMANCE PROFILER & SAFETY INTEGRITY HORIZONS (ORTOGONAL):", fontsize=7.8, fontweight="bold", color="#38BDF8", zorder=4)
    prof_desc = (
        "• T_system (Hardware / Frame): T_capture + T_pre + T_infer + T_pose + T_geom + T_track + T_fsm ≈ 18.5 - 20.5 ms por cuadro.\n"
        "• T_event (Respuesta Física Total): Paso normal con debounce (N_confirm=3) ≈ 81.7 ms  |  Aproximación rápida (vn ≥ 1.6 m/s) bypass = 19 ms."
    )
    ax.text(0.08, 0.128, prof_desc, fontsize=6.8, color="#E2E8F0", linespacing=1.35, va="top", zorder=4)

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p1.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 2: GEOMETRÍA PROYECTIVA Y HOMOGRAFÍA PLANAR (Zw = 0)
# ==============================================================================
def render_page_2(pdf):
    fig, ax = create_base_page(2, 8, "02. Geometría y Homografía")

    draw_card(ax, 0.04, 0.70, 0.92, 0.22, "1. EL COLAPSO DE PERSPECTIVA: RESTRICCIÓN PLANAR (Zw = 0)")

    geo_text = (
        "Una cámara monocular 2D pierde intrínsecamente la coordenada de profundidad Z: infinitos puntos a lo largo del rayo proyectan\n"
        "al mismo píxel (u, v). La matriz general de proyección de cámara es de dimension 3x4:\n"
    )
    ax.text(0.065, 0.885, geo_text, fontsize=7.8, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    math_eq = (
        r" \cdot [u, v, 1]^T = \mathbf{P}_{3 \times 4} [X_w, Y_w, 0, 1]^T \Rightarrow "
        r"s \cdot [u, v, 1]^T = \mathbf{H}_{3 \times 3} [X_w, Y_w, 1]^T \Leftrightarrow "
        r"[X_w, Y_w, 1]^T = \mathbf{H}^{-1} (s \cdot [u, v, 1]^T)$"
    )
    ax.text(0.5, 0.825, math_eq, fontsize=8.5, color="#0F172A", ha="center", va="center", zorder=4)

    geo_explain = (
        "Al rastrear exclusivamente los tobillos apoyados sobre el suelo, fijamos físicamente Zw = 0. La tercera columna de proyección\n"
        "se anula matemáticamente, colapsando el sistema a una matriz H invertible de 3x3. Esto permite transformar píxeles a metros\n"
        "reales mediante álgebra lineal pura en menos de 0.05 ms, sin recurrir a costosos sensores LiDAR o cámaras estéreo."
    )
    ax.text(0.065, 0.77, geo_explain, fontsize=7.5, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    draw_card(ax, 0.04, 0.44, 0.92, 0.245, "2. ALGORITMO DLT, GRADOS DE LIBERTAD Y CONDICIONAMIENTO")

    dlt_text = (
        "• Grados de Libertad: La matriz H posee 9 coeficientes, pero al estar definida en coordenadas homogéneas proyectivas hasta\n"
        "  un factor de escala arbitrario (H y λH representan la misma transformación), tiene exactamente 9 - 1 = 8 grados de libertad.\n"
        "• Determinación Exacta: Cada correspondencia de punto (u, v) ↔ (X, Y) genera 2 ecuaciones lineales algebraicamente independientes.\n"
        "  Con exactamente 4 puntos coplanares no colineales, se forma un sistema determinado de 8x8 con residuo RMSE = 0.00 m.\n"
        "• Calibración Sobredeterminada (N > 4): Para medir error real de reproyección se requieren N > 4 marcadores o puntos de test.\n"
        "• Verificación de Colinealidad: En N = 4, ningún triplete puede ser colineal (Área(Δ) > ε). En N > 4, se exige rango afín pleno (rank=3)\n"
        "  y la existencia de al menos un cuadrilátero no degenerado para evitar falsos rechazos en perímetros rectangulares."
    )
    ax.text(0.065, 0.65, dlt_text, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    cond_box = patches.Rectangle((0.065, 0.455), 0.87, 0.040, facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=1, zorder=3)
    ax.add_patch(cond_box)
    cond_math = (
        r"$\kappa(\mathbf{H}) = \frac{\sigma_{\max}(\mathbf{H})}{\sigma_{\min}(\mathbf{H})} < 10^6 \quad \mathrm{(Límite\ de\ Estabilidad)} "
        r"\qquad \mathrm{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N \|\mathbf{X}_i - \mathbf{H}^{-1}\mathbf{x}_i\|^2} \leq 0.05\mathrm{ m}$"
    )
    ax.text(0.5, 0.475, cond_math, fontsize=8.2, color="#0F172A", ha="center", va="center", zorder=4)

    draw_card(ax, 0.04, 0.065, 0.92, 0.36, "3. CÓDIGO FUENTE REAL: VALIDACIÓN Y PROYECCIÓN VECTORIZADA")

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

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.285, code_homography, "src/core/homography.py")

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p2.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 3: PERCEPCIÓN PURA Y ANCLAJE ANATÓMICO (KEYPOINTS VS BBOX)
# ==============================================================================
def render_page_3(pdf):
    fig, ax = create_base_page(3, 8, "03. Percepción y Anclaje")

    draw_card(ax, 0.04, 0.655, 0.92, 0.265, "1. EL ENGAÑO DEL BOUNDING BOX VS ANCLAJE EN TOBILLOS (ADR-001)")

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
    ax.text(0.065, 0.885, p3_text, fontsize=7.6, color=COLOR_TEXT_MAIN, linespacing=1.32, va="top", zorder=3)

    eq_anchor = (
        r"{\mathrm{ground}} = \frac{p_{\mathrm{ankle\_left}} + p_{\mathrm{ankle\_right}}}{2} \quad "
        r"\mathrm{si\ } \min(\mathrm{conf}_L, \mathrm{conf}_R) \geq 0.30$"
    )
    ax.text(0.5, 0.68, eq_anchor, fontsize=8.8, color="#0F172A", ha="center", va="center", zorder=4)

    draw_card(ax, 0.04, 0.38, 0.92, 0.26, "2. DIAGRAMA COMPARATIVO: DEFORMACIÓN DE BBOX ANTE TORSO INCLINADO")

    d_ax = ax
    d_ax.plot([0.10, 0.45], [0.42, 0.42], color="#334155", lw=2, zorder=3)
    d_ax.text(0.12, 0.405, "Piso Físico (Zw = 0)", fontsize=7.2, color=COLOR_TEXT_MUTED, zorder=3)

    d_ax.plot([0.18, 0.20], [0.42, 0.47], color="#1E293B", lw=3, zorder=4)
    d_ax.plot([0.20, 0.32], [0.47, 0.55], color="#1E293B", lw=3, zorder=4)
    d_ax.plot([0.32, 0.38], [0.55, 0.53], color="#1E293B", lw=2.5, zorder=4)
    d_ax.plot(0.34, 0.58, "o", color="#1E293B", ms=8, zorder=4)

    d_ax.plot(0.18, 0.42, "o", color="#16A34A", ms=8, zorder=6)
    d_ax.text(0.18, 0.44, "Tobillos (Real)", fontsize=7.5, fontweight="bold", color="#16A34A", ha="center", zorder=6)

    bbox_rect = patches.Rectangle((0.15, 0.42), 0.25, 0.19, fill=False, edgecolor="#DC2626", ls="--", lw=1.5, zorder=5)
    d_ax.add_patch(bbox_rect)
    d_ax.plot(0.275, 0.42, "x", color="#DC2626", ms=9, mew=2.5, zorder=6)
    d_ax.text(0.275, 0.435, "Bbox Bottom (Error)", fontsize=7.5, fontweight="bold", color="#DC2626", ha="center", zorder=6)

    d_ax.plot([0.24, 0.24], [0.40, 0.60], color="#EF4444", lw=2, ls=":", zorder=5)
    d_ax.text(0.245, 0.59, "Límite Zona Peligro", fontsize=7.2, color="#EF4444", zorder=5)

    comp_text = (
        "ANÁLISIS DE ERROR GEOMÉTRICO:\n"
        "• El operario tiene los pies afuera de la zona (x = 0.18 m).\n"
        "• El Bounding Box se ensancha hacia la derecha por el torso y brazos inclinados.\n"
        "• La base del Bbox calcula x = 0.275 m → DENTRO DE PELIGRO (Falso Positivo).\n"
        "• El Keypoint de tobillos calcula x = 0.18 m → FUERA DE PELIGRO (Correcto).\n"
        "• Resultado: Cero falsas paradas ante posturas corporales o herramientas."
    )
    d_ax.text(0.50, 0.58, comp_text, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.32, va="top", zorder=4)

    draw_card(ax, 0.04, 0.065, 0.92, 0.30, "3. CÓDIGO FUENTE: JERARQUÍA DE DEGRADACIÓN DE ANCLAJE (ADR-007)")

    code_anchor = """# src/pipeline/safety_pipeline.py (Extracción de Anclaje Robusto)
def extract_ground_anchor(kpts: np.ndarray, bbox: Tuple[float, ...]) -> Tuple[Tuple[float, float], AnchorSource, float]:
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

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_anchor, "src/pipeline/safety_pipeline.py")

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p3.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 4: CINEMÁTICA BAYESIANA, FILTRO DE KALMAN 2D Y ASOCIACIÓN HÚNGARA
# ==============================================================================
def render_page_4(pdf):
    fig, ax = create_base_page(4, 8, "04. Cinemática y Tracking")

    draw_card(ax, 0.04, 0.69, 0.92, 0.23, "1. FILTRO DE KALMAN 2D: VELOCIDAD CONSTANTE Y COVARIANZAS")

    k_text = (
        "El jitter de detección en píxeles produce saltos estocásticos de posición métrica de ±15 mm. El Filtro de Kalman 2D\n"
        "estima el vector de estado cinemático continuo x = [X, Y, vx, vy]^T en coordenadas del mundo real:\n"
    )
    ax.text(0.065, 0.885, k_text, fontsize=7.6, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    math_kalman = (
        r"$\mathbf{x}_k = [X, Y, v_x, v_y]^T, \quad "
        r"\mathbf{x}_k = \mathbf{F}(\Delta t) \mathbf{x}_{k-1} + \mathbf{w}_k, \quad "
        r"\mathbf{z}_k = \mathbf{H}_{obs} \mathbf{x}_k + \mathbf{v}_k$"
    )
    ax.text(0.5, 0.835, math_kalman, fontsize=8.5, color="#0F172A", ha="center", va="center", zorder=4)

    k_eq2 = (
        r"$\mathbf{P}_k^- = \mathbf{F} \mathbf{P}_{k-1} \mathbf{F}^T + \mathbf{Q}, \quad "
        r"\mathbf{K}_k = \mathbf{P}_k^- \mathbf{H}^T (\mathbf{H} \mathbf{P}_k^- \mathbf{H}^T + \mathbf{R})^{-1}, \quad "
        r"\hat{\mathbf{x}}_k = \hat{\mathbf{x}}_k^- + \mathbf{K}_k (\mathbf{z}_k - \mathbf{H}\hat{\mathbf{x}}_k^-)$"
    )
    ax.text(0.5, 0.785, k_eq2, fontsize=8.2, color="#0F172A", ha="center", va="center", zorder=4)

    k_epist = (
        "• Epistemología de Estados (ADR-008): Cada estimación registra su frescura: OBSERVED (fotón óptico fresco k=0),\n"
        "  PREDICTED (dead reckoning seguro 1 ≤ k ≤ 3, ≤ 100 ms) y STALE (divergencia no segura k ≥ 4, relé bloqueado)."
    )
    ax.text(0.065, 0.74, k_epist, fontsize=7.4, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    draw_card(ax, 0.04, 0.375, 0.92, 0.30, "2. GATING ELIPSOIDAL DE MAHALANOBIS Y ASIGNACIÓN GLOBAL HÚNGARA (ADR-011)")

    sub_ax = fig.add_axes([0.075, 0.395, 0.30, 0.22])
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
    sub_ax.text(0.52, 0.46, "Track (x, y)", fontsize=7, fontweight="bold")
    sub_ax.text(0.86, 0.77, "Vector v", fontsize=7.2, fontweight="bold", color="#1E293B")
    sub_ax.set_title("Elipsoide de Innovación Mahalanobis", fontsize=7.2, fontweight="bold", pad=2)
    sub_ax.legend(fontsize=6.2, loc="lower right")
    sub_ax.axis("equal")
    sub_ax.grid(True, ls=":", alpha=0.5)

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
    ax.text(0.42, 0.635, mot_text, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    draw_card(ax, 0.04, 0.065, 0.92, 0.295, "3. CÓDIGO FUENTE: PREDICCIÓN, ACTUALIZACIÓN Y GATING DE INNOVACIÓN")

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

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_kalman, "src/core/kalman_filter.py")

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p4.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 5: SCHMITT TRIGGER ESPACIAL Y STATECHARTS ORTOGONALES
# ==============================================================================
def render_page_5(pdf):
    fig, ax = create_base_page(5, 8, "05. FSM y Lógica de Seguridad")

    draw_card(ax, 0.04, 0.67, 0.92, 0.25, "1. EL PROBLEMA DEL CHATTERING Y EL SCHMITT TRIGGER ESPACIAL (ADR-004)")

    fsm_text = (
        "En los límites de una zona de seguridad, un operario trabajando en el borde genera micro-oscilaciones de detección (chattering)\n"
        "debido al ruido de inferencia de keypoints. Conmutar un relé de parada a 30 Hz destruye físicamente los contactores mecánicos\n"
        "de la máquina en cuestión de horas y causa paradas erráticas continuas.\n\n"
        "La Solución Arquitectónica: Schmitt Trigger con Banda de Histéresis Espacial (Δd = 200 mm):\n"
        "  • Límite de Peligro (P_danger): Polígono interior que activa la conmutación a peligro.\n"
        "  • Límite de Liberación (P_release): Polígono exterior expandido P_release = P_danger ⊕ 0.20 m. El operario debe cruzar\n"
        "    completamente fuera del buffer de 200 mm para que el sistema considere iniciar la desescalada.\n"
        "  • Asimetría de Seguridad:\n"
        "    1. ENTRADA RÁPIDA: Debounce normal N_confirm = 3 cuadros. Pero si el vector de aproximación perpendicular\n"
        "       es rápido (vn ≥ 1.6 m/s según ISO 13855), se produce un BYPASS DINÁMICO INSTANTÁNEO a N_confirm = 1 en 19 ms.\n"
        "    2. SALIDA ESTRICTA: Exige N_release = 5 cuadros consecutivos afuera Y condición estricta de OBSERVED.\n"
        "       Si hay oclusión y el filtro extrapola en PREDICTED, la desescalada se bloquea y trip permanece en True."
    )
    ax.text(0.065, 0.885, fsm_text, fontsize=7.5, color=COLOR_TEXT_MAIN, linespacing=1.3, va="top", zorder=3)

    draw_card(ax, 0.04, 0.370, 0.92, 0.285, "2. DIAGRAMA DE STATECHARTS ORTOGONALES CONCURRENTES (ADR-009)")

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
    s_ax.text(0.25, 0.495, "MÁQUINA", fontsize=8, fontweight="bold", color="#0F172A", ha="center", va="center", zorder=6)

    s_ax.text(0.25, 0.438, "P_danger (Límite Peligro)", fontsize=7.2, fontweight="bold", color="#DC2626", ha="center", zorder=6)
    s_ax.text(0.25, 0.575, "P_release (Banda Histéresis Δd = 200 mm)", fontsize=7.2, fontweight="bold", color="#D97706", ha="center", zorder=6)

    # Right: Orthogonal FSMs (Lowered to avoid title collision)
    fsm1 = patches.FancyBboxPatch((0.48, 0.50), 0.45, 0.09, boxstyle="round,pad=0.006,rounding_size=0.008",
                                  facecolor="#F8FAFC", edgecolor="#2563EB", lw=1.2, zorder=3)
    s_ax.add_patch(fsm1)
    s_ax.text(0.50, 0.575, "1. AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)", fontsize=7.0, fontweight="bold", color="#1E3A8A", zorder=4)
    s_ax.text(0.50, 0.530, "OUTSIDE  ──►  ENTER_PENDING  ──►  INSIDE (Trip=True)  ──►  EXIT_PENDING",
              fontsize=6.6, color=COLOR_TEXT_MAIN, zorder=4)

    fsm2 = patches.FancyBboxPatch((0.48, 0.385), 0.45, 0.09, boxstyle="round,pad=0.006,rounding_size=0.008",
                                  facecolor="#F8FAFC", edgecolor="#059669", lw=1.2, zorder=3)
    s_ax.add_patch(fsm2)
    s_ax.text(0.50, 0.460, "2. CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)", fontsize=7.0, fontweight="bold", color="#065F46", zorder=4)
    s_ax.text(0.50, 0.415, "NORMAL (t < 5s)  ──►  WARNING (5s ≤ t < 10s)  ──►  VIOLATION (t ≥ 10s)",
              fontsize=6.6, color=COLOR_TEXT_MAIN, zorder=4)

    s_ax.annotate("", xy=(0.70, 0.48), xytext=(0.70, 0.50),
                  arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.5), zorder=5)
    s_ax.text(0.71, 0.485, "Guardia: INSIDE (Invariante Fail-Safe t=0s)", fontsize=6.5, color="#DC2626", zorder=5)

    draw_card(ax, 0.04, 0.065, 0.92, 0.290, "3. CÓDIGO FUENTE: EVALUACIÓN DE HISTÉRESIS Y BYPASS DE APROXIMACIÓN RÁPIDA")

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

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_fsm, "src/core/spatial_fsm.py")

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p5.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 6: PRESUPUESTO TEMPORAL ISO 13855:2024 Y ACELERACIÓN EDGE
# ==============================================================================
def render_page_6(pdf):
    fig, ax = create_base_page(6, 8, "06. ISO 13855 y Latencias")

    draw_card(ax, 0.04, 0.68, 0.92, 0.24, "1. MODELO DE SEPARACIÓN TEÓRICO: NORMA ISO 13855:2024")

    iso_text = (
        "La norma internacional ISO 13855:2024 regula el posicionamiento de dispositivos de protección respecto a velocidades de\n"
        "aproximación de partes del cuerpo humano. La distancia mínima de seguridad S está gobernada por la ecuación:\n"
    )
    ax.text(0.065, 0.885, iso_text, fontsize=7.6, color=COLOR_TEXT_MAIN, va="top", zorder=3)

    iso_math = (
        r"$S = (K \cdot T) + C + C_{\mathrm{dyn}} + Z_{\mathrm{extra}}, \quad "
        r"T = t_1(\mathrm{vision}) + t_2(\mathrm{PLC}) + t_3(\mathrm{freno})$"
    )
    ax.text(0.5, 0.835, iso_math, fontsize=8.8, color="#0F172A", ha="center", va="center", zorder=4)

    iso_desc = (
        "• Constante K: 1600 mm/s (aproximación transversal estándar) y 2000 mm/s (aproximación directa perpendicular).\n"
        "• Presupuesto Máximo para Visión (t1): La norma exige t1 ≤ 50 ms (≥ 20 FPS continuos sin caídas).\n"
        "• Doble Horizonte Temporal (ADR-010):\n"
        "  1. Latencia de Hardware por Cuadro (T_system): T_cap + T_pre + T_infer + T_pose + T_geom + T_track + T_fsm ≈ 18.5 - 20.5 ms.\n"
        "  2. Latencia de Reacción Física del Evento (T_event = t_trip - t_physical_entry):\n"
        "     - Aproximación normal con debounce (N_confirm = 3): T_event = (3 - 1) × 33.3 ms + 18.5 ms = 85.1 ms.\n"
        "     - Aproximación rápida (vn ≥ 1.6 m/s): Bypass automático N_confirm = 1 → T_event = T_system ≈ 18.5 ms."
    )
    ax.text(0.065, 0.785, iso_desc, fontsize=7.4, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    draw_card(ax, 0.04, 0.370, 0.92, 0.295, "2. DESGLOSE CRONOMÉTRICO DE LATENCIAS POR ETAPA DEL PIPELINE")

    l_ax = fig.add_axes([0.08, 0.390, 0.39, 0.21])
    stages = ["Captura", "Preproc", "Inferencia", "Keypoints", "Homog", "Kalman", "FSM"]
    times = [1.2, 0.8, 12.5, 1.8, 0.08, 0.45, 0.04]
    bar_colors = ["#64748B", "#64748B", "#DC2626", "#F59E0B", "#38BDF8", "#10B981", "#8B5CF6"]

    bars = l_ax.barh(stages, times, color=bar_colors, edgecolor="none", height=0.65)
    l_ax.set_xlabel("Latencia en Milisegundos (ms)", fontsize=7.0)
    l_ax.grid(True, axis="x", ls=":", alpha=0.6)
    l_ax.tick_params(labelsize=6.8)
    for bar in bars:
        w = bar.get_width()
        l_ax.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{w:.2f} ms", fontsize=6.5, va="center")

    silicon_text = (
        "ANÁLISIS DE ACELERACIÓN EN SILICIO HETEROGÉNEO:\n\n"
        "• Apple Silicon M1 (arm64 - Desarrollo):\n"
        "  - ONNX Runtime + CoreMLExecutionProvider.\n"
        "  - 346 de 354 operadores delegados nativamente al\n"
        "    Apple Neural Engine (ANE) y GPU unificada.\n"
        "  - Latencia de inferencia: 12.5 ms (p95: 14.1 ms, >60 FPS).\n\n"
        "• NVIDIA GTX 1050 (Pascal CC 6.1 - Despliegue Target):\n"
        "  - Incompatibilidad Física: Pascal carece de Tensor Cores;\n"
        "    FP16 está penalizado a 1:64 en silicio.\n"
        "  - Cuantización Obligatoria: Es mandatorio usar INT8\n"
        "    mediante Post-Training Quantization (PTQ) con TensorRT\n"
        "    para lograr tasa de ejecución completa (full-rate)."
    )
    ax.text(0.51, 0.635, silicon_text, fontsize=7.2, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    draw_card(ax, 0.04, 0.065, 0.92, 0.290, "3. CÓDIGO FUENTE: PROFILING DE ALTA RESOLUCIÓN Y CÓMPUTO DE T_EVENT")

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

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_lat, "src/pipeline/safety_pipeline.py")

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p6.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 7: CIERRE DEL GAP SINTÉTICO Y RENDERIZADO PINHOLE FOTORREALISTA
# ==============================================================================
def render_page_7(pdf):
    fig, ax = create_base_page(7, 8, "07. Datos Sintéticos y Gap")

    draw_card(ax, 0.04, 0.68, 0.92, 0.24, "1. EL DOMAIN GAP EN DATOS SINTÉTICOS Y POR QUÉ FALLA EL DIBUJO GEOMÉTRICO (ADR-012)")

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
    ax.text(0.065, 0.885, syn_text, fontsize=7.5, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    draw_card(ax, 0.04, 0.370, 0.92, 0.295, "2. MODELO DE ESCALA PERSPECTIVA ESTENOPEICA Y SOMBRAS GAUSSIANAS")

    p_ax = fig.add_axes([0.08, 0.390, 0.39, 0.21])
    Y_m = np.linspace(0.5, 6.0, 100)
    h_px = 480.0 / (1.0 + 0.165 * Y_m)

    p_ax.plot(Y_m, h_px, color="#2563EB", lw=2.5, label=r"(Y) = \frac{480}{1.0 + 0.165 Y}$")
    p_ax.axhline(480, color="#64748B", ls="--", lw=1.0, label="Máx: 480 px (Y=0)")
    p_ax.axhline(240, color="#DC2626", ls="--", lw=1.0, label="Mín: 240 px (Y=6)")
    p_ax.set_xlabel("Distancia al Suelo Y (metros)", fontsize=7.0)
    p_ax.set_ylabel("Altura del Sujeto h (píxeles)", fontsize=7.0)
    p_ax.grid(True, ls=":", alpha=0.6)
    p_ax.legend(fontsize=6.5)
    p_ax.tick_params(labelsize=6.8)

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
    ax.text(0.51, 0.635, syn_res_text, fontsize=7.2, color=COLOR_TEXT_MAIN, linespacing=1.28, va="top", zorder=3)

    draw_card(ax, 0.04, 0.065, 0.92, 0.290, "3. CÓDIGO FUENTE: COMPOSICIÓN ALFA Y PROYECCIÓN PINHOLE")

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

    draw_code_box(ax, 0.065, 0.080, 0.87, 0.235, code_syn, "src/utils/synthetic_generator.py")

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p7.png", dpi=150)
    plt.close(fig)


# ==============================================================================
# PAGE 8: CATÁLOGO COMPLETO DE ADRS Y GUÍA DE PREGUNTAS DE EXAMEN
# ==============================================================================
def render_page_8(pdf):
    fig, ax = create_base_page(8, 8, "08. ADRs y Preguntas Clave")

    draw_card(ax, 0.04, 0.45, 0.92, 0.47, "1. CATÁLOGO COMPLETO DE ARCHITECTURE DECISION RECORDS (ADRs)")

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

    table_top = 0.880
    row_height = 0.030

    # Table Header (lowered to avoid card title collision)
    th_box = patches.Rectangle((0.065, table_top - 0.024), 0.87, 0.024, facecolor="#1E293B", edgecolor="none", zorder=3)
    ax.add_patch(th_box)
    ax.text(0.08, table_top - 0.012, "ADR", fontsize=7.2, fontweight="bold", color="#38BDF8", va="center", zorder=4)
    ax.text(0.145, table_top - 0.012, "REFERENCIA / ARCHIVO", fontsize=7.2, fontweight="bold", color="#38BDF8", va="center", zorder=4)
    ax.text(0.42, table_top - 0.012, "DECISIÓN ARQUITECTÓNICA & IMPACTO INDUSTRIAL", fontsize=7.2, fontweight="bold", color="#38BDF8", va="center", zorder=4)

    y_cur = table_top - 0.026
    for idx, (num, path, desc) in enumerate(adrs):
        row_bg = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        r_box = patches.Rectangle((0.065, y_cur - row_height), 0.87, row_height, facecolor=row_bg, edgecolor="#E2E8F0", lw=0.5, zorder=3)
        ax.add_patch(r_box)

        ax.text(0.08, y_cur - row_height/2, f"ADR-{num}", fontsize=7.0, fontweight="bold", color="#0F172A", va="center", zorder=4)
        ax.text(0.145, y_cur - row_height/2, path, fontsize=6.2, color="#2563EB", family="monospace", va="center", zorder=4)
        ax.text(0.42, y_cur - row_height/2, desc, fontsize=6.4, color=COLOR_TEXT_MAIN, va="center", zorder=4)
        y_cur -= row_height

    draw_card(ax, 0.04, 0.065, 0.92, 0.365, "2. GUÍA DE PREGUNTAS FUNDAMENTALES PARA ENTREVISTA O DEFENSA TÉCNICA")

    qa_items = [
        ("¿Por qué homografía planar 3x3 y no un modelo de Deep Learning monocular 3D?",
         "Porque fijando Zw = 0 con tobillos, la geometría euclidiana resuelve el espacio con precisión milimétrica en < 0.05 ms con 8 grados de libertad deterministas, sin consumir VRAM ni sufrir alucinaciones de profundidad."),
        ("¿Por qué un sistema de 4 puntos de calibración tiene siempre RMSE = 0?",
         "Porque 4 puntos aportan 8 ecuaciones independientes para 8 incógnitas (grados de libertad de H). El sistema es matemáticamente determinado y no tiene grados de libertad sobrantes para medir residuo; para evaluar error real se requiere N > 4."),
        ("¿Cómo se evita que un operario trabajando en el borde destruya contactores por chattering?",
         "Mediante un Schmitt Trigger espacial: se entra al cruzar P_danger pero no se sale hasta cruzar P_release (buffer de 200 mm). La entrada tiene confirmación rápida (19 ms si vn ≥ 1.6 m/s) y la salida exige 5 cuadros continuos con fotones ópticos OBSERVED."),
        ("¿Por qué está prohibido permitir la desescalada de alarma durante el estado PREDICTED de Kalman?",
         "Porque PREDICTED es una extrapolación matemática ciega por oclusión. Desactivar una parada de emergencia sin confirmación sensorial física viola el principio industrial Fail-Safe: ante la duda o falta de luz, la máquina permanece detenida."),
        ("¿Cuál es la diferencia entre T_system y T_event bajo la norma ISO 13855?",
         "T_system es la latencia de hardware por fotograma (~19 ms). T_event es el retardo físico real desde que el cuerpo cruza la línea hasta que el relé abre (~85 ms en paso normal con debounce, y ~19 ms en bypass instantáneo por aproximación rápida).")
    ]

    qa_top = 0.370
    for q, a in qa_items:
        ax.text(0.065, qa_top, f"• {q}", fontsize=7.0, fontweight="bold", color="#1E3A8A", va="top", zorder=3)
        ax.text(0.08, qa_top - 0.015, f"  R: {a}", fontsize=6.6, color=COLOR_TEXT_MAIN, linespacing=1.22, va="top", zorder=3)
        qa_top -= 0.061

    pdf.savefig(fig)
    fig.savefig("/tmp/study_p8.png", dpi=150)
    plt.close(fig)

def main():
    print(f"[*] Generando Guía Maestra de Estudio de Arquitectura en PDF...")
    print(f"[*] Destino: {OUTPUT_PDF}")

    os.makedirs(DOCS_DIR, exist_ok=True)

    with PdfPages(OUTPUT_PDF) as pdf:
        print("  - Renderizando Página 1: Portada, Filosofía y Tesis End-to-End...")
        render_page_1(pdf)
        print("  - Renderizando Página 2: Geometría Proyectiva y Homografía Planar (Zw = 0)...")
        render_page_2(pdf)
        print("  - Renderizando Página 3: Percepción Pura y Anclaje Anatómico en Tobillos...")
        render_page_3(pdf)
        print("  - Renderizando Página 4: Cinemática Bayesiana, Filtro de Kalman y Gating...")
        render_page_4(pdf)
        print("  - Renderizando Página 5: Schmitt Trigger Espacial y Statecharts Ortogonales...")
        render_page_5(pdf)
        print("  - Renderizando Página 6: Presupuesto Temporal ISO 13855 y Aceleración Edge...")
        render_page_6(pdf)
        print("  - Renderizando Página 7: Cierre del Synthetic Domain Gap y Pinhole...")
        render_page_7(pdf)
        print("  - Renderizando Página 8: Catálogo Completo de ADRs y Preguntas Clave...")
        render_page_8(pdf)

    file_size_kb = os.path.getsize(OUTPUT_PDF) / 1024.0
    print(f"[✓] PDF generado con éxito total: {OUTPUT_PDF} ({file_size_kb:.1f} KB, 8 páginas)")

if __name__ == "__main__":
    main()
