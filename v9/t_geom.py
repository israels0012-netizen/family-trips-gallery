import pfx,sim,sys
from parse import load
SIZES=[(390,844),(800,600),(1280,800),(1440,900)]
PAGES=['balance','pnl','cashflow','ratios','comparisons','settings']
MODALS=['','drill','kpi','exec','exceptions','unchanged','fx','errors','insights','additional','notes','evidence','evidencedetail','links','drivers','charts','ai','backup','copy','restoreconfirm','deleteconfirm','importconfirm']
def run(path):
    sp=pfx.SPList()
    if 'v8' in path: pfx.SP_COLUMNS.append('field_13')
    a=sim.start(sp,path=path)
    a.globals['varV97Section']='balance_100'; a.globals['varV97Doc']='DOC-001'; a.globals['varV97DriverTarget']='pnl_r236'
    top=[n for n in a.order if a.ctrls[n].parent is None]
    issues={}; evald=0
    for (w,h) in SIZES:
        a.width,a.height=w,h
        for pg in PAGES:
            for md in MODALS:
                if md and pg!='balance': continue
                a.globals['varV97Page']=pg; a.globals['varV97Modal']=md
                for n in top:
                    c=a.ctrls[n]
                    try:
                        if not pfx.tobool(a.prop(n,'Visible')): continue
                        x,y,wd,ht=(pfx.tonum(a.prop(n,p)) for p in ('X','Y','Width','Height'))
                    except pfx.PfxError as e:
                        issues.setdefault(n,set()).add('ERR '+e.msg[:60]); continue
                    if wd<=1 and ht<=1: continue
                    evald+=1
                    bad=[]
                    if x<-0.5 or y<-0.5: bad.append('neg')
                    if x+wd>w+0.5: bad.append('right')
                    if y+ht>h+0.5: bad.append('bottom')
                    if wd<0 or ht<0: bad.append('negsize')
                    if bad: issues.setdefault(n,set()).add('%dx%d %s/%s %s'%(w,h,pg,md or '-',','.join(bad)))
    print(path,'evaluated',evald,'controls with issues',len(issues))
    for n,v in sorted(issues.items()):
        v=sorted(v); print('  ',n,len(v),v[:3])
run(sys.argv[1])
