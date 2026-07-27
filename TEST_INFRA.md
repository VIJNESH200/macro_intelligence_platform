# E2E Test Infra: macro_intelligence_platform

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | `classify_rrg_quadrant` function | ORIGINAL_REQUEST §R1 | 5      | 5      | ✓      |
| 2 | `build_aligned_panel` alignment | ORIGINAL_REQUEST §R1 | 5      | 5      | ✓      |
| 3 | Descriptive Validation & Gate | ORIGINAL_REQUEST §R2 | 5      | 5      | ✓      |
| 4 | Predictive Signal & Testing | ORIGINAL_REQUEST §R3 | 5      | 5      | ✓      |
| 5 | API Export & Notebook | ORIGINAL_REQUEST §R4 | 5      | 5      | ✓      |

## Test Architecture
- Test runner: `pytest tests/e2e/`
- Test case format: pytest functions with mock/synthetic data.
- Directory layout:
  - `tests/e2e/test_tier1_feature.py`
  - `tests/e2e/test_tier2_boundary.py`
  - `tests/e2e/test_tier3_cross_feature.py`
  - `tests/e2e/test_tier4_workload.py`
- Pass/Fail semantics: 0 exit code on success. Since implementation is missing, tests will fail initially. E2E track only *writes* the tests.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full pipeline from raw data to API result | F1, F2, F3, F4, F5 | High     |
| 2 | Early termination at descriptive validation gate | F1, F2, F3 | Medium   |
| 3 | Missing observations flagged in contingency | F2, F3 | Medium   |
| 4 | Synthetic failing predictive signal | F4 | Medium   |
| 5 | Successful predictive signal with notebook | F4, F5 | High     |

## Coverage Thresholds
- Tier 1: ≥5 per feature (25 total)
- Tier 2: ≥5 per feature (where boundaries exist) (25 total)
- Tier 3: pairwise coverage of major feature interactions (10 total)
- Tier 4: ≥5 realistic application scenarios (5 total)
