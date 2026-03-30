"""
Update Jupyter notebooks for local execution:
- Replace Google Drive / Colab mount paths with ../data/
- Replace GCS bucket paths (gs://...) with ../data/
- Remove references to GCP service account key file
- Remove Colab-specific notebook links
"""
import json
import re
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"

REPLACEMENTS = [
    # Google Drive Colab mount paths
    (r"/content/drive/MyDrive/", "../data/"),
    # GCS bucket paths (both known buckets)
    (r"gs://ig-politik-posts/", "../data/"),
    (r"gs://ig-politik-stories/", "../data/"),
]

SERVICE_ACCOUNT_PATTERN = re.compile(
    r'["\']?[^\s"\']*local-grove-153811[^\s"\']*["\']?'
)

COLAB_LINK_PATTERN = re.compile(
    r'https://colab\.research\.google\.com/drive/[A-Za-z0-9_-]+'
)


def process_source(source: str) -> tuple[str, list[str]]:
    """Apply replacements to a cell source string. Returns (new_source, list_of_changes)."""
    changes = []

    for pattern, replacement in REPLACEMENTS:
        count = len(re.findall(pattern, source))
        if count:
            source = re.sub(pattern, replacement, source)
            changes.append(f"Replaced '{pattern}' → '{replacement}' ({count}x)")

    if SERVICE_ACCOUNT_PATTERN.search(source):
        source = SERVICE_ACCOUNT_PATTERN.sub(
            '"# REMOVED: GCP service account key not needed for local execution"',
            source,
        )
        changes.append("Removed GCP service account key reference")

    if COLAB_LINK_PATTERN.search(source):
        source = COLAB_LINK_PATTERN.sub(
            "# REMOVED: Colab link (run notebook locally)",
            source,
        )
        changes.append("Removed Colab notebook link")

    return source, changes


notebooks = sorted(NOTEBOOKS_DIR.glob("*.ipynb"))
print(f"Processing {len(notebooks)} notebooks in {NOTEBOOKS_DIR}\n")

total_changes = 0
for nb_path in notebooks:
    with open(nb_path) as f:
        nb = json.load(f)

    nb_changes = []
    for cell in nb.get("cells", []):
        raw = cell.get("source", "")
        # source can be a string or list of strings
        if isinstance(raw, list):
            joined = "".join(raw)
            new_source, changes = process_source(joined)
            if changes:
                # Split back into lines preserving newlines
                cell["source"] = [
                    line + ("\n" if i < len(new_source.splitlines()) - 1 else "")
                    for i, line in enumerate(new_source.splitlines())
                ]
                nb_changes.extend(changes)
        elif isinstance(raw, str):
            new_source, changes = process_source(raw)
            if changes:
                cell["source"] = new_source
                nb_changes.extend(changes)

    if nb_changes:
        with open(nb_path, "w") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print(f"  {nb_path.name}: {len(nb_changes)} change(s)")
        for c in nb_changes:
            print(f"    - {c}")
        total_changes += len(nb_changes)
    else:
        print(f"  {nb_path.name}: no changes needed")

print(f"\nDone. {total_changes} total changes across {len(notebooks)} notebooks.")
