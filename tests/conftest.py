import sys
from pathlib import Path

# Ensure the source package is importable without needing installation.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
