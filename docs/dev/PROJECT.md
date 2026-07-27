# Project: macro_intelligence_platform
# Scope: RRG Sector Rotation Integration

## Architecture
- `integrations/rrg`: vendored RRG code.
- `analytics`: add modules for RRG quadrant classification and alignment with monthly macro data.
- `features`: contingency table, chi-square test, predictive signal modeling.
- `api.py`: expose `SectorRotationResult` and `sector_rotation_signal`.
- `ui`/`exports`: JSON exports, PDF narrative, static site updates.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Phase A: Plumbing | Vendor RRG code via git subtree, build `classify_rrg_quadrant`, resample weekly data to month-end. | none | IN_PROGRESS |
| 2 | Phase B: Descriptive Validation | Contingency table (macro quadrant x RRG quadrant), chi-square/Fisher's test, decision gate (stop if nothing significant). | M1 | PLANNED |
| 3 | Phase C: Predictive Signal | Forward relative return models, Diebold-Mariano test on held-out window. (Only if M2 passes) | M2 | PLANNED |
| 4 | Phase D & E: Expose and Wire API | `SectorRotationResult` dataclass, API function, exports, PDF, `publish.yml` integration. | M3 | PLANNED |

## Interface Contracts
### `analytics` ↔ `features`
- `build_aligned_panel` output should seamlessly feed into the descriptive validation and predictive modeling pipelines.
- `SectorRotationResult` dataclass format should align with existing API design patterns.

## Code Layout
- Root: `macro_intelligence_platform`
- Modules: `analytics`, `features`, `ui`, `exports`, `scripts`, `tests`
