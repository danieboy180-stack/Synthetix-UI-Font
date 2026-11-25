"""Export the family.  Run after varbuild.py.

V6 hardening (98/100 plan items 53, 60, 62, 76, 78):
  * validity is COMPUTED per weight (strict build, contour topology vs Regular, fit error vs contract), not declared
  * only weights that are public AND pass every computed gate are shipped (fonts/ttf, fonts/woff, fonts/woff2);
    experimental weights go to fonts/experimental/ as TTF only, are never hashed into the release checksums and never
    get web formats
  * a PUBLIC weight failing a gate is a hard error (non-zero exit); stale outputs are removed first
  * WOFF2 needs brotli: when it is missing the report says NOT RUN (STACKRA_REQUIRE_WOFF2=1 turns that into a failure)
  * release manifest records environment, git commit, per-file SHA-256 and size budgets
"""
import os, sys, json, hashlib, shutil
import buildenv
import contract as K
import fontbuild, varbuild
from fontTools.ttLib import TTFont

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def sha_file(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def sha_tree(d):
    h = hashlib.sha256()
    for root, _, fs in sorted(os.walk(d)):
        for fn in sorted(fs):
            p = os.path.join(root, fn)
            h.update(os.path.relpath(p, d).encode()); h.update(open(p, 'rb').read())
    return h.hexdigest()


def main():
    for d in ('fonts/ttf', 'fonts/woff', 'fonts/woff2', 'fonts/experimental', 'sources/masters'):
        shutil.rmtree(f'{BASE}/{d}', ignore_errors=True)
    for d in ('fonts/ttf', 'fonts/woff', 'fonts/experimental', 'sources/masters', 'reports/qa', 'reports/build_reports'):
        os.makedirs(f'{BASE}/{d}', exist_ok=True)
    try:
        import brotli; has_brotli = True
    except Exception:
        has_brotli = False
    require_woff2 = os.environ.get('STACKRA_REQUIRE_WOFF2') == '1'
    allw = list(K.PUBLIC_WEIGHTS) + list(K.EXPERIMENTAL_WEIGHTS)
    errors = []
    try:
        Mp, fitp = varbuild.build_masters(list(K.PUBLIC_WEIGHTS), strict=True)
    except fontbuild.BuildError as e:
        print('BUILD FAILED:', e, file=sys.stderr); return 2
    Mx, fitx = varbuild.build_masters(list(K.EXPERIMENTAL_WEIGHTS), strict=False)
    M = dict(Mp); M.update(Mx); fit = dict(fitp); fit.update(fitx)
    validity = {}; shipped = []
    for w in allw:
        nm = K.WEIGHT_NAMES[w]; public = w in K.PUBLIC_WEIGHTS
        c, g, log = fontbuild.make_master('A', w, strict=public)
        topo = {} if w == K.AXIS_DEFAULT else varbuild.topology_report({K.AXIS_DEFAULT: M[K.AXIS_DEFAULT], w: M[w]}, [K.AXIS_DEFAULT, w])
        gates = {'strict_build': not log, 'topology_vs_regular': not topo, 'fit_err': fit[w] <= K.FIT_ERR_MAX_UNITS}
        passes = all(gates.values())
        validity[w] = {'style': nm, 'stem': round(c.v, 1), 'fit_err_max_units': fit[w], 'gates': gates,
                       'build_failures': log, 'topology_issues': topo, 'public': public,
                       'valid_for_release': bool(public and passes)}
        if public and not passes:
            errors.append(f'public weight {w} ({nm}) failed gates: ' + ', '.join(k for k, v in gates.items() if not v))
        if not public and passes:
            validity[w]['note'] = 'passes all gates now: promotion needs a dated DECISIONS.md entry, not an automatic switch'
        if public and passes:
            p = f'{BASE}/fonts/ttf/StackraSans-{nm}.ttf'
            fontbuild.build_ttf(p, g, c, family=K.FAMILY, style=nm, weight=w)
            fontbuild.write_ufo(f'{BASE}/sources/masters/StackraSans-{nm}.ufo', 'A', w, g, c, style=nm)
            f = TTFont(p); f.flavor = 'woff'; f.save(f'{BASE}/fonts/woff/StackraSans-{nm}.woff')
            if has_brotli:
                os.makedirs(f'{BASE}/fonts/woff2', exist_ok=True)
                f = TTFont(p); f.flavor = 'woff2'; f.save(f'{BASE}/fonts/woff2/StackraSans-{nm}.woff2')
            shipped.append(w)
        elif not public:
            fontbuild.build_ttf(f'{BASE}/fonts/experimental/StackraSans-{nm}-EXPERIMENTAL-NOT-VALIDATED.ttf', g, c,
                                family=K.FAMILY + ' Experimental', style=nm, weight=w)
    vfp = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
    if os.path.exists(vfp):
        vf = TTFont(vfp); vf.flavor = 'woff'; vf.save(f'{BASE}/fonts/woff/StackraSans-VF.woff')
        if has_brotli:
            vf = TTFont(vfp); vf.flavor = 'woff2'; os.makedirs(f'{BASE}/fonts/woff2', exist_ok=True)
            vf.save(f'{BASE}/fonts/woff2/StackraSans-VF.woff2')
    else:
        errors.append('variable font missing: run varbuild.py first')
    if not has_brotli and require_woff2:
        errors.append('WOFF2 required (STACKRA_REQUIRE_WOFF2=1) but the brotli module is unavailable')
    json.dump({'weights': validity, 'woff2': 'built' if has_brotli else 'NOT RUN: brotli module unavailable'},
              open(f'{BASE}/reports/qa/weights_validity.json', 'w'), indent=1)
    # checksums + manifest: shipped artefacts only (experimental and proto files are excluded on purpose)
    sums = {}; sizes = {}
    for root, _, fs in os.walk(f'{BASE}/fonts'):
        if any(x in root for x in ('proto', 'experimental')): continue
        for fn in sorted(fs):
            if fn.endswith(('.ttf', '.woff', '.woff2')):
                pth = os.path.join(root, fn); rel = os.path.relpath(pth, BASE)
                sums[rel] = sha_file(pth); sizes[rel] = os.path.getsize(pth)
    sums = dict(sorted(sums.items()))
    json.dump(sums, open(f'{BASE}/reports/build_reports/checksums.json', 'w'), indent=1)
    budgets = {}
    def budget(rel, limit):
        if rel in sizes: budgets[rel] = {'bytes': sizes[rel], 'limit': limit, 'pass': sizes[rel] <= limit}
        else: budgets[rel] = {'bytes': None, 'limit': limit, 'pass': None, 'status': 'NOT MEASURED (file not built)'}
    budget('fonts/variable/StackraSans-VF.ttf', K.BUDGET_VF_TTF_BYTES)
    budget('fonts/woff2/StackraSans-VF.woff2', K.BUDGET_VF_WOFF2_BYTES)
    for w in shipped: budget(f'fonts/woff2/StackraSans-{K.WEIGHT_NAMES[w]}.woff2', K.BUDGET_STATIC_WOFF2_BYTES)
    manifest = {'environment': buildenv.env_info(), 'family': K.FAMILY, 'name_status': 'WORKING NAME - legally uncleared',
                'version': K.UNIQUE_ID_SUFFIX, 'shipped_weights': shipped, 'files': sums, 'sizes': sizes,
                'sources': {os.path.relpath(os.path.join(BASE, 'sources/masters', d), BASE): sha_tree(os.path.join(BASE, 'sources/masters', d))
                            for d in sorted(os.listdir(f'{BASE}/sources/masters')) if d.endswith('.ufo')},
                'size_budgets': budgets}
    json.dump(manifest, open(f'{BASE}/reports/build_reports/release_manifest.json', 'w'), indent=1)
    print('exported', len(sums), 'files; shipped weights:', shipped,
          '| experimental (not shipped):', [w for w in K.EXPERIMENTAL_WEIGHTS])
    for k, v in budgets.items(): print('  budget', k, v)
    if errors:
        for e in errors: print('EXPORT FAILED:', e, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
