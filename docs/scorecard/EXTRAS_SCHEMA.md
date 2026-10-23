# Scorecard data contracts

The scorecard page (`docs/scorecard/`) reads three JS globals. All three are generated or hand-curated
files loaded by `index.html` before `scorecard.jsx`:

| Global | File | Produced by |
|---|---|---|
| `window.SCORECARD_DATA` | `scorecard_data.js` | `eval/metadata_eval.py` (do not edit by hand) |
| `window.DATASET_EXTRAS` | `dataset_extras.js` | `eval/build_extras.py` from `data/ego-datasets/extras/*.extras.json` (do not edit by hand) |
| `window.METRICS_GUIDE` | `metrics_guide.js` | hand-written copy explaining every score |

Dataset identity is the exact `name` string used in `scorecard_data.js` (e.g. `"EPIC-KITCHENS-100"`,
`"EgoSuite-Open100K (EgoDemo)"`). The per-dataset extras file is named by the same slug rule the QP
files use: lowercase, spaces → `-`, `/` → `-`, parentheses removed.
Example: `Human Archive (HA-Ego)` → `data/ego-datasets/extras/human-archive-ha-ego.extras.json`.

---

## 1. `data/ego-datasets/extras/<slug>.extras.json`

One file per dataset. Every field is required unless marked optional. Use `null` for unknown, never
an empty string. Only official sources (project site, paper, the authors' GitHub, the authors' Hugging Face
repo, the authors' YouTube channel). Every URL must have been checked to return HTTP 200 at curation time.

```jsonc
{
  "name": "Ego4D",                                   // exact SCORECARD_DATA name
  "tagline": "3,670 h of daily-life video from 931 wearers across 74 sites, densely narrated.",
                                                     // ≤ 140 chars, plain English, concrete numbers
  "links": {
    "project":     "https://ego4d-data.org/",        // official landing page (required, may equal download)
    "paper":       "https://arxiv.org/abs/2110.07058", // arXiv/DOI/OpenReview; null if no paper
    "huggingface": null,                             // official HF dataset/collection URL; null if none
    "github":      "https://github.com/facebookresearch/Ego4d", // official code/toolkit; null if none
    "download":    "https://ego4d-data.org/docs/start-here/"    // where a user actually starts downloading
  },
  "hfDatasetId": null,                               // "org/name" when `links.huggingface` is a *dataset*
                                                     // repo (not a collection); used for the embedded viewer
  "hfViewer": false,                                 // true only if https://datasets-server.huggingface.co/is-valid?dataset=<id>
                                                     // reports "viewer": true or "preview": true
  "annotations": {
    "format": "JSON",                                // primary on-disk annotation format(s)
    "coverageNote": "Narrations cover 100 % of footage; gaze, 3D and hand-object subsets are partial.",
                                                     // ≤ 160 chars, optional
    "types": {                                       // ALL 13 keys required, in this order
      "narrations":       { "present": true,  "note": "Dense timestamped free-text narrations" },
      "action_labels":    { "present": true,  "note": "Moments / FHO verb-noun segments" },
      "object_boxes":     { "present": true,  "note": "FHO object boxes on keyframes" },
      "segmentation":     { "present": false, "note": null },
      "hand_pose":        { "present": true,  "note": "EgoPose subset (hand keypoints)" },
      "body_pose":        { "present": true,  "note": "EgoPose subset (3D body)" },
      "object_pose":      { "present": false, "note": null },
      "gaze":             { "present": true,  "note": "~80 h with eye gaze" },
      "camera_pose":      { "present": true,  "note": "Subset with SLAM trajectories" },
      "depth":            { "present": false, "note": null },
      "scene_3d":         { "present": true,  "note": "612 h with 3D scans / point clouds" },
      "audio_transcript": { "present": true,  "note": "AV diarization + transcripts subset" },
      "qa_language":      { "present": true,  "note": "NLQ / Episodic memory queries" }
    },
    "sample": "{\n  \"video_uid\": \"...\",\n  \"narration_text\": \"#C C picks up the knife\",\n  \"timestamp_sec\": 12.4\n}"
                                                     // ≤ 15 lines, a real or faithfully abridged record;
                                                     // string, use \n for newlines; null if annotations absent
  },
  "samples": [                                       // 0–4 items; prefer 1 image/gif + 1 video or viewer
    { "kind": "image",     "src": "https://.../teaser.png", "caption": "Frames from the 74 collection sites", "credit": "ego4d-data.org" },
    { "kind": "video",     "src": "https://.../clip.mp4",   "caption": "...", "credit": "..." },   // direct mp4/webm only
    { "kind": "youtube",   "src": "VIDEO_ID",               "caption": "...", "credit": "..." },   // 11-char id only
    { "kind": "hf-viewer", "src": "org/name",               "caption": "...", "credit": "Hugging Face" }  // only when hfViewer is true
  ],
  "verifiedAt": "2026-10-23"                         // date the URLs were last checked
}
```

### Annotation type vocabulary (fixed keys and meaning)

| key | label shown in UI | meaning |
|---|---|---|
| `narrations` | Narrations | Free-text descriptions of what the wearer does, timestamped |
| `action_labels` | Action labels | Verb/noun or activity classes with temporal segments |
| `object_boxes` | Object boxes | 2D bounding boxes for objects or hands |
| `segmentation` | Segmentation | Pixel masks (hands, objects, semantic) |
| `hand_pose` | Hand pose | 2D/3D hand keypoints or MANO params |
| `body_pose` | Body pose | 2D/3D body keypoints or SMPL params |
| `object_pose` | Object 6-DoF pose | 3D object pose and/or object CAD/mesh models |
| `gaze` | Eye gaze | Gaze point or direction |
| `camera_pose` | Camera pose | 6-DoF camera trajectory (SLAM/odometry/MoCap) |
| `depth` | Depth | Per-frame depth maps (sensor or stereo) |
| `scene_3d` | 3D scene | Point clouds, meshes, scans of the environment |
| `audio_transcript` | Transcripts | Speech transcription / diarization |
| `qa_language` | Q&A / language | Question-answer pairs, instructions, captions beyond narrations |

`present` is `true`, `false` or `null` (unknown). `note` is ≤ 90 chars or `null`.

---

## 2. `docs/scorecard/dataset_extras.js` (generated)

```js
window.DATASET_EXTRAS = { "<name>": { ...the file above minus nothing... }, ... };
```

Generated by `python3 eval/build_extras.py`, which validates every file against this schema and fails
loudly on a bad key, a missing annotation type, an unknown `kind`, or a `hf-viewer` sample without
`hfViewer: true`. The UI must tolerate a dataset with no entry (render nothing for that section).

---

## 3. `docs/scorecard/metrics_guide.js` (hand-written)

```js
window.METRICS_GUIDE = {
  version: "1.0",
  legend: { green: "≥ 70", amber: "40–69", red: "< 40", gray: "no data" },
  overall: {
    label: "Overall",
    short: "...",      // ≤ 120 chars: one sentence a newcomer understands
    how:   "...",      // ≤ 300 chars: exactly how it is computed, matching eval/metadata_eval.py and scorecard.jsx
    good:  "..."       // ≤ 120 chars: what a high score means in practice
  },
  dimensions: [        // the five radar dimensions + the two extra table columns, in this order
    { key: "technical",     label: "Technical",     color: "var(--c-accent-tech)",   inputs: ["fps","res"],          short, how, good },
    { key: "scale",         label: "Scale",         color: "var(--c-accent-scale)",  inputs: ["scale"],              short, how, good },
    { key: "annotation",    label: "Annotation",    color: "var(--c-accent-rel)",    inputs: ["annCov"],             short, how, good },
    { key: "accessibility", label: "Accessibility", color: "var(--c-accent-access)", inputs: ["lic","acc"],          short, how, good },
    { key: "tooling",       label: "Tooling",       color: "var(--c-accent-hw)",     inputs: ["dl","doc"],           short, how, good },
    { key: "reliability",   label: "Reliability",   color: "var(--c-accent-rel)",    inputs: ["camCal","annCov"],    short, how, good },
    { key: "fit",           label: "Downstream fit",color: "var(--c-accent-fit)",    inputs: ["actRecog","handPose","nav"], short, how, good }
  ],
  metrics: {           // every per-metric score in SCORECARD_DATA, keyed by its field name
    fps:          { label: "Frame rate",            unit: "fps",   short, how, good },
    res:          { label: "Resolution",            unit: "px",    short, how, good },
    camCal:       { label: "Camera calibration",    unit: "tier",  short, how, good },
    annCov:       { label: "Annotation coverage",   unit: "%",     short, how, good },
    lic:          { label: "License clarity",       unit: "tier",  short, how, good },
    acc:          { label: "Access level",          unit: "tier",  short, how, good },
    dl:           { label: "Dataloader",            unit: "tier",  short, how, good },
    doc:          { label: "Documentation",         unit: "0–3",   short, how, good },
    scale:        { label: "Scale",                 unit: "hours", short, how, good },
    envDiv:       { label: "Environment diversity", unit: "count", short, how, good },
    demoDiv:      { label: "Participant diversity", unit: "count", short, how, good },
    dlEff:        { label: "Download efficiency",   unit: "h/GB",  short, how, good },
    completeness: { label: "Metadata completeness", unit: "%",     short, how, good },
    citations:    { label: "Citations",             unit: "count", short, how, good },
    fileEval:     { label: "File verification",     unit: "—",     short, how, good }
  },
  usecases: {          // the three selectable "Fit" use cases
    actRecog: { label: "Action Recognition",      short, how, good },
    handObj:  { label: "Hand-Object Interaction", short, how, good },
    nav:      { label: "Navigation",              short, how, good }
  },
  ranking: {           // how the leaderboard orders datasets
    short: "...",
    how:   "...",
    caveats: ["...", "..."]   // ≤ 3 bullets, ≤ 110 chars each
  }
};
```

`overall` is defined as the plain mean of the five radar dimensions (technical, scale, annotation,
accessibility, tooling), ignoring dimensions that are null. Downstream fit is use-case dependent and is
shown as its own column, never folded into Overall.
