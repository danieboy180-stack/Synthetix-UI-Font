"""Step 8: fail if any file listed in reports/scorer.lock.json changed. Nobody edits the judge.
Also fails if tools/scorer/ contains a file that is not in the lock (a new unlocked scorer file is also a change)."""
import os, sys, json, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lock = json.load(open(os.path.join(ROOT, 'reports/scorer.lock.json')))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
bad = []
for rel, h in lock['sha256'].items():
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p): bad.append(('MISSING', rel))
    elif sha(p) != h: bad.append(('CHANGED', rel))
sd = os.path.join(ROOT, 'tools/scorer')
for fn in sorted(os.listdir(sd)):
    rel = 'tools/scorer/' + fn
    if fn.endswith('.py') and rel not in lock['sha256']: bad.append(('UNLOCKED', rel))
print('scorer.lock: %d files checked, %d problems' % (len(lock['sha256']), len(bad)))
for k, r in bad: print('  %-9s %s' % (k, r))
sys.exit(1 if bad else 0)
