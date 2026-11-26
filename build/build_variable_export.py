"""Variable font + production exports. Run after build_static.py. Deterministic (fixed timestamps, pinned fontTools)."""
import sys, os, json, shutil, hashlib, io
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
try:
    import brotli  # real wheel preferred
except ImportError:
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'brotli_node_shim'))      # fallback: Node zlib brotli (pip wheel unavailable offline)
from fontTools.ttLib import TTFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools import varLib, subset
from fontTools.otlLib.builder import buildStatTable
import calendar

CFG = json.load(open(os.path.join(ROOT, 'build', 'config.json')))
MAC = 2082844800
STAMP = int(os.environ.get('SOURCE_DATE_EPOCH', CFG['source_date_epoch'])) + MAC
M = os.path.join(ROOT, 'build', 'masters')
STYLES = [('Regular', 400), ('Medium', 500), ('SemiBold', 600)]
OUT = {k: os.path.join(ROOT, 'fonts', k) for k in ('ttf', 'woff', 'woff2', 'variable', 'subsets')}

SUBSETS = {
    'latin': "0000-00FF,0131,0152-0153,02BB-02BC,02C6,02DA,02DC,0304,0308,0329,2000-206F,2044,20A6,20AC,2122,2191,2193,2212,2215,FEFF,FFFD",
    'latin-lite': "0000-00FF,0131,0152-0153,02BB-02BC,02C6,02DA,02DC,0304,0308,0329,2000-206F,2044,20A6,20AC,2122,2191,2193,2212,2215,FEFF,FFFD",
    'latin-ext': "0100-02BA,02BD-02C5,02C7-02CC,02CE-02D7,02DD-02FF,0304,0308,0329,1D00-1DBF,1E00-1E9F,1EF2-1EFF,2020,20A0-20A5,20A7-20AB,20AD-20C0,2113,2C60-2C7F,A720-A7FF",
    'african': "0181,0186,018A,0190,0198-0199,01B3-01B4,01F8-01F9,0253-0254,0257,025B,02BC,0300-0304,0306-0308,030C,0323,1E3E-1E3F,1E44-1E45,1E62-1E63,1EB8-1EB9,1ECA-1ECD,1EE4-1EE5,014A-014B",
    'symbols': "2070-209F,2116,2153-215B,2190-2195,2248,2260,2264-2265,221E,2713,20B5,20B9,2044",
}


def parse_ranges(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-'); out.extend(range(int(a, 16), int(b, 16) + 1))
        else:
            out.append(int(part, 16))
    return out


def build_variable():
    ds = DesignSpaceDocument()
    ax = AxisDescriptor(); ax.name = 'Weight'; ax.tag = 'wght'; ax.minimum, ax.default, ax.maximum = 400, 400, 600
    ds.addAxis(ax)
    for style, w in STYLES:
        s = SourceDescriptor(); s.path = os.path.join(M, 'SynthetixUI-%s.ttf' % style); s.name = 'master_' + style; s.familyName = 'Synthetix UI'; s.styleName = style
        s.location = {'Weight': w}; ds.addSource(s)
        i = InstanceDescriptor(); i.familyName = 'Synthetix UI'; i.styleName = style; i.name = style; i.location = {'Weight': w}; ds.addInstance(i)
    vf, _, _ = varLib.build(ds)
    n = vf['name']
    for i in (1, 2, 3, 4, 6, 16, 17):
        n.removeNames(nameID=i)
    ver = CFG['font_version']
    for nid, v in {1: 'Synthetix UI', 2: 'Regular', 3: 'Synthetix UI;%s;SynthetixUIVF-Regular' % ver, 4: 'Synthetix UI Regular', 6: 'SynthetixUIVF-Regular'}.items():
        n.setName(v, nid, 3, 1, 0x409); n.setName(v, nid, 1, 0, 0)
    vf['head'].fontRevision = float(ver); vf['head'].created = STAMP; vf['head'].modified = STAMP
    vf['OS/2'].usWeightClass = 400
    if 'STAT' in vf: del vf['STAT']
    buildStatTable(vf, [dict(tag='wght', name='Weight', values=[dict(value=400, name='Regular', flags=2), dict(value=500, name='Medium'), dict(value=600, name='SemiBold')])], elidedFallbackName=2)
    vf['head'].created = STAMP; vf['head'].modified = STAMP
    vf.recalcTimestamp = False      # otherwise save() stamps wall-clock time (found by tools/check_reproducible.py)
    return vf


def save(font, path, flavor=None):
    font.flavor = flavor
    if flavor == 'woff':
        font.flavorData = None
    font.save(path)


LITE_FEATURES = ['kern', 'liga', 'ccmp', 'locl', 'mark', 'mkmk', 'tnum', 'pnum', 'case', 'zero', 'lnum', 'ss13']


def subset_font(src_path, unicodes, flavor, features=('*',)):
    f = TTFont(src_path, recalcTimestamp=False)
    o = subset.Options(); o.layout_features = list(features); o.name_IDs = ['*']; o.notdef_outline = True; o.glyph_names = False; o.hinting = False   # web subsets: glyph names are dead weight
    o.legacy_kern = False; o.drop_tables += []; o.recalc_timestamp = False; o.canonical_order = True
    s = subset.Subsetter(o); s.populate(unicodes=unicodes); s.subset(f)
    f['head'].created = STAMP; f['head'].modified = STAMP
    return f


def sha(path): return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    for d in OUT.values():
        os.makedirs(d, exist_ok=True)
    sizes = {}
    # statics
    for style, _ in STYLES:
        src = os.path.join(M, 'SynthetixUI-%s.ttf' % style); name = 'SynthetixUI-%s' % style
        shutil.copyfile(src, os.path.join(OUT['ttf'], name + '.ttf'))
        for flav, ext in (('woff', 'woff'), ('woff2', 'woff2')):
            f = TTFont(src, recalcTimestamp=False); f.flavor = flav; f.save(os.path.join(OUT[ext], name + '.' + ext))
        for sub, rng in SUBSETS.items():
            if sub == 'latin-lite': continue
            f = subset_font(src, parse_ranges(rng), 'woff2'); f.flavor = 'woff2'
            p = os.path.join(OUT['subsets'], '%s-%s.woff2' % (name, sub)); f.save(p); sizes['static/%s/%s' % (style, sub)] = os.path.getsize(p)
    # variable
    vf = build_variable(); vp = os.path.join(OUT['variable'], 'SynthetixUI[wght].ttf'); vf.save(vp)
    f = TTFont(vp, recalcTimestamp=False); f.flavor = 'woff2'; f.save(os.path.join(OUT['variable'], 'SynthetixUI[wght].woff2'))
    for sub, rng in SUBSETS.items():
        f = subset_font(vp, parse_ranges(rng), 'woff2', LITE_FEATURES if sub == 'latin-lite' else ('*',)); f.flavor = 'woff2'
        p = os.path.join(OUT['subsets'], 'SynthetixUI[wght]-%s.woff2' % sub); f.save(p); sizes['variable/%s' % sub] = os.path.getsize(p)
    json.dump(sizes, open(os.path.join(ROOT, 'reports', 'subset_sizes.json'), 'w'), indent=1)
    # checksums for every shipped font file (sorted, repo-relative)
    lines = []
    for d in ('ttf', 'woff', 'woff2', 'variable', 'subsets'):
        for fn in sorted(os.listdir(OUT[d])):
            lines.append('%s  fonts/%s/%s' % (sha(os.path.join(OUT[d], fn)), d, fn))
    open(os.path.join(ROOT, 'fonts', 'SHA256SUMS.txt'), 'w').write('\n'.join(lines) + '\n')
    print('exported', len(lines), 'files')


if __name__ == '__main__':
    main()
