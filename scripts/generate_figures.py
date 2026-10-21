#!/usr/bin/env python3
"""
scripts/generate_figures.py
Generates the complete suite of architectural diagrams and benchmark charts
for Edge Safety Guard (Vision-Based Restricted Zone Monitoring).

Complies strictly with data-visualization skill guidelines:
- seaborn-v0_8-whitegrid base styling
- Colorblind-friendly palettes (blue/orange/slate)
- Insight-driven titles and unit-labeled axes
- High DPI (200 dpi) for crisp rendering
- 100% English terminology and annotations
"""

import os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Ellipse, ArrowStyle

OUTPUT_DIR = Path("/Users/xander/Projects/edge-safety-guard/docs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Shared Color Palette (Colorblind-friendly)
COLOR_PRIMARY = "#2563EB"       # Vibrant Blue
COLOR_SECONDARY = "#DD8452"     # Muted Orange
COLOR_ACCENT = "#55A868"        # Accessible Green
COLOR_DANGER = "#DC2626"        # Vivid Red
COLOR_WARNING = "#D97706"       # Amber
COLOR_SLATE_DARK = "#1E293B"    # Slate 800
COLOR_SLATE_MED = "#475569"     # Slate 600
COLOR_SLATE_LIGHT = "#94A3B8"   # Slate 400
COLOR_BG_CARD = "#F8FAFC"       # Slate 50
COLOR_BORDER = "#CBD5E1"        # Slate 300


def apply_base_style():
    """Apply standard clean styling for publication charts."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "figure.dpi": 200,
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "axes.edgecolor": COLOR_BORDER,
        "grid.color": "#E2E8F0",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
    })


def generate_pipeline_flow(output_path: Path):
    """Figure 1: 4-Layer Decoupled Architecture Flowchart."""
    fig = plt.figure(figsize=(13.5, 4.2), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 4.2)
    ax.axis("off")

    cards = [
        {
            "num": "1",
            "title": "PERCEPTION",
            "subtitle": "Deep Learning Layer",
            "header_color": "#1E293B",
            "items": [
                "• RTSP / V4L2 + Foveated ROI",
                "• YOLO11n-Pose ONNX Engine",
                "• Ankle Anchors (kp 15 & 16)",
                "• 2D IoU & Anchor Deduplication",
            ],
            "x": 0.4,
        },
        {
            "num": "2",
            "title": "GEOMETRY",
            "subtitle": "Projective Math Layer",
            "header_color": "#0F4C81",
            "items": [
                "• Planar DLT Homography H (3x3)",
                "• Condition Gate: κ(H) < 10¹²",
                "• Ground Contact Mapping (Zw = 0)",
                "• Metric Plane (X, Y) & Deduplication",
            ],
            "x": 3.7,
        },
        {
            "num": "3",
            "title": "ESTIMATION",
            "subtitle": "Kinematics & Tracking",
            "header_color": "#1E5631",
            "items": [
                "• Kalman Predict (2D CV Model)",
                "• Mahalanobis Gating (χ²₂ ≤ 9.210)",
                "• Hungarian Assignment + Joseph Update",
                "• Epistemic States (OBS / PRED / STALE)",
            ],
            "x": 7.0,
        },
        {
            "num": "4",
            "title": "DECISION",
            "subtitle": "Formal Statecharts Layer",
            "header_color": "#9A3412",
            "items": [
                "• Prepared Geometries (GEOS C-API)",
                "• Spatial Schmitt Trigger (Δd = 200 mm)",
                "• Velocity Bypass (vn ≥ 1.6 m/s)",
                "• Orthogonal Dwell & Fail-Safe Trip",
            ],
            "x": 10.3,
        },
    ]

    card_width = 2.8
    card_height = 3.6
    y_card = 0.3

    for i, c in enumerate(cards):
        x = c["x"]
        # Outer Card Box
        card_box = FancyBboxPatch(
            (x, y_card), card_width, card_height,
            boxstyle="Round,pad=0.04,rounding_size=0.15",
            facecolor="#FFFFFF", edgecolor=COLOR_BORDER, linewidth=1.2, zorder=2
        )
        ax.add_patch(card_box)

        # Header Box
        header_h = 0.85
        header_y = y_card + card_height - header_h
        header_box = FancyBboxPatch(
            (x, header_y), card_width, header_h,
            boxstyle="Round,pad=0.04,rounding_size=0.15",
            facecolor=c["header_color"], edgecolor="none", zorder=3
        )
        ax.add_patch(header_box)

        # Header Text
        ax.text(x + card_width / 2, header_y + 0.52, f"{c['num']}. {c['title']}",
                color="#FFFFFF", fontsize=11.5, fontweight="bold", ha="center", va="center", zorder=4)
        ax.text(x + card_width / 2, header_y + 0.22, c["subtitle"],
                color="#CBD5E1", fontsize=8.5, ha="center", va="center", zorder=4)

        # Items Text
        y_text = header_y - 0.45
        for item in c["items"]:
            ax.text(x + 0.22, y_text, item, color="#334155", fontsize=9.2,
                    va="center", ha="left", zorder=4)
            y_text -= 0.55

        # Connecting Chevron / Arrow to next card
        if i < len(cards) - 1:
            arrow_x = x + card_width + 0.12
            arrow_y = y_card + card_height / 2
            ax.annotate(
                "", xy=(arrow_x + 0.26, arrow_y), xytext=(arrow_x, arrow_y),
                arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=2.4, mutation_scale=15),
                zorder=5
            )

    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_bbox_vs_ankles(output_path: Path):
    """Figure 2: Geometric Ground Anchor Comparison (Ankle Keypoints vs Bounding Box Centroid)."""
    apply_base_style()
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)

    # Coordinates
    floor_y = 0.0
    boundary_x = 0.0

    # Danger Zone Shading
    ax.axvspan(boundary_x, 3.5, color="#FEE2E2", alpha=0.5, label="Restricted Hazard Zone ($P_{\\mathrm{danger}}$)")
    ax.axvspan(-3.5, boundary_x, color="#F8FAFC", alpha=0.5, label="Safe Workcell Zone")

    # Danger Boundary Line
    ax.axvline(boundary_x, color=COLOR_DANGER, linestyle="--", linewidth=2.5, zorder=3)

    # Floor Line
    ax.axhline(floor_y, color=COLOR_SLATE_DARK, linewidth=3, zorder=4)
    ax.text(-3.3, -0.22, "Physical Floor Plane ($Z_w = 0$)", color=COLOR_SLATE_MED, fontsize=9.5, fontweight="bold")

    # Worker Skeleton (Leaning strongly into the hazard zone)
    # Feet at X = -0.65 (Safely outside)
    ankle_x, ankle_y = -0.65, 0.0
    knee_x, knee_y = -0.50, 0.65
    hip_x, hip_y = -0.30, 1.25
    shoulder_x, shoulder_y = 0.55, 1.85   # Crosses boundary into danger zone!
    head_x, head_y = 0.75, 2.20           # Deep inside danger zone in 2D
    hand_x, hand_y = 1.15, 1.70           # Reaching arm

    # Draw Bones
    bones = [
        ([ankle_x, knee_x], [ankle_y, knee_y]),
        ([knee_x, hip_x], [knee_y, hip_y]),
        ([hip_x, shoulder_x], [hip_y, shoulder_y]),
        ([shoulder_x, head_x], [shoulder_y, head_y]),
        ([shoulder_x, hand_x], [shoulder_y, hand_y]),
    ]
    for bx, by in bones:
        ax.plot(bx, by, color="#1E293B", linewidth=4.5, solid_capstyle="round", zorder=5)

    # Head Circle
    head_circle = plt.Circle((head_x, head_y), 0.18, color="#1E293B", zorder=6)
    ax.add_patch(head_circle)

    # 2D Bounding Box enclosing the worker
    bbox_xmin, bbox_xmax = -0.85, 1.35
    bbox_ymin, bbox_ymax = 0.0, 2.45
    bbox_rect = patches.Rectangle(
        (bbox_xmin, bbox_ymin), bbox_xmax - bbox_xmin, bbox_ymax - bbox_ymin,
        linewidth=2.0, edgecolor="#DC2626", facecolor="none", linestyle=":", zorder=4
    )
    ax.add_patch(bbox_rect)
    ax.text(bbox_xmin + 0.08, bbox_ymax - 0.28, "2D Bounding Box\n(YOLO Pose)", color="#DC2626", fontsize=9.0, fontweight="bold")

    # Hazard Boundary Label (positioned higher and clearly separated)
    ax.text(boundary_x + 0.12, 2.7, "Hazard Boundary Line ($P_{\\mathrm{danger}}$)",
            color=COLOR_DANGER, fontsize=10.5, fontweight="bold", va="center")
    bbox_bc_x = (bbox_xmin + bbox_xmax) / 2.0  # = 0.25 (INSIDE DANGER ZONE!)
    bbox_bc_y = 0.0
    ax.scatter([bbox_bc_x], [bbox_bc_y], s=180, color="#DC2626", marker="X", zorder=7)

    # Ankle Contact Anchor Point (Real Ground Contact)
    ax.scatter([ankle_x], [ankle_y], s=180, color=COLOR_ACCENT, marker="o", edgecolors="#065F46", linewidth=2, zorder=7)

    # Clean Callouts with clear separation to avoid overlap
    ax.annotate(
        "Ankle Contact Anchor (Zw = 0)\n• Invariant ground support\n• Outcome: TRUE SAFE (X = -0.65 m)",
        xy=(ankle_x, ankle_y), xytext=(-2.9, 0.8),
        arrowprops=dict(arrowstyle="->", color=COLOR_ACCENT, lw=2.0),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#ECFDF5", edgecolor=COLOR_ACCENT, lw=1.5),
        fontsize=9.5, fontweight="bold", color="#065F46", zorder=8
    )

    ax.annotate(
        "BBox Base / Centroid (Zw = 0)\n• Deformed by torso tilt\n• Outcome: FALSE POSITIVE TRIP (X = +0.25 m)",
        xy=(bbox_bc_x, bbox_bc_y), xytext=(0.8, 0.8),
        arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2.0),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.5),
        fontsize=9.5, fontweight="bold", color="#991B1B", zorder=8
    )

    ax.set_title("Ground Anchor Comparison: Ankle Contact ($Z_w=0$) vs BBox Centroid Deformation",
                 pad=18, fontsize=12.5)
    ax.set_xlabel("Metric Floor Position X (meters)")
    ax.set_ylabel("Vertical Height Y (meters)")
    ax.set_xlim(-3.5, 2.5)
    ax.set_ylim(-0.4, 2.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_schmitt_trigger(output_path: Path):
    """Figure 3: Spatial Schmitt Trigger with Dual Hysteresis Band."""
    apply_base_style()
    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=200)

    # Machine Dimensions
    mach_w, mach_h = 3.0, 1.8
    mach_x, mach_y = -mach_w / 2, -mach_h / 2

    # Danger Zone Boundary (P_danger)
    danger_pad = 1.0
    dang_w = mach_w + 2 * danger_pad
    dang_h = mach_h + 2 * danger_pad
    dang_x = -dang_w / 2
    dang_y = -dang_h / 2

    # Release Zone Boundary (P_release = P_danger + Delta d)
    delta_d = 0.9  # visual hysteresis margin representing Delta d = 200 mm
    rel_w = dang_w + 2 * delta_d
    rel_h = dang_h + 2 * delta_d
    rel_x = -rel_w / 2
    rel_y = -rel_h / 2

    # Outer Hysteresis Band Box
    rel_box = FancyBboxPatch(
        (rel_x, rel_y), rel_w, rel_h,
        boxstyle="Round,pad=0.1,rounding_size=0.4",
        facecolor="#FEF3C7", edgecolor="#D97706", linewidth=2.5, linestyle="--",
        zorder=1, label="P_release (Release Boundary, Hysteresis Band)"
    )
    ax.add_patch(rel_box)

    # Danger Zone Box
    dang_box = FancyBboxPatch(
        (dang_x, dang_y), dang_w, dang_h,
        boxstyle="Round,pad=0.08,rounding_size=0.3",
        facecolor="#FEE2E2", edgecolor="#DC2626", linewidth=2.8, linestyle="-",
        zorder=2, label="P_danger (Immediate Trip Boundary)"
    )
    ax.add_patch(dang_box)

    # Center Machine Core Box
    mach_box = FancyBboxPatch(
        (mach_x, mach_y), mach_w, mach_h,
        boxstyle="Square,pad=0.05",
        facecolor="#334155", edgecolor="#0F172A", linewidth=2.0, zorder=3
    )
    ax.add_patch(mach_box)

    # Machine Text
    ax.text(0, 0.15, "HAZARDOUS MACHINERY", color="#FFFFFF",
            fontsize=12, fontweight="bold", ha="center", va="center", zorder=4)
    ax.text(0, -0.25, "(Robot Manipulator / High-Speed Cell)", color="#94A3B8",
            fontsize=9, ha="center", va="center", zorder=4)

    # Labels for boundaries
    ax.text(0, dang_y + 0.35, "P_danger: Immediate Trip Boundary (t = 0.0 s)",
            color="#B91C1C", fontsize=10.5, fontweight="bold", ha="center", va="center", zorder=4)
    ax.text(0, rel_y + 0.40, "P_release: Spatial Hysteresis Band (Δd = 200 mm, N_release = 5 frames)",
            color="#B45309", fontsize=10.5, fontweight="bold", ha="center", va="center", zorder=4)

    # Dimension indicator for Delta d
    dim_x = dang_x + dang_w + 0.15
    ax.annotate(
        "", xy=(dim_x, 0), xytext=(dim_x + delta_d - 0.1, 0),
        arrowprops=dict(arrowstyle="<->", color="#B45309", lw=2.0),
        zorder=5
    )
    ax.text(dim_x + delta_d / 2 - 0.05, 0.28, "Δd = 200 mm", color="#B45309",
            fontsize=9.5, fontweight="bold", ha="center", zorder=5)

    # Operational Policy Annotations (Positioned clearly above the boundary)
    ax.text(-4.8, 3.4, "ENTRY POLICY (Fast Fail-Safe):\n• Normal speed: Debounce N_confirm = 3 frames\n• High speed (vn ≥ 1.6 m/s): Instant 1-frame bypass",
            fontsize=9, color="#1E293B", bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor="#CBD5E1", lw=1))

    ax.text(1.2, 3.4, "EXIT POLICY (Strictly Conservative):\n• Requires N_release = 5 consecutive frames\n• Strictly OBSERVED photons (occlusions blocked)",
            fontsize=9, color="#1E293B", bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor="#CBD5E1", lw=1))

    ax.set_xlim(-5.2, 5.2)
    ax.set_ylim(-3.2, 4.3)
    ax.axis("off")
    ax.set_title("Spatial Schmitt Trigger: Dual Hysteresis Band to Prevent Boundary Chattering",
                 pad=12, fontsize=12.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_kalman_mahalanobis(output_path: Path):
    """Figure 4: Mahalanobis Innovation Gating Ellipsoid."""
    apply_base_style()
    fig, ax = plt.subplots(figsize=(8.5, 6.2), dpi=200)

    # Center track position (0, 0)
    ax.scatter([0], [0], s=140, color="#0F172A", zorder=5)
    ax.text(0.04, -0.05, "Track State $\\hat{\\mathbf{x}}_k$", fontsize=11, fontweight="bold", color="#0F172A")

    # Innovation vector v
    vx, vy = 0.52, 0.38
    ax.annotate(
        "", xy=(vx, vy), xytext=(0, 0),
        arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=2.8, mutation_scale=18),
        zorder=6
    )
    ax.text(vx + 0.05, vy + 0.10, "Innovation Vector $\\mathbf{v} = \\mathbf{z} - H\\hat{\\mathbf{x}}$",
            fontsize=10.5, fontweight="bold", color="#0F172A",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.9), zorder=7)

    # Covariance Ellipses (Angle = 36 degrees along velocity vector)
    angle = 36

    # 1-sigma ellipse (68.3%)
    e1 = Ellipse((0, 0), width=0.8, height=0.35, angle=angle,
                 edgecolor="#60A5FA", facecolor="none", linewidth=1.8, linestyle="-",
                 label="1σ Innovation Contour (68.3%)", zorder=3)
    ax.add_patch(e1)

    # 2-sigma ellipse (95.4%)
    e2 = Ellipse((0, 0), width=1.5, height=0.65, angle=angle,
                 edgecolor="#2563EB", facecolor="none", linewidth=2.0, linestyle="-",
                 label="2σ Innovation Contour (95.4%)", zorder=3)
    ax.add_patch(e2)

    # Mahalanobis 99% gating boundary: chi2(2, 0.99) = 9.21 (sqrt = 3.034)
    e_gate = Ellipse((0, 0), width=2.45, height=1.05, angle=angle,
                     edgecolor="#DC2626", facecolor="#FEE2E2", alpha=0.35, linewidth=2.6, linestyle="-",
                     label="Mahalanobis Gating Boundary $\\chi^2_2(0.99) = 9.210$", zorder=2)
    ax.add_patch(e_gate)

    ax.set_title(r"Mahalanobis Innovation Gating: Dynamic Validation Gate $\chi^2_2 \leq 9.210$", pad=14)
    ax.set_xlabel("Normalized Longitudinal Innovation $\\Delta X$ (m)")
    ax.set_ylabel("Normalized Lateral Innovation $\\Delta Y$ (m)")
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.0, 1.1)
    ax.legend(loc="lower right", frameon=True, facecolor="#FFFFFF", edgecolor=COLOR_BORDER)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_latency_breakdown(output_path: Path):
    """Figure 5: Granular Stage Latency Breakdown (Horizontal Bar Chart)."""
    apply_base_style()
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)

    stages = [
        "Frame Capture",
        "Letterbox Preprocess",
        "YOLO11n-Pose Inference",
        "Keypoint Extraction",
        "Planar DLT Homography",
        "Kalman Tracking & Gating",
        "Spatial FSM & Statechart",
    ]
    # Reverse order so pipeline runs top to bottom
    stages.reverse()

    latencies = [1.20, 0.80, 12.50, 1.80, 0.08, 0.45, 0.04]
    latencies.reverse()

    # Colors: highlight inference as primary compute stage
    colors = [
        COLOR_SLATE_MED,    # FSM
        COLOR_ACCENT,       # Kalman
        COLOR_PRIMARY,      # Homography
        COLOR_WARNING,      # Keypoints
        COLOR_DANGER,       # Inference (Bottleneck)
        COLOR_SLATE_MED,    # Preprocess
        COLOR_SLATE_MED,    # Capture
    ]

    bars = ax.barh(stages, latencies, color=colors, height=0.6, zorder=3)

    # Direct value annotations
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.25, bar.get_y() + bar.get_height() / 2,
            f"{width:.2f} ms",
            ha="left", va="center", fontsize=10, fontweight="bold", color="#1E293B"
        )

    ax.set_title("Pipeline Stage Latency Breakdown (Total $T_{\\mathrm{system}} \\approx 16.9\\text{ ms} \\ll 50\\text{ ms Budget}$)", pad=14)
    ax.set_xlabel("Latency per Stage (ms)")
    ax.set_xlim(0, 15.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Annotate total latency and budget note
    ax.text(
        8.2, 1.2,
        "Total Reaction Time:\n$T_{\\mathrm{pipeline}} = 16.87\\text{ ms}$\nThroughput: $\\approx 51.4\\text{ FPS}$\nISO 13855 Target: $T_1 \\leq 50\\text{ ms}$",
        fontsize=9.5, color="#1E293B",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor=COLOR_BORDER, lw=1.2)
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_pinhole_scaling(output_path: Path):
    """Figure 6: Pinhole Perspective Anthropometric Scale Curve."""
    apply_base_style()
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=200)

    # Ground distance Y in meters
    y_vals = np.linspace(0.5, 6.0, 200)
    # Anthropometric height formula from calibrated pinhole camera
    h_vals = 480.0 / (1.0 + 0.165 * y_vals)

    # Plot scale curve
    ax.plot(y_vals, h_vals, color=COLOR_PRIMARY, linewidth=3.2,
            label=r"Anthropometric Scale $h(Y) = \frac{480}{1.0 + 0.165 \cdot Y}$", zorder=3)

    # Reference asymptotes / thresholds
    ax.axhline(480, color=COLOR_SLATE_MED, linestyle="--", linewidth=1.8,
               label="Max Theoretical Height: 480 px (at Y = 0 m)", zorder=2)
    ax.axhline(241.2, color=COLOR_DANGER, linestyle="--", linewidth=1.8,
               label="Min Resolution Bound: 241 px (at Y = 6 m)", zorder=2)

    # Operational zone shading
    ax.axvspan(1.0, 5.0, color="#EFF6FF", alpha=0.6, label="Active Monitoring Workcell ($Y \\in [1.0, 5.0]\\text{ m}$)")

    ax.set_title("Pinhole Perspective Anthropometric Scale Curve $h(Y)$", pad=14)
    ax.set_xlabel("Ground Distance Y (meters)")
    ax.set_ylabel("Apparent Subject Height h (pixels)")
    ax.set_xlim(0.4, 6.2)
    ax.set_ylim(190, 530)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="lower left", frameon=True, facecolor="#FFFFFF", edgecolor=COLOR_BORDER)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def main():
    print(f"Rendering figures into: {OUTPUT_DIR}")
    generate_pipeline_flow(OUTPUT_DIR / "pipeline_flow.png")
    generate_bbox_vs_ankles(OUTPUT_DIR / "bbox_vs_ankles.png")
    generate_schmitt_trigger(OUTPUT_DIR / "schmitt_trigger.png")
    generate_kalman_mahalanobis(OUTPUT_DIR / "kalman_mahalanobis.png")
    generate_latency_breakdown(OUTPUT_DIR / "latency_breakdown.png")
    generate_pinhole_scaling(OUTPUT_DIR / "pinhole_scaling.png")
    print("All 6 architectural and benchmark figures successfully generated in English!")


if __name__ == "__main__":
    main()
