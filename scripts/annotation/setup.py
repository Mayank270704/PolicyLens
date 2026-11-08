"""One-time setup: create the original-blank-batch backup and the protected
file-hash baseline used by the historical-immutability checks. Safe to run
multiple times -- never overwrites an existing backup or baseline entry
for a file whose hash it already recorded unchanged; any actual content
change in a protected file will show up as a hash mismatch on later runs.

Run directly:
    python scripts/annotation/setup.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema, state
else:
    from . import schema, state

PROTECTED_FILES = {
    "canonical_corpus_unique_texts": schema.CORPUS_PATH,
    "historical_training_600": schema.HISTORICAL_600_PATH,
    "historical_provisional_400": schema.HISTORICAL_400_PATH,
    "historical_targeted_134_master": schema.HISTORICAL_134_PATH,
    "historical_targeted_134_blind": schema.HISTORICAL_134_BLIND_PATH,
}


def build_protected_baseline(force: bool = False) -> dict:
    if schema.PROTECTED_BASELINE_PATH.exists() and not force:
        with open(schema.PROTECTED_BASELINE_PATH, encoding="utf-8") as f:
            return json.load(f)

    baseline = {
        "created_utc": schema.utcnow_iso(),
        "note": "SHA-256 of files that this annotation experiment must never modify. "
                "A mismatch on re-check means one of these was altered after the baseline "
                "was recorded -- investigate before proceeding.",
        "files": {
            name: schema.sha256_file(path) for name, path in PROTECTED_FILES.items() if path.exists()
        },
    }
    schema.PROTECTED_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(schema.PROTECTED_BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    return baseline


def check_protected_baseline() -> list[str]:
    """Returns a list of human-readable problems; empty list = all clean."""
    if not schema.PROTECTED_BASELINE_PATH.exists():
        return ["No protected_baseline.json found; run setup.py first."]
    with open(schema.PROTECTED_BASELINE_PATH, encoding="utf-8") as f:
        baseline = json.load(f)
    problems = []
    for name, recorded_hash in baseline.get("files", {}).items():
        path = PROTECTED_FILES.get(name)
        if path is None or not path.exists():
            problems.append(f"{name}: file missing ({path})")
            continue
        current_hash = schema.sha256_file(path)
        if current_hash != recorded_hash:
            problems.append(f"{name}: SHA-256 changed! Recorded={recorded_hash} Current={current_hash}")
    return problems


def main() -> int:
    created_backup = state.ensure_backup(schema.MAIN_BATCH_PATH, schema.MAIN_BATCH_BACKUP_PATH)
    print(f"Main batch backup {'created' if created_backup else 'already present'}: "
          f"{schema.MAIN_BATCH_BACKUP_PATH}")

    baseline = build_protected_baseline()
    print(f"Protected baseline ({len(baseline['files'])} files): {schema.PROTECTED_BASELINE_PATH}")

    if not schema.STATE_PATH.exists():
        state.save_state({"batches": {}})
        print(f"Initialized {schema.STATE_PATH}")
    else:
        print(f"State file already present: {schema.STATE_PATH}")

    problems = check_protected_baseline()
    if problems:
        print("\nWARNING -- protected file check found issues:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nAll protected historical/source files match their recorded baseline hash.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
