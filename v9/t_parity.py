import pfx,sim,json,re
from actions import *
D=json.load(open('DATA.json',encoding='utf-8'))
rows={r['id']:r for p in D['pages'].values() for r in p['rows']}
def tpl_drill(sid,amt,pc,q='',mode='original'):
    base=rows.get(sid); allr=D['drilldownData'].get(sid,[])
    bAbs=max(abs(float(base.get('current') or 0)),abs(float(base.get('compare') or 0)),0.000001)
    out=[]
    for i,r in enumerate(allr):
        mx=max(abs(float(r.get('current') or 0)),abs(float(r.get('compare') or 0)))
        num=(amt==0 and pc==0) or (amt>0 and mx>=amt) or (pc>0 and mx/bAbs*100>=pc)
        hay=' '.join(str(r.get(k) or '') for k in ('desc','account','code','entity','company','sourceType')).lower()
        if num and (not q or q.lower() in hay): out.append((i,r))
    if mode=='desc': out.sort(key=lambda x:(-(float(x[1].get('current') or 0)),x[0]))
    if mode=='asc': out.sort(key=lambda x:((float(x[1].get('current') or 0)),x[0]))
    tr=[x for x in out if x[1].get('sourceType')!='additional_entry']; ad=[x for x in out if x[1].get('sourceType')=='additional_entry']
    return [(x[1].get('account'),x[1].get('current')) for x in tr+ad]
sp=pfx.SPList(); a=sim.start(sp)
a.globals['varV97Modal']='drill'
cases=0; mism=[]
for sid in D['drilldownData']:
    for amt,pc in [(0,0),(50,0),(0,10),(50,10),(1000,0),(0,50)]:
        for mode in ('original','desc','asc'):
            for q in ('','בנק','trial_balance'):
                a.globals['varV97Section']=sid; a.globals['varV97DrillSort']=mode
                a.set_text('V97Min',str(amt)); a.set_text('V97Pct',str(pc)); a.set_text('V97ModalSearch',q)
                got=[(r['Account'],r['Current']) for r in a.prop('V97Drill','Items')]
                exp=tpl_drill(sid,amt,pc,q,mode)
                cases+=1
                if got!=exp: mism.append((sid,amt,pc,mode,q,len(got),len(exp)))
print('B01/B18 drill parity cases',cases,'mismatches',len(mism),mism[:5])
# export uses same population/order
a.globals['varV97Section']='balance_310'; a.set_text('V97Min','50'); a.set_text('V97Pct','10'); a.set_text('V97ModalSearch',''); a.globals['varV97DrillSort']='desc'
n_items=len(a.prop('V97Drill','Items')); a.select('V97ExportView'); t=G(a,'varV97ExportText').split('\n')
print('drill export lines',len(t)-3,'gallery',n_items,'header',t[1].split('\t'),'cols',set(len(l.split('\t')) for l in t[1:]))
# ---- profit drivers vs template
def milestones(rid):
    row=rows[rid]; key=rid.replace('pnl_',''); code=str(row.get('code') or key).strip().upper()
    if re.fullmatch(r'(T|U)\d*',code,re.I) or re.fullmatch(r'(T|U)\d+',key): return ['r236','r270','r289']
    if re.fullmatch(r'(V|W)\d*',code,re.I) or re.fullmatch(r'(V|W)\d+',key): return ['r270','r289']
    if re.fullmatch(r'(VA|VB|VD|VE)\d*',code,re.I) or re.fullmatch(r'(VA|VB|VD|VE)\d*',key,re.I): return ['r289']
    pr=D['pages']['pnl']['rows']; parents=[];seen={rid};frontier=[rid]
    while frontier:
        nxt=[]
        for p in pr:
            if p['id'] in seen or not isinstance(p.get('children'),list): continue
            if any(c in frontier for c in p['children']): parents.append(p);seen.add(p['id']);nxt.append(p['id'])
        frontier=nxt
    text=' '.join(str(x) for r in [row]+parents for x in (r.get('code'),r.get('name')) if x).lower()
    if re.search(r'מימון|finance|מסים|מיסים|tax|חברות מוחזקות|associate|הוצאות אחרות|הכנסות אחרות|other expense|other income',text): return ['r289']
    if re.search(r'עלות המכר|עלות המכירות|cost of sales|cogs|מכירות|הכנסות|revenue|sales',text): return ['r236','r270','r289']
    if re.search(r'מכירה ושיווק|שיווק|הנהלה וכלליות|הנהלה|כלליות|selling|marketing|general and administrative|administrative|תפעול',text): return ['r270','r289']
    return []
def sales_sign():
    r=rows['pnl_metric_sales']; v=float(r.get('current') or 0)
    return 1 if v>0 else -1
def tpl_drivers(kind):
    ms={'gross':'r236','operating':'r270','net':'r289'}[kind]; mult=sales_sign(); out=[]
    for item in D['pages']['pnl']['rows']:
        if item.get('children'): continue
        if ms not in milestones(item['id']): continue
        code=str(item.get('code') or item['id'].replace('pnl_','')).upper(); name=str(item.get('name') or '')
        isr=bool(re.match('^T',code)) or ('הכנס' in name and 'הוצא' not in name)
        ise=bool(re.match('^(U|V|W|VD)',code)) or bool(re.search('עלות|הוצא|מסים על ההכנסה',name))
        for r in D['drilldownData'].get(item['id'],[]):
            c=float(r.get('current') or 0); p=float(r.get('compare') or 0)
            imp=abs(c)-abs(p) if isr else (-(abs(c)-abs(p)) if ise else mult*(c-p))
            if abs(imp)<0.005: continue
            out.append((r.get('account'),round(imp,6)))
    out.sort(key=lambda x:-abs(x[1])); return out[:5]
for kind,tgt in [('gross','pnl_r236'),('operating','pnl_r270'),('net','pnl_r289')]:
    a.globals['varV97DriverTarget']=tgt; a.globals['varV97Modal']='drivers'
    got=[(r['Account'],round(r['Impact'],6)) for r in a.prop('V97Drivers','Items')]
    exp=tpl_drivers(kind)
    print('A01 drivers',kind,'match' if got==exp else 'DIFF',got[:5] if got!=exp else '')
    if got!=exp: print('   expected',exp)
print('unhandled',sim.unhandled(a))
