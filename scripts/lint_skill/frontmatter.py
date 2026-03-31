"""Frontmatter parsing and caching."""

from pathlib import Path
from typing import Dict, Optional, Tuple

from .reporting import Finding

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RESERVED_WORDS = {"anthropic", "claude"}
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024

# ---------------------------------------------------------------------------
# File cache — read each file at most once across all checks
# ---------------------------------------------------------------------------

_file_text_cache: Dict[Path, str] = {}
_frontmatter_cache: Dict[Path, Tuple[Optional[Dict[str, str]], str]] = {}


def read_text(path: Path) -> str:
    """Read file text, cached."""
    resolved = path.resolve()
    if resolved not in _file_text_cache:
        _file_text_cache[resolved] = path.read_text(encoding="utf-8")
    return _file_text_cache[resolved]


def read_frontmatter(path: Path) -> Tuple[Optional[Dict[str, str]], str]:
    """Parse frontmatter from file, cached."""
    resolved = path.resolve()
    if resolved not in _frontmatter_cache:
        text = read_text(path)
        _frontmatter_cache[resolved] = parse_frontmatter(text)
    return _frontmatter_cache[resolved]


def parse_frontmatter(text: str) -> Tuple[Optional[Dict[str, str]], str]:
    """Parse YAML frontmatter between --- delimiters.

    Returns (frontmatter_dict, body) or (None, full_text) if no frontmatter.
    Handles simple key: value, key: "value", and nested one-level mappings.
    Also handles YAML lists like [a, b, c] and - item syntax.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, text

    fm: Dict = {}
    current_key = None
    current_list = None

    for line in lines[1:end_idx]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check if this is a list item under a key (e.g., "  - item")
        if stripped.startswith("- ") and current_key and current_list is not None:
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue

        # Check for indented key (nested mapping)
        indent = len(line) - len(line.lstrip())
        if indent > 0 and ":" in stripped:
            # Nested key under current_key
            if current_list is not None:
                fm[current_key] = current_list
                current_list = None
            k, _, v = stripped.partition(":")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if current_key:
                if not isinstance(fm.get(current_key), dict):
                    fm[current_key] = {}
                fm[current_key][k] = v
            continue

        # Top-level key: value
        if current_list is not None:
            fm[current_key] = current_list
            current_list = None

        if ":" not in stripped:
            continue

        k, _, v = stripped.partition(":")
        k = k.strip()
        v = v.strip()

        # Handle inline list [a, b, c]
        if v.startswith("[") and v.endswith("]"):
            items = [item.strip().strip('"').strip("'") for item in v[1:-1].split(",")]
            fm[k] = items
            current_key = k
            current_list = None
            continue

        # Handle value that starts a list on next lines
        if v == "":
            current_key = k
            current_list = []
            continue

        v = v.strip('"').strip("'")
        fm[k] = v
        current_key = k
        current_list = None

    if current_list is not None and current_key:
        fm[current_key] = current_list

    body = "\n".join(lines[end_idx + 1:])
    return fm, body
