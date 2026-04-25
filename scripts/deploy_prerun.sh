#!/bin/bash
# Deploy cron prerun scripts to ~/.hermes/scripts/ (required for scheduler security)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_SCRIPTS="$HOME/.hermes/scripts"
mkdir -p "$HERMES_SCRIPTS"
for script in cron/rss_health_checker.py; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        cp "$SCRIPT_DIR/$script" "$HERMES_SCRIPTS/"
        chmod +x "$HERMES_SCRIPTS/${script##*/}"
        echo "✅ Deployed $script → $HERMES_SCRIPTS/"
    fi
done
