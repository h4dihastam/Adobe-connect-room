#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=10000}"
exec python -m gunicorn app:app --bind "0.0.0.0:${PORT}"
