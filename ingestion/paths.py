"""Shared path helpers for ingestion and constituent seeds."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"
CONSTITUENT_SOURCES_PATH = REPO_ROOT / "docs" / "constituent_sources.yml"
SEEDS_DIR = REPO_ROOT / "storage" / "seeds"
RAW_DIR = REPO_ROOT / "storage" / "raw"
TICKER_OVERRIDES_PATH = REPO_ROOT / "ingestion" / "constituents" / "ticker_overrides.csv"


def seed_path(market_code: str) -> Path:
    return SEEDS_DIR / market_code / "constituents.csv"


def raw_dir(market_code: str) -> Path:
    return RAW_DIR / market_code
