import json, numpy as np, sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fmeasure import *
REF=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','reference','report_reference.json')))
WORDS={'Sphinx':([38,36,31,8,31,34],[8,8,9,9,6],218),'of':([37,21],[4],62),'black':([36,6,32,33,31],[8,9,6,7],168),'quartz':([36,31,32,18,21,30],[9,9,8,5,6],205),'judge':([14,31,36,34,34],[8,8,8,8],181),'my':([53,35],[5],93),'vow':([34,37,54],[4,4],133)}
SPACE_GAPS={'x o':19,'f b':23,'k q':19,', j':19,'e m':23,'y v':17}
def runs(col,thr=0.04):
    r=[];s=None
    for i,v in enumerate(col):
        if v>thr and s is None: s=i
        if v<=thr and s is not None: r.append((s,i-1)); s=None
    if s is not None: r.append((s,len(col)-1))
    return r
def glyph_img(R,line,ch,idx=None):
    L=R[line]; gs=[g for g in L['glyphs'] if g['ch']==ch]; g=gs[0] if idx is None else gs[idx]
    a=cov(L['gray']); return g,a[g['y0']:g['y1']+1,g['x0']:g['x1']+1]
def stems(R):
    out={}; cap=49.0
    g,a=glyph_img(R,'caps','H'); H,W=a.shape; rows=a[int(H*0.62):int(H*0.88),:]  # below crossbar
    out['H stem L']=float(np.median(rows[:,:int(W*0.35)].sum(axis=1))); out['H stem R']=float(np.median(rows[:,-int(W*0.35):].sum(axis=1)))
    g,a=glyph_img(R,'caps','E'); H,W=a.shape; col=a[:,int(W*0.78)]; rr=runs(col)
    out['E arms']=[float(col[s:e+1].sum()) for s,e in rr] if len(rr)==3 else None
    g,a=glyph_img(R,'caps','T'); H,W=a.shape; out['T stem']=float(np.median(a[int(H*0.4):int(H*0.8),:].sum(axis=1)))
    g,a=glyph_img(R,'caps','O'); H,W=a.shape; mid=a[int(H*0.45):int(H*0.55),:]; m=np.median(mid,axis=0)
    out['O sides']=[float(m[:W//2].sum()),float(m[W//2:].sum())]; col=a[:,W//2]; out['O top/bottom']=[float(col[:H//2].sum()),float(col[H//2:].sum())]
    g,a=glyph_img(R,'lower','n'); H,W=a.shape; out['n stem']=float(np.median(a[int(H*0.55):int(H*0.9),:int(W*0.4)].sum(axis=1)))
    g,a=glyph_img(R,'lower','l'); H,W=a.shape; out['l stem']=float(np.median(a[int(H*0.3):int(H*0.8),:].sum(axis=1)))
    g,a=glyph_img(R,'lower','o'); H,W=a.shape; m=np.median(a[int(H*0.45):int(H*0.55),:],axis=0); col=a[:,W//2]
    out['o sides']=[float(m[:W//2].sum()),float(m[W//2:].sum())]; out['o top/bottom']=[float(col[:H//2].sum()),float(col[H//2:].sum())]
    g,a=glyph_img(R,'lower','e'); H,W=a.shape; col=a[:,W//2]; rr=runs(col); out['e crossbar']=float(col[rr[1][0]:rr[1][1]+1].sum()) if len(rr)==3 else None
    g,a=glyph_img(R,'lower','z'); H,W=a.shape; out['z bars']=[float(a[:,int(W*0.15)][runs(a[:,int(W*0.15)])[0][0]:runs(a[:,int(W*0.15)])[0][1]+1].sum()), float(a[:,int(W*0.85)][runs(a[:,int(W*0.85)])[-1][0]:runs(a[:,int(W*0.85)])[-1][1]+1].sum())]
    return out
def evaluate(path,weight=400,cap_px=49.0,verbose=True):
    R=measure_all(path,cap_px,weight); E={}
    cap=cap_px
    # vertical (px)
    gl={g['ch']:g for g in R['caps']['glyphs']}; lb=R['lower']['base']; cb=R['caps']['base']
    low={g['ch']:g for g in R['lower']['glyphs']}; dg={g['ch']:g for g in R['digits']['glyphs']}; db=R['digits']['base']
    V={'cap H':cb-gl['H']['y0']+1,'x-height flat (v,w,x,z)':float(np.median([lb-low[c]['y0']+1 for c in 'vwxz'])),'ascender l':lb-low['l']['y0']+1,'ascender b,d,h,k':float(np.median([lb-low[c]['y0']+1 for c in 'bdhk'])),
       'desc p,q,y':float(np.median([low[c]['y1']-lb for c in 'pqy'])),'desc g,j':float(np.median([low[c]['y1']-lb for c in 'gj'])),'t height':lb-low['t']['y0']+1,'digit 1,4,7 height':float(np.median([db-dg[c]['y0']+1 for c in '147'])) if db else None,'Q below baseline':gl['Q']['y1']-cb}
    TV={'cap H':49,'x-height flat (v,w,x,z)':35,'ascender l':51,'ascender b,d,h,k':51.5,'desc p,q,y':12,'desc g,j':13,'t height':45,'digit 1,4,7 height':49,'Q below baseline':5}
    E['vertical']={k:(V[k],TV[k]) for k in V}
    # widths
    ws=[]
    for line,grp,key in (('caps','uppercase',None),('lower','lowercase',None)):
        for g in R[line]['glyphs']:
            ref=REF[grp][g['ch']]['W']; ws.append((g['ch'],g['W'],ref))
    digs=[g for g in R['digits']['glyphs']]
    for g in digs:
        if g['ch'].isdigit(): ws.append((g['ch'],g['W'],REF['digits'][g['ch']]['W']))
        elif g['ch'] in REF['punct']: ws.append((g['ch'],g['W'],REF['punct'][g['ch']]['W']))
    E['widths']=ws
    err=np.array([(c-r)/r*100 for _,c,r in ws]); E['width_stats']=dict(n=len(ws),mape=float(np.mean(np.abs(err))),signed=float(err.mean()),max=float(np.max(np.abs(err))),sd=float(err.std()),mae_px=float(np.mean([abs(c-r) for _,c,r in ws])))
    # string ink widths
    def inkw(line,start=None,end=None):
        g=R[line]['glyphs']; g=[x for x in g if x['ch'].isdigit()][:10] if line=='digits' else g; return g[-1]['x1']-g[0]['x0']+1
    E['strings']={'A-Z':(inkw('caps'),1207),'a-z':(inkw('lower'),955),'pangram':(inkw('pangram'),1209),'digits 0-9':(inkw('digits'),396)}
    # pair gaps
    def gaps(line,grp,pairs):
        gs=R[line]['glyphs']; out={}
        for a,b in zip(gs,gs[1:]):
            p=a['ch']+b['ch']
            if p in pairs: out[p]=(b['x0']-a['x1']-1,pairs[p]['gap'])
        return out
    pu=gaps('caps','uppercase',REF['pair_gaps_upper']); pl=gaps('lower','lowercase',REF['pair_gaps_lower']); pl.pop('ij',None)
    E['pair_gaps']={'upper':pu,'lower':pl}
    allp=list(pu.values())+list(pl.values()); d=np.array([c-r for c,r in allp]); E['gap_stats']=dict(n=len(d),rms=float(np.sqrt((d**2).mean())),mae=float(np.abs(d).mean()),signed=float(d.mean()),max=float(np.abs(d).max()),within1=float((np.abs(d)<=1).mean()))
    # pangram word gaps
    pg=R['pangram']['glyphs']; txt=[g for g in pg]; idx=0; wg=[];wi=[]
    chars=[c for c in "Sphinx of black quartz, judge my vow." if c!=' ']
    pos=0
    for w,(ws_,gs_,m) in WORDS.items():
        n=len(ws_); seg=pg[pos:pos+n]; 
        cg=[seg[i+1]['x0']-seg[i]['x1']-1 for i in range(n-1)]
        for c,r in zip(cg,gs_): wg.append(c-r)
        wi.append((w,seg[-1]['x1']-seg[0]['x0']+1,m)); pos+=n
        if w in('quartz','vow'): pos+=1   # skip comma / period glyph
    E['pangram_word_gap_stats']=dict(n=len(wg),rms=float(np.sqrt(np.mean(np.square(wg)))),signed=float(np.mean(wg)))
    E['pangram_words']=wi
    # space gaps
    sg={}; 
    for k,v in SPACE_GAPS.items():
        a,b=k.split(' '); 
        for i in range(len(pg)-1):
            if pg[i]['ch']==a and pg[i+1]['ch']==b and abs(pg[i]['adv'][1]-pg[i+1]['adv'][0])<40: sg[k]=(pg[i+1]['x0']-pg[i]['x1']-1,v)
    E['space_gaps']=sg
    E['stems']=stems(R); E['dots']={'i dot W,H':None}
    # dots: i dot size from component above stem
    gi=[g for g in R['lower']['glyphs'] if g['ch']=='i'][0]; E['i_box_W']=gi['W']; per=[g for g in R['digits']['glyphs'] if g['ch']=='.'][0]; E['period']=(per['W'],per['H'])
    E['_meta']=dict(px=R['_px'],fonts=R['_ok'],cap_em=R['_cap_em'])
    return E,R
