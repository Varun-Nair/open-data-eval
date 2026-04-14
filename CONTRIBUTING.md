# Contributing to Open Data Eval

Thanks for helping build the definitive data quality catalog for AI/ML datasets.

## How to Contribute

### Submit a new dataset
Open a [Dataset Submission](../../issues/new?template=dataset_submission.yml) issue. We'll verify and add it.

### Report a correction
Open a [Data Correction](../../issues/new?template=data_correction.yml) issue with the current value, correct value, and your source.

### Suggest improvements
Open a [Feature Request](../../issues/new?template=feature_request.yml) issue.

### Submit a PR
Fork, make changes, and submit a PR using our template. All PRs must pass the verification checklist.

## Data Standards

### Column Values

**Category** — must be one of:
Large-scale foundation, Classic, Action recognition, Hand-object interaction, Body pose, Gaze and eye tracking, Industrial and procedural, Social interaction, Ego-exo cross-view, Navigation and localization, 3D reconstruction, Object detection, VQA and language, Audio-visual, Driving, Video generation, Lifelogging, Surgical, Child egocentric, Drone FPV, Sports, Expert assistance, Assistive, Animal, Tracking

**Access Level** — must be one of:
Open, Gated-Open, Restricted, Commercial, Unavailable

**License Type** — must be one of:
CC-BY-4.0, CC-BY-NC-4.0, CC-BY-SA-4.0, CC-BY-NC-SA-4.0, CC-BY-NC-ND-4.0, MIT, Apache 2.0, Custom Academic, Custom Open, S-Lab License, Mixed, Not specified

**URL Status** — must be one of:
Live, Live but broken, Dead, Redirect

**Modalities** — semicolon-separated, using these terms:
RGB video, Depth (RGB-D), Depth (stereo), Audio, IMU, Eye gaze, Hand pose annotations, Body pose annotations, Force/torque, Tactile, Motion capture, SLAM/odometry, 3D point clouds, 3D scene reconstruction, LiDAR, Event camera, Optical flow, Narrations/captions

### Formatting Rules

- **Total Hours**: plain numbers only. No parentheticals. "~10" not "~10 (43 subjects x 5 recipes)".
- **Number of Participants**: plain numbers only. "37" not "37 participants; 45 kitchens".
- **No emoji** in any CSV cell.
- **License check**: before marking "Not specified", check website, GitHub LICENSE file, paper appendix, and download page. Note what you checked in Key Findings/Issues.
- **Paper over website**: when info conflicts, trust the paper.

### Verification

Every dataset entry must have:
1. Primary URL actually fetched (not guessed)
2. Download mechanism verified (not just landing page)
3. License checked across 4 sources
4. All fields using standardized vocabulary
