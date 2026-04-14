# Open Data Eval

> What is good data? We're building the definitive quality evaluation suite for AI/ML datasets.

[![Datasets Audited](https://img.shields.io/badge/datasets%20audited-103-blue)](https://github.com/Varun-Nair/open-data-eval)
[![Quality Profiles](https://img.shields.io/badge/quality%20profiles-16-5b21b6)](https://varun-nair.github.io/open-data-eval/scorecard/)
[![Live Scorecard](https://img.shields.io/badge/scorecard-live-059669)](https://varun-nair.github.io/open-data-eval/scorecard/)
[![ISO 5259-2](https://img.shields.io/badge/ISO%205259--2-aligned-0369a1)](https://www.iso.org/standard/81088.html)
[![License](https://img.shields.io/badge/license-CC--BY--4.0-green)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](https://github.com/Varun-Nair/open-data-eval/issues)

We audit ML datasets the way code gets audited — systematically, quantitatively, transparently.

---

## Live Scorecard

**[varun-nair.github.io/open-data-eval/scorecard/](https://varun-nair.github.io/open-data-eval/scorecard/)**

Interactive quality profiles for 16 egocentric and manipulation datasets. Scores computed from catalog metadata and paper research. ISO/IEC 5259-2 aligned.

![Scorecard preview](docs/assets/scorecard-preview.png)

---

## Quick Start

1. **Browse the scorecard** → [varun-nair.github.io/open-data-eval/scorecard/](https://varun-nair.github.io/open-data-eval/scorecard/)
2. **Pick a dataset** → use the dropdown or Compare view to find what fits your use case
3. **Read its quality profile** → `data/quality-profiles/profiles/<dataset>.qp.json`

---

## What We Evaluate

| Dimension | What it measures | Status |
|-----------|-----------------|--------|
| Technical | FPS, resolution, audio | ✅ Live |
| Accessibility | License, download, docs | ✅ Live |
| Reliability | Calibration, annotation coverage | ✅ Live |
| Scale & Diversity | Hours, environments, participants | ✅ Live |
| Downstream Fit | Modality fit per use-case | ✅ Live |
| Content Quality | Hand visibility, scene diversity | 🔜 Phase 1b |
| Derivative | Model lift per dataset | 🔜 Phase 3 |

---

## Dataset Catalog

103 egocentric video datasets audited across 33 fields each.

| Metric | Value |
|--------|-------|
| Datasets audited | 103 |
| Total video hours | 23,000+ |
| Fully accessible | 94 (91%) |
| Broken downloads | 5 (5%) |
| Dead links | 2 (2%) |
| **No license specified** | **67 of 103 (65%)** |

### URL Status
```
Live                ████████████████████████████████████████████ 94
Broken download     ██ 5
Redirect            █ 2
Dead                █ 2
```

### Access Level
```
Open                ████████████████████████████████████████████ 74
Gated-Open          ██████████ 19
Restricted          █████ 9
Unavailable         █ 1
```

### License
```
Not specified       ████████████████████████████████████████████ 67
Custom Academic     ████████ 14
CC-BY-NC-4.0        ███████ 12
CC-BY-4.0           █ 2
CC-BY-NC-SA-4.0     █ 2
Apache-2.0          █ 2
S-Lab License       █ 1
Mixed               █ 1
Custom Open         █ 1
```

### Modalities (across all 103 datasets)
```
RGB Video           ████████████████████████████████████████████ 103
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
```

### Accessibility Rankings

Which datasets are easiest to actually get and use?

| Rank | Dataset | Score | Access | License | Summary |
|------|---------|-------|--------|---------|---------|
| 1 | EPIC-KITCHENS-100 | 9.8 | Open | CC-BY-NC-4.0 | Gold standard kitchen ego dataset. 3 download options incl. Academic Torrents. |
| 2 | HO-Cap | 9.5 | Open | CC-BY-4.0 | Multi-view RGB-D with HoloLens ego. Best-licensed hand-object dataset. |
| 3 | EPIC-KITCHENS-55 | 9.2 | Open | CC-BY-NC-4.0 | Superseded by EK-100 but still clean and fully accessible. |
| 4 | DexYCB | 9.2 | Open | CC-BY-NC-4.0 | NVIDIA multi-view hand-grasping benchmark. Direct download, confirmed license. |
| 5 | EgoDex | 9.2 | Open | CC-BY-NC-ND-4.0 | 829h from Apple Vision Pro. Direct curl download from Apple CDN. |

Full rankings: [`data/ego-datasets/accessibility_rankings.csv`](data/ego-datasets/accessibility_rankings.csv)

<details>
<summary>Top issues (broken links, missing licenses, unverified downloads)</summary>

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

67 open datasets have no license specified. Full list: [`issues_and_findings.csv`](data/ego-datasets/issues_and_findings.csv)

</details>

---

## Quality Profiles

Each dataset gets a machine-readable Quality Profile (QP) — a structured record of what a dataset is and how good it is, computed at a specific evaluation level.

- **Croissant-compatible JSON-LD** — slots into MLCommons metadata infrastructure
- **ISO/IEC 5259-2 aligned** — 9 of 23 quality characteristics mapped at metadata level
- **Progressively enriched** — metadata → file → frame → content (each phase adds depth)

16 profiles live in [`data/quality-profiles/profiles/`](data/quality-profiles/profiles/).

**Example: `data/quality-profiles/profiles/ego4d.qp.json`**

```json
{
  "@context": {
    "cr": "http://mlcommons.org/croissant/",
    "qp": "http://opendataeval.org/qp/",
    "iso": "http://opendataeval.org/iso5259/"
  },
  "@type": "cr:Dataset",
  "name": "Ego4D",
  "dct:conformsTo": "http://opendataeval.org/qp/1.0",
  "qp:qualityProfile": {
    "qp:schemaVersion": "1.0",
    "qp:evalLevel": "metadata",
    "qp:evaluatedAt": "2026-04-14",
    "scores": {
      "fps": { "score": 1.0, "raw_value": 30.0 },
      "resolution": { "score": 1.0, "short_edge": 1080 },
      "license_clarity": { "score": 0.5, "tier": "custom" },
      "accessibility": { "score": 0.8 },
      "annotation_coverage": { "score": 0.75 },
      "...": "13 scores total"
    },
    "classifications": ["capture_device", "lens_type", "video_format", "annotation_format"],
    "confidence": { "metadata_completeness": 0.87 }
  }
}
```

---

## Scoring Methodology

### Accessibility Score (0–10)

Ease of Access scores are computed from six components:

| Component | Max Points | How |
|-----------|-----------|-----|
| Access Level | 3 | Open=3, Gated=2, Restricted=1, Unavailable=0 |
| URL Status | 2 | Live=2, Broken/Redirect=1, Dead=0 |
| License Clarity | 2 | Standard (CC-BY, MIT, Apache)=2, Named custom=1, None=0 |
| Documentation | 1.5 | Excellent=1.5, Good=1, Basic=0.5, None=0 |
| Dataloader | 1 | Available=1, None=0 |
| Commercial Clarity | 0.5 | Explicitly permitted=0.5, Explicitly banned=0.25, Unclear=0 |

### Metadata Eval (Phase 1a)

Quality profiles contain 13 numeric scores across five dimensions, computed from catalog metadata and paper research:

| Dimension | Scores |
|-----------|--------|
| Technical | FPS, resolution |
| Scale | Total hours, environment diversity, participant count |
| Annotation | Coverage (% of footage annotated) |
| Accessibility | License clarity, access level, URL status, dataloader, documentation |
| Reliability | Camera calibration tier, modality richness per use-case |

Each profile also includes 4 classifications (device, lens, video format, annotation format) and a metadata completeness confidence score. See [`docs/`](docs/) for the full specification.

---

## Data Files

| File | Description |
|------|-------------|
| [`data/ego-datasets/ego_dataset_catalog.csv`](data/ego-datasets/ego_dataset_catalog.csv) | Full catalog, 33 fields per dataset |
| [`data/ego-datasets/accessibility_rankings.csv`](data/ego-datasets/accessibility_rankings.csv) | All 103 datasets ranked by accessibility score |
| [`data/ego-datasets/access_summary.csv`](data/ego-datasets/access_summary.csv) | Aggregate counts by access level, license, modality, category |
| [`data/ego-datasets/issues_and_findings.csv`](data/ego-datasets/issues_and_findings.csv) | Flagged issues (dead links, unverified downloads, missing licenses) |
| [`data/ego-datasets/datasets_by_category.csv`](data/ego-datasets/datasets_by_category.csv) | Datasets grouped and ranked within each category |
| [`data/ego-datasets/datasets_by_family.csv`](data/ego-datasets/datasets_by_family.csv) | Dataset family groupings (EPIC-KITCHENS, Project Aria, Ego4D, etc.) |
| [`data/ego-datasets/catalog_health_report.csv`](data/ego-datasets/catalog_health_report.csv) | Per-dataset completeness audit (missing fields) |
| [`data/quality-profiles/profiles/`](data/quality-profiles/profiles/) | 16 machine-readable QP JSON files |
| [`docs/scorecard/`](docs/scorecard/) | GitHub Pages scorecard source |

---

## Roadmap

- [x] Phase 0: Dataset catalog — 103 ego datasets, 33 fields each
- [x] Phase 1a: Metadata Eval — quality profiles for 16 datasets, live scorecard
- [ ] Phase 1b: File Eval — ffprobe verification on downloaded files (codec, actual fps, corruption)
- [ ] Phase 1c: Frame Eval — ML models on sampled frames (hand visibility, blur, occlusion)
- [ ] Phase 2: Robot dataset catalog
- [ ] Phase 3: Derivative scoring — which data produces better models?
- [ ] Interactive comparison tool

---

## 5-Layer Scoring Framework

| Layer | Name | Signals |
|-------|------|---------|
| 1 | Technical Quality | Resolution, fps, codec, sharpness, frame drops |
| 2 | Content Quality | Hand visibility, action density, scene diversity |
| 3 | Collective Quality | Diversity indices, demographic balance, coverage |
| 4 | Derivative Quality | Downstream model lift — which data actually makes models better |
| 5 | Accessibility | License, download, documentation, dataloader |

Phase 1a covers Layer 5 fully and Layers 1–3 partially from metadata. Layers 2–4 require downloaded files and model runs.

---

## Contributing

Open an issue or PR. The catalog and quality profiles are the most useful place to contribute — adding missing fields, correcting errors, or extending coverage to new datasets.

Browse the [live scorecard](https://varun-nair.github.io/open-data-eval/scorecard/) to see what's been evaluated and what's missing.

---

## Citation

```bibtex
@misc{open-data-eval,
  author = {Varun Nair},
  title  = {Open Data Eval: A Systematic Quality Evaluation Suite for Egocentric and Manipulation Datasets},
  year   = {2026},
  url    = {https://github.com/Varun-Nair/open-data-eval}
}
```

---

*Licensed under [CC-BY-4.0](LICENSE). Copyright Varun Nair 2026.*
