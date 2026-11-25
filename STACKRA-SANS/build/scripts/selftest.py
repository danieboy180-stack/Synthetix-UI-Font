"""Negative tests: prove the integrity gates really FAIL when they should (98/100 plan items 28, 53, 84).
A gate that has never been seen failing is not evidence.  Exit code 1 if any gate failed to fail."""
import sys
import buildenv
import contract as K
import glyphset, fontbuild, varbuild
from geom import *

results = []


def expect(name, cond):
    results.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name)


def raises_build_error(fn):
    try:
        fn(); return False
    except fontbuild.BuildError:
        return True


orig = list(glyphset.R)
try:
    # 1. a glyph-drawing exception must be fatal in strict mode and merely logged otherwise
    def boom(c): raise ValueError('injected')
    glyphset.R[:] = [(n, u, (boom if n == 'A' else f), l, r) for (n, u, f, l, r) in orig]
    expect('strict build raises on a glyph exception', raises_build_error(lambda: fontbuild.make_master('A', 400)))
    _, _, log = fontbuild.make_master('A', 400, strict=False)
    expect('non-strict build logs the exception instead', 'A' in log and 'injected' in log['A'])
    # 2. an empty outline on an inked glyph must be fatal; 'space' may stay empty
    glyphset.R[:] = [(n, u, ((lambda c: []) if n == 'B' else f), l, r) for (n, u, f, l, r) in orig]
    expect('strict build raises on an empty outline', raises_build_error(lambda: fontbuild.make_master('A', 400)))
finally:
    glyphset.R[:] = orig
c, g, log = fontbuild.make_master('A', 400)
expect('clean build has no failures and space is the only empty glyph', not log and [n for n, d in g.items() if not d['contours']] == ['space'])

# 3. contour-level topology report must flag differing contour counts and swapped contours
def fake(cs): return (None, {'X': {'contours': cs}})
sq = lambda x0, y0, x1, y1: rect(x0, y0, x1, y1)
one = [sq(0, 0, 100, 100)]; two = [sq(0, 0, 100, 100), sq(300, 300, 400, 400)]
expect('topology report flags contour-count mismatch', varbuild.topology_report({300: fake(one), 400: fake(two)}, [300, 400]).get('X'))
far = [sq(900, 0, 1000, 100)]
expect('topology report flags contours that jump position', varbuild.topology_report({300: fake(one), 400: fake(far)}, [300, 400]).get('X'))
expect('topology report accepts compatible masters', not varbuild.topology_report({300: fake(one), 400: fake([sq(5, 5, 110, 105)])}, [300, 400]))

# 4. point-level report must flag differing segment counts
a = [[L((0, 0), (1, 0)), L((1, 0), (1, 1)), L((1, 1), (0, 0))]]; b = [[L((0, 0), (1, 0)), L((1, 0), (0, 0))]]
expect('point report flags segment-count mismatch', varbuild.point_compat_report({300: {'X': a}, 400: {'X': b}}, [300, 400], ['X']).get('X'))

bad = [n for n, ok in results if not ok]
print(f'{len(results) - len(bad)}/{len(results)} negative tests behave')
sys.exit(1 if bad else 0)
