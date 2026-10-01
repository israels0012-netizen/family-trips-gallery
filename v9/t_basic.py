import pfx,sim,json
from actions import *
res={}
sp=pfx.SPList(); a=sim.start(sp)
r07=row(a,'ratios_R07'); cash=row(a,'balance_group_cash')
eid=post(a,'pnl_2420','balance_100',10,'הוצאה ידנית','operating')
res['post']=dict(ok=ok(a),entries=len(C(a,'colV97Entries')),R07_before=r07,R07_after=row(a,'ratios_R07'),cash=(cash,row(a,'balance_group_cash')),cf_close=row(a,'cf_close'),msg=G(a,'varV97SaveMessage'))
# concurrency: second user
b=sim.start(sp,user='User B')
note(a,'balance_100','A note'); note(b,'balance_110','B note'); reload(a)
res['concurrent_diff_keys']=sorted((n['Key'],n['Text']) for n in C(a,'colV97Notes'))
note(a,'balance_100','A2'); note(b,'balance_100','B2'); reload(a); reload(b)
res['same_key_last_wins']=([n['Text'] for n in C(a,'colV97Notes') if n['Key']=='balance_100'],[n['Text'] for n in C(b,'colV97Notes') if n['Key']=='balance_100'])
# note delete
note(a,'balance_110',''); reload(b)
res['note_deleted']=[n['Key'] for n in C(b,'colV97Notes')]
# materiality setting shared
materiality(a,77); reload(b)
res['materiality_shared']=(G(a,'varV97Materiality'),G(b,'varV97Materiality'))
res['unhandled']=sim.unhandled(a)+sim.unhandled(b)
for k,v in res.items(): print(k,':',v)
