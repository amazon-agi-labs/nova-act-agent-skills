#!/usr/bin/env python3
"""Replicate publishable content from NovaActSkills to the GitHub repo.

Usage:
    python3 scripts/replicate_to_github.py              # clone + sync to temp dir
    python3 scripts/replicate_to_github.py --dry-run    # show what would be copied
    python3 scripts/replicate_to_github.py --target-dir /tmp/my-clone
"""

import argparse
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

GITHUB_REPO = "https://github.com/amazon-agi-labs/nova-act-agent-skills.git"

# Files and directories to copy from package root into the cloned repo.
PUBLISHABLE_ITEMS = [
    "skills",
    "powers",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "NOTICE",
    "Makefile",
    ".github",
    "scripts",
    ".gitignore",
]

IGNORE_PATTERNS = shutil.ignore_patterns("__pycache__", "*.pyc")


def find_package_root() -> Path:
    """Return the NovaActSkills package root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def clone_or_pull(target_dir: Path) -> Path:
    """Clone the GitHub repo into target_dir, or pull if already cloned.

    Returns the path to the cloned repo directory.
    """
    repo_dir = target_dir / "nova-act-agent-skills"
    if (repo_dir / ".git").is_dir():
        print(f"[pull] Updating existing clone at {repo_dir}")
        subprocess.run(["git", "pull", "--rebase"], cwd=repo_dir, check=True)
    else:
        print(f"[clone] Cloning {GITHUB_REPO} into {target_dir}")
        subprocess.run(["git", "clone", GITHUB_REPO], cwd=target_dir, check=True)
    return repo_dir


def sync_content(source: Path, dest: Path, *, dry_run: bool = False) -> None:
    """Copy publishable items from source to dest, replacing existing content."""
    for item_name in PUBLISHABLE_ITEMS:
        src = source / item_name
        dst = dest / item_name
        if not src.exists():
            print(f"  [skip] {item_name} (not found in source)")
            continue
        if dry_run:
            kind = "dir " if src.is_dir() else "file"
            print(f"  [dry-run] would copy {kind} {item_name}")
            continue
        # Remove old version first so deletions propagate
        if dst.is_dir():
            shutil.rmtree(dst)
        elif dst.exists():
            dst.unlink()
        # Copy
        if src.is_dir():
            shutil.copytree(src, dst, ignore=IGNORE_PATTERNS)
        else:
            shutil.copy2(src, dst)
        print(f"  [copied] {item_name}")


def show_status_and_instructions(repo_dir: Path) -> None:
    """Stage changes, print status, and print human instructions."""
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    result = subprocess.run(
        ["git", "status", "--short"], cwd=repo_dir, capture_output=True, text=True
    )
    status = result.stdout.strip()
    if not status:
        print("\nNo changes detected — repo is already up to date.")
        return

    branch = f"update/content-sync-{date.today().isoformat()}"
    print(f"\n--- Changes staged ({len(status.splitlines())} files) ---")
    print(status)
    print(f"\n--- Next steps (run from {repo_dir}) ---")
    print(f'  cd {repo_dir}')
    print(f'  git commit -m "Sync content from NovaActSkills ({date.today().isoformat()})"')
    print(f"  git checkout -b {branch}")
    print(f"  git push -u origin {branch}")
    print(f"  # Then open a PR against main on GitHub")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replicate NovaActSkills content to the GitHub repo."
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=None,
        help="Directory to clone the repo into (default: temp directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without cloning or copying",
    )
    args = parser.parse_args()

    source = find_package_root()
    print(f"Source: {source}")

    if args.dry_run:
        print("\nDry-run — items that would be synced:")
        sync_content(source, Path("/dev/null"), dry_run=True)
        return

    if args.target_dir:
        target_dir = args.target_dir.resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = Path(tempfile.mkdtemp(prefix="nova-act-skills-"))
        print(f"Target: {target_dir}")

    repo_dir = clone_or_pull(target_dir)
    print("\nSyncing content...")
    sync_content(source, repo_dir)
    show_status_and_instructions(repo_dir)


if __name__ == "__main__":
    main()
