#!/usr/bin/env bash
# Launch an interactive MJCF viewer in YOUR terminal (stays up until Ctrl-C).
# Run this in your own Antigravity terminal so it isn't reaped as a background task.
#
#   bash scripts/serve_viewer.sh                 # toddlerbot_2xc on port 8091
#   bash scripts/serve_viewer.sh toddlerbot_3_0_2xc 8092
#
set -euo pipefail
ROBOT="${1:-toddlerbot_2xc}"
PORT="${2:-8091}"
REPO="/ws/user/yzdong/src/github/toddlerbot"
cd "$REPO"
source .venv/bin/activate
SCENE="toddlerbot/descriptions/${ROBOT}/scene.xml"
echo "Serving $SCENE on 0.0.0.0:$PORT"
echo "Open:  forward port $PORT in Antigravity, or http://192.168.1.118:$PORT"
echo "Stop:  Ctrl-C"
exec python scripts/view_mjcf.py --mjcf "$SCENE" --host 0.0.0.0 --port "$PORT"
