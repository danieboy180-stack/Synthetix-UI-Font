#!/usr/bin/env bash
# Double-build reproducibility proof (ledger A73/B6): build the same tree twice in two separate directories and
# compare every shipped file hash.  Exit 1 on any difference.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
A="$(mktemp -d)"; B="$(mktemp -d)"
for D in "$A" "$B"; do
  mkdir -p "$D/STACKRA-SANS"; (cd "$SRC" && tar --exclude=fonts --exclude=reports --exclude=sources/masters --exclude=build/vf_masters -cf - .) | tar -xf - -C "$D/STACKRA-SANS"
  ( cd "$D/STACKRA-SANS/build" && SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1795392000}" bash ./build_all.sh >"$D/log.txt" 2>&1 ) || { echo "build failed in $D"; tail -20 "$D/log.txt"; exit 1; }
done
python3 - "$A" "$B" <<'PY'
import json, sys
a = json.load(open(f'{sys.argv[1]}/STACKRA-SANS/reports/build_reports/checksums.json'))
b = json.load(open(f'{sys.argv[2]}/STACKRA-SANS/reports/build_reports/checksums.json'))
ma = json.load(open(f'{sys.argv[1]}/STACKRA-SANS/reports/build_reports/release_manifest.json'))['sources']
mb = json.load(open(f'{sys.argv[2]}/STACKRA-SANS/reports/build_reports/release_manifest.json'))['sources']
diff = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)] + [k for k in sorted(set(ma) | set(mb)) if ma.get(k) != mb.get(k)]
print(f'{len(a)} files and {len(ma)} UFO trees compared; differences: {diff or "none"}')
sys.exit(1 if diff else 0)
PY
