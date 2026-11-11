"""Atomically publish one verified staged export without overwriting an existing path."""
import os
from pathlib import Path
import stat


def _export_path_is_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def promote_export_artifact(staged_file, target_file):
    """Hard-link a same-directory staging file to a new target; never unlink either path.

    The caller must own/validate the stage and clean it separately after success. A file
    system that cannot create hard links fails closed; there is no copy/replace fallback.
    """
    staged = Path(staged_file)
    target = Path(target_file)
    if not staged.is_absolute() or not target.is_absolute() or staged == target:
        raise ValueError("Distinct absolute staging and target paths required")
    if staged.parent != target.parent or not staged.parent.is_dir():
        raise ValueError("Stage and target must share an existing directory")
    if any(_export_path_is_link(parent) for parent in (staged.parent, *staged.parent.parents)):
        raise ValueError("Linked/reparse parent path refused")
    if _export_path_is_link(staged) or not staged.is_file():
        raise ValueError("Stage must be a regular non-linked file")
    if target.exists() or _export_path_is_link(target):
        raise FileExistsError("Export target already exists; overwrite refused")
    before = staged.stat()
    os.link(staged, target, follow_symlinks=False)
    after = target.stat()
    if (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, after.st_size):
        raise RuntimeError("Published file identity differs; preserve both paths for inspection")
    return {"schema": "gameassetai.export-promotion.v1", "status": "published",
            "target": str(target), "bytes": after.st_size,
            "stage_retained": True, "overwrite_performed": False}
# Retained bounded Blender capability; product support remains evidence-scoped.
