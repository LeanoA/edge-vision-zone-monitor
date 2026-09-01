# Tasks: Keypoint Coordinate Inversion & Industrial Ground Calibration

**Change ID:** `keypoint-unletterbox-and-industrial-calibration`  
**Status:** COMPLETED  

---

### Phase 1: Pipeline Keypoint Transformation
- [x] 1.1 Implement vectorized `unletterbox_keypoints` in `src/pipeline/safety_pipeline.py`
- [x] 1.2 Refactor `extract_ground_anchor` in `src/pipeline/safety_pipeline.py` for native frame space calculations
- [x] 1.3 Apply `unletterbox_keypoints` in `SafetyPipeline.parse_detections` to populate unletterboxed coordinates in `PoseDetection`

### Phase 2: Unit & Integration Tests
- [x] 2.1 Add unit tests for `unletterbox_keypoints` (letterbox and pillarbox) in `tests/test_pipeline.py`
- [x] 2.2 Update and verify `PoseDetection` keypoints assertions in `tests/test_pipeline.py`

### Phase 3: Verification & Execution
- [x] 3.1 Run full test suite (`pytest`) to guarantee 100% pass rate (166/166 passed)
- [x] 3.2 Execute `mendeley_industrial` test harness and verify telemetry and snapshot alignment
