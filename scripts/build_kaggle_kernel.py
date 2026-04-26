#!/usr/bin/env python3
"""Stage a Kaggle kernel bundle that includes the current repo snapshot."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "kaggle_kernel"
DIST_DIR = REPO_ROOT / "dist" / "kaggle_kernel"
REPO_BUNDLE_DIR = DIST_DIR / "HyperAgents-Locally"
REPO_BUNDLE_ZIP = DIST_DIR / "repo_bundle.zip"

IGNORE_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "venv",
    ".venv",
    "dist",
    "outputs_local",
    ".kaggle-outputs",
}

IGNORE_SUFFIXES = {".pyc", ".pyo"}


def should_ignore(path: Path) -> bool:
    if path.name in IGNORE_NAMES:
        return True
    if path.suffix in IGNORE_SUFFIXES:
        return True
    return False


def copy_repo_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item == DIST_DIR or item == TEMPLATE_DIR:
            continue
        if should_ignore(item):
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*IGNORE_NAMES, "*.pyc", "*.pyo"))
        else:
            shutil.copy2(item, target)


def write_repo_zip(src: Path, zip_path: Path) -> None:
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for item in src.rglob("*"):
            if not item.is_file():
                continue
            if DIST_DIR in item.parents or TEMPLATE_DIR in item.parents:
                continue
            if any(part in IGNORE_NAMES for part in item.parts):
                continue
            if item.suffix in IGNORE_SUFFIXES:
                continue
            zf.write(item, item.relative_to(src))


def detect_kaggle_username() -> str:
    for candidate in (
        Path.home() / ".kaggle" / "kaggle.json",
        Path.home() / ".config" / "kaggle" / "kaggle.json",
    ):
        if candidate.exists():
            data = json.loads(candidate.read_text(encoding="utf-8"))
            username = data.get("username")
            if username:
                return username
    return "your-kaggle-username"


def write_metadata(username: str) -> None:
    metadata_path = DIST_DIR / "kernel-metadata.json"
    metadata = json.loads((TEMPLATE_DIR / "kernel-metadata.json").read_text(encoding="utf-8"))
    metadata["id"] = f"{username}/hyperagents-factory-openrouter"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE_DIR / "run_factory.py", DIST_DIR / "run_factory.py")
    shutil.copy2(TEMPLATE_DIR / "README.md", DIST_DIR / "README.md")
    copy_repo_tree(REPO_ROOT, REPO_BUNDLE_DIR)
    write_repo_zip(REPO_ROOT, REPO_BUNDLE_ZIP)
    write_metadata(detect_kaggle_username())

    print(f"Built Kaggle kernel bundle at: {DIST_DIR}")
    print("Next:")
    print(f"  cd {REPO_ROOT}")
    print("  python3 scripts/build_kaggle_kernel.py")
    print("  kaggle kernels push -p dist/kaggle_kernel --accelerator NvidiaTeslaT4")


if __name__ == "__main__":
    main()
