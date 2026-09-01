# Specification: Dataset Downloader (`dataset-downloader`)

## NEW Capabilities

### Capability: Automated Benchmark Dataset Downloading
The `download_datasets.py` CLI script and helper library MUST provide automated, robust retrieval, verification, and extraction of empirical surveillance video benchmarks:

1. **Dataset Registry Support**:
   - The downloader MUST maintain a registry of known datasets, at minimum supporting `opencv_vtest`, `openvino_people`, `pets2009_s2_l1`, and `oxford_town_centre`.
   - Each registry entry MUST specify target file name, primary download URL, mirror URLs, and target configuration path.

2. **Mirror Failover and Resilience**:
   - When attempting download, the downloader MUST attempt the primary URL first.
   - If the primary URL fails (HTTP 4xx, 5xx, timeout, connection error), the downloader MUST sequentially attempt registered mirrors.
   - If all remote endpoints fail, the downloader MUST output clear instructions for manual placement in `data/raw/<dataset_name>/`.

3. **Integrity and Non-Destructive Storage**:
   - Downloads MUST be saved into `data/raw/<dataset_name>/<filename>`.
   - If the target file already exists and is non-empty, the downloader MUST skip downloading unless `--force` is specified.
   - The CLI MUST support `--list` to show all available datasets and their download status.

#### Scenario: Successful baseline dataset download
- **GIVEN** an active network connection and dataset name `opencv_vtest`
- **WHEN** `python scripts/download_datasets.py --dataset opencv_vtest` is executed
- **THEN** the script SHALL download `vtest.avi` into `data/raw/opencv_vtest/`
- **AND** the downloaded file SHALL be non-empty ($> 1\text{ MB}$).

#### Scenario: Existing file skip behavior
- **GIVEN** `data/raw/opencv_vtest/vtest.avi` already exists
- **WHEN** `python scripts/download_datasets.py --dataset opencv_vtest` is executed without `--force`
- **THEN** the script SHALL report that the dataset is already present and skip network requests.

#### Scenario: Listing datasets
- **WHEN** `python scripts/download_datasets.py --list` is executed
- **THEN** the script SHALL output a formatted table showing available dataset names, descriptions, priorities, and local presence status.
