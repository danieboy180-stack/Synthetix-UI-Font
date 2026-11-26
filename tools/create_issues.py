"""Step 9: create the GitHub Issues listed in reports/issues/issues.json (24 gates + 52 glyphs).
Run in Codespaces (GITHUB_TOKEN is set there) or with GH_TOKEN exported:  python tools/create_issues.py [--dry-run]
Idempotent: skips titles that already exist (open or closed)."""
import os, sys, json, urllib.request
REPO = os.environ.get('GITHUB_REPOSITORY', 'danieboy180-stack/Synthetix-UI-Font')
TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
issues = json.load(open(os.path.join(ROOT, 'reports/issues/issues.json')))
dry = '--dry-run' in sys.argv
if not TOKEN and not dry: sys.exit('set GH_TOKEN or GITHUB_TOKEN (or use --dry-run)')
def api(method, path, data=None):
    req = urllib.request.Request('https://api.github.com/repos/%s%s' % (REPO, path), method=method,
        data=json.dumps(data).encode() if data else None,
        headers={'Authorization': 'Bearer %s' % TOKEN, 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))
existing = set()
if not dry:
    page = 1
    while True:
        batch = api('GET', '/issues?state=all&per_page=100&page=%d' % page)
        if not batch: break
        existing |= {b['title'] for b in batch if 'pull_request' not in b}; page += 1
made = skipped = 0
for it in issues:
    if it['title'] in existing: skipped += 1; continue
    if dry: print('would create:', it['title']); continue
    api('POST', '/issues', dict(title=it['title'], body=it['body'], labels=it['labels'])); made += 1
print('created', made, 'skipped', skipped, 'total', len(issues))
