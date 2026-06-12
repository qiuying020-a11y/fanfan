#!/usr/bin/env bash
set -e
echo "Starting backend (FastAPI + Uvicorn) on http://127.0.0.1:8000 ..."
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
