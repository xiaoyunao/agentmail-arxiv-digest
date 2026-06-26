import os
from pathlib import Path

from arxiv_digest.cleanup import cleanup_runtime_files


def test_cleanup_runtime_files_removes_old_files_and_empty_dirs(tmp_path):
    old_file = tmp_path / "out" / "old.md"
    new_file = tmp_path / "out" / "new.md"
    old_file.parent.mkdir()
    old_file.write_text("old", encoding="utf-8")
    new_file.write_text("new", encoding="utf-8")

    now = 1_000_000.0
    old_mtime = now - 8 * 24 * 60 * 60
    new_mtime = now
    old_file.touch()
    new_file.touch()
    Path(old_file).chmod(0o600)
    Path(new_file).chmod(0o600)
    os.utime(old_file, (old_mtime, old_mtime))
    os.utime(new_file, (new_mtime, new_mtime))

    removed = cleanup_runtime_files([str(tmp_path / "out")], keep_days=7, now=now)

    assert old_file in removed
    assert not old_file.exists()
    assert new_file.exists()


def test_cleanup_runtime_files_drop_cache_is_explicit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".arxiv_digest_cache.sqlite3"
    cache.write_text("cache", encoding="utf-8")

    cleanup_runtime_files([], drop_cache=False)
    assert cache.exists()

    removed = cleanup_runtime_files([], drop_cache=True)
    assert Path(".arxiv_digest_cache.sqlite3") in removed
    assert not cache.exists()
