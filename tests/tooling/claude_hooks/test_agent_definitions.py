"""Every reviewer in .claude/agents/ has frontmatter the harness can register: it parses as YAML
and carries name, description, tools and model. An unquoted ': ' in a description breaks the
parse and the harness has no valid reviewer definition to register."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

AGENTS = Path(__file__).resolve().parents[3] / ".claude" / "agents"
REQUIRED = ("name", "description", "tools", "model")


def _frontmatter(text: str) -> str:
    lines = text.splitlines()
    assert lines and lines[0] == "---", "file does not start with a --- frontmatter fence"
    end = lines.index("---", 1)
    return "\n".join(lines[1:end])


def test_there_are_reviewer_definitions_to_check() -> None:
    assert sorted(AGENTS.glob("*.md"))


@pytest.mark.parametrize("path", sorted(AGENTS.glob("*.md")), ids=lambda p: p.name)
def test_reviewer_frontmatter_parses_with_the_required_keys(path: Path) -> None:
    meta = yaml.safe_load(_frontmatter(path.read_text(encoding="utf-8")))
    assert isinstance(meta, dict), path.name
    for key in REQUIRED:
        assert meta.get(key), f"{path.name} frontmatter is missing {key}"
    assert meta["name"] == path.stem


def test_an_unquoted_colon_in_a_description_is_caught() -> None:
    broken = "---\nname: x\ndescription: Narrow trigger: the content\ntools: Read\nmodel: sonnet\n---\n"
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(_frontmatter(broken))
