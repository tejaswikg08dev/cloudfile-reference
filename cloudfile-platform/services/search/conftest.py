"""Make `app`, `tests`, and `shared` importable when running pytest."""
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _SERVICE_ROOT.parents[1]

for path in (str(_SERVICE_ROOT), str(_REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)
