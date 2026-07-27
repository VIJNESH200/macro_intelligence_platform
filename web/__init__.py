from __future__ import annotations
"""
Web layer for the Macro Intelligence Platform.
==============================================
A FastAPI service over the existing compute layer (`api.py`, `analytics/`,
`research/`) plus a React single-page frontend.

This package is additive: the matplotlib desktop app (`main.py` -> `ui/app.py`)
is untouched and still runs independently.

    uvicorn web.server:app --reload
"""
