"""All lint check functions."""

import re
from pathlib import Path
from typing import List, Tuple

from .reporting import Finding
from .frontmatter import (
    RESERVED_WORDS, MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH,
    read_text, read_frontmatter,
)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
XML_TAG_PATTERN = re.compile(r"<[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>")
FIRST_SECOND_PERSON = re.compile(
    r"\b(I can|I will|I am|You can|You will|You are|I\'m|You\'re)\b", re.IGNORECASE
)
REF_PATH_PATTERN = re.compile(r"`(references/[^\s`]+\.md)`")
STEER_PATH_PATTERN = re.compile(r"`(steering/[^\s`]+\.md)`")
BACKTICK_MD_REF = re.compile(r"`([a-zA-Z0-9_.-]+\.md)`")
MD_LINK_TARGET = re.compile(r"\]\(([a-zA-Z0-9_./-]+\.md)\)")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BODY_LINE_LIMIT = 500
PARITY_DIFF_SUMMARY_LIMIT = 5

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lines_outside_code_blocks(text: str) -> List[str]:
    """Return lines that are not inside fenced code blocks."""
    result = []
    in_fence = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            result.append(line)
    return result


def _extract_section_entries(text: str, prefix: str) -> List[str]:
    """Extract filenames from the 'Steering Files' section of a SKILL.md or POWER.md."""
    pattern = re.compile(rf"`{re.escape(prefix)}/([^\s`]+\.md)`")
    in_section = False
    entries = []
    for line in text.split("\n"):
        if re.match(r"^##\s+Steering Files", line):
            in_section = True
            continue
        if in_section and re.match(r"^##\s+", line) and "Steering" not in line:
            break  # next top-level section
        if in_section:
            for m in pattern.finditer(line):
                entries.append(m.group(1))
    return entries


# ---------------------------------------------------------------------------
# Frontmatter checks
# ---------------------------------------------------------------------------


def _check_frontmatter_name(dir_path: Path, md_name: str, check: str,
                            strict: bool = False) -> List[Finding]:
    """Check frontmatter 'name' field. strict=True adds format/reserved-word checks (skills)."""
    findings = []
    md_file = dir_path / md_name
    fm, _ = read_frontmatter(md_file)

    if fm is None:
        return [Finding(check, "error", f"{md_name}: No frontmatter found")]

    name = fm.get("name")
    if name is None:
        return [Finding(check, "error", f"{md_name}: Missing required 'name' field")]

    if strict:
        if len(name) > MAX_NAME_LENGTH:
            findings.append(Finding(check, "error",
                f"{md_name}: name '{name}' exceeds {MAX_NAME_LENGTH} chars ({len(name)} chars)"))
        if not NAME_PATTERN.match(name):
            findings.append(Finding(check, "error",
                f"{md_name}: name '{name}' must be lowercase letters, numbers, and hyphens only (matching ^[a-z0-9][a-z0-9-]*$)"))
        for reserved in RESERVED_WORDS:
            if reserved in name.lower():
                findings.append(Finding(check, "error",
                    f"{md_name}: name '{name}' contains reserved word '{reserved}'"))

    if name != dir_path.name:
        findings.append(Finding(check, "error",
            f"{md_name}: name '{name}' does not match parent directory '{dir_path.name}'"))

    return findings


def _check_frontmatter_description(dir_path: Path, md_name: str, check: str,
                                    strict: bool = False) -> List[Finding]:
    """Check frontmatter 'description' field. strict=True adds length/XML/voice checks (skills)."""
    findings = []
    md_file = dir_path / md_name
    fm, _ = read_frontmatter(md_file)

    if fm is None:
        return [Finding(check, "error", f"{md_name}: No frontmatter found")]

    desc = fm.get("description")
    if desc is None:
        return [Finding(check, "error", f"{md_name}: Missing required 'description' field")]

    if not desc.strip():
        findings.append(Finding(check, "error", f"{md_name}: 'description' field is empty"))
        if not strict:
            return findings

    if strict:
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            findings.append(Finding(check, "error",
                f"{md_name}: description exceeds {MAX_DESCRIPTION_LENGTH} chars ({len(desc)} chars)"))
        if XML_TAG_PATTERN.search(desc):
            findings.append(Finding(check, "error",
                f"{md_name}: description contains XML tags"))
        match = FIRST_SECOND_PERSON.search(desc)
        if match:
            findings.append(Finding(check, "warning",
                f"{md_name}: description uses first/second person ('{match.group()}'). Prefer third-person voice."))

    return findings


def check_frontmatter_power_extras(power_dir: Path) -> List[Finding]:
    """Rule 5: frontmatter-power-extras"""
    check = "frontmatter-power-extras"
    findings = []
    power_md = power_dir / "POWER.md"
    fm, _ = read_frontmatter(power_md)

    if fm is None:
        findings.append(Finding(check, "warning", f"{power_md.name}: No frontmatter found"))
        return findings

    if "displayName" not in fm:
        findings.append(Finding(check, "warning",
            f"{power_md.name}: Missing recommended 'displayName' field"))

    if "keywords" not in fm:
        findings.append(Finding(check, "warning",
            f"{power_md.name}: Missing recommended 'keywords' field"))

    return findings


# ---------------------------------------------------------------------------
# Reference / steering file consistency checks
# ---------------------------------------------------------------------------


def _check_files_listed(main_file: Path, subdir: Path, prefix: str,
                        pattern: re.Pattern, check: str) -> List[Finding]:
    """Check every file on disk in subdir is referenced in main_file."""
    findings = []
    if not subdir.is_dir():
        return findings
    text = read_text(main_file)
    referenced = {m for m in pattern.findall(text)}  # e.g. "references/qa_tests.md"
    for f in sorted(subdir.iterdir()):
        if f.is_file() and f.suffix == ".md":
            expected_ref = f"{prefix}/{f.name}"
            if expected_ref not in referenced:
                findings.append(Finding(check, "error",
                    f"{f.name} exists on disk but is not referenced in {main_file.name}"))
    return findings


def _check_files_exist(main_file: Path, subdir: Path, pattern: re.Pattern,
                       check: str) -> List[Finding]:
    """Check every referenced path in main_file exists on disk."""
    findings = []
    text = read_text(main_file)
    referenced = sorted(set(pattern.findall(text)))
    for ref_path in referenced:
        full = main_file.parent / ref_path
        if not full.exists():
            findings.append(Finding(check, "error",
                f"{ref_path} referenced in {main_file.name} but file does not exist"))
    return findings


# ---------------------------------------------------------------------------
# Body line count checks
# ---------------------------------------------------------------------------


def _check_body_lines(md_file: Path, check: str) -> List[Finding]:
    """Check that body (after frontmatter) is under BODY_LINE_LIMIT lines."""
    findings = []
    _, body = read_frontmatter(md_file)
    line_count = len(body.strip().split("\n")) if body.strip() else 0
    if line_count >= BODY_LINE_LIMIT:
        findings.append(Finding(check, "error",
            f"{md_file.name}: body is {line_count} lines (limit {BODY_LINE_LIMIT})"))
    return findings


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Cross-reference integrity checks
# ---------------------------------------------------------------------------


def _check_crossrefs_in_dir(subdir: Path, dir_prefix: str) -> Tuple[List[Finding], List[Finding]]:
    """Check cross-references within a directory.

    Returns (sibling_path_findings, target_exist_findings).
    """
    sibling_findings = []
    target_findings = []
    if not subdir.is_dir():
        return sibling_findings, target_findings

    sibling_files = {f.name for f in subdir.iterdir() if f.is_file() and f.suffix == ".md"}

    for f in sorted(subdir.iterdir()):
        if not f.is_file() or f.suffix != ".md":
            continue
        lines = _lines_outside_code_blocks(read_text(f))
        content = "\n".join(lines)

        # Collect all .md references (backtick and link targets)
        refs = set(BACKTICK_MD_REF.findall(content) + MD_LINK_TARGET.findall(content))

        for ref in refs:
            # Check for directory-prefixed paths (e.g. references/foo.md inside references/)
            if "/" in ref:
                if ref.startswith(f"{dir_prefix}/"):
                    sibling_findings.append(Finding("crossref-sibling-paths", "warning",
                        f"{dir_prefix}/{f.name}: use '{ref.split('/')[-1]}' instead of '{ref}' (sibling-relative)"))
                # Skip other directory-prefixed refs (external links)
                continue

            # Check target exists as sibling
            if ref != f.name and ref not in sibling_files:
                target_findings.append(Finding("crossref-targets-exist", "warning",
                    f"{dir_prefix}/{f.name}: references '{ref}' which does not exist in {dir_prefix}/"))

    return sibling_findings, target_findings


# ---------------------------------------------------------------------------
# Skill / Power parity checks
# ---------------------------------------------------------------------------


def check_parity_file_sets(skill_dir: Path, power_dir: Path) -> List[Finding]:
    """Rule 14: parity-file-sets — references/ and steering/ must have identical filenames."""
    check = "parity-file-sets"
    findings = []
    ref_dir = skill_dir / "references"
    steer_dir = power_dir / "steering"

    ref_files = {f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix == ".md"} if ref_dir.is_dir() else set()
    steer_files = {f.name for f in steer_dir.iterdir() if f.is_file() and f.suffix == ".md"} if steer_dir.is_dir() else set()

    for f in sorted(ref_files - steer_files):
        findings.append(Finding(check, "error", f"references/{f} exists but steering/{f} does not"))
    for f in sorted(steer_files - ref_files):
        findings.append(Finding(check, "error", f"steering/{f} exists but references/{f} does not"))

    return findings


def check_parity_content(skill_dir: Path, power_dir: Path) -> List[Finding]:
    """Content parity — paired files should differ only in path prefix substitution."""
    check = "parity-content"
    findings = []
    ref_dir = skill_dir / "references"
    steer_dir = power_dir / "steering"
    if not ref_dir.is_dir() or not steer_dir.is_dir():
        return findings

    ref_files = {f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix == ".md"}
    steer_files = {f.name for f in steer_dir.iterdir() if f.is_file() and f.suffix == ".md"}
    paired = sorted(ref_files & steer_files)
    mismatched = 0

    for fname in paired:
        ref_text = read_text(ref_dir / fname)
        steer_text = read_text(steer_dir / fname)

        # Normalize: substitute path prefixes so expected differences cancel out
        normalized_ref = ref_text.replace("references/", "PARITY_PREFIX/")
        normalized_steer = steer_text.replace("steering/", "PARITY_PREFIX/")

        if normalized_ref != normalized_steer:
            mismatched += 1
            # Summarize what differs
            ref_lines = normalized_ref.split("\n")
            steer_lines = normalized_steer.split("\n")
            diff_lines = []
            max_lines = max(len(ref_lines), len(steer_lines))
            for i in range(max_lines):
                rl = ref_lines[i] if i < len(ref_lines) else "<missing>"
                sl = steer_lines[i] if i < len(steer_lines) else "<missing>"
                if rl != sl:
                    diff_lines.append(i + 1)
            summary = f"lines {diff_lines[:PARITY_DIFF_SUMMARY_LIMIT]}" + (f" (+{len(diff_lines)-PARITY_DIFF_SUMMARY_LIMIT} more)" if len(diff_lines) > PARITY_DIFF_SUMMARY_LIMIT else "")
            findings.append(Finding(check, "warning",
                f"{fname}: unexpected content differences at {summary}"))

    return findings


def check_parity_steering_sections(skill_dir: Path, power_dir: Path) -> List[Finding]:
    """Rule 15: parity-steering-sections — SKILL.md and POWER.md steering sections must list same entries."""
    check = "parity-steering-sections"
    findings = []

    skill_text = read_text(skill_dir / "SKILL.md")
    power_text = read_text(power_dir / "POWER.md")

    skill_entries = _extract_section_entries(skill_text, "references")
    power_entries = _extract_section_entries(power_text, "steering")

    skill_set = set(skill_entries)
    power_set = set(power_entries)

    if len(skill_entries) != len(power_entries):
        findings.append(Finding(check, "error",
            f"SKILL.md lists {len(skill_entries)} entries, POWER.md lists {len(power_entries)} entries"))

    for f in sorted(skill_set - power_set):
        findings.append(Finding(check, "error",
            f"references/{f} in SKILL.md but steering/{f} missing from POWER.md"))
    for f in sorted(power_set - skill_set):
        findings.append(Finding(check, "error",
            f"steering/{f} in POWER.md but references/{f} missing from SKILL.md"))

    return findings
