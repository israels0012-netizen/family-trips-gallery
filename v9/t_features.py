import pfx,sim,json
from actions import *
R={}
sp=pfx.SPList(); a=sim.start(sp)
def export(modal,**kw):
    a.globals['varV97Modal']=modal
    for k,v in kw.items(): a.globals[k]=v
    a.select('V97ExportView'); t=G(a,'varV97ExportText'); return t.split('\n')
# B20: description containing tab/newline
eid=post(a,'pnl_2420','balance_100',5,'שורה\tעם טאב\nושורה','operating','R\t9')
# exports
for md,kw in [('drill',{'varV97Section':'balance_100'}),('evidence',{'varV97EvidenceFilter':'all'}),('additional',{'varV97EntryFilter':'all'}),('exceptions',{}),('unchanged',{}),('exec',{})]:
    a.set_text('V97Min','0' if md!='exceptions' else str(G(a,'varV97Materiality'))); a.set_text('V97Pct','0'); a.set_text('V97ModalSearch','')
    try:
        L=export(md,**kw); cols=set(len(l.split('\t')) for l in L if l)
        R['export_'+md]=dict(lines=len(L),col_counts=sorted(cols),header=L[0][:80] if md!='drill' else L[1][:80])
    except Exception as e: R['export_'+md]='ERR '+str(e)
a.globals['varV97EntryFilter']='manual'; L=export('additional'); R['export_additional_manual_only']=len(L)
# B04 copy comparisons
a.globals['varV97Page']='comparisons'; a.globals['varV97Modal']=''; a.select('V97CopyTable'); R['B04_copy_comparisons_rows']=len(a.clipboard.split('\n'))-1
a.globals['varV97Page']='balance'; a.select('V97CopyTable'); R['copy_balance_rows']=(len(a.clipboard.split('\n'))-1,len(a.prop('V97Main','Items')))
# B05 evidence workflow
a.globals['varV97Modal']='evidence'; a.globals['varV97EvidenceFilter']='all'; a.set_text('V97ModalSearch','')
items=a.prop('V97Evidence','Items'); R['B05_targets']=len(items)
a.globals['varV97EvidenceFilter']='attention'; att=a.prop('V97Evidence','Items'); R['B05_attention']=len(att)
tk=att[0]['TargetKey']
review(a,tk,'handled','נבדק מול אישור')
a.globals['varV97EvidenceFilter']='handled'; R['B05_handled_after_mark']=[x['TargetKey'] for x in a.prop('V97Evidence','Items')]==[tk]
a.globals['varV97EvidenceFilter']='attention'; R['B05_attention_after']=len(a.prop('V97Evidence','Items'))
a.globals['varV97EvidenceKey']=tk; raw=a.prop('V97EvidenceRaw','Default'); R['B05_detail_has_history']='היסטוריית טיפול' in raw and 'נבדק' in raw
review(a,tk,'auto'); R['B05_back_to_auto']=(len(C(a,'colV97Reviews')),len(C(a,'colV97History')))
a.globals['varV97EvidenceSort']='desc'; a.globals['varV97EvidenceFilter']='all'; amts=[x['SortAmount'] for x in a.prop('V97Evidence','Items')]; R['B05_sort_desc']=amts==sorted(amts,reverse=True)
# B07 evidence readable
a.globals['varV97Doc']='DOC-001'; a.globals['varV97EvidenceKey']=''; a.select('V97EvidenceReadable')
cards=C(a,'colV97EvidenceDetails'); R['B07_cards']=(len(cards),[c['Heading'][:22] for c in cards][:8])
R['B07_unmatched_with_reason']=sum(1 for c in cards if c['Heading'].startswith('פריט ללא התאמה') and 'סיבה' in c['Body'])
a.globals['varV97Doc']='DOC-017'; a.select('V97EvidenceReadable'); R['B07_group_checks_doc17']=[c['Heading'] for c in C(a,'colV97EvidenceDetails') if 'קבוצתית' in c['Heading']][:3]
# B06/B16 manual link to section-level target + external doc
link(a,'DOC-005','general:balance_810:'); R['B06_section_link']=(ok(a),[l['Key'] for l in C(a,'colV97Links')])
a.globals['varV97LinkTarget']='drill:balance_100:1010004'; a.set_text('V97ExtDocName','אישור בנק'); a.set_text('V97ExtDocUrl','https://bank.example/conf.pdf'); a.select('V97ExtDocAdd')
ext=[d for d in C(a,'colV97Docs')]; R['B16_ext_doc']=(ok(a),[(d['DocId'][:4],d['Name']) for d in ext],[l['TargetKey'] for l in C(a,'colV97Links')])
a.globals['varV97Doc']=ext[0]['DocId']; a.select('V97OpenDoc'); R['B16_open']=a.launched[-1:]
item=[x for x in a.prop('V97Documents','Items') if x['DocId']==ext[0]['DocId']][0]
a.select('V97DocumentDelete',item); R['B16_delete_cascade']=(len(C(a,'colV97Docs')),[l['TargetKey'] for l in C(a,'colV97Links')])
# B15
a.select('V97SaveHtml'); h=G(a,'varV97ExportText'); R['B15_html']=(h.startswith('<!DOCTYPE html>'),h.count('<table>'),len(h))
a.select('V97ExportAll'); R['B15_export_all_lines']=len(a.clipboard.split('\n'))
# B21 valuation
a.globals['varV97Market']=1000.0
for rr in C(a,'colV97Rows'):
    if rr['RowId']=='balance_total_equity': saved=rr['Current']; rr['Current']=0.0
R['B21_zero_equity']=(a.prop('V97Valuation','Text').split('\n')[1],a.prop('V97PriceToBook','Text').split('\n')[1])
for rr in C(a,'colV97Rows'):
    if rr['RowId']=='balance_total_equity': rr['Current']=saved
R['B21_normal']=(a.prop('V97Valuation','Text').split('\n')[1],a.prop('V97PriceToBook','Text').split('\n')[1],a.prop('V97PriceEarnings','Text').split('\n')[1])
# B14 FX reversed range with synthetic rows
fx=dict(C(a,'colV97Drill')[0]); fx.update({'Key':'fx1','HasFx':True,'OtherCurrent':10.0,'Rate':3.7,'OtherCurrency':'USD'}); fx2=dict(fx); fx2.update({'Key':'fx2','Rate':4.1})
a.cols['colV97Drill'].extend([fx,fx2]); a.globals['varV97Modal']='fx'; a.set_text('V97ModalSearch','')
def fxr(lo,hi): a.set_text('V97FxMin',lo); a.set_text('V97FxMax',hi); return [r['Rate'] for r in a.prop('V97Fx','Items')]
R['B14_fx']=dict(all=fxr('',''),rev=fxr('4.5','3.5'),min_only=fxr('3.7',''),max_only=fxr('','4.1'))
a.cols['colV97Drill']=a.cols['colV97Drill'][:-2]
# KPI and table texts
R['kpi0']=a.prop('V97Kpi0','Text').replace('\n',' / ')
mi=a.prop('V97Main','Items'); R['row_texts']=[(a.prop('V97RowName','Text',item=r),a.prop('V97RowCurrent','Text',item=r),a.prop('V97RowPct','Text',item=r)) for r in mi[:4]]
R['footer']=a.prop('V97Footer','Text')
R['unhandled']=sim.unhandled(a); R['notes_err']=[n for n in a.notes if n[0]=='Error'][-3:]
for k,v in R.items(): print(k,':',v)
