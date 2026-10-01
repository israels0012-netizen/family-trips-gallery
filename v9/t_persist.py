import pfx,sim,json
from actions import *
R={}
def snapshots(sp): return [(r['ID'],r['field_10'],r['field_11']) for r in sp.rows if r['field_3']=='V97Snapshot9']
# ---- A03: 620 events after the restore point, row limit 500 -> paged, complete
sp=pfx.SPList(); a=sim.start(sp)
for i in range(620): raw_event(sp,'Notes','balance_100' if i%2 else 'balance_110',{'Key':'balance_100' if i%2 else 'balance_110','Text':'n%d'%i,'At':'x'})
reload(a)
R['A03_620_events']=dict(ok=ok(a),notes=sorted((n['Key'],n['Text']) for n in C(a,'colV97Notes')),loaded=len(C(a,'colV97Events')),queries=sp.queries)
# small row limit -> more pages than allowed -> must stop, not claim sync
sp.limit=50; reload(a)
R['A03_limit50_incomplete']=dict(remote=G(a,'varV97RemoteReady'),msg=G(a,'varV97SaveMessage')[:90],notes_kept=len(C(a,'colV97Notes')))
sp.limit=500; reload(a); R['A03_recovered']=ok(a)
# ---- checkpoint after events become older than 10 minutes
sp.tick(minutes=15); reload(a)
R['checkpoint']=dict(ok=ok(a),snaps=snapshots(sp),parts=len([r for r in sp.rows if r['field_3']=='V97SnapPart9']),through=G(a,'varV97Through'))
before=sorted((n['Key'],n['Text']) for n in C(a,'colV97Notes'))
c=sim.start(sp,user='C'); R['checkpoint_roundtrip_same_state']=before==sorted((n['Key'],n['Text']) for n in C(c,'colV97Notes')) and ok(c)
R['events_loaded_after_checkpoint']=len(C(c,'colV97Events'))
# ---- B11: large state -> chunked snapshot
for i in range(70): raw_event(sp,'Notes','balance_%d'%[100,110,120,130,200][i%5] if i<5 else 'pnl_2420' if i==5 else 'balance_100',{'Key':'x','Text':'y'})  # wrong payload keys -> ignored (B10)
R['B10_bad_events_ignored']=None
reload(c); R['B10_bad_events_ignored']=dict(ok=ok(c),warn=G(c,'varV97LoadWarn'))
keys=[r['RowId'] for r in C(c,'colV97Base') if r['Kind']=='item'][:70]
for k in keys: raw_event(sp,'Notes',k,{'Key':k,'Text':'L'*1000,'At':'x'})
sp.tick(minutes=15); reload(c)
parts=[r for r in sp.rows if r['field_3']=='V97SnapPart9' and r['field_17']==G(c,'varV97SnapId')]
R['B11_large_state']=dict(ok=ok(c),notes=len(C(c,'colV97Notes')),parts=len(parts),maxlen=max(len(p['AuditNote']) for p in parts))
d=sim.start(sp,user='D'); R['B11_reload_fresh_client']=dict(ok=ok(d),notes=len(C(d,'colV97Notes')))
# ---- A04: restore vs stale checkpoint / stale writer
bk=backup_text(d)
st=json.loads(bk); st['Notes']=[{'Key':'balance_100','Text':'RESTORED','At':'x'}]
restore(d,json.dumps(st,ensure_ascii=False))
R['A04_restore']=dict(ok=ok(d),gen=G(d,'varV97Gen'),notes=[(n['Key'],n['Text']) for n in C(d,'colV97Notes')])
# stale client c (gen1) writes a note -> must not override restore; must be told
note(c,'balance_110','STALE EDIT')
R['A04_stale_writer']=dict(ok=ok(c),gen=G(c,'varV97Gen'),notes=[(n['Key'],n['Text']) for n in C(c,'colV97Notes')],notify=[x for x in c.notes if x[0] in('Warning','NotificationType.Warning')][-1:])
# stale checkpoint of gen1 with high Through written later cannot win
c.globals['varV97Gen']=1; c.globals['varV97Through']=0; c.globals['varV97CheckpointNeeded']=True
c.cols['colV97Win']=[{'Entity':'Notes','Key':'balance_100','EventId':99999,'Deleted':False,'Payload':json.dumps({'Key':'balance_100','Text':'OLD','At':'x'})}]
c.cols['colV97Events']=[{'EventId':99999,'Created':sp.clock.replace(year=2025)}]
c.globals['varV97RemoteReady']=True; c.globals['varV97Syncing']=False
c.select('V97Checkpoint')
e=sim.start(sp,user='E')
R['A04_stale_checkpoint']=dict(snaps=snapshots(sp)[-3:],fresh_notes=[(n['Key'],n['Text']) for n in C(e,'colV97Notes')],gen=G(e,'varV97Gen'))
# race: event written with old gen after restore (gen check passed before restore)
raw_event(sp,'Notes','balance_100',{'Key':'balance_100','Text':'RACE','At':'x'},gen=1)
reload(e); R['A04_race_old_gen_event_ignored']=[(n['Key'],n['Text']) for n in C(e,'colV97Notes')]
# ---- A05: delete entry with dependents
eid=post(e,'pnl_2420','balance_100',10,'למחיקה')
tk='drill:pnl_2420:MANUAL-'+eid
link(e,'DOC-001',tk); review(e,tk,'handled','בדקתי'); note(e,'MANUAL|'+eid+'|D','הערה לשורה')
R['A05_before']=dict(links=len(C(e,'colV97Links')),reviews=len(C(e,'colV97Reviews')),notes=[n['Key'] for n in C(e,'colV97Notes')],ok=ok(e))
delete_entry(e,eid)
R['A05_after']=dict(ok=ok(e),entries=len(C(e,'colV97Entries')),links=len(C(e,'colV97Links')),reviews=len(C(e,'colV97Reviews')),notes=[n['Key'] for n in C(e,'colV97Notes')],msg=G(e,'varV97SaveMessage'))
# orphan from older data still loads (lenient), e.g. link to a missing manual account
raw_event(sp,'Links','drill:pnl_2420:MANUAL-ghost|DOC-001',{'Key':'drill:pnl_2420:MANUAL-ghost|DOC-001','TargetKey':'drill:pnl_2420:MANUAL-ghost','DocId':'DOC-001','Section':'pnl_2420','Account':'MANUAL-ghost','Name':'x'},gen=G(e,'varV97Gen'))
reload(e); R['A05_orphan_dropped_not_blocking']=dict(ok=ok(e),links=len(C(e,'colV97Links')),warn=G(e,'varV97LoadWarn'))
# ---- B09 strict import: orphan review rejected
st=json.loads(backup_text(e)); st['Reviews']=[{'Key':'LINK|NOT-A-REAL-TARGET','Status':'טופל','Note':'x','At':'now'}]; st['Version']=2
restore(e,json.dumps(st,ensure_ascii=False))
R['B09_orphan_review_import']=dict(ok=ok(e),msg=G(e,'varV97SaveMessage')[:120],gen=G(e,'varV97Gen'))
st=json.loads(backup_text(e)); st['Dataset']='WRONG'; restore(e,json.dumps(st))
R['import_wrong_dataset']=G(e,'varV97SaveMessage')[:60]
# ---- B08: corrupt latest snapshot header/content
f=sim.start(sp,user='F'); good=[(n['Key'],n['Text']) for n in C(f,'colV97Notes')]
hdr=[r for r in sp.rows if r['field_3']=='V97Snapshot9'][-1]
sid='bad-snap'; payload=json.dumps({'V':9,'Dataset':'WRONG','Gen':hdr['field_11']+5,'Through':0,'SnapId':sid,'Kind':'restore','Items':[{'Entity':'Notes','Key':'balance_100','EventId':0,'Deleted':False,'Payload':json.dumps({'Key':'balance_100','Text':'foreign','At':'x'})}]})
sp.insert({'field_1':'GFL','field_2':'2025','field_3':'V97SnapPart9','field_10':1,'field_11':hdr['field_11']+5,'field_14':'V97Canvas_981f9bfb1d611fb5','field_17':sid,'AuditNote':payload})
sp.insert({'field_1':'GFL','field_2':'2025','field_3':'V97Snapshot9','field_10':0,'field_11':hdr['field_11']+5,'field_14':'V97Canvas_981f9bfb1d611fb5','field_17':sid,'AuditNote':json.dumps({'V':9,'Dataset':'V97Canvas_981f9bfb1d611fb5','Gen':hdr['field_11']+5,'Through':0,'SnapId':sid,'Kind':'restore','Parts':1,'Length':len(payload)})})
reload(f)
R['B08_foreign_snapshot']=dict(remote=G(f,'varV97RemoteReady'),msg=G(f,'varV97SaveMessage')[:80],notes_unchanged=[(n['Key'],n['Text']) for n in C(f,'colV97Notes')]==good)
# missing part
for r in sp.rows:
    if r['field_17']==sid: r['field_3']='X'
reload(f); R['B08_cleanup_ok']=ok(f)
# ---- B12 full audit log
f.select('V97AuditLogLoad'); txt=G(f,'varV97ExportText')
R['B12_audit_log_lines']=(txt.count('\n')-1, len([r for r in sp.rows if r['field_3']=='V97Event9']))
R['unhandled']=sum((sim.unhandled(x) for x in (a,c,d,e,f)),[])
for k,v in R.items(): print(k,':',v)
