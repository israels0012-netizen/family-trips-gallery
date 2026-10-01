import pfx,sim,json
from actions import *
pfx.SP_COLUMNS.append('field_13')
sp=pfx.SPList()
v8=sim.start(sp,path='v8_src.txt',user='V8 user')
print('v8 start',sim.state(v8))
# v8 actions
v8.globals['varV97Debit']='pnl_2420'; v8.globals['varV97Credit']='balance_100'; v8.globals['varV97Flow']='operating'
v8.set_text('V97Amount','10'); v8.set_text('V97Description','v8 entry'); v8.set_text('V97Reference','R1'); v8.select('V97Post')
eid=C(v8,'colV97Entries')[0]['Id'] if C(v8,'colV97Entries') else None
v8.globals['varV97NoteKey']='balance_100'; v8.set_text('V97Note','v8 note'); v8.select('V97NoteApply')
v8.globals['varV97EvidenceKey']='DOC-001|0'; v8.set_text('V97EvidenceNote','checked'); v8.select('V97Review0')
v8.globals['varV97Doc']='DOC-002'; v8.globals['varV97Section']='balance_100'; v8.set_text('V97LinkAccount','1010004'); v8.select('V97LinkAdd')
v8.globals['varV97Doc']='DOC-003'; v8.set_text('V97EvidenceUrl','https://example.org/doc3.pdf'); v8.select('V97SetUrl')
print('v8 state',sim.state(v8),len(C(v8,'colV97Entries')),len(C(v8,'colV97Notes')),len(C(v8,'colV97Reviews')),len(C(v8,'colV97Links')),len(C(v8,'colV97Urls')))
print('v8 unhandled',sim.unhandled(v8)[:3])
print('sp types',sorted(set(r['field_3'] for r in sp.rows)))
v9=sim.start(sp,user='V9 user')
print('v9 after migration',sim.state(v9))
print(' entries',[(e['Description'],e['Amount']) for e in C(v9,'colV97Entries')])
print(' notes',[(n['Key'],n['Text']) for n in C(v9,'colV97Notes')])
print(' reviews',[(r['Key'],r['Status'],r['Note']) for r in C(v9,'colV97Reviews')])
print(' links',[(l['Key']) for l in C(v9,'colV97Links')])
print(' urls',[(u['DocId'],u['Url']) for u in C(v9,'colV97Urls')])
print(' R07',row(v9,'ratios_R07'),' v8 R07',row(v8,'ratios_R07'))
print(' snaps',[(r['field_3'],r['field_10'],r['field_11']) for r in sp.rows if r['field_3'] in('V97Snapshot9',)])
# v8 backup import into v9
v8.select('V97Actionbackup'); bk=G(v8,'varV97ExportText')
restore(v9,bk); print('import v8 backup',sim.state(v9),[(r['Key'],r['Status']) for r in C(v9,'colV97Reviews')])
# v8 checkpoint path: produce Snapshot8 by >=100 events? simulate snapshot8 already created at v8 start
print('unhandled',sim.unhandled(v9))
