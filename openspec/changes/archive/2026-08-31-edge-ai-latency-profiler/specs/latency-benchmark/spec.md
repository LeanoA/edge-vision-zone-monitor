# Specification: latency-benchmark (Delta)

## MODIFIED Requirements

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
