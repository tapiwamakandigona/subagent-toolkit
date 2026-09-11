#!/bin/sh
# Phase 1 of the two-phase run (imported from Codex cloud environments): setup
# runs ONCE before the loop, may use the network, installs dependencies, and
# starts/health-checks anything the agent needs. Agent iterations then run in
# phase 2 (offline by default via sandbox.sh). Keep this idempotent.
set -eu
# {{install_cmd}}                      # e.g. npm ci / pip install -r requirements.txt
# {{smoke_cmd}}                        # e.g. start dev server and curl a health URL
echo "init.sh is a template; replace the placeholder commands for this project." >&2
exit 1
