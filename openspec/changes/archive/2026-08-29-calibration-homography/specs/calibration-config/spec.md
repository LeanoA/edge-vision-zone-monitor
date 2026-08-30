# Specification: Calibration Configuration (`calibration-config`)

## Overview
The `calibration-config` capability defines the declarative YAML configuration schema and validation pipeline for camera parameters, coplanar calibration point correspondences (mapping 2D pixel coordinates to metric ground-plane coordinates in meters), and reprojection accuracy bounds. It guarantees that spatial transformation configurations are complete, strictly typed, geometrically admissible, and well-formed before initializing homography projection components.

## ADDED Requirements

### Requirement: Declarative YAML Calibration Configuration Structure
The system MUST provide a structured YAML configuration schema (e.g. `configs/default_config.yaml`) containing camera resolution parameters, coplanar calibration correspondences, and reprojection error tolerance thresholds.

#### Scenario: Loading and parsing valid YAML calibration file
- **GIVEN** a valid YAML configuration file containing `camera` dimensions and a `calibration` block with paired `image_points` and `world_points`
- **WHEN** the configuration loader parses the file
- **THEN** the configuration SHALL be deserialized into a typed configuration dictionary or data structure
- **AND** all required sections (`camera`, `calibration`) SHALL be present and accessible.

#### Scenario: Handling missing or unreadable configuration file
- **GIVEN** a configuration file path that does not exist or lacks read permissions
- **WHEN** the configuration loader attempts to load the file
- **THEN** the loader SHALL raise a `FileNotFoundError` or `IOError`
- **AND** the error message SHALL specify the missing file path.

---

### Requirement: Calibration Correspondence Cardinality and 1:1 Matching
The calibration schema MUST enforce that point correspondences contain at least 4 coplanar pairs ($N \ge 4$), and that the number of 2D image points matches the number of ground-plane world points exactly ($N_{\text{image}} = N_{\text{world}}$).

#### Scenario: Validating sufficient point correspondences (N >= 4)
- **GIVEN** a calibration configuration specifying 4 or more corresponding point pairs
- **WHEN** the schema validator validates point correspondence cardinality
- **THEN** the validation SHALL succeed without raising an exception.

#### Scenario: Rejecting insufficient point correspondences (N < 4)
- **GIVEN** a calibration configuration containing fewer than 4 point correspondences (e.g., 3 point pairs)
- **WHEN** the schema validator validates the configuration
- **THEN** the validator SHALL raise a `ValueError` indicating that at least 4 point correspondences are required for planar homography estimation.

#### Scenario: Rejecting mismatched point correspondence counts
- **GIVEN** a calibration configuration where `image_points` has $N$ elements and `world_points` has $M$ elements where $N \ne M$
- **WHEN** the schema validator validates correspondence alignment
- **THEN** the validator SHALL raise a `ValueError` detailing the count mismatch between image points and world points.

#### Scenario: Rejecting empty point arrays
- **GIVEN** a calibration configuration with an empty list or null value for `image_points` or `world_points`
- **WHEN** the schema validator processes the configuration
- **THEN** the validator SHALL raise a `ValueError` indicating that calibration points cannot be empty.

---

### Requirement: Coordinate Data Type and Boundary Validation
The calibration schema MUST enforce strict data typing and coordinate domain bounds on all configuration fields, ensuring image coordinates $(u, v)$ reside within camera resolution bounds and metric coordinates $(X_w, Y_w)$ represent valid real-world measurements in meters.

#### Scenario: Validating numerical coordinate types within image boundaries
- **GIVEN** camera resolution $W = 1920, H = 1080$ and image points with coordinates $0 \le u \le W$ and $0 \le v \le H$
- **WHEN** coordinate boundary validation is executed
- **THEN** all point coordinates SHALL be validated as finite floating-point or integer numbers
- **AND** no coordinate out-of-bounds error SHALL be raised.

#### Scenario: Rejecting non-numeric coordinate values
- **GIVEN** a calibration point entry containing string or non-numerical values (e.g., `["x", 100]`)
- **WHEN** the schema validator checks coordinate types
- **THEN** the validator SHALL raise a `TypeError` or `ValueError` identifying the non-numeric field.

#### Scenario: Rejecting image points exceeding camera frame dimensions
- **GIVEN** camera resolution $W = 1920, H = 1080$ and an image point $(u, v) = (2048, 500)$ exceeding frame width
- **WHEN** boundary validation is performed
- **THEN** the validator SHALL raise a `ValueError` indicating that pixel coordinate $(2048, 500)$ exceeds the camera resolution bounds.

#### Scenario: Validating camera resolution parameters
- **GIVEN** camera configuration fields `width`, `height`, and optional `fps`
- **WHEN** camera dimensions are evaluated
- **THEN** `width` and `height` MUST be positive integers greater than zero
- **AND** non-positive or non-integer resolution specifications SHALL raise a `ValueError`.

---

### Requirement: Reprojection Threshold Configuration
The configuration schema SHALL define an optional or defaulted `reprojection_threshold_rmse` parameter specifying the maximum acceptable root mean square error in meters, defaulting to $0.05\text{ m}$.

#### Scenario: Utilizing explicit reprojection threshold
- **GIVEN** a configuration defining `reprojection_threshold_rmse: 0.03`
- **WHEN** the calibration parameters are loaded
- **THEN** the active reprojection threshold SHALL be set to $0.03\text{ m}$.

#### Scenario: Applying default reprojection threshold when omitted
- **GIVEN** a configuration omitting the `reprojection_threshold_rmse` key
- **WHEN** the calibration parameters are loaded
- **THEN** the active reprojection threshold SHALL default to $0.05\text{ m}$.

#### Scenario: Rejecting non-positive reprojection threshold
- **GIVEN** a configuration specifying `reprojection_threshold_rmse: -0.01` or `reprojection_threshold_rmse: 0.0`
- **WHEN** threshold validation is performed
- **THEN** the validator SHALL raise a `ValueError` requiring a strictly positive reprojection error bound.
