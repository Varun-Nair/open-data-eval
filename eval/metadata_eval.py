#!/usr/bin/env python3
"""
Metadata Eval — Open Data Eval Quality Profile Generator
Phase 1a: Computes 13 quality scores + 4 classifications per dataset.

Sources: ego_dataset_catalog.csv (catalog fields) + PAPER_METADATA below (paper-researched).
Paper priority rule: when paper and catalog conflict, paper values are used and the discrepancy
is noted in the score's 'source' field.

Outputs
-------
  data/quality-profiles/profiles/{slug}.qp.json   Croissant-compatible JSON-LD (ISO 5259-2)
  data/quality-profiles/metadata_eval_summary.csv  Flat comparison table (16 datasets)
  docs/scorecard/scorecard_data.js                 window.SCORECARD_DATA for GitHub Pages

Usage
-----
  python eval/metadata_eval.py [catalog_path] [output_dir]
  python eval/metadata_eval.py  # uses defaults

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLE 1: Ego4D (fully-populated egocentric QP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "@type": "cr:Dataset",
  "name": "Ego4D",
  "qp:qualityProfile": {
    "scores": {
      "fps":                {"score": 1.0,   "raw_value": 30, "source": "catalog"},
      "resolution":         {"score": 1.0,   "width": 1920, "height": 1080, "source": "paper:2110.07058"},
      "modality_richness":  {"scores_by_usecase": {"vla_pretraining": {"score": 0.672},
                                                    "action_recognition": {"score": 0.847},
                                                    "robot_policy_learning": {"score": 0.079}}},
      "camera_calibration": {"score": 0.0,   "tier": "none",
                              "notes": "No calibration in base dataset. 7 heterogeneous device types.",
                              "source": "paper:2110.07058"},
      "license_clarity":    {"score": 0.5,   "tier": "custom_named"},
      "accessibility":      {"score": 0.75,  "raw_score": 7.5},
      "scale":              {"score": 0.891, "total_hours": 3670},
      "dataloader":         {"score": 1.0,   "framework": "pytorch"},
      "documentation_quality": {"score": 1.0, "rating": 3},
      "annotation_coverage": {"score": 1.0,  "notes": "3.85M narrations = 100% temporal coverage",
                               "source": "paper:2110.07058"},
      "download_efficiency": {"score": 0.857, "hours_per_gb": 0.524, "download_size_gb": 7000},
      "environment_diversity": {"score": 0.673, "unique_environments": 74},
      "demographic_diversity": {"score": 1.0,   "participants": 931, "geographic_locations": 9}
    },
    "classifications": {
      "capture_device": {"value": "Multiple: GoPro (Hero 4/6/7/8/9/Max), Vuzix Blade, Pupil Labs Invisible, ZShades, ORDRO EP6, iVue Rincon 1080, Weeview"},
      "lens_type":      {"value": "varies", "fov_degrees": null},
      "video_format":   {"value": "MP4"},
      "annotation_format": {"value": "JSON"}
    },
    "confidence": {"metadata_completeness": {"score": 1.0, "filled_fields": 16, "total_fields": 16}}
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLE 2: DROID (Phase 2 preview — robot dataset)
Source: arXiv 2403.12945 | 76K demos, ~564h, 350 environments
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "@type": "cr:Dataset",
  "name": "DROID",
  "qp:qualityProfile": {
    "scores": {
      "fps":                {"score": 0.3,   "raw_value": 15},
      "resolution":         {"score": 0.546, "width": 640, "height": 480, "tier": "480p"},
      "modality_richness":  {"scores_by_usecase": {
        "robot_policy_learning": {"score": 0.74,
          "note": "critical_ratio=1.0 (RGB+Prop+Gripper). Important: End-EE+Lang=0.5. Bonus=0"},
        "vla_pretraining":       {"score": 0.879,
          "note": "critical_ratio=1.0 (RGB+Lang). Important: Prop=0.33. Bonus=IMU=0.2"},
        "manipulation":          {"score": 0.253,
          "note": "critical_ratio=0.5 (RGB only; no Depth). Caps the score severely."}}},
      "camera_calibration": {"score": 0.5,   "tier": "intrinsics_distortion",
                              "notes": "Per-camera intrinsics + distortion in dataset. No extrinsics released."},
      "license_clarity":    {"score": 1.0,   "tier": "standard", "license": "Apache-2.0"},
      "accessibility":      {"score": 0.8,   "note": "Open + Live + Apache + PyTorch dataloader"},
      "scale":              {"score": 0.614, "total_hours": 564},
      "dataloader":         {"score": 1.0,   "framework": "pytorch"},
      "documentation_quality": {"score": 0.67, "rating": 2},
      "annotation_coverage": {"score": 1.0,  "notes": "100% language-annotated demos via structured task descriptions"},
      "download_efficiency": {"score": null,  "notes": "Download size not published (HuggingFace streaming)"},
      "environment_diversity": {"score": 0.842, "unique_environments": 350},
      "demographic_diversity": {"score": null, "notes": "Robot arms, not humans — metric N/A"}
    },
    "classifications": {
      "capture_device": {"value": "Multiple robot-mounted RGB cameras (wrist + external views)"},
      "lens_type":      {"value": "rectilinear", "fov_degrees": null},
      "video_format":   {"value": "MP4"},
      "annotation_format": {"value": "JSON"}
    },
    "confidence": {"metadata_completeness": {"score": 0.875, "filled_fields": 14, "total_fields": 16}}
  }
}
Note: DROID robot_policy_learning score (0.74) >> Ego4D (0.079). This is the Phase 2 signal.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import csv
import json
import math
import os
import sys
from datetime import datetime


# ============================================================
# TARGET DATASETS
# ============================================================
TARGET_DATASETS = [
    "Ego4D", "Ego-Exo4D", "EPIC-KITCHENS-100", "EPIC-KITCHENS-55", "HD-EPIC",
    "EgoLife", "Xperience-10M", "OpenEgo", "EgoVid-5M",
    "HOI4D", "HOT3D", "ARCTIC", "EgoDex", "TACO",
    "Egocentric-10K", "Egocentric-100K",
]


# ============================================================
# PAPER-RESEARCHED METADATA
# Rule: paper over catalog. Null if not found in paper.
# ============================================================
PAPER_METADATA = {
    "Ego4D": {
        # arXiv 2110.07058 (CVPR 2022)
        "capture_device": "Multiple: GoPro (Hero 4/6/7/8/9/Max), Vuzix Blade, Pupil Labs Invisible, ZShades, ORDRO EP6, iVue Rincon 1080, Weeview",
        "calibration_tier": 0.0,
        "calibration_notes": "No calibration provided. 7 heterogeneous device types across 74 collection sites; each site selected its device. Device metadata available in JSON manifests.",
        "lens_type": "varies",
        "fov_degrees": None,
        "resolution_override": "1920x1080",  # paper: "primarily 1080p"; standardized 540p also available
        "fps_override": None,                  # already in catalog: "30 (standardized); native varies"
        "annotation_coverage": 1.0,
        "annotation_notes": "Narrations=100% of 3,670h. Other annotations partial: Gaze 80h (2.2%), 3D 612h (17%), Stereo 491h (13%), FHO 116h.",
        "download_size_gb": 7000,              # ego4d-data.org: ~7TB primary full-scale
        "geo_locations": 9,                    # 9 countries, 74 worldwide sites
        "arxiv_id": "2110.07058",
        "paper_ref": "arXiv:2110.07058",
    },
    "Ego-Exo4D": {
        # arXiv 2311.18259 (CVPR 2024)
        "capture_device": "Project Aria Gen 1 (ego) + GoPro (4–5 stationary per take; model not stated in paper)",
        "calibration_tier": 1.0,
        "calibration_notes": "Full intrinsics + extrinsics + distortion for Aria (Kannala-Brandt K3 fisheye) and GoPro (OpenCV fisheye, gopro_calibs.csv). Aria uses time-varying online MPS calibration (validated).",
        "lens_type": "fisheye",
        "fov_degrees": 110,                    # Aria RGB 110° FOV
        "resolution_override": "1408x1408",    # paper: Aria RGB native; catalog says "8MP RGB ego (Aria)"
        "fps_override": 30,                    # paper HTML: "30 fps and 1408×1408 resolution" (Aria RGB primary stream)
        "annotation_coverage": 0.986,
        "annotation_notes": "4,965 / 5,035 takes (~98.6%) have atomic action descriptions (432K sentences). >200K annotator-hours total.",
        "download_size_gb": 38450,             # docs.ego-exo4d-data.org: ~37.5 TiB full
        "geo_locations": 6,                    # 6+ countries, 13 cities
        "arxiv_id": "2311.18259",
        "paper_ref": "arXiv:2311.18259",
    },
    "EPIC-KITCHENS-100": {
        # arXiv 2006.13256 (IJCV 2022)
        "capture_device": "GoPro Hero 5 Black (legacy EK-55 footage) + GoPro Hero 7 Black (EK-100 extension)",
        "calibration_tier": 0.0,
        "calibration_notes": "No calibration in base EK-100 paper. EPIC-Fields (NeurIPS 2023) provides retroactive COLMAP intrinsics+extrinsics as a separate companion — not part of this dataset.",
        "lens_type": "rectilinear",
        "fov_degrees": 94,                     # GoPro Hero linear mode, ~94° diagonal
        "resolution_override": None,            # catalog already correct: "1920x1080 (Full HD)"
        "fps_override": None,                   # catalog already correct: 60/50fps
        "annotation_coverage": 1.0,
        "annotation_notes": "100% of 100h has audio narrations. 89,977 dense action segments. EPIC-Fields: per-frame 6-DoF camera pose for 671/700 videos.",
        "download_size_gb": 740,               # dataset page: ~740 GiB zipped
        "geo_locations": 4,                    # Bristol, Toronto, Catania, Seattle
        "arxiv_id": "2006.13256",
        "paper_ref": "arXiv:2006.13256",
    },
    "EPIC-KITCHENS-55": {
        # arXiv 1804.02748 (ECCV 2018)
        "capture_device": "GoPro Hero 5 Black",
        "calibration_tier": 0.0,
        "calibration_notes": "No calibration in base EK-55 paper. EPIC-Fields provides retroactive calibration as a separate companion dataset.",
        "lens_type": "rectilinear",
        "fov_degrees": 94,
        "resolution_override": None,            # catalog correct
        "fps_override": None,                   # catalog: 60fps
        "annotation_coverage": 1.0,
        "annotation_notes": "100% narrations (collected post-hoc). 39,594 action segments. 454,255 object bboxes (selected frames).",
        "download_size_gb": 701,               # dataset page: ~701 GB unzipped
        "geo_locations": 4,
        "arxiv_id": "1804.02748",
        "paper_ref": "arXiv:1804.02748",
    },
    "HD-EPIC": {
        # arXiv 2502.04144 (CVPR 2025)
        "capture_device": "GoPro (EPIC-KITCHENS family; specific Hero model not confirmed in HD-EPIC paper)",
        "calibration_tier": None,               # not confirmed; paper mentions Aria MPS but device is GoPro family; ambiguous
        "calibration_notes": "Not provided in HD-EPIC. EPIC-Fields (NeurIPS 2023) provides retroactive COLMAP calibration as a separate companion dataset.",
        "lens_type": "rectilinear",             # inferred from EPIC-KITCHENS family (GoPro linear mode)
        "fov_degrees": 94,                      # inferred
        "resolution_override": None,            # catalog: "1920x1080 (assumed; EPIC-KITCHENS family standard)" — parses correctly
        "fps_override": None,
        "annotation_coverage": None,            # 263 annotations/min but coverage fraction not stated
        "annotation_notes": "263 annotations/min (densest in EPIC family). Digital kitchen twins. Coverage fraction not stated in paper.",
        "download_size_gb": 2300,              # catalog: 2.3 TiB
        "geo_locations": 1,                    # UK (Bristol area, per EPIC-KITCHENS)
        "arxiv_id": "2502.04144",
        "paper_ref": "arXiv:2502.04144",
    },
    "EgoLife": {
        # arXiv 2503.03803 (CVPR 2025)
        "capture_device": "Project Aria (ego) + GoPro Hero (exo)",
        "calibration_tier": 0.85,              # Aria hardware provides full calibration; EgoLife paper does not separately validate
        "calibration_notes": "Project Aria provides intrinsics + extrinsics + distortion (F-Theta model) per hardware spec. EgoLife paper does not separately describe calibration procedure.",
        "lens_type": "fisheye",
        "fov_degrees": 110,                    # Aria RGB
        "resolution_override": "1408x1408",    # Aria RGB native; catalog says "Aria glasses native + GoPro"
        "fps_override": 30,                    # Aria standard RGB fps
        "annotation_coverage": None,
        "annotation_notes": "JSON captions, QA pairs, transcripts for structured activities. Coverage fraction not stated in paper.",
        "download_size_gb": None,
        "geo_locations": 1,                    # single EgoHouse location
        "arxiv_id": "2503.03803",
        "paper_ref": "arXiv:2503.03803",
    },
    "Xperience-10M": {
        # No formal paper as of April 2026; HuggingFace dataset card only
        "capture_device": None,                # no paper; device not stated in dataset card
        "calibration_tier": None,              # calibration in annotation.hdf5 but tier not described
        "calibration_notes": "Calibration data present in annotation.hdf5/calibration/. Tier (intrinsics/distortion/extrinsics/validated) not described in dataset card.",
        "lens_type": "fisheye",               # HuggingFace card: 4 fisheye + 2 rectified stereo video streams
        "fov_degrees": None,
        "resolution_override": None,           # not stated in dataset card
        "fps_override": None,                  # not stated in dataset card
        "annotation_coverage": None,
        "annotation_notes": None,
        "download_size_gb": 31900,             # HuggingFace card: ~31.9 TB compressed download
        "geo_locations": None,
        "arxiv_id": None,
        "paper_ref": None,
    },
    "OpenEgo": {
        # arXiv 2509.05513
        "capture_device": "Multiple (aggregated: CaptainCook4D, HOI4D, HoloAssist, EgoDex, HOT3D, HO-Cap)",
        "calibration_tier": 0.85,              # dataset-specific intrinsics + per-frame extrinsics supplied; validation not stated
        "calibration_notes": "Per-dataset intrinsics + per-frame world-to-camera extrinsics unified across 6 source datasets. Distortion/validation not described for aggregated pipeline.",
        "lens_type": "varies",                 # aggregated from multiple source datasets with mixed optics
        "fov_degrees": None,
        "resolution_override": None,           # genuinely varies across source datasets
        "fps_override": 15,                   # paper: 15 fps (standardized across all sources)
        "annotation_coverage": None,           # language annotations "partially verified"; coverage fraction not stated
        "annotation_notes": "MANO 21-joint hand poses + world-frame extrinsics for all frames. Language annotations automatically generated, only partially verified.",
        "download_size_gb": None,
        "geo_locations": None,
        "arxiv_id": "2509.05513",
        "paper_ref": "arXiv:2509.05513",
    },
    "EgoVid-5M": {
        # arXiv 2411.08380 (NeurIPS 2025)
        "capture_device": "Multiple (inherited from Ego4D source videos; see Ego4D for device list)",
        "calibration_tier": 0.5,
        "calibration_notes": "Intrinsics provided per clip (3×3 matrix at 540p resolution). Camera pose trajectories from ParticleSfM/IMU fusion. Distortion coefficients not stated in paper.",
        "lens_type": "varies",
        "fov_degrees": None,
        "resolution_override": "1920x1080",    # source clips at 1080p; paper confirms "1080P and 540P" formats
        "fps_override": None,                   # varies per clip; stored as per-clip metadata
        "annotation_coverage": 1.0,
        "annotation_notes": "All 5M clips: MLLM text annotations (100%). Kinematic pose via SfM/VIO (100% propagated). ~65K clips (1.3%) have validated IMU-accurate kinematics.",
        "download_size_gb": 7100,              # paper: 1080P = ~7.1 TB
        "geo_locations": None,                 # inherited from Ego4D but not disaggregated
        "arxiv_id": "2411.08380",
        "paper_ref": "arXiv:2411.08380",
    },
    "HOI4D": {
        # arXiv 2203.01577 (CVPR 2022)
        "capture_device": "Kinect v2 (ToF RGB-D) + Intel RealSense D455 (structured-light RGB-D), both helmet-mounted",
        "calibration_tier": 0.35,
        "calibration_notes": "Sensors pre-calibrated before capture. Intrinsics matrix and per-frame pose trajectory provided (Open3D pinhole format). Distortion coefficients not described in paper.",
        "lens_type": None,                     # Kinect v2 + RealSense D455; neither is fisheye; rectilinear inferred but not stated
        "fov_degrees": None,
        "resolution_override": "1024x768",     # paper: 1024×768 RGB frames
        "fps_override": 15,                    # paper: 20-second sequences at 15 fps = 300 frames
        "total_hours_override": 22.2,          # paper: 4000 sequences × 20s = 80,000s = 22.2h
        "annotation_coverage": 1.0,
        "annotation_notes": "Action labels: 100% frame-wise. Panoptic segmentation and hand pose propagated to all frames via optimization pipeline.",
        "download_size_gb": None,
        "geo_locations": None,
        "arxiv_id": "2203.01577",
        "paper_ref": "arXiv:2203.01577",
    },
    "HOT3D": {
        # arXiv 2411.19167 (CVPR 2025)
        "capture_device": "Project Aria Gen 1 + Meta Quest 3, with OptiTrack motion-capture ground truth",
        "calibration_tier": 1.0,
        "calibration_notes": "Full intrinsics + extrinsics + distortion for Aria (F-Theta fisheye, MPS online validation) and Quest 3 (ChArUco board calibration). Time-varying Aria calibration validated.",
        "lens_type": "fisheye",
        "fov_degrees": 110,                    # Aria RGB 110° FOV; Aria mono 150° FOV
        "resolution_override": None,            # catalog already has "1408x1408 (Aria RGB); 640x480 (Aria mono); 1280x1024 (Quest 3)"
        "fps_override": None,                   # catalog: 30fps
        "annotation_coverage": 0.77,
        "annotation_notes": "1.16M / 1.5M multi-view frames passed QA and have full 3D hand+object pose (77%). Organized into 3,832 clips of 150 frames each.",
        "download_size_gb": None,              # VRS dataset size not publicly disclosed
        "geo_locations": 1,                    # Meta Reality Labs, Zurich
        "arxiv_id": "2411.19167",
        "paper_ref": "arXiv:2411.19167",
    },
    "ARCTIC": {
        # arXiv 2204.13662 (CVPR 2023)
        "capture_device": "54 Vicon Vantage-16 IR MoCap cameras + 9 RGB cameras (make/model not stated in paper)",
        "calibration_tier": 0.85,
        "calibration_notes": "Calibrated intrinsics (3×3) + 8 distortion parameters per RGB camera. Per-frame egocentric camera trajectory provided. Calibration methodology not described in paper.",
        "lens_type": "rectilinear",            # standard RGB cameras (not fisheye); confirmed by search result — no fisheye noted
        "fov_degrees": None,
        "resolution_override": "2800x2000",    # paper: 2800×2000 for all 9 RGB views
        "fps_override": 30,                    # paper: 30 fps
        "total_hours_override": 2.17,          # 339 sequences × ~23s = 7,797s = 2.17h (egocentric view only)
        "annotation_coverage": 1.0,
        "annotation_notes": "All 2.1M frames annotated with MANO hand meshes, SMPL-X body, articulated objects, dynamic contact fields via MoCap pipeline.",
        "download_size_gb": 900,               # GitHub data README: ~900 GB total
        "geo_locations": 1,                    # MPI-IS, Tübingen
        "arxiv_id": "2204.13662",
        "paper_ref": "arXiv:2204.13662",
    },
    "EgoDex": {
        # arXiv 2505.11709
        "capture_device": "Apple Vision Pro (visionOS 2, ARKit multi-camera SLAM)",
        "calibration_tier": 0.85,
        "calibration_notes": "Intrinsics (3×3, constant per recording) + extrinsics at 30Hz stored in HDF5. Distortion handled internally by ARKit; coefficients not explicitly provided in dataset.",
        "lens_type": "rectilinear",            # Apple Vision Pro passthrough cameras (ARKit); rectilinear confirmed by paper
        "fov_degrees": None,
        "resolution_override": None,            # catalog already has 1080p
        "fps_override": None,                   # catalog already has 30fps
        "annotation_coverage": 1.0,
        "annotation_notes": "All 829h include 3D pose annotations at 30Hz (head, upper body, 68 hand joints per-confidence). Task-level language annotations per sequence.",
        "download_size_gb": 1600,              # paper: ~2.0 TB on disk
        "geo_locations": None,                 # not stated in paper
        "arxiv_id": "2505.11709",
        "paper_ref": "arXiv:2505.11709",
    },
    "TACO": {
        # arXiv 2401.08399 (CVPR 2024)
        "capture_device": "Intel RealSense L515 (ego, helmet-mounted) + 12 FLIR industrial cameras (allo) + NOKOV MoCap (6 Mars4H IR cameras)",
        "calibration_tier": 0.85,
        "calibration_notes": "Intrinsics via checkerboard (OpenCV calibrateCamera). Extrinsics via P4P+RANSAC (12 known markers). K+R+T per camera as JSON. Distortion not explicitly stated as released.",
        "lens_type": "rectilinear",
        "fov_degrees": None,
        "resolution_override": "1920x1080",    # ego RealSense L515 RGB; FLIR: 4096×3000
        "fps_override": 30,
        "annotation_coverage": 1.0,
        "annotation_notes": "100% of sequences have per-frame 3D hand-object meshes, 2D segmentation, and action labels via automatic pipeline.",
        "download_size_gb": None,              # not stated in paper; BaiduNetDisk, no total size
        "geo_locations": 1,                    # Tsinghua University
        "arxiv_id": "2401.08399",
        "paper_ref": "arXiv:2401.08399",
    },
    "Egocentric-10K": {
        # HuggingFace dataset card + external reporting
        "capture_device": "Build AI Gen 1 (proprietary head-mounted monocular fisheye camera)",
        "calibration_tier": 0.5,
        "calibration_notes": "Per-worker intrinsics JSON (Kannala-Brandt equidistant fisheye: fx, fy, cx, cy + k1-k4 distortion coefficients). No extrinsics provided.",
        "lens_type": "fisheye",
        "fov_degrees": 128,                    # dataset card: 128° horizontal
        "resolution_override": "1920x1080",    # dataset card
        "fps_override": 30,
        "annotation_coverage": None,
        "annotation_notes": "Evaluation subset (30K labeled frames) available separately. Main corpus has hand-visibility metadata only, no per-frame semantic annotations.",
        "total_hours_override": 10000,         # dataset card: 10,000 hours
        "download_size_gb": 16400,             # dataset card: ~16.4 TB
        "geo_locations": 1,                    # US (85 factories)
        "arxiv_id": None,
        "paper_ref": "HuggingFace:builddotai/Egocentric-10K",
    },
    "Egocentric-100K": {
        # HuggingFace dataset card + external reporting
        "capture_device": "Build AI Gen 1 (proprietary head-mounted monocular fisheye camera)",
        "total_hours_override": 100405,        # dataset card: 100,405 hours
        "calibration_tier": 0.5,
        "calibration_notes": "Per-worker intrinsics JSON (Kannala-Brandt equidistant fisheye: fx, fy, cx, cy + k1-k4 distortion coefficients). No extrinsics. Same device as Egocentric-10K.",
        "lens_type": "fisheye",
        "fov_degrees": None,                   # same Gen 1 device but not explicitly confirmed in 100K card
        "resolution_override": "456x256",      # distributed resolution (downscaled from capture); paper confirms
        "fps_override": 30,
        "annotation_coverage": None,
        "annotation_notes": "Evaluation subset (30K labeled frames) available separately. Main corpus has no per-frame semantic annotations.",
        "download_size_gb": 24790,             # dataset card: ~24.79 TB
        "geo_locations": 1,                    # Southeast Asia (multiple countries; 1 region)
        "arxiv_id": None,
        "paper_ref": "HuggingFace:builddotai/Egocentric-100K",
    },
}


# ============================================================
# SCORING FUNCTIONS
# ============================================================

def score_fps(fps_str):
    """30+ = 1.0. Piecewise continuous below. Returns (score, fps_value)."""
    import re
    if not fps_str or fps_str.lower().strip() in ('unknown', 'not specified', 'not reported', 'varies', 'n/a', ''):
        return None, None
    numbers = re.findall(r'(\d+(?:\.\d+)?)', fps_str)
    if not numbers:
        return None, None
    fps = float(numbers[0])
    if fps >= 30:
        score = 1.0
    elif fps >= 24:
        score = 0.7 + 0.3 * (fps - 24) / 6
    elif fps >= 15:
        score = 0.3 + 0.4 * (fps - 15) / 9
    else:
        score = max(0.05, 0.3 * (fps / 15))
    return round(score, 3), fps


def score_resolution(res_str):
    """Short-edge scoring. 1080+ = 1.0. Returns (score, w, h, tier)."""
    import re
    if not res_str or res_str.lower().strip() in ('unknown', 'not specified', 'not reported', 'varies', 'variable', 'n/a', ''):
        return None, None, None, None

    match = re.search(r'(\d{3,5})\s*[xX×]\s*(\d{3,5})', res_str)
    if match:
        w, h = int(match.group(1)), int(match.group(2))
    else:
        p_match = re.search(r'(\d{3,4})\s*p', res_str.lower())
        if p_match:
            h = int(p_match.group(1))
            w = int(h * 16 / 9)
        elif '4k' in res_str.lower():
            w, h = 3840, 2160
        elif '2k' in res_str.lower():
            w, h = 2560, 1440
        else:
            return None, None, None, None

    s = min(w, h)
    if s >= 1080:
        score, tier = 1.0, "1080p+"
    elif s >= 720:
        score, tier = 0.7 + 0.3 * (s - 720) / 360, "720p"
    elif s >= 480:
        score, tier = 0.3 + 0.4 * (s - 480) / 240, "480p"
    else:
        score, tier = max(0.05, 0.3 * (s / 480)), f"<480p ({s}p)"
    return round(score, 3), w, h, tier


MODALITY_PROFILES = {
    "manipulation": {
        "critical":  ["RGB video", "Depth"],
        "important": ["Hand pose annotations", "Tactile", "Force/torque",
                      "Narrations/captions", "Proprioception", "Gripper state"],
        "bonus":     ["Audio", "IMU", "Optical flow", "Object bounding boxes",
                      "End-effector pose", "Segmentation masks"],
    },
    "action_recognition": {
        "critical":  ["RGB video"],
        "important": ["Audio", "Narrations/captions", "Optical flow"],
        "bonus":     ["Eye gaze", "Hand pose annotations", "IMU", "Object bounding boxes"],
    },
    "hand_pose_estimation": {
        "critical":  ["RGB video", "Hand pose annotations"],
        "important": ["Depth", "Stereo"],
        "bonus":     ["Tactile", "IMU", "Segmentation masks"],
    },
    "navigation": {
        "critical":  ["RGB video", "IMU"],
        "important": ["Depth", "SLAM/odometry", "3D point clouds"],
        "bonus":     ["Audio", "Stereo", "LiDAR", "Segmentation masks"],
    },
    "robot_policy_learning": {
        "critical":  ["RGB video", "Proprioception", "Gripper state"],
        "important": ["Depth", "End-effector pose", "Narrations/captions", "Force/torque"],
        "bonus":     ["Tactile", "Audio", "Joint torques"],
    },
    "vla_pretraining": {
        "critical":  ["RGB video", "Narrations/captions"],
        "important": ["Depth", "Hand pose annotations", "Proprioception"],
        "bonus":     ["Audio", "IMU", "Eye gaze", "SLAM/odometry", "Optical flow"],
    },
}


def parse_modalities(mod_str):
    if not mod_str:
        return set()
    mods = set()
    for m in mod_str.split(';'):
        m = m.strip()
        if not m:
            continue
        if m.startswith('Depth'):
            mods.add('Depth')
        elif m.startswith('Hand pose'):
            mods.add('Hand pose annotations')
        elif m.startswith('Body pose'):
            mods.add('Body pose annotations')
        elif m.startswith('3D scene'):
            mods.add('3D scene reconstruction')
        elif m.startswith('3D point'):
            mods.add('3D point clouds')
        elif m.startswith('SLAM'):
            mods.add('SLAM/odometry')
        elif m.startswith('Narrations'):
            mods.add('Narrations/captions')
        else:
            mods.add(m)
    return mods


def score_modality_richness(mod_str):
    present = parse_modalities(mod_str)
    results = {}
    for uc, profile in MODALITY_PROFILES.items():
        ct = len(profile["critical"])
        it = len(profile["important"])
        bt = len(profile["bonus"])
        cp = [m for m in profile["critical"] if m in present]
        ip = [m for m in profile["important"] if m in present]
        bp = [m for m in profile["bonus"] if m in present]
        cr = len(cp) / ct if ct > 0 else 1.0
        ir = len(ip) / it if it > 0 else 0.0
        br = len(bp) / bt if bt > 0 else 0.0
        score = cr ** 2 * (0.60 + 0.28 * ir + 0.12 * br)
        results[uc] = {
            "critical":  {"present": cp, "missing": [m for m in profile["critical"] if m not in present], "ratio": round(cr, 2)},
            "important": {"present": ip, "missing": [m for m in profile["important"] if m not in present], "ratio": round(ir, 2)},
            "bonus":     {"present": bp, "missing": [m for m in profile["bonus"] if m not in present], "ratio": round(br, 2)},
            "score": round(score, 3),
        }
    return {"modalities_present": sorted(list(present)), "modality_count": len(present),
            "scores_by_usecase": results, "source": "catalog", "iso_mapping": "Div-ML"}


def score_camera_calibration(tier, notes):
    """
    1.0 = intrinsics + distortion + extrinsics, validated
    0.85 = intrinsics + distortion + extrinsics, unvalidated
    0.5  = intrinsics + distortion only
    0.35 = intrinsics only
    0.0  = none
    None = unknown (pending)
    """
    TIER_LABELS = {
        1.0:  "intrinsics_extrinsics_validated",
        0.85: "intrinsics_extrinsics_unvalidated",
        0.5:  "intrinsics_distortion",
        0.35: "intrinsics_only",
        0.0:  "none",
    }
    if tier is None:
        return None, None, notes
    return tier, TIER_LABELS.get(tier, "unknown"), notes


def score_license_clarity(license_str):
    STANDARD = {'CC-BY-4.0', 'CC-BY-NC-4.0', 'CC-BY-SA-4.0', 'CC-BY-NC-SA-4.0',
                'CC-BY-NC-ND-4.0', 'MIT', 'Apache 2.0', 'Apache-2.0', 'BSD'}
    CUSTOM   = {'Custom Academic', 'Custom Open', 'S-Lab License', 'Mixed'}
    lic = (license_str or '').strip()
    if lic in STANDARD:
        return 1.0, "standard"
    elif lic in CUSTOM:
        return 0.5, "custom_named"
    else:
        return 0.0, "not_specified"


def score_accessibility(row):
    ACCESS = {'Open': 3, 'Gated-Open': 2, 'Restricted': 1, 'Unavailable': 0}
    URL    = {'Live': 2, 'Live but broken': 1, 'Redirect': 1, 'Dead': 0}
    STANDARD = {'CC-BY-4.0', 'CC-BY-NC-4.0', 'CC-BY-SA-4.0', 'CC-BY-NC-SA-4.0',
                'CC-BY-NC-ND-4.0', 'MIT', 'Apache 2.0', 'Apache-2.0', 'BSD'}
    CUSTOM   = {'Custom Academic', 'Custom Open', 'S-Lab License', 'Mixed'}
    lic = row.get('License Type', '').strip()
    lic_s = 2 if lic in STANDARD else (1 if lic in CUSTOM else 0)
    try:
        doc = float(row.get('Documentation Quality (0-3)', 0) or 0)
        doc_s = {3: 1.5, 2: 1.0, 1: 0.5, 0: 0.0}.get(int(doc), 0)
    except (ValueError, TypeError):
        doc_s = 0
    dl = (row.get('Dataloader Available?', '') or '').strip().lower()
    dl_s = 1.0 if dl.startswith('yes') else 0.0
    comm = (row.get('Commercial Use Permitted?', '') or '').strip()
    comm_s = 0.5 if comm.lower().startswith('yes') else (0.25 if comm.lower().startswith('no') else 0.0)
    raw = (ACCESS.get(row.get('Access Level', '').strip(), 0) +
           URL.get(row.get('URL Status', '').strip(), 0) +
           lic_s + doc_s + dl_s + comm_s)
    return round(raw / 10.0, 3), round(raw, 2)


def score_scale(hours_str):
    if not hours_str or str(hours_str).lower() in ('unknown', 'not reported', 'not specified', 'n/a', ''):
        return None, None
    h = str(hours_str).strip().replace('~', '').replace('<', '').replace('+', '').replace(',', '')
    try:
        hours = float(h)
    except ValueError:
        return None, None
    return min(round(math.log10(hours + 1) / math.log10(10001), 3), 1.0), hours


def score_dataloader(dl_str):
    if not dl_str:
        return 0.0, False, None
    dl = dl_str.strip().lower()
    if dl.startswith('yes'):
        for fw in ('pytorch', 'tensorflow', 'jax', 'huggingface'):
            if fw in dl:
                return 1.0, True, fw
        return 0.8, True, "unspecified"
    elif 'community' in dl or 'unofficial' in dl:
        return 0.5, True, "community"
    return 0.0, False, None


def score_documentation(doc_str):
    try:
        r = float(doc_str)
        return round(r / 3.0, 3), int(r)
    except (ValueError, TypeError):
        return 0.0, 0


def score_download_efficiency(hours_str, size_gb):
    """hours_per_gb from known hours and size in GB. Score assigned after pool ranking."""
    if size_gb is None:
        return None, None, None
    if not hours_str or str(hours_str).lower() in ('unknown', 'not reported', 'not specified', ''):
        return None, None, None
    h = str(hours_str).strip().replace('~', '').replace('<', '').replace('+', '').replace(',', '')
    try:
        hours = float(h)
    except ValueError:
        return None, None, None
    if size_gb <= 0:
        return None, None, None
    return round(hours / size_gb, 4), hours, size_gb


def score_environment_diversity(scenes_str, max_scenes):
    if not scenes_str or str(scenes_str).lower() in ('unknown', 'not specified', 'not reported', 'n/a', ''):
        return None, None
    s = str(scenes_str).strip().replace('~', '').replace('+', '').replace(',', '')
    try:
        n = float(s.split()[0])
    except (ValueError, IndexError):
        return None, None
    if max_scenes <= 0:
        return 0.0, n
    return round(math.log10(n + 1) / math.log10(max_scenes + 1), 3), n


def score_demographic_diversity(participants_str, geo_locations, max_product):
    if not participants_str or str(participants_str).lower() in ('unknown', 'not specified', 'not reported', 'n/a', ''):
        return None, None, None
    p = str(participants_str).strip().replace('~', '').replace('+', '').replace(',', '')
    try:
        parts = float(p.split()[0])
    except (ValueError, IndexError):
        return None, None, None
    locs = geo_locations if geo_locations is not None else 1
    product = parts * locs
    if max_product <= 0:
        return 0.0, parts, locs
    return round(math.log10(product + 1) / math.log10(max_product + 1), 3), parts, locs


def compute_metadata_completeness(qp_profile):
    s = qp_profile["scores"]
    c = qp_profile["classifications"]
    fields = [
        s["fps"]["score"],
        s["resolution"]["score"],
        s["modality_richness"]["scores_by_usecase"]["manipulation"]["score"],
        s["camera_calibration"]["score"],
        s["license_clarity"]["score"],
        s["accessibility"]["score"],
        s["scale"]["score"],
        s["dataloader"]["score"],
        s["documentation_quality"]["score"],
        s["annotation_coverage"]["score"],
        s["download_efficiency"]["score"],
        s["environment_diversity"]["score"],
        s["demographic_diversity"]["score"],
        c["capture_device"]["value"],
        c["lens_type"]["value"],
        c["video_format"]["value"],
    ]
    filled = sum(1 for f in fields if f is not None)
    return round(filled / len(fields), 3), filled, len(fields)


# ============================================================
# BUILD QP
# ============================================================

def build_qp(row, max_scenes, max_demo_product, citations_map=None):
    name = row['Dataset Name'].strip()
    pm = PAPER_METADATA.get(name, {})

    # --- resolve fps: paper override, then catalog ---
    fps_raw = row.get('Frame Rate (fps)', '').strip()
    if pm.get('fps_override') is not None:
        fps_score, fps_val = score_fps(str(pm['fps_override']))
        fps_source = f"paper:{pm.get('paper_ref', 'unknown')}"
    else:
        fps_score, fps_val = score_fps(fps_raw)
        fps_source = "catalog"

    # --- resolve resolution: paper override, then catalog ---
    res_raw = row.get('Resolution', '').strip()
    res_input = pm.get('resolution_override') or res_raw
    res_source = (f"paper:{pm.get('paper_ref', 'unknown')}"
                  if pm.get('resolution_override') else "catalog")
    if pm.get('resolution_override') and pm['resolution_override'].lower() == res_raw.lower():
        res_source = "catalog"  # no actual conflict
    res_score, res_w, res_h, res_tier = score_resolution(res_input)

    # --- modality richness from catalog ---
    mod_result = score_modality_richness(row.get('Modalities Present', ''))

    # --- camera calibration from paper ---
    cal_score, cal_label, cal_notes = score_camera_calibration(
        pm.get('calibration_tier'), pm.get('calibration_notes'))
    cal_source = (f"paper:{pm.get('paper_ref', 'unknown')}"
                  if pm.get('calibration_tier') is not None else "pending_paper_review")

    # --- license, accessibility from catalog ---
    lic_score, lic_tier = score_license_clarity(row.get('License Type', ''))
    acc_score, acc_raw = score_accessibility(row)

    # --- scale: paper override takes priority over catalog ---
    hours_raw = (str(pm['total_hours_override'])
                 if pm.get('total_hours_override') is not None
                 else row.get('Total Hours', ''))
    scale_score, scale_hours = score_scale(hours_raw)

    # --- dataloader, documentation from catalog ---
    dl_score, dl_avail, dl_fw = score_dataloader(row.get('Dataloader Available?', ''))
    doc_score, doc_rating = score_documentation(row.get('Documentation Quality (0-3)', ''))

    # --- annotation coverage from paper ---
    ann_cov = pm.get('annotation_coverage')
    ann_score = ann_cov
    ann_source = (f"paper:{pm.get('paper_ref', 'unknown')}"
                  if ann_cov is not None else "pending_paper_review")

    # --- download efficiency: use paper size if available ---
    size_gb = pm.get('download_size_gb')
    eff_hpg, eff_hours, eff_gb = score_download_efficiency(hours_raw, size_gb)

    # --- environment diversity from catalog ---
    env_score, env_count = score_environment_diversity(
        row.get('Number of Scenes/Environments', ''), max_scenes)

    # --- demographic diversity: paper geo_locations + catalog participants ---
    geo = pm.get('geo_locations')
    demo_score, demo_parts, demo_locs = score_demographic_diversity(
        row.get('Number of Participants', ''), geo, max_demo_product)

    # --- video format: parse from catalog File Formats field ---
    fmt_raw = row.get('File Formats', row.get('Video Format', '')).strip()
    fmt_val = fmt_raw if fmt_raw and fmt_raw.lower() not in ('n/a', 'unknown', '') else None

    qp = {
        "@context": {
            "@vocab": "http://schema.org/",
            "cr":  "http://mlcommons.org/croissant/",
            "qp":  "http://opendataeval.org/qp/",
            "iso": "http://opendataeval.org/iso5259/",
        },
        "@type": "cr:Dataset",
        "name":  name,
        "url":   row.get('Primary URL', ''),
        "dct:conformsTo": "http://opendataeval.org/qp/1.0",
        "qp:qualityProfile": {
            "qp:schemaVersion": "1.0",
            "qp:evalLevel":     "metadata",
            "qp:evaluatedAt":   datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "qp:evaluatedBy":   "open-data-eval",
            "scores": {
                "fps": {
                    "score": fps_score, "raw_value": fps_val,
                    "method": "piecewise_continuous",
                    "source": fps_source, "iso_mapping": "Acc-ML",
                },
                "resolution": {
                    "score": res_score, "width": res_w, "height": res_h,
                    "short_edge": min(res_w, res_h) if res_w and res_h else None,
                    "tier": res_tier,
                    "method": "piecewise_continuous",
                    "source": res_source, "iso_mapping": "Acc-ML",
                },
                "modality_richness": mod_result,
                "camera_calibration": {
                    "score": cal_score, "tier": cal_label, "notes": cal_notes,
                    "method": "tier",
                    "source": cal_source, "iso_mapping": "Aud-ML",
                },
                "license_clarity": {
                    "score": lic_score, "license_type": row.get('License Type', '').strip(),
                    "tier": lic_tier,
                    "commercial_use": row.get('Commercial Use Permitted?', '').strip(),
                    "method": "tier",
                    "source": "catalog", "iso_mapping": "Cpl-ML",
                },
                "accessibility": {
                    "score": acc_score, "raw_score": acc_raw,
                    "access_level": row.get('Access Level', '').strip(),
                    "url_status":   row.get('URL Status', '').strip(),
                    "method": "weighted_sum_normalized",
                    "source": "catalog", "iso_mapping": "Acs-ML",
                },
                "scale": {
                    "score": scale_score, "total_hours": scale_hours,
                    "method": "log10(hrs+1)/log10(10001)",
                    "source": (f"paper:{pm.get('paper_ref')}" if pm.get('total_hours_override') is not None else "catalog"),
                    "iso_mapping": "Eff-ML",
                },
                "dataloader": {
                    "score": dl_score, "available": dl_avail, "framework": dl_fw,
                    "method": "tier",
                    "source": "catalog", "iso_mapping": "Acs-ML",
                },
                "documentation_quality": {
                    "score": doc_score, "rating": doc_rating,
                    "method": "normalized_0_3",
                    "source": "catalog", "iso_mapping": "Und-ML",
                },
                "annotation_coverage": {
                    "score": ann_score,
                    "notes": pm.get('annotation_notes'),
                    "method": "ratio",
                    "source": ann_source, "iso_mapping": "Com-ML",
                },
                "download_efficiency": {
                    "score": None,  # filled by compute_download_efficiency_percentiles()
                    "hours_per_gb": eff_hpg, "total_hours": eff_hours,
                    "download_size_gb": eff_gb,
                    "method": "percentile_rank",
                    "source": "catalog+paper", "iso_mapping": "Eff-ML",
                },
                "environment_diversity": {
                    "score": env_score, "unique_environments": env_count,
                    "method": "log_normalized",
                    "source": "catalog", "iso_mapping": "Div-ML",
                },
                "demographic_diversity": {
                    "score": demo_score, "participants": demo_parts,
                    "geographic_locations": demo_locs,
                    "method": "log_normalized_product",
                    "source": "catalog+paper", "iso_mapping": "Div-ML",
                },
            },
            "classifications": {
                "capture_device": {
                    "value": pm.get('capture_device'),
                    "documented": pm.get('capture_device') is not None,
                    "source": (f"paper:{pm.get('paper_ref')}" if pm.get('capture_device') else "pending_paper_review"),
                    "iso_mapping": "Ide-ML",
                },
                "lens_type": {
                    "value":       pm.get('lens_type'),
                    "fov_degrees": pm.get('fov_degrees'),
                    "documented":  pm.get('lens_type') is not None,
                    "source": (f"paper:{pm.get('paper_ref')}" if pm.get('lens_type') else "pending_paper_review"),
                    "iso_mapping": "Ide-ML",
                },
                "video_format": {
                    "value":  fmt_val,
                    "source": "catalog",
                },
                "annotation_format": {
                    "value":  row.get('Annotation Format', '').strip() or None,
                    "source": "catalog",
                },
            },
            "context": {
                "total_hours":        scale_hours,
                "participants":       row.get('Number of Participants', '').strip(),
                "scenes_environments":row.get('Number of Scenes/Environments', '').strip(),
                "commercial_use":     row.get('Commercial Use Permitted?', '').strip(),
                "category":           row.get('Category', '').strip(),
                "year":               row.get('Year', '').strip(),
                "paper":              row.get('Primary Paper', '').strip(),
                "approximate_citations": row.get('Approximate Citations', '').strip(),
                "citations": (citations_map or {}).get(name),
                "no_paper": pm.get("arxiv_id") is None and not (pm.get("paper_ref") or "").startswith("arXiv"),
            },
            "confidence": {},  # filled below
        },
    }

    comp_score, comp_filled, comp_total = compute_metadata_completeness(qp["qp:qualityProfile"])
    qp["qp:qualityProfile"]["confidence"] = {
        "metadata_completeness": {
            "score": comp_score, "filled_fields": comp_filled, "total_fields": comp_total,
            "method": "ratio",
            "iso_mapping": ["Com-ML", "Und-ML"],
        }
    }
    return qp


def compute_download_efficiency_percentiles(qps):
    hpg_vals = [(qp["name"], qp["qp:qualityProfile"]["scores"]["download_efficiency"]["hours_per_gb"])
                for qp in qps if qp["qp:qualityProfile"]["scores"]["download_efficiency"]["hours_per_gb"] is not None]
    if not hpg_vals:
        return
    sorted_hpg = sorted(v for _, v in hpg_vals)
    for qp in qps:
        hpg = qp["qp:qualityProfile"]["scores"]["download_efficiency"]["hours_per_gb"]
        if hpg is not None:
            rank = sum(1 for v in sorted_hpg if v <= hpg) / len(sorted_hpg)
            qp["qp:qualityProfile"]["scores"]["download_efficiency"]["score"] = round(rank, 3)
    # Recompute completeness now that efficiency score is filled
    for qp in qps:
        cs, cf, ct = compute_metadata_completeness(qp["qp:qualityProfile"])
        qp["qp:qualityProfile"]["confidence"]["metadata_completeness"]["score"] = cs
        qp["qp:qualityProfile"]["confidence"]["metadata_completeness"]["filled_fields"] = cf


def generate_summary_csv(qps, path):
    rows = []
    for qp in qps:
        p = qp["qp:qualityProfile"]
        s = p["scores"]
        uc = s["modality_richness"]["scores_by_usecase"]
        rows.append({
            "dataset_name":           qp["name"],
            "category":               p["context"]["category"],
            "year":                   p["context"]["year"],
            "total_hours":            p["context"]["total_hours"],
            "fps_score":              s["fps"]["score"],
            "fps_raw":                s["fps"]["raw_value"],
            "resolution_score":       s["resolution"]["score"],
            "resolution_tier":        s["resolution"]["tier"],
            "camera_calibration":     s["camera_calibration"]["score"],
            "calibration_tier":       s["camera_calibration"]["tier"],
            "modality_manipulation":  uc["manipulation"]["score"],
            "modality_action_recog":  uc["action_recognition"]["score"],
            "modality_hand_pose":     uc["hand_pose_estimation"]["score"],
            "modality_navigation":    uc["navigation"]["score"],
            "modality_robot_policy":  uc["robot_policy_learning"]["score"],
            "modality_vla":           uc["vla_pretraining"]["score"],
            "modality_count":         s["modality_richness"]["modality_count"],
            "license_clarity":        s["license_clarity"]["score"],
            "accessibility":          s["accessibility"]["score"],
            "scale":                  s["scale"]["score"],
            "dataloader":             s["dataloader"]["score"],
            "documentation":          s["documentation_quality"]["score"],
            "annotation_coverage":    s["annotation_coverage"]["score"],
            "download_efficiency":    s["download_efficiency"]["score"],
            "hours_per_gb":           s["download_efficiency"]["hours_per_gb"],
            "download_size_gb":       s["download_efficiency"]["download_size_gb"],
            "environment_diversity":  s["environment_diversity"]["score"],
            "demographic_diversity":  s["demographic_diversity"]["score"],
            "capture_device":         p["classifications"]["capture_device"]["value"],
            "lens_type":              p["classifications"]["lens_type"]["value"],
            "fov_degrees":            p["classifications"]["lens_type"]["fov_degrees"],
            "annotation_format":      p["classifications"]["annotation_format"]["value"],
            "metadata_completeness":  p["confidence"]["metadata_completeness"]["score"],
        })
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def generate_scorecard_data_js(qps, path):
    """Generate window.SCORECARD_DATA for the GitHub Pages scorecard."""
    def parse_citations(s):
        if not s: return None
        import re
        s = str(s).strip()
        if s.startswith('<'): return None   # "fewer than N" — value unknown, don't display
        m = re.search(r'(\d+)', re.sub(r'[~,+\s,]', '', s))
        return int(m.group(1)) if m else None

    def cal_checklist(tier):
        if tier is None:
            return dict(intrinsics=None, distortion=None, extrinsics=None, validated=None)
        if tier == "none":
            return dict(intrinsics=False, distortion=False, extrinsics=False, validated=False)
        if tier == "intrinsics_only":
            return dict(intrinsics=True, distortion=False, extrinsics=False, validated=False)
        if tier == "intrinsics_distortion":
            return dict(intrinsics=True, distortion=True, extrinsics=False, validated=False)
        if tier == "intrinsics_extrinsics_unvalidated":
            return dict(intrinsics=True, distortion=True, extrinsics=True, validated=False)
        if tier == "intrinsics_extrinsics_validated":
            return dict(intrinsics=True, distortion=True, extrinsics=True, validated=True)
        return dict(intrinsics=None, distortion=None, extrinsics=None, validated=None)

    entries = []
    for qp in qps:
        p  = qp["qp:qualityProfile"]
        s  = p["scores"]
        cl = p["classifications"]
        uc = s["modality_richness"]["scores_by_usecase"]
        cc = cal_checklist(s["camera_calibration"]["tier"])
        entries.append({
            "name":         qp["name"],
            "cat":          p["context"]["category"],
            "yr":           p["context"]["year"],
            "hrs":          p["context"]["total_hours"],
            # fps
            "fps":          s["fps"]["score"],
            "fpsRaw":       s["fps"]["raw_value"],
            "fpsSource":    s["fps"]["source"],
            # resolution
            "res":          s["resolution"]["score"],
            "resW":         s["resolution"]["width"],
            "resH":         s["resolution"]["height"],
            "resTier":      s["resolution"]["tier"],
            "resSource":    s["resolution"]["source"],
            # calibration
            "camCal":       s["camera_calibration"]["score"],
            "camCalTier":   s["camera_calibration"]["tier"],
            "camCalNotes":  s["camera_calibration"]["notes"],
            "camCalSource": s["camera_calibration"]["source"],
            "calIntrinsics": cc["intrinsics"],
            "calDistortion": cc["distortion"],
            "calExtrinsics": cc["extrinsics"],
            "calValidated":  cc["validated"],
            # modality
            "manip":        uc["manipulation"]["score"],
            "actRecog":     uc["action_recognition"]["score"],
            "handPose":     uc["hand_pose_estimation"]["score"],
            "nav":          uc["navigation"]["score"],
            "robot":        uc["robot_policy_learning"]["score"],
            "vla":          uc["vla_pretraining"]["score"],
            "modCount":     s["modality_richness"]["modality_count"],
            "modalities":   s["modality_richness"]["modalities_present"],
            # license / access
            "lic":          s["license_clarity"]["score"],
            "licTier":      s["license_clarity"]["tier"],
            "licType":      s["license_clarity"]["license_type"],
            "acc":          s["accessibility"]["score"],
            "accLevel":     s["accessibility"]["access_level"],
            "accUrlStatus": s["accessibility"]["url_status"],
            # scale
            "scale":        s["scale"]["score"],
            "scaleSource":  s["scale"]["source"],
            # dataloader / docs
            "dl":           s["dataloader"]["score"],
            "dlFramework":  s["dataloader"]["framework"],
            "doc":          s["documentation_quality"]["score"],
            "docRating":    s["documentation_quality"]["rating"],
            # annotation coverage
            "annCov":       s["annotation_coverage"]["score"],
            "annCovNotes":  s["annotation_coverage"]["notes"],
            "annCovSource": s["annotation_coverage"]["source"],
            # download efficiency
            "dlEff":        s["download_efficiency"]["score"],
            "dlEffHPG":     s["download_efficiency"]["hours_per_gb"],
            "dlSizeGB":     s["download_efficiency"]["download_size_gb"],
            # diversity
            "envDiv":       s["environment_diversity"]["score"],
            "envDivCount":  s["environment_diversity"]["unique_environments"],
            "demoDiv":      s["demographic_diversity"]["score"],
            "demoParts":    s["demographic_diversity"]["participants"],
            "demoGeo":      s["demographic_diversity"]["geographic_locations"],
            # completeness + classifications
            "completeness": p["confidence"]["metadata_completeness"]["score"],
            "captureDevice":cl["capture_device"]["value"],
            "lensType":     cl["lens_type"]["value"],
            "fovDegrees":   cl["lens_type"]["fov_degrees"],
            "videoFormat":  cl["video_format"]["value"],
            "annotFormat":  cl["annotation_format"]["value"],
            "citations":    (p["context"].get("citations") or {}).get("count"),
            "noPaper":      p["context"].get("no_paper", False),
        })

    js_entries = json.dumps(entries, indent=2)
    js = f"// Auto-generated by eval/metadata_eval.py — do not edit manually\n"
    js += f"// Generated: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
    js += f"window.SCORECARD_DATA = {js_entries};\n"
    with open(path, 'w') as f:
        f.write(js)


# ============================================================
# CITATION FETCHING
# ============================================================

CITATIONS_CACHE_PATH = "data/quality-profiles/citations_cache.json"


def fetch_all_citations(paper_metadata):
    """
    Fetch live citation counts from Semantic Scholar.
    - arXiv IDs: /paper/arXiv:{id}?fields=citationCount
    - Title search: /paper/search?query={name}&fields=citationCount&limit=1
    - No arXiv + no paper (Egocentric-10K/100K): returns None
    Rate-limited to 2 req/sec (public API, no key required).
    Caches successful fetches in CITATIONS_CACHE_PATH — re-runs skip already-fetched entries.
    Returns dict: {name: {"count": N, "source": "...", "fetched_at": "YYYY-MM-DD"} | None}
    """
    import urllib.request, urllib.parse, json as _json, time
    from datetime import date

    # Load cache — preserves successful fetches across re-runs
    cache = {}
    if os.path.exists(CITATIONS_CACHE_PATH):
        with open(CITATIONS_CACHE_PATH) as f:
            cache = _json.load(f)

    today = date.today().isoformat()
    BASE = "https://api.semanticscholar.org/graph/v1"
    results = {}

    import urllib.error

    def _get(url, retries=4):
        """GET with exponential backoff on 429."""
        req = urllib.request.Request(url, headers={"User-Agent": "open-data-eval/1.0"})
        delay = 10
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    return _json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
        return None

    def _save_cache():
        os.makedirs(os.path.dirname(CITATIONS_CACHE_PATH), exist_ok=True)
        with open(CITATIONS_CACHE_PATH, 'w') as f:
            _json.dump(cache, f, indent=2)

    for name, pm in paper_metadata.items():
        # Use cache if already successfully fetched
        if name in cache:
            results[name] = cache[name]
            status = cache[name]['count'] if cache[name] else 'no paper'
            print(f"  {name}: {status} (cached)")
            continue

        arxiv_id = pm.get("arxiv_id")

        if arxiv_id is None and pm.get("paper_ref") and \
                not pm["paper_ref"].startswith("HuggingFace"):
            # Title search (Xperience-10M or future dataset without arXiv)
            query = urllib.parse.quote(name)
            url = f"{BASE}/paper/search?query={query}&fields=citationCount&limit=1"
            try:
                data = _get(url)
                papers = (data or {}).get("data", [])
                if papers and papers[0].get("citationCount") is not None:
                    results[name] = cache[name] = {
                        "count": papers[0]["citationCount"],
                        "source": "semantic_scholar_search",
                        "fetched_at": today,
                    }
                    print(f"  {name}: {results[name]['count']} (title search)")
                else:
                    results[name] = cache[name] = None
                    print(f"  {name}: not found (title search)")
            except Exception as e:
                results[name] = None
                print(f"  {name}: search failed ({e})")
            _save_cache()
            time.sleep(2)

        elif arxiv_id is None:
            # No paper (Egocentric-10K, Egocentric-100K)
            results[name] = cache[name] = None
            _save_cache()

        else:
            url = f"{BASE}/paper/arXiv:{arxiv_id}?fields=citationCount"
            try:
                data = _get(url)
                count = (data or {}).get("citationCount")
                if count is not None:
                    results[name] = cache[name] = {
                        "count": count,
                        "source": "semantic_scholar",
                        "fetched_at": today,
                    }
                    print(f"  {name}: {count} (arXiv:{arxiv_id})")
                    _save_cache()
                else:
                    results[name] = None
                    print(f"  {name}: citationCount missing in response")
            except Exception as e:
                results[name] = None
                print(f"  {name}: fetch failed ({e})")
            time.sleep(2)

    return results


# ============================================================
# MAIN
# ============================================================

def main():
    catalog_path = sys.argv[1] if len(sys.argv) > 1 else 'data/ego-datasets/ego_dataset_catalog.csv'
    output_dir   = sys.argv[2] if len(sys.argv) > 2 else 'data/quality-profiles'
    scorecard_dir = 'docs/scorecard'

    with open(catalog_path) as f:
        catalog = list(csv.DictReader(f))

    target_rows = [r for r in catalog if r['Dataset Name'].strip() in TARGET_DATASETS]
    missing = set(TARGET_DATASETS) - {r['Dataset Name'].strip() for r in target_rows}
    if missing:
        print(f"WARNING: not found in catalog: {missing}")
    print(f"Processing {len(target_rows)} / {len(TARGET_DATASETS)} target datasets")

    # Pool-level stats for relative scoring
    all_scenes = []
    for r in catalog:
        s = r.get('Number of Scenes/Environments', '').strip().replace('~', '').replace('+', '').replace(',', '')
        try:
            all_scenes.append(float(s.split()[0]))
        except (ValueError, IndexError):
            pass
    # For demographic diversity: use participants × geo_locations
    all_products = []
    for r in catalog:
        p = r.get('Number of Participants', '').strip().replace('~', '').replace('+', '').replace(',', '')
        try:
            parts = float(p.split()[0])
        except (ValueError, IndexError):
            continue
        name = r['Dataset Name'].strip()
        pm = PAPER_METADATA.get(name, {})
        geo = pm.get('geo_locations', 1) or 1
        all_products.append(parts * geo)
    max_scenes  = max(all_scenes)  if all_scenes  else 1
    max_product = max(all_products) if all_products else 1

    os.makedirs(os.path.join(output_dir, 'profiles'), exist_ok=True)
    os.makedirs(scorecard_dir, exist_ok=True)

    print("Fetching citation counts from Semantic Scholar...")
    citations_map = fetch_all_citations(PAPER_METADATA)

    qps = [build_qp(r, max_scenes, max_product, citations_map) for r in target_rows]
    compute_download_efficiency_percentiles(qps)

    # Write QP JSON files
    for qp in qps:
        slug = (qp["name"].lower()
                .replace(' ', '-').replace('/', '-')
                .replace('(', '').replace(')', ''))
        path = os.path.join(output_dir, 'profiles', f'{slug}.qp.json')
        with open(path, 'w') as f:
            json.dump(qp, f, indent=2)

    # Write summary CSV
    csv_path = os.path.join(output_dir, 'metadata_eval_summary.csv')
    generate_summary_csv(qps, csv_path)

    # Write scorecard data JS
    js_path = os.path.join(scorecard_dir, 'scorecard_data.js')
    generate_scorecard_data_js(qps, js_path)

    # Print overview table
    print(f"\n{'Dataset':<22} {'FPS':>5} {'Res':>5} {'Cal':>5} {'Ann':>5} {'Lic':>5} {'Acc':>5} {'Scale':>5} {'Cmp':>5}")
    print("─" * 72)
    for qp in qps:
        s = qp["qp:qualityProfile"]["scores"]
        c = qp["qp:qualityProfile"]["confidence"]
        def f(v): return f"{v:.2f}" if v is not None else " null"
        print(f"{qp['name']:<22} {f(s['fps']['score']):>5} {f(s['resolution']['score']):>5} "
              f"{f(s['camera_calibration']['score']):>5} {f(s['annotation_coverage']['score']):>5} "
              f"{f(s['license_clarity']['score']):>5} {f(s['accessibility']['score']):>5} "
              f"{f(s['scale']['score']):>5} {f(c['metadata_completeness']['score']):>5}")

    print(f"\nWrote {len(qps)} QP profiles → {output_dir}/profiles/")
    print(f"Wrote summary CSV → {csv_path}")
    print(f"Wrote scorecard data → {js_path}")


if __name__ == '__main__':
    main()
