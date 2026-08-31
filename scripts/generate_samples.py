#!/usr/bin/env python3
"""
scripts/generate_samples.py
CLI Script to generate deterministic synthetic benchmark videos for industrial safety pipeline testing.
"""

import argparse
from pathlib import Path
import sys

# Ensure repository root is on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.synthetic_generator import SyntheticVideoGenerator


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for synthetic video generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic benchmark videos for industrial vision safety evaluation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/samples"),
        help="Directory where generated MP4 videos will be saved.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default_config.yaml"),
        help="Path to calibration YAML configuration file.",
    )
    parser.add_argument(
        "--sequence",
        type=str,
        choices=["all", "a", "b", "c"],
        default="all",
        help="Specific sequence to generate ('a': Clean Incursion, 'b': Occlusion, 'c': Dwell Loitering, 'all': All three).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target frame rate for generated video streams.",
    )
    return parser.parse_args()


def main() -> None:
    """Main CLI entrypoint."""
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🎥 INDUSTRIAL VISION SAFETY GUARD — SYNTHETIC VIDEO GENERATOR")
    print("=" * 70)
    print(f"Output Directory : {args.output_dir.resolve()}")
    print(f"Calibration File : {args.config.resolve()}")
    print(f"FPS              : {args.fps}")
    print(f"Sequence Mode    : {args.sequence.upper()}")
    print("-" * 70)

    generator = SyntheticVideoGenerator(
        config_path=args.config if args.config.exists() else None,
        fps=args.fps,
    )

    generated = []
    if args.sequence in ("all", "a"):
        out_a = args.output_dir / "sequence_a_clean_incursion.mp4"
        print(f"[*] Generating Sequence A: Clean Incursion -> {out_a.name}...")
        path_a = generator.generate_sequence_a(out_a, duration_s=6.0)
        generated.append(path_a)

    if args.sequence in ("all", "b"):
        out_b = args.output_dir / "sequence_b_occlusion_coasting.mp4"
        print(f"[*] Generating Sequence B: Lower-Limb Occlusion -> {out_b.name}...")
        path_b = generator.generate_sequence_b(out_b, duration_s=6.0)
        generated.append(path_b)

    if args.sequence in ("all", "c"):
        out_c = args.output_dir / "sequence_c_dwell_loitering.mp4"
        print(f"[*] Generating Sequence C: Dwell Time & Loitering -> {out_c.name}...")
        path_c = generator.generate_sequence_c(out_c, duration_s=10.0)
        generated.append(path_c)

    print("=" * 70)
    print(f"✅ Successfully generated {len(generated)} synthetic sample video(s):")
    for p in generated:
        size_kb = p.stat().st_size / 1024.0
        print(f"  • {p.name:<38} ({size_kb:.1f} KB)")
    print("=" * 70)


if __name__ == "__main__":
    main()
