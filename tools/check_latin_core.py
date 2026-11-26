"""Coverage against Google's official GF_Latin_Core *letters* (source: googlefonts/glyphsets via the glyphsets PyPI README, release 0.6.19,
'glyphsets compare GF_Latin_Kernel GF_Latin_Core': Kernel letters A-Za-z + 168 extra letters). Core has 324 glyphs in total; the other 104
(numbers, punctuation, symbols, marks) could NOT be retrieved offline, so this check is PARTIAL by construction and says so."""
import os, json, sys
from fontTools.ttLib import TTFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LETTERS = ("A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z ª º À Á Â Ã Ä Å Æ Ç È É Ê Ë Ì Í Î Ï Ð Ñ Ò Ó Ô Õ Ö Ø Ù Ú Û Ü Ý Þ ß à á â ã ä å æ ç è é ê ë ì í î ï ð ñ ò ó ô õ ö ø ù ú û ü ý þ ÿ "
           "Ā ā Ă ă Ą ą Ć ć Ċ ċ Č č Ď ď Đ đ Ē ē Ė ė Ę ę Ě ě Ğ ğ Ġ ġ Ģ ģ Ħ ħ Ī ī Į į İ ı Ķ ķ Ĺ ĺ Ļ ļ Ľ ľ Ł ł Ń ń Ņ ņ Ň ň Ő ő Œ œ Ŕ ŕ Ř ř Ś ś Ş ş Š š Ť ť Ū ū Ů ů Ű ű Ų ų Ŵ ŵ Ŷ ŷ Ÿ Ź ź Ż ż Ž ž Ș ș Ț ț ȷ Ẁ ẁ Ẃ ẃ Ẅ ẅ ẞ Ỳ ỳ").split()
def main():
    res = {}
    for style in ('Regular', 'Medium', 'SemiBold'):
        f = TTFont(os.path.join(ROOT, 'fonts/ttf/SynthetixUI-%s.ttf' % style)); cm = f.getBestCmap()
        res[style] = dict(letters_checked=len(LETTERS), missing=[c for c in LETTERS if ord(c) not in cm], unencoded_idotaccent_present=any(g.lower() == 'idotaccent' for g in f.getGlyphOrder()))
    ok = all(not v['missing'] for v in res.values())
    out = dict(source='googlefonts/glyphsets 0.6.19 README (GF_Latin_Core letters)', passed_letters=ok, per_master=res,
               not_verified='104 non-letter Core glyphs; unencoded glyph /idotaccent (Lithuanian i + accent stacking) is absent',
               scope_note='U+017F (long s) and U+0192 (florin) are NOT in the official Core letter list.')
    json.dump(out, open(os.path.join(ROOT, 'reports/latin_core_letters.json'), 'w'), indent=1)
    print('Latin Core letters (%d):' % len(LETTERS), 'PASS' if ok else 'FAIL', {k: v['missing'] for k, v in res.items()}); return 0 if ok else 1
if __name__ == '__main__': sys.exit(main())
