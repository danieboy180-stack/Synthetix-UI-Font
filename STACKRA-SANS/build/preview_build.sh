#!/usr/bin/env bash
# Vercel preview build: rebuild the fonts from source, run the integrity gates, then generate the static preview site.
# Output directory: preview/dist  (the deployed site).  Heavier gates (dense interpolation, confusables) run in build_all.sh, not here.
set -euo pipefail
cd "$(dirname "$0")/scripts"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1795392000}" PYTHONHASHSEED=0 LC_ALL=C
python3 varbuild.py > /dev/null
python3 export_family.py
python3 qa_font.py
python3 make_preview.py
