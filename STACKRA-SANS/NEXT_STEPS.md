# Next steps (ordered)
1. Fix 6/9, s terminals, a/g shapes, straight quotes, < >; re-run `qa_font.py`, `interp_test.py`, `confusables.py`.
2. Add per-master geometry for SemiBold/Bold with validity gates (PROCEDURE_REVIEW §5); add intermediate masters if 350/450 stay > 2%.
3. Fix I/l (≤0.60): longer tail or serif alternate (ss01) for identifiers.
4. Spacing then kerning with separate training/validation pair sets; proofs in words.
5. African letters + marks (hook system first: ɓ ɗ ƙ ƴ), then GPOS anchors, then NFC/NFD/stack tests with HarfBuzz.
6. OpenType: tnum/pnum/lnum/onum/zero/frac/sups/subs/sinf/case/ss01 with behaviour tests.
7. Run Fontspector/FontBakery + native OS tests in CI; WOFF2.
8. External: name clearance, licensing, two independent reviews, owner sign-off.
