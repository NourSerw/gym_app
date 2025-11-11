import sys
from pathlib import Path

# Make project root importable so `from db.db import database` works
# when running `python src\main.py` (common when working inside `src`).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.db import database


if __name__ == "__main__":
    db = database()