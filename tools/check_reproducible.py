"""Clean-copy rebuild: copy only the inputs (baseline/, build/*.py|json, tools/brotli_node_shim) to a fresh temp dir, build there,
and compare SHA-256 of every shipped font file with the committed ones. TTF/WOFF/variable hashes depend only on fontTools (pinned);
WOFF2 hashes additionally depend on the brotli compressor build (recorded in reports/build-environment.json)."""
import os, sys, shutil, subprocess, tempfile, hashlib, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def main():
    tmp = tempfile.mkdtemp(prefix='sx-clean-')
    shutil.copytree(os.path.join(ROOT, 'baseline'), os.path.join(tmp, 'baseline'))
    os.makedirs(os.path.join(tmp, 'build')); os.makedirs(os.path.join(tmp, 'reports')); os.makedirs(os.path.join(tmp, 'tools'))
    for fn in os.listdir(os.path.join(ROOT, 'build')):
        if fn.endswith(('.py', '.json')): shutil.copy(os.path.join(ROOT, 'build', fn), os.path.join(tmp, 'build', fn))
    shutil.copytree(os.path.join(ROOT, 'tools', 'brotli_node_shim'), os.path.join(tmp, 'tools', 'brotli_node_shim'))
    for cmd in ('build/build_static.py', 'build/build_variable_export.py'):
        r = subprocess.run([sys.executable, os.path.join(tmp, cmd)], capture_output=True, text=True, cwd=tmp)
        if r.returncode: print(r.stdout, r.stderr); return 2
    mism = []; n = 0
    for line in open(os.path.join(ROOT, 'fonts', 'SHA256SUMS.txt')):
        h, rel = line.split()
        if os.environ.get('SX_SKIP_WOFF2_HASH') and rel.endswith('.woff2'): continue   # WOFF2 bytes depend on the brotli build
        n += 1
        q = os.path.join(tmp, rel)
        if not os.path.exists(q) or sha(q) != h: mism.append(rel)
    res = dict(files_compared=n, mismatches=mism, clean_copy=tmp, identical=not mism)
    json.dump(res, open(os.path.join(ROOT, 'reports', 'reproducibility.json'), 'w'), indent=1)
    print('reproducible:', not mism, '| files', n, '| mismatches', mism[:5]); return 1 if mism else 0
if __name__ == '__main__': sys.exit(main())
