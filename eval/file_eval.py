#!/usr/bin/env python3
"""
eval/file_eval.py — File-level evaluation pipeline for quality profiling.

Runs ffprobe on every video file in a dataset directory, checks annotation
coverage, compares claimed vs actual metadata, and outputs a file_eval_report.json.
Can also append a "file_eval" section directly into a quality profile QP JSON.

Usage
-----
  python eval/file_eval.py <dataset_dir>
  python eval/file_eval.py <dataset_dir> -o /path/to/report.json
  python eval/file_eval.py <dataset_dir> --append-qp <profile.qp.json>

Outputs
-------
  <dataset_dir>/file_eval_report.json   Full report with per-file ffprobe results,
                                        distributions, annotation coverage, and discrepancies
  (optional) Updated <profile>.qp.json  Adds "file_eval" section to existing QP
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── ffprobe helpers ──────────────────────────────────────────────────────────

def run_ffprobe(video_path: Path):
    """Run ffprobe and return (parsed_dict, error_string)."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return None, "ffprobe not found — install ffmpeg"
    except subprocess.TimeoutExpired:
        return None, "ffprobe timeout"
    if result.returncode != 0:
        return None, result.stderr.strip()
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def parse_video_stream(probe_data: dict) -> dict | None:
    """Extract video-stream metadata from ffprobe output."""
    if not probe_data:
        return None
    streams = probe_data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        return None

    def parse_rate(rate_str):
        if rate_str and "/" in rate_str:
            try:
                n, d = rate_str.split("/")
                return round(int(n) / int(d), 4) if int(d) else None
            except Exception:
                pass
        return None

    fps = parse_rate(video.get("r_frame_rate")) or parse_rate(video.get("avg_frame_rate"))

    duration_sec = None
    for src in (video, probe_data.get("format", {})):
        if "duration" in src:
            try:
                duration_sec = float(src["duration"])
                break
            except ValueError:
                pass

    nb_frames = None
    try:
        v = int(video.get("nb_frames", 0))
        nb_frames = v if v > 0 else None
    except (ValueError, TypeError):
        pass
    if nb_frames is None and fps and duration_sec:
        nb_frames = int(round(fps * duration_sec))

    bitrate_kbps = None
    for src in (video, probe_data.get("format", {})):
        if "bit_rate" in src:
            try:
                bitrate_kbps = int(src["bit_rate"]) // 1000
                break
            except (ValueError, TypeError):
                pass

    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    return {
        "codec":        video.get("codec_name"),
        "width":        video.get("width"),
        "height":       video.get("height"),
        "fps":          fps,
        "duration_sec": duration_sec,
        "nb_frames":    nb_frames,
        "bitrate_kbps": bitrate_kbps,
        "pix_fmt":      video.get("pix_fmt"),
        "has_audio":    bool(audio_streams),
        "audio_codecs": [s.get("codec_name") for s in audio_streams],
    }


# ── statistics ───────────────────────────────────────────────────────────────

def compute_distribution(values: list) -> dict | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)

    def pct(p):
        return vals[min(int(p * (n - 1)), n - 1)]

    result = {
        "n":    n,
        "mean": round(statistics.mean(vals), 4),
        "min":  round(vals[0], 4),
        "max":  round(vals[-1], 4),
    }
    if n > 1:
        result["std"] = round(statistics.stdev(vals), 4)
        result["p5"]  = round(pct(0.05), 4)
        result["p95"] = round(pct(0.95), 4)
    return result


# ── annotation coverage ──────────────────────────────────────────────────────

def check_annotation_coverage(
    clip_ids: list[str],
    annotations_dir: Path,
) -> dict | None:
    if not annotations_dir.exists():
        return None

    result = {}
    for subdir in sorted(annotations_dir.iterdir()):
        if not subdir.is_dir():
            continue

        covered, missing = [], []
        for cid in clip_ids:
            if list(subdir.glob(f"{cid}.*")):
                covered.append(cid)
            else:
                missing.append(cid)

        result[subdir.name] = {
            "clips_covered":  len(covered),
            "clips_total":    len(clip_ids),
            "coverage_pct":   round(len(covered) / len(clip_ids) * 100, 1) if clip_ids else 0,
            "missing":        missing or None,
        }
    return result


# ── discrepancy checks ───────────────────────────────────────────────────────

def check_manifest_vs_actual(
    manifest: dict,
    per_file: dict,
) -> list[dict]:
    issues = []
    stats = manifest.get("stats", {})

    claimed_clips = stats.get("total_clips")
    actual_clips = len(per_file)
    if claimed_clips is not None and claimed_clips != actual_clips:
        issues.append({
            "source": "manifest.json",
            "field": "total_clips",
            "claimed": claimed_clips,
            "actual": actual_clips,
            "severity": "high" if abs(actual_clips - claimed_clips) > 1 else "low",
        })

    claimed_dur = stats.get("total_duration_sec")
    actual_dur = sum(
        r["video"]["duration_sec"]
        for r in per_file.values()
        if r.get("video") and r["video"].get("duration_sec")
    )
    if claimed_dur is not None and abs(actual_dur - claimed_dur) > 0.5:
        issues.append({
            "source": "manifest.json",
            "field": "total_duration_sec",
            "claimed": claimed_dur,
            "actual": round(actual_dur, 3),
            "delta_sec": round(actual_dur - claimed_dur, 3),
            "severity": "low",
        })

    return issues


def check_clip_metadata_vs_actual(
    clip_metadata: list[dict],
    per_file: dict,
) -> list[dict]:
    issues = []
    for clip in clip_metadata:
        cid = clip.get("clip_id")
        if not cid or cid not in per_file:
            continue
        actual = per_file[cid].get("video") or {}

        checks = [
            ("fps",           clip.get("fps"),                   actual.get("fps"),          1.0,  "medium"),
            ("duration_sec",  clip.get("duration_sec"),           actual.get("duration_sec"), 0.1,  "low"),
            ("total_frames",  clip.get("total_frames"),           actual.get("nb_frames"),    2,    "low"),
        ]
        for field, claimed, actual_val, tol, sev in checks:
            if claimed is not None and actual_val is not None:
                if abs(actual_val - claimed) > tol:
                    issues.append({
                        "source": "metadata/clips.json",
                        "clip_id": cid,
                        "field": field,
                        "claimed": claimed,
                        "actual": actual_val if field != "duration_sec" else round(actual_val, 4),
                        "delta": round(actual_val - claimed, 4),
                        "severity": sev,
                    })

        # Resolution: string comparison
        claimed_res = clip.get("resolution")
        if claimed_res and actual.get("width") and actual.get("height"):
            actual_res = f"{actual['width']}x{actual['height']}"
            if claimed_res != actual_res:
                issues.append({
                    "source": "metadata/clips.json",
                    "clip_id": cid,
                    "field": "resolution",
                    "claimed": claimed_res,
                    "actual": actual_res,
                    "severity": "medium",
                })

        # Codec: loose match (hevc ↔ h265)
        claimed_codec = (clip.get("codec") or "").lower()
        actual_codec  = (actual.get("codec") or "").lower()
        if claimed_codec and actual_codec:
            ALIASES = {frozenset({"hevc", "h265"}), frozenset({"avc", "h264"}), frozenset({"vp9", "vp09"})}
            if claimed_codec != actual_codec:
                aliased = any(
                    claimed_codec in pair and actual_codec in pair for pair in ALIASES
                )
                if not aliased:
                    issues.append({
                        "source": "metadata/clips.json",
                        "clip_id": cid,
                        "field": "codec",
                        "claimed": claimed_codec,
                        "actual": actual_codec,
                        "severity": "medium",
                    })

    return issues


def check_sensor_vs_video_resolution(
    per_file: dict,
    sensors_dir: Path,
    sample_n: int = 5,
) -> list[dict]:
    issues = []
    if not sensors_dir.exists():
        return issues

    for cid in list(per_file)[:sample_n]:
        sf = sensors_dir / f"{cid}.jsonl"
        if not sf.exists():
            continue
        try:
            with open(sf) as fh:
                frame0 = json.loads(fh.readline())
            intr = frame0.get("camera", {}).get("intrinsics", {})
            sw, sh = intr.get("width"), intr.get("height")
            vw = per_file[cid].get("video", {}).get("width")
            vh = per_file[cid].get("video", {}).get("height")
            if sw and vw and (sw != vw or sh != vh):
                issues.append({
                    "source": f"annotations/sensors/{cid}.jsonl",
                    "clip_id": cid,
                    "field": "sensor_intrinsics_resolution_vs_video",
                    "claimed": f"{sw}x{sh}",
                    "actual":  f"{vw}x{vh}",
                    "note": "Sensor intrinsics reference full-capture resolution; exported video is cropped/scaled",
                    "severity": "info",
                })
        except Exception:
            continue
    return issues


# ── main ──────────────────────────────────────────────────────────────────────

def run_file_eval(dataset_dir: Path, output_path: Path | None = None) -> dict:
    dataset_dir = Path(dataset_dir).expanduser().resolve()
    if not dataset_dir.exists():
        print(f"ERROR: directory not found: {dataset_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"File eval: {dataset_dir.name}")

    # ── Load manifest ─────────────────────────────────────────────────────────
    manifest = None
    manifest_path = dataset_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        print(f"  manifest:     {manifest_path.name}")

    # ── Load per-clip metadata ────────────────────────────────────────────────
    clip_metadata = None
    clips_json = dataset_dir / "metadata" / "clips.json"
    if clips_json.exists():
        with open(clips_json) as f:
            clip_metadata = json.load(f)
        print(f"  clip metadata: {clips_json.relative_to(dataset_dir)}")

    # ── Find video files ──────────────────────────────────────────────────────
    clips_dir = dataset_dir / "clips"
    if clips_dir.exists():
        exts = ("*.mp4", "*.MP4", "*.mov", "*.MOV", "*.avi", "*.AVI", "*.mkv", "*.MKV", "*.webm")
        video_files = sorted(
            p for ext in exts for p in clips_dir.glob(ext)
        )
    else:
        video_files = sorted(
            p for ext in ("*.mp4", "*.MP4", "*.mov", "*.MOV", "*.avi", "*.AVI", "*.mkv", "*.MKV")
            for p in dataset_dir.rglob(ext)
            if ".git" not in p.parts
        )

    if not video_files:
        print("ERROR: no video files found", file=sys.stderr)
        sys.exit(1)

    print(f"  video files:  {len(video_files)}")

    # ── ffprobe each file ────────────────────────────────────────────────────
    per_file: dict[str, dict] = {}
    errors: list[dict] = []

    for vf in video_files:
        cid = str(vf.relative_to(dataset_dir).with_suffix(""))
        print(f"    {vf.name}", end="", flush=True)
        probe, err = run_ffprobe(vf)
        if err:
            print(f"  ERROR: {err}")
            errors.append({"file": str(vf.relative_to(dataset_dir)), "error": err})
            continue

        vi = parse_video_stream(probe)
        size_mb = round(vf.stat().st_size / (1024 * 1024), 3)
        per_file[cid] = {"file": str(vf.relative_to(dataset_dir)), "size_mb": size_mb, "video": vi}

        if vi:
            print(
                f"  {vi.get('codec','?')} "
                f"{vi.get('width','?')}x{vi.get('height','?')} "
                f"{vi.get('fps','?')}fps "
                f"{round(vi.get('duration_sec') or 0, 2)}s "
                f"{'audio' if vi.get('has_audio') else 'no-audio'}"
            )
        else:
            print("  (no video stream)")

    # ── Distributions ────────────────────────────────────────────────────────
    valid = [r["video"] for r in per_file.values() if r.get("video")]
    distributions = {
        "fps":          compute_distribution([v.get("fps") for v in valid]),
        "duration_sec": compute_distribution([v.get("duration_sec") for v in valid]),
        "bitrate_kbps": compute_distribution([v.get("bitrate_kbps") for v in valid]),
        "nb_frames":    compute_distribution([v.get("nb_frames") for v in valid]),
        "file_size_mb": compute_distribution([r.get("size_mb") for r in per_file.values()]),
    }

    resolution_counts: dict[str, int] = {}
    for v in valid:
        if v.get("width") and v.get("height"):
            key = f"{v['width']}x{v['height']}"
            resolution_counts[key] = resolution_counts.get(key, 0) + 1

    codec_counts: dict[str, int] = {}
    for v in valid:
        if v.get("codec"):
            codec_counts[v["codec"]] = codec_counts.get(v["codec"], 0) + 1

    audio_clips = sum(1 for v in valid if v.get("has_audio"))
    total_dur   = round(sum(v.get("duration_sec") or 0 for v in valid), 3)
    total_frames = sum(v.get("nb_frames") or 0 for v in valid)
    total_mb    = round(sum(r.get("size_mb") or 0 for r in per_file.values()), 3)

    summary = {
        "total_files":         len(video_files),
        "files_probed":        len(per_file),
        "files_with_errors":   len(errors),
        "total_duration_sec":  total_dur,
        "total_hours":         round(total_dur / 3600, 5),
        "total_frames":        total_frames,
        "total_size_mb":       total_mb,
        "resolutions":         resolution_counts,
        "codecs":              codec_counts,
        "clips_with_audio":    audio_clips,
        "clips_without_audio": len(valid) - audio_clips,
    }

    # ── Annotation coverage ───────────────────────────────────────────────────
    clip_ids = list(per_file.keys())
    ann_coverage = check_annotation_coverage(clip_ids, dataset_dir / "annotations")

    # ── Discrepancies ─────────────────────────────────────────────────────────
    discrepancies: list[dict] = []

    if manifest:
        discrepancies += check_manifest_vs_actual(manifest, per_file)

    if clip_metadata:
        discrepancies += check_clip_metadata_vs_actual(clip_metadata, per_file)

    discrepancies += check_sensor_vs_video_resolution(
        per_file, dataset_dir / "annotations" / "sensors"
    )

    # ── Assemble report ───────────────────────────────────────────────────────
    report = {
        "eval_type":           "file",
        "dataset_path":        str(dataset_dir),
        "evaluated_at":        datetime.now(timezone.utc).isoformat(),
        "summary":             summary,
        "distributions":       distributions,
        "annotation_coverage": ann_coverage,
        "discrepancies":       discrepancies or None,
        "errors":              errors or None,
        "per_file":            per_file,
    }

    # ── Write report ──────────────────────────────────────────────────────────
    if output_path is None:
        output_path = dataset_dir / "file_eval_report.json"
    output_path = Path(output_path)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nWrote → {output_path}")

    if discrepancies:
        print(f"\n⚠  {len(discrepancies)} discrepancy(ies) found:")
        for d in discrepancies:
            prefix = f"[{d['clip_id']}] " if "clip_id" in d else ""
            src = f"({d.get('source', '?')})"
            print(f"   {prefix}{d['field']}: claimed={d.get('claimed')!r}  actual={d.get('actual')!r}  {src}")

    return report


def _compare_vs_qp(report: dict, qp: dict) -> list[dict]:
    """Compare file_eval results against QP claims; return discrepancy list."""
    profile = qp.get("qp:qualityProfile", qp)
    scores  = profile.get("scores", {})
    dist    = report.get("distributions", {})
    issues  = []

    # FPS: compare QP claimed raw_value vs measured mean fps
    qp_fps = (scores.get("fps") or {}).get("raw_value")
    actual_fps = (dist.get("fps") or {}).get("mean")
    if qp_fps is not None and actual_fps is not None:
        if abs(actual_fps - qp_fps) > 1.0:
            issues.append({
                "source":   "qp_vs_actual",
                "field":    "fps",
                "claimed":  qp_fps,
                "actual":   round(actual_fps, 4),
                "delta":    round(actual_fps - qp_fps, 4),
                "severity": "medium" if abs(actual_fps - qp_fps) < 15 else "high",
            })

    # Resolution: compare QP claimed width×height vs most common resolution in sample
    res_score = scores.get("resolution") or {}
    qp_w, qp_h = res_score.get("width"), res_score.get("height")
    resolutions = report.get("summary", {}).get("resolutions", {})
    if qp_w and qp_h and resolutions:
        qp_res_str = f"{qp_w}x{qp_h}"
        # Most common resolution in sample
        dominant_res = max(resolutions, key=resolutions.__getitem__)
        if dominant_res != qp_res_str:
            issues.append({
                "source":   "qp_vs_actual",
                "field":    "resolution",
                "claimed":  qp_res_str,
                "actual":   dominant_res,
                "severity": "medium",
            })

    return issues


def append_file_eval_to_qp(report: dict, qp_path: Path) -> None:
    """Append the file_eval summary to an existing QP JSON file."""
    qp_path = Path(qp_path)
    with open(qp_path) as f:
        qp = json.load(f)

    s = report["summary"]

    # Merge per-file discrepancies with QP-level comparison
    existing_discs = report.get("discrepancies") or []
    qp_discs = _compare_vs_qp(report, qp)
    all_discs = existing_discs + qp_discs

    fe = {
        "eval_type":       "file",
        "evaluated_at":    report["evaluated_at"],
        "dataset_path":    report["dataset_path"],
        "summary": {
            "total_files":        s["total_files"],
            "total_duration_sec": s["total_duration_sec"],
            "total_hours":        s["total_hours"],
            "total_frames":       s["total_frames"],
            "total_size_mb":      s["total_size_mb"],
            "resolutions":        s["resolutions"],
            "codecs":             s["codecs"],
            "clips_with_audio":   s["clips_with_audio"],
            "clips_without_audio": s["clips_without_audio"],
        },
        "distributions": {
            k: v for k, v in report["distributions"].items() if v is not None
        },
        "annotation_coverage": report.get("annotation_coverage"),
        "discrepancies": all_discs or None,
    }

    if qp_discs:
        print(f"\n⚠  {len(qp_discs)} QP-vs-actual discrepancy(ies):")
        for d in qp_discs:
            print(f"   {d['field']}: claimed={d.get('claimed')!r}  actual={d.get('actual')!r}")

    qp_profile = qp.get("qp:qualityProfile", qp)
    qp_profile["file_eval"] = fe
    if "qp:qualityProfile" in qp:
        qp["qp:qualityProfile"] = qp_profile

    with open(qp_path, "w") as f:
        json.dump(qp, f, indent=2)
    print(f"Appended file_eval → {qp_path.name}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="File-level evaluation pipeline for quality profiling"
    )
    parser.add_argument("dataset_dir", help="Path to dataset directory")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Report output path (default: <dataset_dir>/file_eval_report.json)"
    )
    parser.add_argument(
        "--append-qp", default=None, metavar="QP_JSON",
        help="Append file_eval section to an existing .qp.json profile"
    )
    args = parser.parse_args()

    out = Path(args.output) if args.output else None
    report = run_file_eval(args.dataset_dir, out)

    if args.append_qp:
        append_file_eval_to_qp(report, Path(args.append_qp))
