"""Fixtures for manifest.py's frontmatter parser (CRLF, no-EOL, folded
scalars, colons in values, nested one-level maps)."""

import manifest


def test_basic_frontmatter():
    text = "---\nname: my-skill\ndescription: Does things.\n---\n\nBody.\n"
    fm = manifest.parse_frontmatter(text)
    assert fm == {"name": "my-skill", "description": "Does things."}


def test_crlf_line_endings():
    text = "---\r\nname: my-skill\r\ndescription: Does things.\r\n---\r\nBody.\r\n"
    fm = manifest.parse_frontmatter(text)
    assert fm["name"] == "my-skill"
    assert fm["description"] == "Does things."


def test_closing_delimiter_at_eof_without_newline():
    text = "---\nname: my-skill\ndescription: Does things.\n---"
    fm = manifest.parse_frontmatter(text)
    assert fm["name"] == "my-skill"


def test_colons_in_values():
    text = "---\ndescription: Use when: always. See https://example.com/x\n---\n"
    fm = manifest.parse_frontmatter(text)
    assert fm["description"] == "Use when: always. See https://example.com/x"


def test_folded_scalar_detected():
    text = "---\nname: s\ndescription: >\n  folded line one\n  folded line two\n---\n"
    problems = []
    fm = manifest.parse_frontmatter(text, problems)
    assert any("folded/literal scalar" in p for p in problems)
    assert fm["description"] == ">"


def test_literal_scalar_detected():
    text = "---\ndescription: |\n  literal\n---\n"
    problems = []
    manifest.parse_frontmatter(text, problems)
    assert any("folded/literal scalar" in p for p in problems)


def test_nested_metadata_map():
    text = (
        "---\n"
        "name: my-skill\n"
        "description: Does things.\n"
        "license: MIT\n"
        "metadata:\n"
        '  version: "1.1.0"\n'
        "---\n"
    )
    fm = manifest.parse_frontmatter(text)
    assert fm["license"] == "MIT"
    assert fm["metadata"] == {"version": "1.1.0"}


def test_empty_scalar_value_is_empty_string():
    text = "---\nname: my-skill\ndescription:\n---\n"
    fm = manifest.parse_frontmatter(text)
    assert fm["description"] == ""


def test_symmetric_quote_stripping_only():
    text = "---\na: \"quoted\"\nb: 'don't stop'\nc: 'lone\n---\n"
    fm = manifest.parse_frontmatter(text)
    assert fm["a"] == "quoted"
    assert fm["b"] == "don't stop"  # symmetric quotes stripped
    assert fm["c"] == "'lone"  # unmatched quote preserved


def test_no_frontmatter_returns_empty():
    assert manifest.parse_frontmatter("# Just a heading\n") == {}
