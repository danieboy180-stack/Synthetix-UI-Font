"""Generates the static preview site (preview/dist) from the freshly built fonts and the QA reports.
Honest by construction: the gate counts shown on the page are read from reports/qa/qa_gates.json of THIS build."""
import os, json, shutil, html
import buildenv
import contract as K

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIST = f'{BASE}/preview/dist'


def main():
    shutil.rmtree(DIST, ignore_errors=True); os.makedirs(f'{DIST}/fonts')
    have = {}
    for sub in ('variable', 'ttf', 'woff2', 'woff'):
        d = f'{BASE}/fonts/{sub}'
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                shutil.copy(f'{d}/{fn}', f'{DIST}/fonts/{fn}'); have[fn] = True
    def src(stem):
        parts = []
        if f'{stem}.woff2' in have: parts.append(f"url(fonts/{stem}.woff2) format('woff2')")
        if f'{stem}.woff' in have: parts.append(f"url(fonts/{stem}.woff) format('woff')")
        parts.append(f"url(fonts/{stem}.ttf) format('truetype')")
        return ', '.join(parts)
    try: qa = json.load(open(f'{BASE}/reports/qa/qa_gates.json'))
    except Exception: qa = {}
    ok = sum(1 for v in qa.values() if v['pass']); tot = len(qa)
    try: man = json.load(open(f'{BASE}/reports/build_reports/release_manifest.json')); commit = man['environment']['git_commit'][:7]
    except Exception: commit = 'unknown'
    faces = [f"@font-face{{font-family:'Stackra VF';src:{src('StackraSans-VF')};font-weight:300 500;font-display:swap}}"]
    for w in K.PUBLIC_WEIGHTS:
        nm = K.WEIGHT_NAMES[w]
        faces.append(f"@font-face{{font-family:'Stackra {nm}';src:{src('StackraSans-' + nm)};font-weight:{w};font-display:swap}}")
    links = ''.join(f'<a href="fonts/{html.escape(fn)}">{html.escape(fn)}</a>' for fn in sorted(have) if fn.startswith('StackraSans'))
    page = TEMPLATE.replace('/*FACES*/', '\n'.join(faces)).replace('%%GATES%%', f'{ok}/{tot}' if tot else 'not run') \
                   .replace('%%COMMIT%%', commit).replace('%%LINKS%%', links).replace('%%VERSION%%', K.UNIQUE_ID_SUFFIX)
    open(f'{DIST}/index.html', 'w', encoding='utf-8').write(page)
    print('preview built:', len(have), 'font files; gates', f'{ok}/{tot}')


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stackra Sans V6 preview (dev build)</title>
<style>
/*FACES*/
:root{--bg:#fff;--fg:#111;--mut:#666;--line:#e3e3e3;--card:#f6f6f6;--warn:#fff4d6;--warnfg:#5c4300}
@media (prefers-color-scheme:dark){:root{--bg:#121212;--fg:#f2f2f2;--mut:#a0a0a0;--line:#2c2c2c;--card:#1c1c1c;--warn:#3a2f10;--warnfg:#ffdf8a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 'Stackra VF',system-ui,sans-serif;font-weight:400;padding:20px max(16px,env(safe-area-inset-right)) 60px max(16px,env(safe-area-inset-left))}
main{max-width:860px;margin:0 auto}
h1{font-size:clamp(34px,8vw,64px);line-height:1.05;margin:.2em 0 .1em;font-weight:var(--w,400)}
h2{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:36px 0 10px;font-family:system-ui,sans-serif;font-weight:600}
.warn{background:var(--warn);color:var(--warnfg);padding:12px 14px;border-radius:10px;font:14px/1.45 system-ui,sans-serif}
.card{background:var(--card);border-radius:12px;padding:16px;overflow-wrap:anywhere}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
input[type=range]{width:100%}
.big{font-size:clamp(28px,7vw,56px);line-height:1.15}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.mut{color:var(--mut);font:13px/1.4 system-ui,sans-serif}
.links a{display:inline-block;margin:0 10px 8px 0;font:13px system-ui,sans-serif;color:inherit}
.fallback{font-family:system-ui,sans-serif}
code{font-family:ui-monospace,monospace}
</style></head><body><main>
<div class="warn"><b>Dev build %%VERSION%% (commit %%COMMIT%%).</b> Working name, legally uncleared; not releasable. Integrity gates for this build: <b>%%GATES%%</b> pass.
The I/l confusable design gate is currently failing; Hausa, Yoruba and Igbo letters are not drawn yet.</div>

<h1 id="hero">Sell on WhatsApp. Get paid in &#8358;.</h1>
<div class="card"><label class="mut" for="w">Weight (variable axis): <b id="wv">400</b></label>
<input id="w" type="range" min="300" max="500" step="1" value="400"></div>

<h2>Sizes</h2>
<div class="card"><div style="font-size:72px;line-height:1.1">Aa Gg 6 9</div><div style="font-size:48px">Merchant orders</div><div style="font-size:24px">Your order is ready for pickup today.</div>
<p style="font-size:16px">Order 1042: 3 items, total &#8358;45,800.00. Pay by transfer or card; we will confirm by message.</p>
<p style="font-size:14px">Delivery in Lagos takes 1-2 days. Delivery to other states takes 3-5 days.</p><p style="font-size:12px">Prices include VAT. Returns accepted within 7 days.</p></div>

<h2>Characters</h2>
<div class="card big" id="chars">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>0123456789 &#8358;12,500.00<br>! ? . , : ; - ' " ( ) + = / &lt; &gt; [ ] _ | *</div>

<h2>Look-alikes (I l 1, O 0, rn m, cl d, vv w)</h2>
<div class="card big">Il1 &nbsp;O0 &nbsp;rn m &nbsp;cl d &nbsp;vv w</div>

<h2>Static weights (separate files)</h2>
<div class="cols">
<div class="card"><div class="mut">Light 300</div><div class="big" style="font-family:'Stackra Light';font-weight:300">Handgloves 2024</div></div>
<div class="card"><div class="mut">Regular 400</div><div class="big" style="font-family:'Stackra Regular';font-weight:400">Handgloves 2024</div></div>
<div class="card"><div class="mut">Medium 500</div><div class="big" style="font-family:'Stackra Medium';font-weight:500">Handgloves 2024</div></div></div>

<h2>Not supported yet (falls back to the system font)</h2>
<div class="card fallback big">&#595; &#599; &#409; &#7865; &#7885; &#7779; &#324;</div>
<p class="mut">These Hausa, Yoruba and Igbo letters are not drawn in this build, so the browser substitutes another font.</p>

<h2>Files</h2>
<div class="links">%%LINKS%%</div>
<p class="mut">Source: github.com/danieboy180-stack/Synthetix-UI-Font, branch v6-stackra-sans. Step-by-step status: STACKRA-SANS/v6_ledger.json.</p>
</main>
<script>
var s=document.getElementById('w'),v=document.getElementById('wv');
function set(){var w=s.value;v.textContent=w;document.documentElement.style.setProperty('--w',w);
['hero','chars'].forEach(function(i){var e=document.getElementById(i);if(e){e.style.fontVariationSettings="'wght' "+w;}});}
s.addEventListener('input',set);set();
</script></body></html>
"""

if __name__ == '__main__':
    main()
