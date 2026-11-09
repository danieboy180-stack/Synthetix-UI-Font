# Cross-platform QA (Stage 11) — what ran and what did not

| Check | Status |
|---|---|
| Chromium: TTF/WOFF/WOFF2/variable advance parity; DPR 1-3; 200% zoom and text size; dark mode; forced colours; reduced motion; weight mapping (no synthetic bold) | PASS (`reports/checks_v4.json`, `reports/engine_parity_chromium.json`) |
| Firefox, WebKit | NOT RUN (not installed). `python tools/engine_parity.py chromium firefox webkit` + `.github/workflows/ci.yml` are ready. |
| iOS (UIFontMetrics / Dynamic Type), Android (sp / font scale) | NOT RUN. `tokens/dist/SynthetixTokens.swift`, `synthetix_type.xml`, `synthetix_ui_fontfamily.xml` are generated but **unverified** (never compiled). Platform font-API details must be confirmed against current Apple/Android docs. |
| Windows DirectWrite / GDI clipping | Metrics fixed (winDescent 340) but NOT RUN on Windows. |
| Hinting | Fonts ship unhinted with `gasp`; ttfautohint was not available. Decide after Windows checks. |

**iOS:** add the three static TTFs to the target, list them in `UIAppFonts`, use `SynthetixType.body.font()`.
**Android:** copy TTFs to `res/font/synthetix_ui_{regular,medium,semibold}.ttf` (lowercase names), add `synthetix_ui_fontfamily.xml` as `res/font/synthetix_ui.xml`, apply `SxText.*` styles.
**Dark mode:** light text on dark reads heavier; tokens use wght 470/570 for medium/semibold on the variable build (body stays 400, the axis minimum). Values are proposals; judge them on real screens.
