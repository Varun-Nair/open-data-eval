#!/usr/bin/env python3
"""
Recompute the catalog summary statistics from data/ego-datasets/ego_dataset_catalog.csv.

Writes
  data/ego-datasets/access_summary.csv   Type,Value,Count (CRLF, like the other catalog CSVs)
  README.md  "Dataset Catalog" section   the metric table and the four bar charts

Usage
  python3 eval/catalog_stats.py            # rewrite both files
  python3 eval/catalog_stats.py --check    # print a diff and exit 1 if either file is stale

Definitions (matching the values the README carried when each row was introduced)
  Datasets audited      number of catalog rows
  Total video hours     sum of the numeric "Total Hours" values ("~N" counts as N; "<N",
                        "Unknown", "Not reported" are skipped), excluding HOURS_EXCLUDED,
                        floored to the nearest 500 and printed as "N+"
  Fully accessible      rows whose URL Status is exactly "Live"
  Broken downloads      URL Status "Live but broken"
  Dead links            URL Status "Dead"
  No license specified  License Type "Not specified"
Bar charts: the largest bar is BAR_WIDTH blocks, every other bar is max(1, round(count/max*BAR_WIDTH)).
"""
import csv
import difflib
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "ego-datasets" / "ego_dataset_catalog.csv"
SUMMARY = ROOT / "data" / "ego-datasets" / "access_summary.csv"
README = ROOT / "README.md"

# Hours that are announced estimates for data nobody can download yet; they would
# swamp the real total.  Remove an entry once the dataset actually ships.
HOURS_EXCLUDED = {
    "Egocentric-1M": "~1,000,000 h is an estimate from the series name; HF page returns 401, not released",
}

BAR_WIDTH = 44
LABEL_WIDTH = 20

URL_STATUS_LABELS = {"Live but broken": "Broken download"}
MODALITY_LABELS = {
    "RGB video": "RGB Video", "Eye gaze": "Eye Gaze", "Hand pose annotations": "Hand Pose",
    "Body pose annotations": "Body Pose", "SLAM/odometry": "SLAM/Odometry",
    "Narrations/captions": "Narrations", "3D point clouds": "3D Point Clouds",
    "3D scene reconstruction": "3D Scene Recon.", "Depth (stereo)": "Depth (Stereo)",
    "Motion capture": "Motion Capture", "Optical flow": "Optical Flow",
    "Object tracking": "Object Tracking", "Hand masks": "Hand Masks",
    "3D hand pose annotations": "3D Hand Pose", "Object bounding boxes": "Object BBoxes",
}


def parse_hours(value):
    m = re.match(r"^\s*~?\s*([\d,]+(?:\.\d+)?)\s*$", value or "")
    return float(m.group(1).replace(",", "")) if m else None


def compute(rows, n_fields):
    n = len(rows)
    by = lambda col: Counter(r[col].strip() for r in rows)
    url, access, lic = by("URL Status"), by("Access Level"), by("License Type")
    mods = Counter()
    for r in rows:
        for m in r["Modalities Present"].split(";"):
            if m.strip():
                mods[m.strip()] += 1
    hours = sum(parse_hours(r["Total Hours"]) or 0
                for r in rows if r["Dataset Name"].strip() not in HOURS_EXCLUDED)
    hours_floor = int(hours // 500 * 500)
    return {
        "n": n, "n_fields": n_fields, "hours": hours, "hours_floor": hours_floor,
        "url": url, "access": access, "license": lic, "modalities": mods,
        "live": url.get("Live", 0), "broken": url.get("Live but broken", 0),
        "dead": url.get("Dead", 0), "no_license": lic.get("Not specified", 0),
    }


def ordered(counter, alphabetical=False):
    if alphabetical:
        return OrderedDict(sorted(counter.items()))
    # count descending, ties keep first-seen (catalog) order
    return OrderedDict(sorted(counter.items(), key=lambda kv: -kv[1]))


def summary_csv(stats):
    out = ["Type,Value,Count"]
    for typ, counter, alpha in (("Access Level", stats["access"], True), ("URL Status", stats["url"], True),
                                ("License", stats["license"], False), ("Modality", stats["modalities"], False)):
        for value, count in ordered(counter, alpha).items():
            out.append(f"{typ},{value},{count}")
    return "\r\n".join(out) + "\r\n"


def bar_chart(counter, labels=None):
    items = ordered(counter)
    top = max(items.values())
    lines = []
    for value, count in items.items():
        label = (labels or {}).get(value, value)
        blocks = max(1, round(count / top * BAR_WIDTH))
        lines.append(f"{label:<{LABEL_WIDTH}}{'█' * blocks} {count}")
    return "\n".join(lines)


def pct(part, whole):
    return f"{round(part / whole * 100)}%"


def replace_once(text, pattern, repl, flags=re.M):
    new, k = re.subn(pattern, repl, text, count=1, flags=flags)
    if k != 1:
        sys.exit(f"README pattern not found: {pattern!r}")
    return new


def replace_block(text, heading_pattern, heading_repl, body):
    """Replace the fenced code block that follows a '### ...' heading."""
    pattern = r"(" + heading_pattern + r")\n```\n.*?\n```"
    new, k = re.subn(pattern, lambda m: f"{heading_repl}\n```\n{body}\n```", text, count=1, flags=re.S)
    if k != 1:
        sys.exit(f"README block not found: {heading_pattern!r}")
    return new


def readme_text(current, s):
    n = s["n"]
    t = current
    t = replace_once(t, r"^\d+ egocentric video datasets audited across \d+ fields each\.$",
                     f"{n} egocentric video datasets audited across {s['n_fields']} fields each.")
    t = replace_once(t, r"^\| Datasets audited \| .* \|$", f"| Datasets audited | {n} |")
    t = replace_once(t, r"^\| Total video hours \| .* \|$", f"| Total video hours | {s['hours_floor']:,}+ |")
    t = replace_once(t, r"^\| Fully accessible \| .* \|$", f"| Fully accessible | {s['live']} ({pct(s['live'], n)}) |")
    t = replace_once(t, r"^\| Broken downloads \| .* \|$", f"| Broken downloads | {s['broken']} ({pct(s['broken'], n)}) |")
    t = replace_once(t, r"^\| Dead links \| .* \|$", f"| Dead links | {s['dead']} ({pct(s['dead'], n)}) |")
    t = replace_once(t, r"^\| \*\*No license specified\*\* \| .* \|$",
                     f"| **No license specified** | **{s['no_license']} of {n} ({pct(s['no_license'], n)})** |")
    t = replace_block(t, r"### URL Status", "### URL Status", bar_chart(s["url"], URL_STATUS_LABELS))
    t = replace_block(t, r"### Access Level", "### Access Level", bar_chart(s["access"]))
    t = replace_block(t, r"### License", "### License", bar_chart(s["license"]))
    t = replace_block(t, r"### Modalities \(across all \d+ datasets\)",
                      f"### Modalities (across all {n} datasets)", bar_chart(s["modalities"], MODALITY_LABELS))
    return t


def main():
    check = "--check" in sys.argv
    with CATALOG.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        n_fields = len(reader.fieldnames)
    s = compute(rows, n_fields)
    print(f"{s['n']} datasets, {s['n_fields']} fields; hours {s['hours']:,.1f} -> {s['hours_floor']:,}+ "
          f"(excluded: {', '.join(HOURS_EXCLUDED) or 'none'}); Live {s['live']}, broken {s['broken']}, "
          f"dead {s['dead']}, no licence {s['no_license']}")

    outputs = {
        SUMMARY: summary_csv(s),
        README: readme_text(README.read_text(encoding="utf-8"), s),
    }
    stale = False
    for path, new in outputs.items():
        old = path.read_bytes().decode("utf-8")
        if old == new:
            print(f"up to date  {path.relative_to(ROOT)}")
            continue
        stale = True
        if check:
            print(f"STALE       {path.relative_to(ROOT)}")
            sys.stdout.writelines(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                       str(path.relative_to(ROOT)), "regenerated"))
        else:
            path.write_bytes(new.encode("utf-8"))
            print(f"rewrote     {path.relative_to(ROOT)}")
    if check and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
