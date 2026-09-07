## 📊 Functional Quality, Multi-Object Tracking & Reaction Profile

### 1. Sequence A Clean Incursion (Calibrated Ground Truth, 180 frames)
- **MOTA (Multi-Object Tracking Accuracy):** `0.9611` (96.1%)
- **IDF1 (Identity Preservation F1):** `0.9808` (98.1%)
- **Precision / Recall:** `0.9676` / `0.9944`
- **ID Switches ($IDS$):** `0` | **Ghost Tracks:** `1` | **False Positives:** `6`
- **Leading Ankle Entry Frame:** `Frame 50`
- **Body Centroid Entry Frame:** `Frame 54`
- **Safety Relay Trip Frame:** `Frame 52`
- **Physical Reaction Latency (from Ankle):** `+66.67 ms` (Debounce: `2 frames` @ 30 FPS)
- **Lead Margin (vs Body Centroid):** `-66.67 ms` (Trip asserted ahead of centroid entry due to stride reach)

### 2. PETS2009 Crowd & Dynamic Occlusion Tracking Ablation
- **Evaluated Frames:** `200` frames
- **Throughput:** `49.4 FPS` (Mean $T_1$: `19.67 ms`)
- **Unique Tracks Handled:** `3`
- **Danger Intrusions:** `5` frames
- **Lockout / Coasting Frames:** `135` frames
- **Coasting Safety Invariant Verified:** `✅ PASS`
