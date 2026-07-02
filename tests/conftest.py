import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Make the repo's script modules importable in tests.
for rel in ("harness/scripts", "skills/web-data-extraction/scripts"):
    p = str(REPO_ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)
