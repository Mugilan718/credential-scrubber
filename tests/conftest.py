import sys
from pathlib import Path

# engine.py lives at the repo root, one level up from tests/ - not a package,
# so make it importable regardless of the directory pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
