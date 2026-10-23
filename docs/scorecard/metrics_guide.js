// Open Data Eval — plain-English guide to every score on the scorecard.
// Hand-written. Keep each `short` to one sentence; `how` must match eval/metadata_eval.py exactly.
// Schema: docs/scorecard/EXTRAS_SCHEMA.md (section 3)
//
// Limits: short ≤ 120 chars, how ≤ 300 chars, good ≤ 120 chars, each ranking caveat ≤ 110 chars.
// Every score is stored 0–1 in SCORECARD_DATA and displayed ×100; the numbers below use the 0–100 form.
// Validate with: node <scratchpad>/check_guide.js (asserts keys and length limits).
window.METRICS_GUIDE = {
  version: "1.0",
  legend: { green: "≥ 70", amber: "40–69", red: "< 40", gray: "no data" },

  overall: {
    label: "Overall",
    short: "One number, 0 to 100, summarising how complete, open and well-packaged a dataset is.",
    how: "Plain mean of the five dimension scores (Technical, Scale, Annotation, Accessibility, Tooling), each 0–100. A dimension with no data is skipped, and the dataset is then ranked after all complete ones. Downstream fit is never included.",
    good: "70+ means strong across the board; it says nothing about video or label quality, which are not yet measured."
  },

  dimensions: [
    {
      key: "technical", label: "Technical", color: "var(--c-accent-tech)", inputs: ["fps", "res"],
      short: "How sharp and smooth the video is, based on the published frame rate and resolution.",
      how: "Mean of the Frame rate and Resolution scores (scorecard.jsx DIMS); if one is unknown the other stands alone. Both come from the catalog, with paper values overriding the catalog when they differ.",
      good: "100 = at least 30 fps and a 1080p short edge; it is the spec sheet, not a check for blur or dropped frames."
    },
    {
      key: "scale", label: "Scale", color: "var(--c-accent-scale)", inputs: ["scale"],
      short: "How much footage there is, measured in total hours on a logarithmic scale.",
      how: "Identical to the Scale metric: log10(hours + 1) / log10(10001), capped at 1. So 10 h ≈ 26, 100 h ≈ 50, 1,000 h ≈ 75, 10,000 h = 100. Hours come from the paper when stated, else the catalog.",
      good: "Rewards hours only; a 10-hour hand dataset can still be the best for its task. People and places are separate."
    },
    {
      key: "annotation", label: "Annotation", color: "var(--c-accent-rel)", inputs: ["annCov"],
      short: "What share of the footage actually carries labels, as reported in the paper.",
      how: "Identical to the Annotation coverage metric: the fraction of footage (or clips, or episodes) with annotations, read from the primary paper and entered by hand in metadata_eval.py. No paper review yet = no data.",
      good: "100 means every clip is labelled with something; it does not say how rich or accurate the labels are."
    },
    {
      key: "accessibility", label: "Accessibility", color: "var(--c-accent-access)", inputs: ["lic", "acc"],
      short: "How easy it is to legally get the data: a clear license plus open, working downloads.",
      how: "Mean of License clarity and Access level (scorecard.jsx DIMS). Note the license also counts for 2 of the 10 points inside Access level, so a clear license is rewarded twice.",
      good: "High = standard license, open access, live URL; gated datasets score lower on purpose, however good the data."
    },
    {
      key: "tooling", label: "Tooling", color: "var(--c-accent-hw)", inputs: ["dl", "doc"],
      short: "Whether you can start using the data quickly: an official loader and good documentation.",
      how: "Mean of the Dataloader and Documentation scores (scorecard.jsx DIMS). Both come from the catalog's 'Dataloader Available?' and 'Documentation Quality (0-3)' fields.",
      good: "100 = official PyTorch/TF/JAX/HF loader and a 3/3 docs rating; the rating is a curator's judgement, not a test."
    },
    {
      key: "reliability", label: "Reliability", color: "var(--c-accent-rel)", inputs: ["camCal", "annCov"],
      short: "How much you can trust the geometry and labels: camera calibration plus annotation coverage.",
      how: "Mean of Camera calibration and Annotation coverage (CompareTable relScore). Shown as a table column only; it is not one of the five dimensions and does not feed Overall. Missing values are skipped.",
      good: "High = validated intrinsics + extrinsics and near-full labelling; vital for 3D work, less so for pure video tasks."
    },
    {
      key: "fit", label: "Downstream fit", color: "var(--c-accent-fit)", inputs: ["actRecog", "handPose", "nav"],
      short: "How well the recorded sensor streams match the task you pick: action recognition, hand-object or navigation.",
      how: "The modality score for the selected use case (actRecog, handPose or nav field), computed from the catalog's 'Modalities Present' list as cr² × (0.60 + 0.28·ir + 0.12·br). Changes with the use case; never part of Overall.",
      good: "60+ means every critical modality is present; 25 or less means one is missing, so the task is probably out of reach."
    }
  ],

  metrics: {
    fps: {
      label: "Frame rate", unit: "fps",
      short: "How many frames per second the cameras record; smoother video scores higher.",
      how: "Published fps (paper overrides catalog; first number if a range). ≥ 30 fps = 100; 24–30 → 70–100 linear; 15–24 → 30–70 linear; < 15 → 30 × fps/15 with a floor of 5. 'Varies' or unknown = no data.",
      good: "100 = 30 fps or more, the consumer-camera norm; the stated rate is not checked against files unless ffprobe ran."
    },
    res: {
      label: "Resolution", unit: "px",
      short: "How many pixels each frame has, judged by its shorter side (1080 for 1920×1080).",
      how: "Short edge s of the published W×H (paper overrides catalog; '720p' assumes 16:9, '4K' = 3840×2160, '2K' = 2560×1440). s ≥ 1080 = 100; 720–1080 → 70–100; 480–720 → 30–70; < 480 → 30 × s/480, floor 5.",
      good: "100 = Full HD or better on the short edge; 480p datasets still work for many hand-pose and robot tasks."
    },
    camCal: {
      label: "Camera calibration", unit: "tier",
      short: "Whether the dataset ships the camera parameters needed to turn pixels into 3D geometry.",
      how: "Tier assigned by hand from the paper: 100 intrinsics + distortion + extrinsics, validated; 85 the same, unvalidated; 60 intrinsics + extrinsics, undistorted delivery; 50 intrinsics + distortion; 35 intrinsics only; 0 none; no data = paper not yet reviewed.",
      good: "85+ lets you do SLAM, depth and hand-object 3D out of the box; 0 is common and harmless for pure 2D video tasks."
    },
    annCov: {
      label: "Annotation coverage", unit: "%",
      short: "The percentage of the footage that has labels of any kind, according to the paper.",
      how: "Fraction (0–1, shown as %) of footage, clips or episodes with annotations, taken from the primary paper and set by hand in PAPER_METADATA. No computation beyond the ratio; datasets without a paper review show no data.",
      good: "100 means labels span the whole dataset; it counts coverage, not label type, density or accuracy."
    },
    lic: {
      label: "License clarity", unit: "tier",
      short: "Whether the data comes with a recognisable license that tells you what you may do with it.",
      how: "From the catalog License Type: 100 for a standard license (CC-BY / NC / SA / ND 4.0, MIT, Apache 2.0, BSD); 50 for a named custom one (Custom Academic, Custom Open, S-Lab License, Mixed); 0 when none is specified.",
      good: "100 = terms you can read in a minute; note CC-BY-NC scores 100 yet still bans commercial use."
    },
    acc: {
      label: "Access level", unit: "tier",
      short: "How easy it is to actually get the data: open vs gated, working links, docs and a loader.",
      how: "Catalog points out of 10: access Open 3 / Gated-Open 2 / Restricted 1; URL Live 2 / broken or redirect 1 / dead 0; license standard 2 / custom 1; docs rating 3 → 1.5, 2 → 1, 1 → 0.5; dataloader 1; commercial use yes 0.5 / no 0.25 / unclear 0.",
      good: "80+ = click and download today; a sign-up form or approval queue costs points by design, even for great data."
    },
    dl: {
      label: "Dataloader", unit: "tier",
      short: "Whether official code exists to load the data straight into a training framework.",
      how: "From the catalog 'Dataloader Available?' field: 100 if yes and it names PyTorch, TensorFlow, JAX or Hugging Face; 80 if yes with no framework named; 50 for a community or unofficial loader; 0 otherwise.",
      good: "100 means you skip writing a parser; the loader's quality and maintenance are not assessed."
    },
    doc: {
      label: "Documentation", unit: "0–3",
      short: "How well the dataset is explained: website, README, format docs and examples.",
      how: "The catalog's curator rating 'Documentation Quality (0-3)' divided by 3: 0 → 0, 1 → 33, 2 → 67, 3 → 100. A missing or non-numeric rating scores 0.",
      good: "100 = you can understand the files without emailing the authors; it is one curator's judgement, not a checklist."
    },
    scale: {
      label: "Scale", unit: "hours",
      short: "Total hours of recorded video, on a log scale so that 10× more footage adds a fixed step.",
      how: "log10(hours + 1) / log10(10001), capped at 1: 10 h ≈ 26, 100 h ≈ 50, 1,000 h ≈ 75, 10,000 h = 100. Hours come from the paper's total_hours_override when set, else the catalog; '~', '+' and '<' are stripped.",
      good: "Bigger is better for pretraining; a small, dense dataset can still be best for a narrow task."
    },
    envDiv: {
      label: "Environment diversity", unit: "count",
      short: "How many distinct places or scenes were recorded, relative to the largest dataset in the catalog.",
      how: "log10(n + 1) / log10(max + 1), where n is the catalog's 'Number of Scenes/Environments' (first number) and max is the largest such count across the whole catalog, not just the scored datasets. Unknown = no data.",
      good: "High = many kitchens, homes or sites, which helps generalisation; relative, so it shifts when the catalog grows."
    },
    demoDiv: {
      label: "Participant diversity", unit: "count",
      short: "How many different people, in how many places, appear in the data; a proxy for how varied the wearers are.",
      how: "log10(participants × locations + 1) / log10(max + 1): participants from the catalog, geographic locations from the paper (1 if unknown), max = largest product across the whole catalog. Robot datasets have no participants, so no data.",
      good: "High = hundreds of wearers across several countries; it counts people and places, not age, gender or skill."
    },
    dlEff: {
      label: "Download efficiency", unit: "h/GB",
      short: "How many hours of video you get per gigabyte downloaded, compared with the other scored datasets.",
      how: "hours ÷ download size in GB (size from the paper), then a percentile rank within the scored pool: the share of pool datasets with an equal or lower h/GB. Unknown size = no data. Recomputed whenever the pool changes.",
      good: "High = cheap to fetch and store; it also rewards heavy compression or low resolution, so read it with Technical."
    },
    completeness: {
      label: "Metadata completeness", unit: "%",
      short: "How much of the scorecard we could fill in for this dataset; low values mean the other scores are less certain.",
      how: "Share of 16 fields that are non-null: the 13 QP scores (fps, resolution, modality fit, calibration, license, access, scale, dataloader, docs, annotation coverage, download efficiency, environment and participant diversity) + capture device, lens type, video format.",
      good: "100 = everything was documented or researched; a confidence signal, not quality. Coloured green ≥ 80, amber ≥ 55."
    },
    citations: {
      label: "Citations", unit: "count",
      short: "How many papers cite the dataset's primary paper, a rough sign of how widely it is used.",
      how: "Live count from the Semantic Scholar API for the paper's arXiv id (title search as fallback), cached in data/quality-profiles/citations_cache.json. Not a score and not part of any dimension; datasets with no paper show no data.",
      good: "Thousands = a well-trodden benchmark with tooling and baselines; new datasets start near zero regardless of quality."
    },
    fileEval: {
      label: "File verification", unit: "—",
      short: "Whether we downloaded sample files and checked the claimed frame rate and resolution with ffprobe.",
      how: "Present only when eval/file_eval.py has run: files checked, measured mean fps, most common W×H, codec, bitrate, audio, and per-type annotation coverage. fps matches if within 1 fps of the claim; resolution must match exactly; < 100 % coverage is flagged.",
      good: "'ffprobe verified' means the spec sheet survived contact with real files; 'metadata only' means it is unchecked so far."
    }
  },

  usecases: {
    actRecog: {
      label: "Action Recognition",
      short: "Recognising and localising what the wearer is doing over time; needs RGB video, helped by audio and narrations.",
      how: "cr² × (0.60 + 0.28·ir + 0.12·br) from the catalog modality list. Critical: RGB video. Important: Audio, Narrations/captions, Optical flow. Bonus: Eye gaze, Hand pose, IMU, Object bounding boxes. Each ratio = share of that tier present.",
      good: "Almost every dataset clears 60 here; 80+ means most of audio, narrations and optical flow are there, which matter most."
    },
    handObj: {
      label: "Hand-Object Interaction",
      short: "Hand pose, grasping and manipulation; needs both RGB video and hand-pose labels, helped by depth.",
      how: "cr² × (0.60 + 0.28·ir + 0.12·br) from the catalog modality list. Critical: RGB video, Hand pose annotations. Important: Depth, Stereo. Bonus: Tactile, IMU, Segmentation masks. Missing one critical halves cr, so the score caps at 25.",
      good: "60+ means hand-pose labels exist; 25 or less means they are missing, so the dataset is video-only for this task."
    },
    nav: {
      label: "Navigation",
      short: "Navigation, SLAM and 3D scene reasoning; needs RGB video plus IMU, helped by depth, odometry and point clouds.",
      how: "cr² × (0.60 + 0.28·ir + 0.12·br) from the catalog modality list. Critical: RGB video, IMU. Important: Depth, SLAM/odometry, 3D point clouds. Bonus: Audio, Stereo, LiDAR, Segmentation masks. Missing IMU halves cr, so the score caps at 25.",
      good: "60+ means an IMU stream exists; 80+ adds most of depth, odometry and point clouds, which navigation work usually needs."
    }
  },

  ranking: {
    short: "The leaderboard sorts datasets by Overall score, highest first; the top three take the podium.",
    how: "Complete datasets (all five dimensions known) are ordered by Overall, highest first; datasets missing a dimension are ranked after them, so a missing value never inflates a rank; they carry a \"4 of 5 dims\" badge and never reach the podium. Ties break on hours, then name.",
    caveats: [
      "Scores are metadata-level: computed from the catalog and papers, plus ffprobe file checks for a few datasets.",
      "They rate how well a dataset is packaged and documented, not how good its video or labels actually are.",
      "Gated or restricted datasets score lower on Access by design, even when the data behind the form is excellent."
    ]
  }
};
