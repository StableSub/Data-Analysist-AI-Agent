from pathlib import Path

# Project root (this file is at <root>/config/paths.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
META_DIR = DATA_DIR / "meta"
PLOTS_DIR = DATA_DIR / "plots"

# Ensure directories exist
for d in (DATA_DIR, UPLOAD_DIR, META_DIR, PLOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

