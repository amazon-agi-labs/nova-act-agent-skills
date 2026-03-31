"""Check registry and group resolution."""

from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .reporting import Finding
from .frontmatter import read_text
from .checks import (
    _check_frontmatter_name, _check_frontmatter_description,
    check_frontmatter_power_extras,
    _check_files_listed, _check_files_exist,
    _check_body_lines,
    _check_crossrefs_in_dir,
    check_parity_file_sets, check_parity_content, check_parity_steering_sections,
    REF_PATH_PATTERN, STEER_PATH_PATTERN,
)

# ---------------------------------------------------------------------------
# Combined adapter helpers
# ---------------------------------------------------------------------------


def _combined_crossref_sibling(sd: Path, pd: Path) -> List[Finding]:
    return _check_crossrefs_in_dir(sd / "references", "references")[0] + _check_crossrefs_in_dir(pd / "steering", "steering")[0]


def _combined_crossref_targets(sd: Path, pd: Path) -> List[Finding]:
    return _check_crossrefs_in_dir(sd / "references", "references")[1] + _check_crossrefs_in_dir(pd / "steering", "steering")[1]


def _check_crossrefs_in_dir_sibling(subdir: Path, dir_prefix: str) -> List[Finding]:
    return _check_crossrefs_in_dir(subdir, dir_prefix)[0]


def _check_crossrefs_in_dir_targets(subdir: Path, dir_prefix: str) -> List[Finding]:
    return _check_crossrefs_in_dir(subdir, dir_prefix)[1]


def _combined_body_lines(sd: Path, pd: Path) -> List[Finding]:
    return _check_body_lines(sd / "SKILL.md", "body-line-count") + _check_body_lines(pd / "POWER.md", "body-line-count")


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------


def _build_check_registry(skill_dirs: List[Path], power_dirs: List[Path]) -> Dict[str, Tuple]:
    """Build check registry from discovered directories. Returns {name: (callable, scope)}."""
    registry: Dict[str, Tuple] = {}

    for sd in skill_dirs:
        registry["frontmatter-skill-name"] = (
            partial(_check_frontmatter_name, sd, "SKILL.md", "frontmatter-skill-name", strict=True), "skill")
        registry["frontmatter-skill-description"] = (
            partial(_check_frontmatter_description, sd, "SKILL.md", "frontmatter-skill-description", strict=True), "skill")
        registry["references-listed"] = (
            partial(_check_files_listed, sd / "SKILL.md", sd / "references", "references", REF_PATH_PATTERN, "references-listed"), "skill")
        registry["references-exist"] = (
            partial(_check_files_exist, sd / "SKILL.md", sd / "references", REF_PATH_PATTERN, "references-exist"), "skill")
        registry["crossref-sibling-paths"] = (
            partial(_check_crossrefs_in_dir_sibling, sd / "references", "references"), "skill")
        registry["crossref-targets-exist"] = (
            partial(_check_crossrefs_in_dir_targets, sd / "references", "references"), "skill")

    for pd in power_dirs:
        registry["frontmatter-power-name"] = (
            partial(_check_frontmatter_name, pd, "POWER.md", "frontmatter-power-name"), "power")
        registry["frontmatter-power-description"] = (
            partial(_check_frontmatter_description, pd, "POWER.md", "frontmatter-power-description"), "power")
        registry["frontmatter-power-extras"] = (
            partial(check_frontmatter_power_extras, pd), "power")
        registry["steering-listed"] = (
            partial(_check_files_listed, pd / "POWER.md", pd / "steering", "steering", STEER_PATH_PATTERN, "steering-listed"), "power")
        registry["steering-exist"] = (
            partial(_check_files_exist, pd / "POWER.md", pd / "steering", STEER_PATH_PATTERN, "steering-exist"), "power")

    if skill_dirs and power_dirs:
        sd, pd = skill_dirs[0], power_dirs[0]
        registry["body-line-count"] = (partial(_combined_body_lines, sd, pd), "both")
        registry["crossref-sibling-paths"] = (partial(_combined_crossref_sibling, sd, pd), "both")
        registry["crossref-targets-exist"] = (partial(_combined_crossref_targets, sd, pd), "both")
        registry["parity-file-sets"] = (partial(check_parity_file_sets, sd, pd), "both")
        registry["parity-content"] = (partial(check_parity_content, sd, pd), "both")
        registry["parity-steering-sections"] = (partial(check_parity_steering_sections, sd, pd), "both")

    return registry


# ---------------------------------------------------------------------------
# Check groups and resolution
# ---------------------------------------------------------------------------

CHECK_GROUPS = {
    "frontmatter": [
        "frontmatter-skill-name", "frontmatter-skill-description",
        "frontmatter-power-name", "frontmatter-power-description",
        "frontmatter-power-extras",
    ],
    "references": [
        "references-listed", "references-exist",
        "steering-listed", "steering-exist",
    ],
    "tokens": [
        "body-line-count",
    ],
    "crossrefs": [
        "crossref-sibling-paths", "crossref-targets-exist",
    ],
    "parity": [
        "parity-file-sets", "parity-content", "parity-steering-sections",
    ],
}


def resolve_checks(raw: Optional[List[str]]) -> Optional[List[str]]:
    """Expand group names to individual check names. None means all."""
    if not raw:
        return None
    result = []
    for item in raw:
        if item in CHECK_GROUPS:
            result.extend(CHECK_GROUPS[item])
        else:
            result.append(item)
    return result
