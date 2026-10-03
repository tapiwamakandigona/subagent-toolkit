#!/bin/sh
# Optional runner; legacy loop.sh remains available and unchanged.
set -eu
HERE=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HERE/autonomous_loop.py" "$@"
