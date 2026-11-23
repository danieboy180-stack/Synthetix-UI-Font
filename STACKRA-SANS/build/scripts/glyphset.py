"""Glyph registry: name, codepoint, drawing function, sidebearing classes."""
from glyphs_lc import *
from glyphs_uc import *
import glyphs_uc as U

R = []   # (name, unicode, func, lclass, rclass)
def add(name, uni, fn, l, r): R.append((name, uni, fn, l, r))

lc = {'a':'rs','b':'sr','c':'ro','d':'rs','e':'rr','f':'ff','g':'rs','h':'ss','i':'ss','j':'os','k':'sd','l':'ss','m':'ss',
      'n':'ss','o':'rr','p':'sr','q':'rs','r':'sf','s':'rr','t':'fo','u':'ss','v':'dd','w':'dd','x':'dd','y':'dd','z':'ff'}
uc = {'A':'dd','B':'sr','C':'ro','D':'sr','E':'sf','F':'sf','G':'rs','H':'ss','I':'ss','J':'os','K':'sd','L':'sf','M':'ss',
      'N':'ss','O':'rr','P':'sr','Q':'rr','R':'sd','S':'rr','T':'ff','U':'ss','V':'dd','W':'dd','X':'dd','Y':'dd','Z':'ff'}
add('space', 32, U.g_space, 'p', 'p')
for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ': add(ch, ord(ch), getattr(U, 'g_'+ch), uc[ch][0], uc[ch][1])
for ch in 'abcdefghijklmnopqrstuvwxyz': add(ch, ord(ch), getattr(U, 'g_'+ch), lc[ch][0], lc[ch][1])
figs = [('zero','0','rr'),('one','1','fs'),('two','2','of'),('three','3','or'),('four','4','fs'),('five','5','sr'),
        ('six','6','rr'),('seven','7','fd'),('eight','8','rr'),('nine','9','rr')]
for n,ch,cl in figs: add(n, ord(ch), U.GLYPH_FIGS[n], cl[0], cl[1])
punct = [('period','.', 'g_period'),('comma',',','g_comma'),('colon',':','g_colon'),('semicolon',';','g_semicolon'),
         ('exclam','!','g_exclam'),('question','?','g_question'),('hyphen','-','g_hyphen'),('quotesingle',"'",'g_quotesingle'),
         ('quotedbl','"','g_quotedbl'),('plus','+','g_plus'),('equal','=','g_equal'),('slash','/','g_slash'),
         ('parenleft','(','g_parenleft'),('parenright',')','g_parenright')]
for n,ch,f in punct:
    cl = {'g_slash':'dd','g_hyphen':'ff','g_plus':'ff','g_equal':'ff','g_question':'or','g_parenleft':'dd','g_parenright':'dd'}.get(f,'pp')
    add(n, ord(ch), getattr(U,f), cl[0], cl[1])
add('uni20A6', 0x20A6, U.g_naira, 's', 's')
for n,u,f,cl in [('endash',0x2013,'g_endash','ff'),('emdash',0x2014,'g_emdash','ff'),('underscore',0x5F,'g_underscore','ff'),
                 ('bar',0x7C,'g_bar','ss'),('bracketleft',0x5B,'g_bracketleft','ss'),('bracketright',0x5D,'g_bracketright','ss'),
                 ('less',0x3C,'g_less','dd'),('greater',0x3E,'g_greater','dd'),('asterisk',0x2A,'g_asterisk','pp'),
                 ('quoteleft',0x2018,'g_quoteleft','pp'),('quoteright',0x2019,'g_quoteright','pp'),
                 ('quotedblleft',0x201C,'g_quotedblleft','pp'),('quotedblright',0x201D,'g_quotedblright','pp'),
                 ('uni02BC',0x02BC,'g_modifierapostrophe','pp')]:
    add(n,u,getattr(U,f),cl[0],cl[1])

SB = {'s': lambda v: 0.55*v+20, 'r': lambda v: 0.38*v+14, 'd': lambda v: 0.10*v+8, 'f': lambda v: 0.28*v+10,
      'o': lambda v: 0.22*v+10, 'p': lambda v: 0.55*v+14}
