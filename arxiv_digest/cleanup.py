from __future__ import annotations

from pathlib import Path
import time


DEFAULT_CACHE_GLOBS = (
    ".arxiv_digest_cache.sqlite3",
    ".arxiv_digest_cache.sqlite3-*",
)


def cleanup_runtime_files(
    paths: list[str] | tuple[str, ...],
    *,
    keep_days: int = 7,
    drop_cache: bool = False,
    now: float | None = None,
) -> list[Path]:
    if keep_days < 0:
        raise ValueError("keep_days must be non-negative")
    cutoff = (now if now is not None else time.time()) - keep_days * 24 * 60 * 60
    removed: list[Path] = []
    for raw_path in paths:
        root = Path(raw_path)
        if not root.exists():
            continue
        if root.is_file():
            _remove_if_old(root, cutoff, removed)
            continue
        for child in sorted(root.rglob("*"), reverse=True):
            if child.is_file():
                _remove_if_old(child, cutoff, removed)
            elif child.is_dir():
                _remove_empty_dir(child, removed)
        _remove_empty_dir(root, removed)

    if drop_cache:
        for pattern in DEFAULT_CACHE_GLOBS:
            for path in Path(".").glob(pattern):
                if path.is_file():
                    path.unlink()
                    removed.append(path)
    return removed


def _remove_if_old(path: Path, cutoff: float, removed: list[Path]) -> None:
    if path.stat().st_mtime > cutoff:
        return
    path.unlink()
    removed.append(path)


def _remove_empty_dir(path: Path, removed: list[Path]) -> None:
    try:
        path.rmdir()
    except OSError:
        return
    removed.append(path)
