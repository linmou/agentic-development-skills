# Tests scripts/link_skills.sh for safe, configurable, idempotent runtime symlinks.

from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LINKER = REPOSITORY_ROOT / "scripts" / "link_skills.sh"


def write_skill(source_root: Path, name: str) -> Path:
    skill_dir = source_root / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n",
        encoding="utf-8",
    )
    return skill_dir


def run_linker(destination: Path, source_root: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [str(LINKER), str(destination), str(source_root)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(
            args=[str(LINKER), str(destination), str(source_root)],
            returncode=127,
            stderr=str(error),
            stdout="",
        )


def test_links_direct_skills_and_ignores_nested_non_skills(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination = tmp_path / "runtime"
    alpha = write_skill(source_root, "alpha")
    beta = write_skill(source_root, "beta")
    nested = alpha / "references" / "nested"
    nested.mkdir(parents=True)
    (nested / "SKILL.md").write_text("nested", encoding="utf-8")
    (source_root / "skills" / "not-a-skill.txt").write_text("ignore", encoding="utf-8")

    result = run_linker(destination, source_root)

    assert result.returncode == 0, result.stderr
    assert (destination / "alpha").is_symlink()
    assert (destination / "alpha").resolve() == alpha.resolve()
    assert (destination / "beta").is_symlink()
    assert (destination / "beta").resolve() == beta.resolve()
    assert not (destination / "nested").exists()
    assert not (destination / "not-a-skill.txt").exists()


def test_linker_is_idempotent_for_existing_correct_links(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination = tmp_path / "runtime"
    skill = write_skill(source_root, "alpha")
    target_before = (skill / "SKILL.md").read_bytes()
    target_stat_before = (skill / "SKILL.md").stat()

    first = run_linker(destination, source_root)
    before = (destination / "alpha").lstat() if (destination / "alpha").is_symlink() else None
    second = run_linker(destination, source_root)
    after = (destination / "alpha").lstat() if (destination / "alpha").is_symlink() else None

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert before is not None
    assert after is not None
    assert after.st_ino == before.st_ino
    assert (destination / "alpha").resolve() == skill.resolve()
    target_after = (skill / "SKILL.md").read_bytes()
    target_stat_after = (skill / "SKILL.md").stat()
    assert target_after == target_before
    assert target_stat_after.st_mtime_ns == target_stat_before.st_mtime_ns


def test_linker_refuses_to_overwrite_real_path(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination = tmp_path / "runtime"
    write_skill(source_root, "alpha")
    existing = destination / "alpha"
    existing.mkdir(parents=True)
    marker = existing / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")

    result = run_linker(destination, source_root)

    assert result.returncode != 0
    assert "conflict" in result.stderr.lower()
    assert existing.is_dir()
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_linker_refuses_different_existing_symlink(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination = tmp_path / "runtime"
    write_skill(source_root, "alpha")
    other = tmp_path / "other"
    other.mkdir()
    existing = destination / "alpha"
    destination.mkdir()
    existing.symlink_to(other, target_is_directory=True)

    result = run_linker(destination, source_root)

    assert result.returncode != 0
    assert "conflict" in result.stderr.lower()
    assert existing.is_symlink()
    assert existing.resolve() == other.resolve()


def test_linker_rejects_source_and_destination_collision(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    skill = write_skill(source_root, "alpha")
    def snapshot(root: Path) -> dict[str, tuple[str, bytes | str]]:
        result: dict[str, tuple[str, bytes | str]] = {}
        for path in root.rglob("*"):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[relative] = ("symlink", path.readlink().as_posix())
            elif path.is_file():
                result[relative] = ("file", path.read_bytes())
            elif path.is_dir():
                result[relative] = ("dir", b"")
        return result

    before = snapshot(source_root)

    result = run_linker(source_root / "skills", source_root)
    after = snapshot(source_root)

    assert result.returncode != 0
    assert "collision" in result.stderr.lower()
    assert after == before
    assert skill.exists()
