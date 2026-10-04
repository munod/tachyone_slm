"""Test path setup: this workspace first, then the clone via PYTHONPATH."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
