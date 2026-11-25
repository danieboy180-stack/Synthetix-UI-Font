"""Deterministic build environment helpers (plan items 71, 73, 74, 78).

Importing this module pins SOURCE_DATE_EPOCH (fontTools reads it for head.created/modified) so two clean builds
of the same commit produce identical bytes.  A caller may export its own SOURCE_DATE_EPOCH (e.g. the commit time)."""
import os, sys, platform, importlib, subprocess

FIXED_EPOCH = '1795392000'                   # 2026-11-23T00:00:00Z, the audit snapshot date
os.environ.setdefault('SOURCE_DATE_EPOCH', FIXED_EPOCH)
os.environ.setdefault('PYTHONHASHSEED', '0')
os.environ.setdefault('LC_ALL', 'C')

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _ver(mod):
    try:
        m = importlib.import_module(mod)
        return getattr(m, '__version__', 'present')
    except Exception:
        return None


def git_commit():
    try:
        return subprocess.check_output(['git', '-C', BASE, 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return 'unknown (not a git checkout)'


def env_info():
    mods = ['fontTools', 'numpy', 'scipy', 'PIL', 'brotli', 'uharfbuzz', 'skia', 'pathops', 'fontbakery', 'playwright']
    return {'python': sys.version.split()[0], 'platform': platform.platform(), 'machine': platform.machine(),
            'source_date_epoch': os.environ.get('SOURCE_DATE_EPOCH'),
            'packages': {m: _ver(m) for m in mods}, 'git_commit': git_commit()}
