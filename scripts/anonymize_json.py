"""
Anonymize annotator PII and redact GCS image URLs in LabelStudio JSON export files.

Changes made:
- completed_by.email → annotatorN@redacted.example
- completed_by.first_name → "Annotator"
- completed_by.last_name → "N"
- data.image / data.Image GCS URLs → basename filename only
- project ID → removed
"""
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

JSON_FILES = [
    DATA_DIR / "2024-06-14-Post-Gesichter-Annotationen-w-reviews.json",
    DATA_DIR / "2024-06-14-Post-Gesichter-Annotationen-w-o-reviews.json",
    DATA_DIR / "2024-01-16-Count-People-Stories-Human-Annotations.json",
]

# Build a consistent annotator mapping by scanning all files first
def build_annotator_map(files):
    seen = {}  # id -> email
    for path in files:
        if not path.exists():
            print(f"  WARNING: {path.name} not found, skipping")
            continue
        with open(path) as f:
            data = json.load(f)
        for task in data:
            for ann in task.get("annotations", []):
                cb = ann.get("completed_by", {})
                if isinstance(cb, dict) and cb.get("id"):
                    seen[cb["id"]] = cb.get("email", "")
    # Sort by ID for stable mapping
    mapping = {}
    for i, uid in enumerate(sorted(seen.keys()), start=1):
        mapping[uid] = i
    return mapping


def strip_gcs_url(url: str) -> str:
    """Strip gs://bucket-name/ prefix, keep relative path."""
    return re.sub(r"^gs://[^/]+/", "", url)


def anonymize_file(path: Path, annotator_map: dict):
    if not path.exists():
        print(f"  SKIP: {path.name} not found")
        return

    with open(path) as f:
        data = json.load(f)

    for task in data:
        # Redact GCS image URL
        if "data" in task and isinstance(task["data"], dict):
            for key in ("image", "Image"):
                if key in task["data"] and isinstance(task["data"][key], str):
                    task["data"][key] = strip_gcs_url(task["data"][key])

        # Remove project ID
        task.pop("project", None)

        for ann in task.get("annotations", []):
            cb = ann.get("completed_by")
            if isinstance(cb, dict) and cb.get("id") in annotator_map:
                n = annotator_map[cb["id"]]
                cb["email"] = f"annotator{n}@redacted.example"
                cb["first_name"] = "Annotator"
                cb["last_name"] = str(n)

    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"  Anonymized {path.name}")


print("Building annotator map across all files...")
annotator_map = build_annotator_map(JSON_FILES)
print(f"  Found {len(annotator_map)} unique annotators:")
for uid, n in sorted(annotator_map.items()):
    print(f"    ID {uid} → annotator{n}")

print("\nAnonymizing files...")
for path in JSON_FILES:
    anonymize_file(path, annotator_map)

print("\nDone.")
