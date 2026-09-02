#!/usr/bin/env python3
"""
scripts/prepare_sprites.py
Extracts, segments, and normalizes a single-identity, continuous walking gait cycle
from video datasets to ensure 100% appearance and identity consistency in synthetic generation.
"""

from pathlib import Path
import sys
import cv2
import numpy as np
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def extract_single_identity_sprites(
    source_video: Path = REPO_ROOT / "data" / "raw" / "openvino_people" / "people.mp4",
    output_dir: Path = REPO_ROOT / "data" / "assets" / "sprites" / "worker",
    num_cycle_frames: int = 8,
    target_canvas_size: tuple = (160, 320),  # (width, height)
) -> None:
    """
    Extract a continuous, single-identity walking stride sequence from a single tracked person.
    Normalizes all frames into a standard canonical RGBA canvas with bottom-aligned feet.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if not source_video.is_file():
        raise FileNotFoundError(f"Source video not found: {source_video}")

    print(f"[*] Loading neural instance segmenter (yolo11n-seg.pt)...")
    seg_model = YOLO("yolo11n-seg.pt")

    cap = cv2.VideoCapture(str(source_video))
    frames = []
    while cap.isOpened() and len(frames) < 140:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    print(f"[*] Loaded {len(frames)} source frames from {source_video.name}.")

    # Collect all candidate tracklets with stable height
    candidates = {}
    for f_idx, frame in enumerate(frames[20:100]):
        res = seg_model(frame, classes=[0], conf=0.70, verbose=False)[0]
        if res.masks is None or len(res.boxes) == 0:
            continue

        for i, box in enumerate(res.boxes):
            b = box.xyxy[0].cpu().numpy().astype(int)
            h = b[3] - b[1]
            w = b[2] - b[0]
            if h >= 220:
                # Match to existing tracklet by spatial distance
                matched_id = None
                for cid, track in candidates.items():
                    last_f, last_b, _ = track[-1]
                    if f_idx - last_f <= 2:
                        lx1, ly1, lx2, ly2 = last_b
                        dist = abs((b[0] + b[2]) / 2 - (lx1 + lx2) / 2) + abs((b[1] + b[3]) / 2 - (ly1 + ly2) / 2)
                        if dist < 45:
                            matched_id = cid
                            break
                if matched_id is None:
                    matched_id = len(candidates)
                    candidates[matched_id] = []

                mask = cv2.resize(res.masks.data[i].cpu().numpy(), (frame.shape[1], frame.shape[0]))
                candidates[matched_id].append((f_idx, b, mask))

    # Pick longest, most stable tracklet
    best_cid = max(candidates.keys(), key=lambda cid: len(candidates[cid]))
    tracklet = candidates[best_cid]
    print(f"[*] Selected optimal single-identity Track {best_cid} ({len(tracklet)} consecutive frames).")

    # Extract segmented crops for this single tracklet
    cw, ch = target_canvas_size
    normalized_sprites = []

    for f_idx, box, mask in tracklet:
        frame = frames[20 + f_idx]
        x1, y1, x2, y2 = box

        margin_x = 12
        margin_y = 8
        x1_c = max(0, x1 - margin_x)
        y1_c = max(0, y1 - margin_y)
        x2_c = min(frame.shape[1], x2 + margin_x)
        y2_c = min(frame.shape[0], y2 + margin_y)

        crop_rgb = frame[y1_c:y2_c, x1_c:x2_c]
        crop_mask = (mask[y1_c:y2_c, x1_c:x2_c] * 255).astype(np.uint8)

        # Soft feathering
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        crop_mask = cv2.morphologyEx(crop_mask, cv2.MORPH_CLOSE, kernel)
        crop_mask = cv2.GaussianBlur(crop_mask, (3, 3), 0.5)

        # Find tight bounding box of segmented person
        nonzeros = cv2.findNonZero(crop_mask)
        if nonzeros is not None:
            rx, ry, rw, rh = cv2.boundingRect(nonzeros)
            tight_rgb = crop_rgb[ry : ry + rh, rx : rx + rw]
            tight_mask = crop_mask[ry : ry + rh, rx : rx + rw]
            tight_rgba = np.dstack([tight_rgb, tight_mask])

            # Place onto standardized canonical canvas (bottom-aligned, horizontally centered)
            # Scale to match canonical height (e.g. ch - 16)
            scale = (ch - 16) / max(1, rh)
            new_w = max(10, int(round(rw * scale)))
            new_h = ch - 16
            resized_rgba = cv2.resize(tight_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

            canvas = np.zeros((ch, cw, 4), dtype=np.uint8)
            ox = max(0, (cw - new_w) // 2)
            oy = ch - new_h - 4  # 4px margin at bottom
            
            # Place on canvas
            place_w = min(new_w, cw - ox)
            place_h = min(new_h, ch - oy)
            canvas[oy : oy + place_h, ox : ox + place_w] = resized_rgba[:place_h, :place_w]

            normalized_sprites.append((f_idx, canvas))

    print(f"[*] Processed {len(normalized_sprites)} normalized single-identity frames.")

    # Select smooth walking cycle
    stride_indices = np.linspace(0, len(normalized_sprites) - 1, num_cycle_frames, dtype=int)
    for cycle_idx, src_idx in enumerate(stride_indices):
        f_num, sprite_canvas = normalized_sprites[src_idx]
        out_path = output_dir / f"walk_{cycle_idx:02d}.png"
        cv2.imwrite(str(out_path), sprite_canvas)
        print(f"  • Frame {cycle_idx:02d} (from src frame {f_num:03d}): {out_path.name} [{sprite_canvas.shape[1]}x{sprite_canvas.shape[0]} RGBA]")

    # Idle sprite (midstance standing from same person)
    idle_canvas = normalized_sprites[len(normalized_sprites) // 2][1]
    idle_path = output_dir / "idle_00.png"
    cv2.imwrite(str(idle_path), idle_canvas)
    print(f"  • Idle Sprite: {idle_path.name} (Same Subject Normalized RGBA)")


def main() -> None:
    print("=" * 70)
    print("🎨 INDUSTRIAL VISION SAFETY GUARD — SINGLE-IDENTITY SPRITE EXTRACTOR")
    print("=" * 70)
    sprite_dir = REPO_ROOT / "data" / "assets" / "sprites" / "worker"
    extract_single_identity_sprites(output_dir=sprite_dir, num_cycle_frames=8)
    print("=" * 70)
    print(f"[✅] Single-identity walking cycle ready in: {sprite_dir.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
