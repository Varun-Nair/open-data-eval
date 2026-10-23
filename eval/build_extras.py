#!/usr/bin/env python3
"""
Build docs/scorecard/dataset_extras.js from data/ego-datasets/extras/*.extras.json.

Each extras file holds hand-curated, non-score information for one dataset: official links,
Hugging Face id, annotation inventory, sample media, and a plain-English tagline.
Schema: docs/scorecard/EXTRAS_SCHEMA.md

Usage:
  python3 eval/build_extras.py            # validate + write docs/scorecard/dataset_extras.js
  python3 eval/build_extras.py --check    # validate only
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

EXTRAS_DIR = "data/ego-datasets/extras"
OUT_PATH = "docs/scorecard/dataset_extras.js"
SCORECARD_DATA = "docs/scorecard/scorecard_data.js"

ANNOTATION_KEYS = [
    "narrations", "action_labels", "object_boxes", "segmentation", "hand_pose", "body_pose",
    "object_pose", "gaze", "camera_pose", "depth", "scene_3d", "audio_transcript", "qa_language",
]
SAMPLE_KINDS = {"image", "video", "youtube", "hf-viewer"}
LINK_KEYS = ["project", "paper", "huggingface", "github", "download"]
URL_RE = re.compile(r"^https?://\S+$")


def slugify(name: str) -> str:
    return (name.lower().replace(" ", "-").replace("/", "-")
            .replace("(", "").replace(")", ""))


def load_scorecard_names() -> set:
    """Names present in scorecard_data.js, so extras can be cross-checked."""
    if not os.path.exists(SCORECARD_DATA):
        return set()
    s = open(SCORECARD_DATA).read()
    s = s[s.index("["): s.rindex("]") + 1]
    return {d["name"] for d in json.loads(s)}


def validate(path: str, e: dict, known_names: set) -> list:
    errs = []
    name = e.get("name")
    if not isinstance(name, str) or not name:
        return [f"{path}: missing 'name'"]
    expected = os.path.join(EXTRAS_DIR, f"{slugify(name)}.extras.json")
    if os.path.normpath(path) != os.path.normpath(expected):
        errs.append(f"{path}: file name should be {expected} for name {name!r}")
    if known_names and name not in known_names:
        errs.append(f"{path}: name {name!r} not found in {SCORECARD_DATA}")

    tag = e.get("tagline")
    if not isinstance(tag, str) or not tag.strip():
        errs.append(f"{path}: 'tagline' required")
    elif len(tag) > 140:
        errs.append(f"{path}: 'tagline' longer than 140 chars ({len(tag)})")

    links = e.get("links")
    if not isinstance(links, dict):
        errs.append(f"{path}: 'links' must be an object")
    else:
        for k in LINK_KEYS:
            if k not in links:
                errs.append(f"{path}: links.{k} missing (use null if none)")
            elif links[k] is not None and not (isinstance(links[k], str) and URL_RE.match(links[k])):
                errs.append(f"{path}: links.{k} must be an http(s) URL or null")
        if not links.get("project"):
            errs.append(f"{path}: links.project is required")
        for k in links:
            if k not in LINK_KEYS:
                errs.append(f"{path}: unknown links key {k!r}")

    hf_id = e.get("hfDatasetId")
    if hf_id is not None and not (isinstance(hf_id, str) and re.match(r"^[\w.-]+/[\w.-]+$", hf_id)):
        errs.append(f"{path}: hfDatasetId must look like 'org/name' or be null")
    hf_viewer = e.get("hfViewer")
    if not isinstance(hf_viewer, bool):
        errs.append(f"{path}: hfViewer must be true/false")
    if hf_viewer and not hf_id:
        errs.append(f"{path}: hfViewer true requires hfDatasetId")

    ann = e.get("annotations")
    if not isinstance(ann, dict):
        errs.append(f"{path}: 'annotations' must be an object")
    else:
        if "format" not in ann:
            errs.append(f"{path}: annotations.format missing (use null)")
        cn = ann.get("coverageNote")
        if cn is not None and (not isinstance(cn, str) or len(cn) > 160):
            errs.append(f"{path}: annotations.coverageNote must be ≤160 chars or null")
        types = ann.get("types")
        if not isinstance(types, dict):
            errs.append(f"{path}: annotations.types must be an object")
        else:
            for k in ANNOTATION_KEYS:
                t = types.get(k)
                if not isinstance(t, dict):
                    errs.append(f"{path}: annotations.types.{k} missing")
                    continue
                if t.get("present") not in (True, False, None):
                    errs.append(f"{path}: annotations.types.{k}.present must be true/false/null")
                note = t.get("note")
                if note is not None and (not isinstance(note, str) or len(note) > 90):
                    errs.append(f"{path}: annotations.types.{k}.note must be ≤90 chars or null")
            for k in types:
                if k not in ANNOTATION_KEYS:
                    errs.append(f"{path}: unknown annotation type {k!r}")
        sample = ann.get("sample")
        if sample is not None:
            if not isinstance(sample, str):
                errs.append(f"{path}: annotations.sample must be a string or null")
            elif sample.count("\n") > 14:
                errs.append(f"{path}: annotations.sample longer than 15 lines")

    samples = e.get("samples")
    if not isinstance(samples, list):
        errs.append(f"{path}: 'samples' must be a list (may be empty)")
    else:
        if len(samples) > 4:
            errs.append(f"{path}: at most 4 samples")
        for i, s in enumerate(samples):
            kind = s.get("kind")
            if kind not in SAMPLE_KINDS:
                errs.append(f"{path}: samples[{i}].kind {kind!r} not in {sorted(SAMPLE_KINDS)}")
                continue
            src = s.get("src")
            if kind in ("image", "video"):
                if not (isinstance(src, str) and URL_RE.match(src)):
                    errs.append(f"{path}: samples[{i}].src must be an http(s) URL")
            elif kind == "youtube":
                if not (isinstance(src, str) and re.match(r"^[\w-]{11}$", src)):
                    errs.append(f"{path}: samples[{i}].src must be an 11-char YouTube id")
            elif kind == "hf-viewer":
                if not hf_viewer or src != hf_id:
                    errs.append(f"{path}: samples[{i}] hf-viewer requires hfViewer true and src == hfDatasetId")
            if not isinstance(s.get("caption"), str) or not s["caption"].strip():
                errs.append(f"{path}: samples[{i}].caption required")
            if not isinstance(s.get("credit"), str) or not s["credit"].strip():
                errs.append(f"{path}: samples[{i}].credit required")

    va = e.get("verifiedAt")
    if not (isinstance(va, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", va)):
        errs.append(f"{path}: verifiedAt must be YYYY-MM-DD")

    allowed_top = {"name", "tagline", "links", "hfDatasetId", "hfViewer", "annotations", "samples", "verifiedAt"}
    for k in e:
        if k not in allowed_top:
            errs.append(f"{path}: unknown top-level key {k!r}")
    return errs


def main():
    check_only = "--check" in sys.argv
    files = sorted(glob.glob(os.path.join(EXTRAS_DIR, "*.extras.json")))
    known = load_scorecard_names()
    extras, errors = {}, []
    for path in files:
        try:
            e = json.load(open(path))
        except json.JSONDecodeError as ex:
            errors.append(f"{path}: invalid JSON ({ex})")
            continue
        errs = validate(path, e, known)
        if errs:
            errors.extend(errs)
        else:
            extras[e["name"]] = e

    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} problem(s) in {len(files)} file(s)")
        sys.exit(1)

    missing = sorted(known - set(extras))
    print(f"Validated {len(extras)} extras file(s)")
    if missing:
        print(f"No extras yet for {len(missing)} scored dataset(s): {', '.join(missing)}")
    if check_only:
        return

    js = ("// Auto-generated by eval/build_extras.py from data/ego-datasets/extras/*.extras.json — do not edit manually\n"
          f"// Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
          f"window.DATASET_EXTRAS = {json.dumps(extras, indent=2, ensure_ascii=False)};\n")
    with open(OUT_PATH, "w") as f:
        f.write(js)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
