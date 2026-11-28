# Capture protocol (plan step 11), DRAFT: fields marked TBD need Daniel

Every number in this project is only as good as the captures. Rules:
1. PNG only (never JPEG, never a screenshot of a screenshot), full screen, no OS zoom or display-size change between captures of one set.
2. Same device, same app, same language (English), same theme per set (light first, dark in plan step 25). Record in the table below.
3. Use the app's own text editing view with the **pangram sheet**: `Sphinx of black quartz, judge my vow.` / `ABCDEFGHIJKLMNOPQRSTUVWXYZ` / `abcdefghijklmnopqrstuvwxyz` / `0123456789 !?%&@#$()/-:;,.'"` at three system font sizes (done for Regular, session 1: cap 44, 49, 56 px).
4. Do not crop by hand. Drop the raw file in `reference/captures_private/` (git-ignored); `tools/make_capture_crops.py` cuts the text rows and records the SHA-256.
5. Never commit raw screenshots: they carry account e-mail, phone numbers, usernames.
6. Never overwrite a capture: add a new id and a new row in reference/README.md.

| field | value |
|---|---|
| device model / Android version | TBD (status bar: Android phone, 3-button navigation, 1440 px wide screenshots) |
| app + version | Pinterest, version TBD |
| display size / font size setting | TBD (three different system font sizes were used for sheets A, B, C) |
| density (dpi) / DPR | TBD |
| theme | light (dark: not captured yet) |
| language | English |
| weights captured | Regular only. Still needed: SemiBold, Bold, heading (~70 px cap), big digits (~126 px) |
