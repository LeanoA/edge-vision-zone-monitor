# Specification: Latency Benchmark (`latency-benchmark`)

## Overview
The `latency-benchmark` capability provides an edge-specific performance profiling CLI (`scripts/benchmark.py`) to measure inference latency and throughput under controlled execution conditions. It validates compliance with the critical industrial edge safety budget ($t_{\text{infer}} \le 30\text{ ms}$, equivalent to $\ge 33.3\text{ FPS}$ at p95) on target hardware (Apple Silicon M1 / ARM64).

## ADDED Requirements

### Requirement: Latency Warmup and Statistical Profiling
The benchmark utility MUST implement a high-resolution timing loop using `time.perf_counter_ns()` consisting of an initial warmup phase (minimum 50 iterations) to purge JIT and cache cold-start effects, followed by a measurement phase (minimum 200 iterations).

#### Scenario: Executing warmup and measurement cycles
- **GIVEN** an exported ONNX model and default benchmark parameters (`warmup=50`, `iterations=200`)
- **WHEN** `python scripts/benchmark.py --model models/yolo11n-pose.onnx` is invoked
- **THEN** exactly 50 forward passes SHALL be executed without recording timings
- **AND** exactly 200 timed forward passes SHALL be executed sequentially using synthetic input tensors of shape `(1, 3, 640, 640)`
- **AND** each iteration latency SHALL be measured in nanoseconds via `time.perf_counter_ns()`.

---

### Requirement: Percentile Metrics and FPS Throughput Calculation
The benchmark profiler MUST compute and report comprehensive statistical metrics, including arithmetic mean, standard deviation, p50 (median), p95, and p99 latency percentiles in milliseconds, as well as throughput in frames per second (FPS).

#### Scenario: Calculating distribution percentiles
- **GIVEN** 200 measured inference latency samples in milliseconds
- **WHEN** statistical evaluation runs
- **THEN** the profiler SHALL compute:
  - `mean_ms`: sum of latencies divided by 200
  - `std_ms`: sample standard deviation
  - `p50_ms`: 50th percentile (median) latency
  - `p95_ms`: 95th percentile latency
  - `p99_ms`: 99th percentile latency
  - `fps`: throughput calculated as `1000.0 / mean_ms`.

---

### Requirement: Real-Time Edge Safety Budget Verification
The benchmark CLI MUST evaluate the measured p95 latency against the edge safety budget threshold ($t_{\text{infer}} \le 30.0\text{ ms}$). When running in strict verification mode (`--strict`), it MUST return a non-zero exit code if the budget is breached.

#### Scenario: Benchmark passes edge safety budget
- **GIVEN** benchmark results where `p95_ms` is measured at $22.4\text{ ms}$ (less than or equal to $30.0\text{ ms}$)
- **WHEN** the budget assertion check executes
- **THEN** the utility SHALL output a status indicating budget compliance: `PASS (p95 <= 30.0 ms)`
- **AND** the process SHALL exit with code 0.

#### Scenario: Benchmark breaches edge safety budget in strict mode
- **GIVEN** benchmark results where `p95_ms` is measured at $34.2\text{ ms}$ (exceeding the $30.0\text{ ms}$ threshold)
- **WHEN** the utility runs with `--strict`
- **THEN** the utility SHALL output a status indicating budget violation: `FAIL (p95 > 30.0 ms)`
- **AND** the process SHALL terminate with exit code 1.

---

### Requirement: Benchmark Structured Reporting and Machine-Readable Export
The benchmark CLI SHALL format the profiling results in an aligned console summary table and SHOULD support exporting the benchmark metrics to a structured JSON file via `--json-out <path>`.

#### Scenario: Generating human-readable console table
- **GIVEN** completed benchmark execution
- **WHEN** output is rendered to stdout
- **THEN** an aligned table displaying model path, active execution provider, sample count, mean, std, p50, p95, p99, and FPS SHALL be rendered.

#### Scenario: Exporting metrics to JSON
- **GIVEN** execution with flag `--json-out benchmark_results.json`
- **WHEN** the benchmark run completes
- **THEN** a valid JSON document SHALL be written to `benchmark_results.json` containing keys: `model_path`, `provider`, `warmup_iterations`, `iterations`, `metrics` (`mean_ms`, `std_ms`, `p50_ms`, `p95_ms`, `p99_ms`, `fps`), `budget_ms`, and `passed`.

---

### Requirement: Dual Distribution Latency Profiling
The latency benchmark and profiling engine SHALL report two distinct statistical distributions:
1. **Per-Frame System Latency ($T_{\text{system}}$)**: Granular per-stage breakdown ($T_{\text{capture}}$, $T_{\text{pre}}$, $T_{\text{infer}}$, $T_{\text{pose}}$, $T_{\text{geom}}$, $T_{\text{track}}$, $T_{\text{fsm}}$) with mean, p50, p95, and p99 percentiles.
2. **Physical Safety Event Latency ($T_{\text{event}}$)**: Distribution of reaction latencies measured from initial physical zone entry to safety trip assertion.

#### Scenario: Normal Debounced Intrusion Reaction Time
- **GIVEN** a worker entering $P_{\text{danger}}$ at normal approach speed at $30\text{ fps}$ ($\Delta t = 33.3\text{ ms}$) with $N_{\text{confirm}} = 3$
- **WHEN** the FSM confirms the intrusion and trips the safety relay
- **THEN** the recorded $T_{\text{event}}$ SHALL measure $(3 - 1) \times 33.3\text{ ms} + T_{\text{system}} \approx 66.7\text{ ms} + T_{\text{system}}$.

#### Scenario: Fast Approach Instant Bypass Reaction Time
- **GIVEN** a worker approaching $P_{\text{danger}}$ at $v_n \ge 1.6\text{ m/s}$ (ISO 13855 fast approach)
- **WHEN** the intrusion is detected on frame 1
- **THEN** the debounce counter SHALL be bypassed ($N_{\text{confirm}} = 1$)
- **AND** the recorded $T_{\text{event}}$ SHALL equal $T_{\text{system}}$.
