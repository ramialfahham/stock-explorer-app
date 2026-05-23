"""Run ingestion when invoked as python -m ingestion."""

from ingestion.main import main

if __name__ == "__main__":
    raise SystemExit(main())
