#!/bin/sh
# The canonical budget gate, also used with the high-autonomy profile.
set -eu
HERE=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec sh "$HERE/templates/check_budget.sh" "$@"
