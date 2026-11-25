#!/usr/bin/env bash
# Stackra Sans V6: full build and gate run.
#   ./build_all.sh            integrity gates are FATAL; registered design gates still open are reported, not fatal
#   ./build_all.sh --release  every gate and every blocker in v6_ledger.json must be closed, or this exits non-zero
set -euo pipefail
cd "$(dirname "$0")/scripts"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1795392000}" PYTHONHASHSEED=0 LC_ALL=C
MODE=dev; [ "${1:-}" = "--release" ] && MODE=release
python3 selftest.py                 # the gates must be seen failing before their passes mean anything
python3 varbuild.py                 # 5 masters -> variable font (topology reports, fatal on any mismatch)
python3 export_family.py            # computed weight validity, statics/WOFF/WOFF2, checksums, manifest
python3 qa_font.py                  # integrity gates on every shipped file
python3 interp_test.py              # dense wght sampling every 25 units
python3 fontbuild.py A 400          # proto master used by the confusables gate
DESIGN_OPEN=0
python3 confusables.py A || DESIGN_OPEN=1
python3 release_readiness.py --mode "$MODE" --design-open "$DESIGN_OPEN"
