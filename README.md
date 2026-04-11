# Open Data Eval

> What is good data? We're building the eval suite to answer that.

[![Datasets Audited](https://img.shields.io/badge/datasets%20audited-108-blue)](https://github.com/Varun-Nair/open-data-eval)
[![License](https://img.shields.io/badge/license-CC--BY--4.0-green)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](https://github.com/Varun-Nair/open-data-eval/issues)

We verified every URL. Checked every license across 4 sources. Documented every modality. 69% have no license. 5% have broken downloads.

## Phase 0 Results

| Metric | Value |
|--------|-------|
| Datasets audited | 108 |
| Total video hours | 23,000+ |
| Fully accessible | 100 (93%) ✅ |
| Broken downloads | 5 (5%) ⚠️ |
| Dead links | 1 (1%) ❌ |
| Redirects | 2 (2%) 🔄 |
| **No license specified** | **74 of 108 (69%)** |

### URL Status
```
Live                ████████████████████████████████████████████ 100
Broken download     ██ 5
Redirect            █ 2
Dead                █ 1
```

### Access Level
```
Open                ████████████████████████████████████████████ 78
Gated-Open          ██████████ 19
Restricted          ██████ 10
Unavailable         █ 1
```

### License
```
Not specified       ████████████████████████████████████████████ 74
CC-BY-NC-4.0        ███████ 12
Custom Academic     ████████ 14
CC-BY-4.0           █ 2
CC-BY-NC-SA-4.0     █ 2
CC-BY-NC-ND-4.0     █ 1
S-Lab License       █ 1
Mixed               █ 1
Custom Open         █ 1
```

### Modalities (across all 108 datasets)
```
RGB Video           ████████████████████████████████████████████ 108
Eye Gaze            █████████████ 32
Hand Pose           ██████████ 24
IMU                 █████████ 23
Body Pose           █████████ 22
Audio               ████████ 19
Depth (RGB-D)       ████████ 19
3D Point Clouds     ██████ 14
SLAM/Odometry       ████ 10
Narrations          ████ 9
3D Scene Recon.     ████ 8
Motion Capture      ███ 6
Depth (Stereo)      ███ 6
Optical Flow        █ 2
Object Tracking     █ 1
Multi-view          █ 1
mmWave              █ 1
Hand Masks          █ 1
```

## Accessibility Rankings

Which datasets are easiest to actually get and use?

| Rank | Dataset | Score | Access | License | Summary |
|------|---------|-------|--------|---------|---------|
| 1 | EPIC-KITCHENS-100 | 9.8 | Open | CC-BY-NC-4.0 | Gold standard kitchen ego dataset. 3 download options incl. Academic Torrents. |
| 2 | HO-Cap | 9.5 | Open | CC-BY-4.0 | Multi-view RGB-D with HoloLens ego. Best-licensed hand-object dataset. |
| 3 | EPIC-KITCHENS-55 | 9.2 | Open | CC-BY-NC-4.0 | Superseded by EK-100 but still clean and fully accessible. |
| 4 | DexYCB | 9.2 | Open | CC-BY-NC-4.0 | NVIDIA multi-view hand-grasping benchmark. Direct download, confirmed license. |
| 5 | EgoDex | 9.2 | Open | CC-BY-NC-ND-4.0 | 829h from Apple Vision Pro. Direct curl download from Apple CDN. |

Full rankings: [`data/ego-datasets/accessibility_rankings.csv`](data/ego-datasets/accessibility_rankings.csv)

*Ranked by ease of access, not dataset quality. Quality scoring comes in Phase 1.*

## Scoring Methodology

Ease of Access scores (0-10) are computed from six components:

| Component | Max Points | How |
|-----------|-----------|-----|
| Access Level | 3 | Open=3, Gated=2, Restricted=1, Unavailable=0 |
| URL Status | 2 | Live=2, Broken/Redirect=1, Dead=0 |
| License Clarity | 2 | Standard license (CC-BY, MIT, Apache)=2, Named custom=1, None=0 |
| Documentation | 1.5 | Excellent=1.5, Good=1, Basic=0.5, None=0 |
| Dataloader | 1 | Available=1, None=0 |
| Commercial Clarity | 0.5 | Explicitly permitted=0.5, Explicitly banned=0.25, Unclear=0 |

*These weights are v1. We'll refine based on researcher feedback and Phase 3 derivative scoring.*

## Top Issues

| Dataset | Issue | Severity |
|---------|-------|----------|
| FPVO | Primary URL dead. Dataset unavailable. | High |
| EgoSim | Download availability not confirmed. | High |
| ADL4D | Download availability not confirmed. | High |
| VEDB | Download availability not confirmed. | High |
| EgoCampus | Download availability not confirmed. | High |
| Sanctuaria-Gaze | Download availability not confirmed. | High |
| EasyCom | Download availability not confirmed. | High |
| MultiEgo | Download availability not confirmed. | High |
| CEN | Download availability not confirmed. | High |
| PEDESTRIAN | Download availability not confirmed. | High |
| EgoBlind | Download availability not confirmed. | High |
| EgoExOR | Download availability not confirmed. | High |
| EgoVid-5M | Open data with no license specified. | Medium |
| GTEA | Open data with no license specified. | Medium |
| EGTEA Gaze+ | Open data with no license specified. | Medium |
| HOI4D | Open data with no license specified. | Medium |
| EgoHumans | Open data with no license specified. | Medium |
| EgoExoLearn | Open data with no license specified. | Medium |
| EgoProceL | Open data with no license specified. | Medium |
| EgoObjects | Open data with no license specified. | Medium |
| DR(eye)VE | Open data with no license specified. | Medium |
| EgoTaskQA | Open data with no license specified. | Medium |

*58 open datasets total have no license specified. Full list: [`issues_and_findings.csv`](data/ego-datasets/issues_and_findings.csv)*

## Data Files

- [`data/ego-datasets/ego_dataset_catalog.csv`](data/ego-datasets/ego_dataset_catalog.csv) — full catalog, 33 fields per dataset
- [`data/ego-datasets/accessibility_rankings.csv`](data/ego-datasets/accessibility_rankings.csv) — all 108 datasets ranked by ease of access
- [`data/ego-datasets/access_summary.csv`](data/ego-datasets/access_summary.csv) — aggregate counts by access level, license, modality, and category
- [`data/ego-datasets/issues_and_findings.csv`](data/ego-datasets/issues_and_findings.csv) — flagged issues (dead links, unverified downloads, missing licenses)
- [`data/ego-datasets/datasets_by_category.csv`](data/ego-datasets/datasets_by_category.csv) — datasets grouped and ranked within each category
- [`data/ego-datasets/datasets_by_family.csv`](data/ego-datasets/datasets_by_family.csv) — dataset family groupings (EPIC-KITCHENS, Project Aria, Ego4D, etc.)
- [`data/ego-datasets/catalog_health_report.csv`](data/ego-datasets/catalog_health_report.csv) — per-dataset completeness audit (missing fields)

## Roadmap

- [x] Phase 0: Complete catalog — all 100+ ego datasets
- [ ] Phase 1: Automated quality scoring (hand visibility, scene diversity, technical quality)
- [ ] Phase 2: Robot dataset catalog & scoring
- [ ] Phase 3: Derivative scoring (which data produces better models?)
- [ ] Phase 4: Interactive leaderboard & community platform

## 5-Layer Scoring Framework

| Layer | Name | Signals |
|-------|------|---------|
| 1 | Technical Quality | Resolution, fps, sharpness, frame drops |
| 2 | Content Quality | Hand visibility, action density, tool use, scene diversity |
| 3 | Collective Quality | Diversity indices, balance, coverage, scale |
| 4 | Derivative Quality | Downstream model lift — which data actually makes models better |
| 5 | Accessibility | Can you actually get and use it |

## Contributing

Open an issue or PR. Community contributions welcome.

## Citation

```bibtex
@misc{open-data-eval,
  author = {Varun Nair},
  title  = {Open Data Eval: The Definitive Data Quality Evaluation Suite for Multimodal AI/ML Datasets},
  year   = {2026},
  url    = {https://github.com/Varun-Nair/open-data-eval}
}
```

---

*Licensed under [CC-BY-4.0](LICENSE). Copyright Varun Nair 2026.*
