"""The deploy-time splash patch for Streamlit's index.html: inserted once, never twice, never
into a document whose shape it does not recognise."""

from __future__ import annotations

from pathlib import Path

import patch_streamlit_splash as splash

SAMPLE = '<html><head><title>Streamlit</title></head><body><div id="root"></div></body></html>'


def test_patch_inserts_the_splash_inside_root_once() -> None:
    out = splash.patch(SAMPLE)
    assert out != SAMPLE
    assert out.count(splash.MARKER) == 1
    assert 'id="root"' in out and "Stock Explorer" in out and "Loading" in out
    assert splash.ROOT_DIV not in out


def test_patch_is_idempotent() -> None:
    once = splash.patch(SAMPLE)
    assert splash.patch(once) == once


def test_patch_leaves_an_unrecognised_document_alone() -> None:
    other = "<html><body><div id='app'></div></body></html>"
    assert splash.patch(other) == other


def test_main_patches_then_reports_already_patched(tmp_path: Path, monkeypatch) -> None:
    index = tmp_path / "index.html"
    index.write_text(SAMPLE, encoding="utf-8")
    monkeypatch.setattr(splash, "index_html_path", lambda: index)
    assert splash.main(["--check"]) == 1
    assert splash.main([]) == 0
    assert splash.MARKER in index.read_text(encoding="utf-8")
    assert splash.main(["--check"]) == 0
    assert splash.main([]) == 0
    assert index.read_text(encoding="utf-8").count(splash.MARKER) == 1


def test_main_refuses_an_unrecognised_document(tmp_path: Path, monkeypatch) -> None:
    index = tmp_path / "index.html"
    index.write_text("<html><body></body></html>", encoding="utf-8")
    monkeypatch.setattr(splash, "index_html_path", lambda: index)
    assert splash.main([]) == 1
    assert index.read_text(encoding="utf-8") == "<html><body></body></html>"


def test_the_installed_streamlit_has_the_shape_the_patch_expects() -> None:
    """A Streamlit upgrade that renames the root div would make the deploy step fail loudly
    (exit 1, nothing written); this catches it in CI before Render does."""
    text = splash.index_html_path().read_text(encoding="utf-8")
    assert splash.ROOT_DIV in text or splash.MARKER in text
