"""Shared helpers: path resolution, hashing, write-once output, text normalisation."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT_ENV = "POLICYLENS_INDIAN_SOURCE_ROOT"
DEFAULT_SOURCE_ROOT = REPO_ROOT.parent / "dataset" / "indian"

DERIVED_ROOT = REPO_ROOT / "data" / "processed" / "indian"
ANNOTATION_ROOT = REPO_ROOT / "data" / "annotations" / "indian"
REPORTS_ROOT = REPO_ROOT / "reports"

# Identical to the OLD project's indian/scripts/process_indian_datasets.py so that
# flags recomputed here stay comparable with the recorded ones.
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
AADHAAR_RE = re.compile(r"(?<!\d)[2-9]\d{3}\s?\d{4}\s?\d{4}(?!\d)")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
MENTION_RE = re.compile(r"@\w+")
SIGNOFF_RE = re.compile(
    r"(?m)^\s*(?i:regards|thanks|thank you|sincerely|yours (?:truly|faithfully|sincerely)|warm regards|best regards)\b[,.!]?\s*$|"
    r"\b(?i:regards|thanks|sincerely)\s*,\s*[A-Z][a-z]+|\b(?i:on behalf of)\b")
TERMINAL_RE = re.compile(r"[.!?।)\]\"'”]\s*$")


class SourceError(RuntimeError):
    pass


def resolve_source_root(arg: str | None = None) -> Path:
    root = Path(arg or os.environ.get(SOURCE_ROOT_ENV) or DEFAULT_SOURCE_ROOT).resolve()
    if not (root / "processed").is_dir():
        raise SourceError(
            f"Indian source root {root} has no processed/ folder. Pass --source-root or set {SOURCE_ROOT_ENV}."
        )
    return root


def source_label(path: Path, source_root: Path) -> str:
    """Location label relative to the NEW repo or the OLD workspace root (parent of indian/)."""
    p = Path(path).resolve()
    old_root = Path(source_root).resolve().parent
    if p.is_relative_to(REPO_ROOT):
        return "NEW:" + p.relative_to(REPO_ROOT).as_posix()
    if p.is_relative_to(old_root):
        return "OLD:" + p.relative_to(old_root).as_posix()
    return "EXTERNAL:" + p.name  # pinned by its sha256 in the manifest


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def norm_text(text: str) -> str:
    """NFKC, whitespace collapse, lowercase: the OLD project's duplicate-group normalisation."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "")).strip().lower()


def norm_tweet(text: str) -> str:
    """norm_text after masking @mentions and URLs, so retweets/replies to different users collide."""
    t = URL_RE.sub(" [url] ", text or "")
    t = MENTION_RE.sub(" [user] ", t)
    t = re.sub(r"@\[user\]", " [user] ", t)
    return norm_text(t)


TOKEN_RE = re.compile(r"[\wऀ-ॣ०-ॿ]+")


def token_set(text: str) -> frozenset[str]:
    return frozenset(TOKEN_RE.findall(text))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def new_output_dir(path: Path) -> Path:
    """Create a fresh output directory; refuse to reuse an existing one (write-once)."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} already exists; outputs are write-once. Use a new version name.")
    path.mkdir(parents=True)
    return path


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_json(path: Path, obj) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def write_manifest(out_dir: Path, inputs: dict[str, Path], source_root: Path, extra: dict) -> dict:
    """manifest.json with input/output SHA-256 and row counts; written last."""
    out_dir = Path(out_dir)
    outputs = {}
    for p in sorted(out_dir.iterdir()):
        if p.name == "manifest.json" or not p.is_file():
            continue
        entry = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
        if p.suffix == ".csv":
            with open(p, encoding="utf-8") as f:
                entry["rows"] = sum(1 for _ in csv.reader(f)) - 1
        outputs[p.name] = entry
    man = {
        "created_utc": utc_now(),
        "code_git_commit": git_commit(),
        "inputs": {k: {"location": source_label(v, source_root), "sha256": sha256_file(v)} for k, v in inputs.items()},
        "outputs": outputs,
        **extra,
    }
    write_json(out_dir / "manifest.json", man)
    return man
