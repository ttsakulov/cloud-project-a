#!/bin/bash

HOST="0.0.0.0"
PORT=8000

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH}:${pwd}"

export DATABASE_URL=${DATABASE_URL:-"postgresql://cloud_user:0019okey@localhost/cloud_project_a"}

export $(cat .env | xargs)

python -m uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
