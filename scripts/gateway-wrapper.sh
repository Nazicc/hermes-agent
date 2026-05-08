#!/bin/bash
set -e

HERMES_HOME="/Users/can/.hermes"
PYTHON="/Users/can/.hermes/hermes-agent/venv/bin/python"
ENV_FILE="$HERMES_HOME/.env"

# Load .env into environment
if [ -f "$ENV_FILE" ]; then
    set -a
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        # Strip surrounding quotes and 'export ' prefix
        key="${key#export }"
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        export "$key=$value"
    done < <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
    set +a
fi

export PYTHONPATH="$HERMES_HOME"
export HERMES_HOME

exec "$PYTHON" -m hermes_cli.main gateway run --replace
