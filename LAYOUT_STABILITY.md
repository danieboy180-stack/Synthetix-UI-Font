# Layout-stability promise (from V4.0.10)
Within a major version (V4.x): advance widths, sidebearings and kerning of every existing glyph do not change; glyph IDs of existing glyphs are stable (new glyphs append).
Enforced by `tools/check_regression.py`, run against the previous release's binaries (`baseline/`); any difference outside an explicitly listed change fails the build.
Exception recorded for V4.0.10 only (pre-release): the 17 `.tf` tabular glyphs were re-centred to one exact width per master (Regular 589, Medium/SemiBold 587 units); `multiply.tf` shrank 10/16/26 units.
