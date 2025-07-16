import pytest
from pathlib import Path

from md2gdoc.converter import build_requests_and_text


def test_build_requests_and_text_headings():
    """Test heading parsing."""
    md_content = "# Heading 1\n## Heading 2\n### Heading 3"
    
    full_text, requests = build_requests_and_text(md_content)
    
    assert "Heading 1" in full_text
    assert "Heading 2" in full_text
    assert "Heading 3" in full_text
    
    # Should have 3 heading style requests
    heading_requests = [r for r in requests if "updateParagraphStyle" in r and "namedStyleType" in r["updateParagraphStyle"]["paragraphStyle"]]
    assert len(heading_requests) == 3
    
    # Check heading types
    assert heading_requests[0]["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"] == "HEADING_1"
    assert heading_requests[1]["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"] == "HEADING_2"
    assert heading_requests[2]["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"] == "HEADING_3"


def test_build_requests_and_text_checkboxes():
    """Test checkbox parsing."""
    md_content = "- [ ] Unchecked item\n- [x] Checked item"
    
    full_text, requests = build_requests_and_text(md_content)
    
    assert "Unchecked item" in full_text
    assert "Checked item" in full_text
    
    # Should have 2 checkbox requests
    checkbox_requests = [r for r in requests if "createParagraphBullets" in r]
    assert len(checkbox_requests) == 2
    
    # Check bullet preset
    assert checkbox_requests[0]["createParagraphBullets"]["bulletPreset"] == "BULLET_CHECKBOX"


def test_build_requests_and_text_mentions():
    """Test @mention parsing."""
    md_content = "Hello @john and @jane"
    
    full_text, requests = build_requests_and_text(md_content)
    
    assert "@john" in full_text
    assert "@jane" in full_text
    
    # Should have 2 bold requests for mentions
    bold_requests = [r for r in requests if "updateTextStyle" in r and "bold" in r["updateTextStyle"]["textStyle"]]
    assert len(bold_requests) == 2


def test_build_requests_and_text_bullet_points():
    """Test bullet point parsing."""
    md_content = "- Item 1\n  - Nested item\n- Item 2"
    
    full_text, requests = build_requests_and_text(md_content)
    
    assert "• Item 1" in full_text
    assert "• Nested item" in full_text
    assert "• Item 2" in full_text
    
    # Should have indentation request for nested item
    indent_requests = [r for r in requests if "updateParagraphStyle" in r and "indentStart" in r["updateParagraphStyle"]["paragraphStyle"]]
    assert len(indent_requests) == 1  # Only the nested item should have indentation


def test_build_requests_and_text_empty_lines():
    """Test empty line handling."""
    md_content = "Line 1\n\nLine 2"
    
    full_text, requests = build_requests_and_text(md_content)
    
    assert "Line 1" in full_text
    assert "Line 2" in full_text
    assert "\n\n" in full_text  # Empty line should be preserved