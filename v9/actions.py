import json, pfx, sim
def G(a,k): return a.globals.get(k)
def C(a,k): return a.cols.get(k,[])
def note(a,key,text):
    a.globals['varV97NoteKey']=key; a.set_text('V97Note',text); a.select('V97NoteApply')
def post(a,debit,credit,amount,desc,flow='operating',ref=''):
    a.globals['varV97Debit']=debit; a.globals['varV97Credit']=credit; a.globals['varV97Flow']=flow
    a.set_text('V97Amount',str(amount)); a.set_text('V97Description',desc); a.set_text('V97Reference',ref)
    before={e['Id'] for e in C(a,'colV97Entries')}
    a.select('V97Post')
    new=[e['Id'] for e in C(a,'colV97Entries') if e['Id'] not in before]
    return new[0] if new else None
def delete_entry(a,eid):
    a.globals['varV97DeleteId']=eid; a.globals['varV97Modal']='deleteconfirm'; a.select('V97ConfirmYesdeleteconfirm')
def link(a,doc,target):
    a.globals['varV97Doc']=doc; a.globals['varV97LinkTarget']=target; a.select('V97LinkAdd')
def review(a,target,which,notetext=''):
    a.globals['varV97EvidenceKey']=target; a.set_text('V97EvidenceNote',notetext)
    a.select({'handled':'V97Review0','needsAction':'V97Review1','auto':'V97Review2'}[which])
def reload(a):
    a.select('V97LoadLocal')
def backup_text(a):
    a.select('V97Actionbackup'); return G(a,'varV97ExportText')
def restore(a,text):
    a.globals['varV97ImportText']=text; a.globals['varV97Modal']='importconfirm'; a.select('V97ImportConfirmYes')
def materiality(a,v):
    a.set_text('V97Materiality',str(v)); a.change('V97Materiality')
def row(a,rid,col='Current'):
    for r in C(a,'colV97Rows'):
        if r['RowId']==rid: return r[col]
def ok(a): return G(a,'varV97RemoteReady') and not G(a,'varV97Syncing')
def raw_event(sp,entity,key,payload,deleted=False,gen=1,ds='V97Canvas_981f9bfb1d611fb5',stamp=True,envkey=None):
    env=json.dumps({'V':9,'Dataset':ds,'Gen':gen,'Entity':entity,'Key':envkey or key,'Deleted':deleted,'Payload':json.dumps(payload,ensure_ascii=False),'At':'2026-09-29T20:00:00Z','Author':'raw'},ensure_ascii=False)
    r=sp.insert({'Title':'V97-EVENT9-raw','field_1':'GFL','field_2':'2025','field_3':'V97Event9','field_10':-1,'field_11':gen,'field_14':ds,'AuditNote':env})
    if stamp: sp.update(r['ID'],{'field_10':r['ID']})
    return r['ID']
