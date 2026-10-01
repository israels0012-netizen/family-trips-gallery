import pfx,sim,json
from actions import *
pfx.SP_COLUMNS.append('field_13')
def scenario(path):
    sp=pfx.SPList(); a=sim.start(sp,path=path)
    for d,c,amt,fl in [('pnl_2420','balance_100',10,'operating'),('balance_800','balance_100',25,'investing'),('balance_100','balance_1300',40,'financing'),('pnl_2450','balance_810',7,'noncash'),('pnl_2040','balance_200',3,'noncash')]:
        a.globals['varV97Debit']=d; a.globals['varV97Credit']=c; a.globals['varV97Flow']=fl
        a.set_text('V97Amount',str(amt)); a.set_text('V97Description','t'); a.set_text('V97Reference',''); a.select('V97Post')
    return a
def snap(a):
    rows={r['RowId']:(round(r['Current'],6) if r['Current'] is not None else None, r['Prior']) for r in C(a,'colV97Rows')}
    cand=sorted((c['Key'],c['IsNew'],c['IsGone'],c['IsRound'],c['IsRepeated'],c['IsReverse'],c['Classification']) for c in C(a,'colV97Candidates'))
    ex=[e['RowId'] for e in C(a,'colV97Exec')]
    un=sorted((u['Key'],u['Reason']) for u in C(a,'colV97Unchanged'))
    ch=[(c['Id'],c['Caption'].replace('#','')) for c in C(a,'colV97Charts')]
    iss=sorted((i['Key'],i['Name']) for i in C(a,'colV97RuntimeIssues'))
    return dict(rows=rows,cand=cand,exec=ex,unch=un,charts=[c[0] for c in ch],issues=iss,edges=len(C(a,'colV97Edges')))
v8=snap(scenario('v8_src.txt')); v9=snap(scenario(sim.V9))
for k in v8:
    same=v8[k]==v9[k]
    print(k,'IDENTICAL' if same else 'DIFF')
    if not same and k=='rows':
        print([ (r,v8['rows'][r],v9['rows'].get(r)) for r in v8['rows'] if v8['rows'][r]!=v9['rows'].get(r)][:10])
    elif not same: print(' v8',str(v8[k])[:300],'\n v9',str(v9[k])[:300])
print('entries posted (v9 rows with cf_manual):',[r for r in v9['rows'] if 'manual' in r])
