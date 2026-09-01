#!/usr/bin/env python3
"""
scripts/download_datasets.py
Modular Benchmark Dataset Downloader with Multi-Mirror Failover and Local Ingestion.
"""

import argparse
from dataclasses import dataclass, field
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Tuple
import urllib.error
import urllib.request

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass(frozen=True)
class DatasetMetadata:
    """Metadata specification for a benchmark video dataset."""
    name: str
    description: str
    filename: str
    primary_url: str
    mirrors: Tuple[str, ...] = field(default_factory=tuple)
    priority: int = 1  # 1: Clean baseline, 2: Occlusion/Edge-case, 3: Large crowd
    expected_size_bytes: Optional[int] = None
    default_config: str = ""


# Canonical dataset registry
DATASET_REGISTRY: Dict[str, DatasetMetadata] = {
    "opencv_vtest": DatasetMetadata(
        name="opencv_vtest",
        description="OpenCV Surveillance Pedestrian Sequence (Clean Fixed Camera, 768x576)",
        filename="vtest.avi",
        primary_url="https://raw.githubusercontent.com/opencv/opencv/master/samples/data/vtest.avi",
        mirrors=(
            "https://github.com/opencv/opencv/raw/master/samples/data/vtest.avi",
        ),
        priority=1,
        expected_size_bytes=8131690,
        default_config="configs/datasets/opencv_vtest.yaml",
    ),
    "openvino_people": DatasetMetadata(
        name="openvino_people",
        description="OpenVINO Mall Pedestrian Walkway 1080p Sequence (Clean Ground Plane)",
        filename="people.mp4",
        primary_url="https://storage.openvinotoolkit.org/repositories/openvino_notebooks/data/data/video/people.mp4",
        mirrors=(),
        priority=1,
        expected_size_bytes=3707569,
        default_config="configs/datasets/openvino_people.yaml",
    ),
    "pets2009_s2_l1": DatasetMetadata(
        name="pets2009_s2_l1",
        description="PETS 2009 Benchmark (Sequence S2.L1 View 001 - Multi-Target Walk)",
        filename="pets2009_s2_l1.mp4",
        primary_url="https://raw.githubusercontent.com/sigtot/jpda-python/master/PETS09-S2L1.mp4",
        mirrors=(
            "https://github.com/sigtot/jpda-python/raw/master/PETS09-S2L1.mp4",
        ),
        priority=2,
        expected_size_bytes=13437150,
        default_config="configs/datasets/pets2009_s2_l1.yaml",
    ),
    "mendeley_industrial": DatasetMetadata(
        name="mendeley_industrial",
        description="Mendeley Industrial Safety Dataset (Production Facility CCTV - Unauthorized Machine Intervention)",
        filename="mendeley_unauthorized_intervention.mp4",
        primary_url="https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours/resolve/main/data/1_tr1.mp4",
        mirrors=(),
        priority=1,
        expected_size_bytes=14056111,
        default_config="configs/datasets/mendeley_industrial.yaml",
    ),
    "oxford_town_centre": DatasetMetadata(
        name="oxford_town_centre",
        description="Oxford TownCentre 1080p CCTV Pedestrian Sequence (Loitering & Crossings)",
        filename="TownCentreXVID.avi",
        primary_url="http://www.robots.ox.ac.uk/ActiveVision/Research/Projects/2009bbenfold_headpose/Datasets/TownCentreXVID.avi",
        mirrors=(),
        priority=2,
        default_config="configs/datasets/oxford_town_centre.yaml",
    ),
}


def get_ssl_context():
    """Create a reliable SSL context using certifi or unverified fallback."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return ssl._create_unverified_context()


def download_stream(url: str, target_file: Path, chunk_size: int = 65536) -> bool:
    """
    Download a remote URL to target_file using chunked streaming and progress reporting.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    req = urllib.request.Request(url, headers=headers)
    target_file.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target_file.with_suffix(f"{target_file.suffix}.tmp")
    ssl_ctx = get_ssl_context()

    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as response, open(temp_target, "wb") as out_file:
            content_length = response.getheader("Content-Length")
            total_bytes = int(content_length) if content_length and content_length.isdigit() else None
            downloaded = 0
            start_time = time.perf_counter()

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)

                if total_bytes and total_bytes > 0:
                    pct = (downloaded / total_bytes) * 100.0
                    mb_cur = downloaded / (1024 * 1024)
                    mb_tot = total_bytes / (1024 * 1024)
                    elapsed = max(1e-3, time.perf_counter() - start_time)
                    speed_mb_s = mb_cur / elapsed
                    sys.stdout.write(
                        f"\r  [📥] Progress: {pct:5.1f}% [{mb_cur:5.1f} / {mb_tot:5.1f} MB] ({speed_mb_s:4.1f} MB/s)"
                    )
                    sys.stdout.flush()
                else:
                    mb_cur = downloaded / (1024 * 1024)
                    sys.stdout.write(f"\r  [📥] Downloaded: {mb_cur:5.1f} MB")
                    sys.stdout.flush()

            sys.stdout.write("\n")
            sys.stdout.flush()

        if temp_target.stat().st_size == 0:
            temp_target.unlink(missing_ok=True)
            return False

        temp_target.rename(target_file)
        return True

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as err:
        sys.stdout.write("\n")
        temp_target.unlink(missing_ok=True)
        print(f"  [⚠️] Failed to download from {url}: {err}")
        return False


def fetch_dataset(
    dataset_name: str,
    output_base_dir: Path = REPO_ROOT / "data" / "raw",
    force: bool = False,
) -> Optional[Path]:
    """
    Retrieve dataset assets using primary URL with automated mirror failover.
    """
    if dataset_name not in DATASET_REGISTRY:
        raise ValueError(f"Unknown dataset '{dataset_name}'. Available: {list(DATASET_REGISTRY.keys())}")

    meta = DATASET_REGISTRY[dataset_name]
    dataset_dir = output_base_dir / meta.name
    target_file = dataset_dir / meta.filename

    if target_file.is_file() and target_file.stat().st_size > 0 and not force:
        size_mb = target_file.stat().st_size / (1024 * 1024)
        print(f"[*] Dataset '{meta.name}' already present at: {target_file} ({size_mb:.2f} MB)")
        return target_file

    print(f"[*] Starting download for dataset '{meta.name}' ({meta.description})...")
    urls_to_try = [meta.primary_url] + list(meta.mirrors)

    for i, url in enumerate(urls_to_try, 1):
        print(f"  [Attempt {i}/{len(urls_to_try)}] Fetching: {url}")
        success = download_stream(url, target_file)
        if success:
            size_mb = target_file.stat().st_size / (1024 * 1024)
            print(f"[✅] Successfully downloaded '{meta.name}' to {target_file} ({size_mb:.2f} MB)")
            return target_file

    print(f"[❌] All download mirrors failed for '{meta.name}'.")
    print(f"[ℹ️] You can manually place '{meta.filename}' into: {dataset_dir.resolve()}/")
    return None


def list_datasets(output_base_dir: Path = REPO_ROOT / "data" / "raw") -> None:
    """Print formatted registry catalog with download status."""
    print("=" * 80)
    print(f"{'DATASET NAME':<22} | {'PRIORITY':<8} | {'STATUS':<12} | {'CONFIG PROFILE':<32}")
    print("-" * 80)
    for name, meta in sorted(DATASET_REGISTRY.items(), key=lambda x: (x[1].priority, x[0])):
        target = output_base_dir / meta.name / meta.filename
        if target.is_file() and target.stat().st_size > 0:
            status = f"✅ Present ({target.stat().st_size / (1024*1024):.1f}MB)"
        else:
            status = "❌ Missing"
        priority_str = "P1 (Clean)" if meta.priority == 1 else "P2 (Edge)"
        print(f"{name:<22} | {priority_str:<8} | {status:<12} | {meta.default_config:<32}")
    print("=" * 80)


def parse_args() -> argparse.Namespace:
    """CLI Argument Parser."""
    parser = argparse.ArgumentParser(
        description="Modular Benchmark Dataset Downloader for Industrial Edge Safety Guard",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Dataset identifier to download (e.g. 'opencv_vtest', 'openvino_people', 'pets2009_s2_l1', 'all').",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered datasets, descriptions, and local status.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "raw",
        help="Base directory for downloaded raw datasets.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if target file exists locally.",
    )
    return parser.parse_args()


def main() -> None:
    """Main CLI entrypoint."""
    args = parse_args()

    if args.list or (args.dataset is None):
        list_datasets(args.output_dir)
        if args.dataset is None:
            return

    if args.dataset == "all":
        for ds_name in DATASET_REGISTRY:
            fetch_dataset(ds_name, output_base_dir=args.output_dir, force=args.force)
    else:
        target = fetch_dataset(args.dataset, output_base_dir=args.output_dir, force=args.force)
        if target is None:
            sys.exit(1)


if __name__ == "__main__":
    main()
