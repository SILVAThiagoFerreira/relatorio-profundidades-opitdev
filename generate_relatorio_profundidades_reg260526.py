"""Legacy compatibility wrapper for the new modular entry point."""

from __future__ import annotations

from main import main


if __name__ == "__main__":
    raise SystemExit(main())
