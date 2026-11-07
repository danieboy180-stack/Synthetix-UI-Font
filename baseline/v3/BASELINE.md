# V3 baseline (frozen 2026-11-07)

- Source: `synthetix-ui-v3.zip`, sha256 `e312c04a93ebf75cd82ebd2cf38898102e642423c74274fa7797cff2bb80efa4` (46 files, 900,590 bytes unzipped).
- `MANIFEST.sha256` holds the sha256 of every file in the zip, paths relative to the zip's `synthetix-ui-v3/` folder.
- Checked 2026-11-07: all 46 files re-hashed; the six font files match V3's own `fonts/SHA256SUMS.txt`; the `README.md` and `SHA256SUMS-1.txt` supplied beside the zip are byte-identical to the copies inside it.
- `data/v2_embedded_Regular.woff` has the same sha256 as the v2 Regular WOFF listed in this repo's `fonts/SHA256SUMS.txt` on `main`, so V3's v2 comparison input is the published v2.

## Land it (owner step)

Binaries cannot be pushed through the chat tooling, so the files go in from your machine:

```
git fetch origin && git switch v4 && git pull
unzip -q synthetix-ui-v3.zip -d /tmp/v3
mkdir -p baseline/v3 && cp -R /tmp/v3/synthetix-ui-v3/. baseline/v3/
(cd baseline/v3 && sha256sum -c MANIFEST.sha256)      # macOS: shasum -a 256 -c MANIFEST.sha256
git add baseline/v3 && git commit -m "V4.0.0: land V3 baseline (hash-verified)" && git push
git tag v3-baseline && git push origin v3-baseline
```

After that, nothing under `baseline/v3/` is edited. V4 work goes elsewhere.

## Scorer files pinned by the manifest

`tools/evalref.py`, `tools/geometry.py`, `tools/v3/eval_final.py`, `tools/v3/make_scores.py`, `tools/v3/final_checks.py`. They cannot be re-run as shipped (see `docs/V4_CONTRACT.md`, O-5), so V3's 72.1/100 is recorded, not re-verified.
