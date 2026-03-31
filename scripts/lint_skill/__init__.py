"""Lint and validate agent skill/power files.

Checks frontmatter, references, cross-references, parity, and quality.
Python 3 standard library only — no pip dependencies.

Usage:
    python3 -m scripts.lint_skill                          # all checks
    python3 -m scripts.lint_skill --check frontmatter-skill-name  # specific check
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .reporting import Finding
from .registry import _build_check_registry, resolve_checks, CHECK_GROUPS

# ---------------------------------------------------------------------------
# Repo root detection
# ---------------------------------------------------------------------------


def find_repo_root() -> Path:
    """Find repo root by looking for skills/ and powers/ directories."""
    # Prefer CWD first (allows running from any repo), then script location
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent.parent,
    ]
    for candidate in candidates:
        if (candidate / "skills").is_dir() and (candidate / "powers").is_dir():
            return candidate
    print("ERROR: Cannot find repo root (need skills/ and powers/ directories)", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_skills(root: Path) -> List[Path]:
    """Find all skill directories (contain SKILL.md)."""
    results = []
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                results.append(child)
    return results


def discover_powers(root: Path) -> List[Path]:
    """Find all power directories (contain POWER.md)."""
    results = []
    powers_dir = root / "powers"
    if powers_dir.is_dir():
        for child in sorted(powers_dir.iterdir()):
            if child.is_dir() and (child / "POWER.md").exists():
                results.append(child)
    return results

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_checks(registry: Dict[str, Tuple], selected: Optional[List[str]] = None) -> int:
    """Run selected checks (or all). Returns exit code."""
    checks_to_run = selected if selected else sorted(registry.keys())

    unknown = [c for c in checks_to_run if c not in registry]
    if unknown:
        print(f"ERROR: Unknown checks: {', '.join(unknown)}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(registry.keys()))}", file=sys.stderr)
        return 2

    total = 0
    passed = 0
    warnings = 0
    errors = 0
    all_findings: List[Finding] = []

    for check_name in checks_to_run:
        total += 1
        fn, _ = registry[check_name]
        findings = fn()
        check_errors = [f for f in findings if f.severity == "error"]
        check_warnings = [f for f in findings if f.severity == "warning"]

        if check_errors:
            errors += len(check_errors)
            for f in check_errors:
                print(f"✗ {check_name} [error] {f.message}")
            all_findings.extend(check_errors)
        elif check_warnings:
            warnings += len(check_warnings)
            for f in check_warnings:
                print(f"✗ {check_name} [warning] {f.message}")
            all_findings.extend(check_warnings)
            passed += 1  # warnings don't count as failures
        else:
            passed += 1
            print(f"✓ {check_name}")

    print()
    print(f"{total} checks, {passed} passed, {warnings} warnings, {errors} errors")

    return 1 if errors > 0 else 0

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    groups = ", ".join(CHECK_GROUPS.keys())
    parser = argparse.ArgumentParser(description="Lint agent skill/power files")
    parser.add_argument("--check", action="append", dest="checks",
                        help=f"Run specific check(s) or group(s): {groups}. Can be repeated.")
    args = parser.parse_args()

    root = find_repo_root()
    skill_dirs = discover_skills(root)
    power_dirs = discover_powers(root)

    if not skill_dirs and not power_dirs:
        print("ERROR: No skills or powers found", file=sys.stderr)
        sys.exit(2)

    registry = _build_check_registry(skill_dirs, power_dirs)

    selected = resolve_checks(args.checks)
    exit_code = run_checks(registry, selected)
    sys.exit(exit_code)
