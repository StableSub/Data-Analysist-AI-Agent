from pathlib import Path
import shutil

from config.paths import UPLOAD_DIR
from core.data_processing.ids import gen_dataset_id


def save_upload_to_disk_from_path(file_path: str, filename: str) -> tuple[str, Path, str]:
    """Persist a temporary file into permanent storage and return identifiers.

    Returns: (dataset_id, raw_path, ext)
    """
    ext = Path(filename).suffix.lower().lstrip(".")
    dsid = gen_dataset_id(filename)
    target_dir = UPLOAD_DIR / dsid
    target_dir.mkdir(parents=True, exist_ok=True)
    raw_path = target_dir / f"raw.{ext if ext else 'bin'}"
    shutil.copy2(file_path, raw_path)
    return dsid, raw_path, ext
