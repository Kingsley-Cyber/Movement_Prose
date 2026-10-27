#!/usr/bin/env bash
# Regenerate every seed file from a checkout of Kingsley-Cyber/Movement_Prose at 0d0734d.
# Provenance only: do not run against the repo after P1b (it reads the 0d0734d data).
set -euo pipefail
REPO=${1:?usage: regenerate.sh <repo checkout at 0d0734d> [work dir]}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${2:-$(mktemp -d)}
python3 -I "$HERE/build_seeds.py" "$REPO" "$WORK/seed"
python3 -I "$HERE/build_model_options_cards.py" "$REPO" "$WORK/seed"
python3 -I "$HERE/build_schemas.py" "$REPO" "$WORK/seed" "$WORK/out"
echo "seed tables/JSON: $WORK/seed   schemas, data, cards, templates, report: $WORK/out"
