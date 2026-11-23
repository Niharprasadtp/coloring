import sys
from pathlib import Path

# Make `eink_planner` and `verify_and_preview` importable when pytest runs from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
