# -*- coding: utf-8 -*-
import copy, re, sys
from parse import load
import emit
import f_persist as FP
import f_ui as U
import f_views as V

SRC = 'v8_src.txt'
OUT = 'PowerApps_V97_CANVAS_SHARED_v9_ONE_PASTE.txt'
doc = load(SRC)

# ----------------------------------------------------------------- helpers
def find(name, nodes=None):
    nodes = doc if nodes is None else nodes
    for i, n in enumerate(nodes):
        (k, body), = n.items()
        if k == name:
            return nodes, i, body
        if body.get('Children'):
            r = find(name, body['Children'])
            if r: return r
    return None

def props(name):
    r = find(name)
    if not r: raise KeyError(name)
    return r[2]['Properties']

def setp(name, prop, value):
    p = props(name)
    if not value.startswith('='): raise ValueError(name + prop)
    p[prop] = value

def getp(name, prop):
    return props(name)[prop]

def clone(src, newname, overrides, after=None, parent_children=None):
    nodes, i, body = find(src)
    nb = copy.deepcopy(body)
    nb['Properties'].update(overrides)
    if 'AccessibleLabel' in nb['Properties']:
        nb['Properties']['AccessibleLabel'] = overrides.get('AccessibleLabel', '="' + newname + '"')
    node = {newname: nb}
    if after:
        an, ai, _ = find(after)
        an.insert(ai + 1, node)
    else:
        nodes.insert(i + 1, node)
    return nb

def all_ctrls(nodes=None):
    nodes = doc if nodes is None else nodes
    for n in nodes:
        (k, body), = n.items()
        yield k, body
        if body.get('Children'):
            yield from all_ctrls(body['Children'])

# ------------------------------------------------------- persistence (task 2)
setp('V97LoadShared', 'OnSelect', FP.LOAD_SHARED)
setp('V97Checkpoint', 'OnSelect', FP.CHECKPOINT)
setp('V97ImportState', 'OnSelect', FP.IMPORT_STATE)
setp('V97WriteEvent', 'OnSelect', FP.WRITE_EVENT)
setp('V97PersistAll', 'OnSelect', U.PERSIST_ALL)
for nm, f in [('V97Materialize', FP.MATERIALIZE), ('V97ConvertStage', FP.CONVERT_STAGE),
              ('V97ApplyState', FP.APPLY_STATE), ('V97WriteSnapshot', FP.WRITE_SNAPSHOT),
              ('V97AuditLogLoad', FP.AUDIT_LOG)]:
    clone('V97Checkpoint', nm, {'OnSelect': f}, after='V97Checkpoint')

# Initialize: new schemas, evidence lookup table, template default expansion, chain start
init = getp('V97Initialize', 'OnSelect')
m = re.search(r'ClearCollect\(colV97Entries,.*?ClearCollect\(colV97Store,Table\(\{Payload:""\}\)\);Clear\(colV97Store\);', init, re.S)
assert m, 'init schema block'
init = init[:m.start()] + V.SCHEMAS + '\n' + init[m.end():]
init = init.replace('Set(varV97SaveMessage,"טוען מצב משותף מ-SharePoint...");Select(V97Recalculate);Select(V97LoadShared);Set(varV97EvidenceSort,"original")',
                    'Set(varV97SaveMessage,"טוען מצב משותף מ-SharePoint...");Set(varV97EvidenceSort,"original");Set(varV97DrillSort,"original");'
                    'Set(varV97Gen,0);Set(varV97Through,0);Set(varV97SnapId,"");Set(varV97CachedSnapId,"");Set(varV97CachedSnapText,"");Set(varV97LoadWarn,"");'
                    'Set(varV97LinkTarget,"");Set(varV97PendingWriteCheck,false);Set(varV97WriteGen,0);Set(varV97Legacy,false);\n'
                    + V.INIT_EXTRA + '\nSet(varV97InitPending,true);Select(V97Recalculate)')
assert 'varV97InitPending' in init
setp('V97Initialize', 'OnSelect', init)

# RebuildViews: ordered drill + manual rows, evidence model, chain tail
rv = getp('V97RebuildViews', 'OnSelect')
a = rv.index('=ClearCollect(colV97AllDrill,colV97Drill);')
b = rv.index('ClearCollect(colV97Candidates')
rv = '=' + V.ALLDRILL + '\n' + rv[b:]
a = rv.index('ClearCollect(colV97EvidenceView,colV97Matches);')
b = rv.index('ClearCollect(colV97ChartRows')
rv = rv[:a] + V.EVIDENCE + '\n' + rv[b:]
rv = rv.rstrip() + ';\n' + V.REBUILD_TAIL
setp('V97RebuildViews', 'OnSelect', rv)

# ------------------------------------------------------------ layout (B17)
for k, body in all_ctrls():
    p = body.get('Properties', {})
    for prop in ('X', 'Y', 'Width', 'Height'):
        if prop in p:
            v = str(p[prop])
            v2 = (v.replace('If(V97Background.Width>=900,5,3)', 'If(V97Background.Width>=600,5,3)')
                   .replace('If(V97Background.Width>=900,6,4)', 'If(V97Background.Width>=600,6,4)')
                   .replace('If(V97Background.Width>=900,90,170)', 'If(V97Background.Width>=600,90,170)')
                   .replace('If(V97Background.Width>=900,82,120)', 'If(V97Background.Width>=600,82,120)'))
            if v2 != v: p[prop] = v2
h = getp('V97Main', 'Height')
h2 = h.replace('-38-If(varV97Page="ratios",150,0))', '-38-' + U.MAIN_HEIGHT_RATIOS + ')')
assert h2 != h
setp('V97Main', 'Height', h2)
for nm, pp in U.MK.items():
    for k, v in pp.items():
        setp(nm, k, v)
setp('V97PriceEarnings', 'Width', '=V97Valuation.Width')

# ------------------------------------------------------- main table (template)
for nm, v in U.KPI_TEXT.items(): setp(nm, 'Text', v)
setp('V97RowName', 'Text', U.ROW_NAME)
setp('V97RowCurrent', 'Text', U.ROW_CURRENT)
setp('V97RowPrior', 'Text', U.ROW_PRIOR)
setp('V97RowDiff', 'Text', U.ROW_DIFF)
setp('V97RowDiff', 'Color', '=' + U.ROW_COLOR)
setp('V97RowPct', 'Text', U.ROW_PCT)
setp('V97RowPct', 'Color', '=' + U.ROW_COLOR)
setp('V97CopyTable', 'OnSelect', U.COPY_TABLE)
setp('V97CopyTable', 'Visible', '=varV97Ready && V97Background.Width>=600 && varV97Page<>"settings"')
setp('V97Footer', 'Text', U.FOOTER)
setp('V97CompareNumbers', 'Text', U.COMPARE_NUMBERS)
setp('V97SideNote', 'Text', '="V97 • Canvas 9"&Char(10)&"גמידה • 2025"&Char(10)&If(varV97RemoteReady,"מצב משותף","אין סנכרון")')

# ------------------------------------------------------------- settings page
setp('V97SettingsText', 'Text', U.SETTINGS_TEXT)
setp('V97SettingsText', 'Height', '=If(V97Background.Width>=600,100,150)')
SET_Y = 'If(V97Background.Width>=900,12,62)+100+If(V97Background.Width>=600,90,170)+If(V97Background.Width>=600,82,120)+64+If(V97Background.Width>=600,110,160)'
setp('V97SaveSettings', 'Y', '=' + SET_Y)
setp('V97RestoreSettings', 'Y', '=' + SET_Y)
LX = 'If(V97Background.Width>=900,166,12)'
setp('V97SourceMetadata', 'Y', '=' + SET_Y + '+44')
setp('V97SourceMetadata', 'Width', '=150')
btn_vis = '=varV97Ready && varV97Page="settings"'
clone('V97RestoreSettings', 'V97AuditLog', {'Text': '="יומן שינויים מלא"', 'X': '=' + LX + '+324', 'Y': '=' + SET_Y + '+If(V97Background.Width>=600,0,44)',
      'Width': '=150', 'OnSelect': '=Select(V97AuditLogLoad)', 'Visible': btn_vis})
setp('V97AuditLog', 'X', '=' + LX + '+If(V97Background.Width>=600,324,162)')
setp('V97AuditLog', 'Y', '=' + SET_Y + '+If(V97Background.Width>=600,0,44)')
clone('V97RestoreSettings', 'V97SaveHtml', {'Text': '="שמור דשבורד כ-HTML"', 'X': '=' + LX + '+162', 'Y': '=' + SET_Y + '+If(V97Background.Width>=600,44,88)',
      'Width': '=150', 'OnSelect': '=Select(V97BuildHtml)', 'Visible': btn_vis})
clone('V97RestoreSettings', 'V97Print', {'Text': '="הדפסה"', 'X': '=' + LX + '+If(V97Background.Width>=600,324,0)', 'Y': '=' + SET_Y + '+If(V97Background.Width>=600,44,88)',
      'Width': '=150', 'OnSelect': '=IfError(Print(),Notify("ההדפסה אינה זמינה בסביבה זו",NotificationType.Warning))', 'Visible': btn_vis})
clone('V97RestoreSettings', 'V97ExportAll', {'Text': '="ייצוא כל הדוחות"', 'X': '=' + LX, 'Y': '=' + SET_Y + '+If(V97Background.Width>=600,88,132)',
      'Width': '=150', 'OnSelect': '=Select(V97BuildExportAll)', 'Visible': btn_vis})

# ------------------------------------------------------------ drill (B01/B18/B19)
setp('V97Drill', 'Items', U.DRILL_ITEMS)
setp('V97DrillRow', 'Text', U.DRILL_ROW)
setp('V97DrillRow', 'OnSelect', U.DRILL_ROW_SELECT)
setp('V97DrillRecon', 'Text', U.DRILL_RECON)
setp('V97DrillRecon', 'Height', '=60')
setp('V97DrillRecon', 'Y', '=Parent.Height-265')
setp('V97Drill', 'Height', '=Max(70,Parent.Height-410)')
setp('V97MinLabel', 'Text', U.MIN_LABEL)
setp('V97PctLabel', 'Text', U.PCT_LABEL)
for nm in ('V97MinLabel', 'V97PctLabel'):
    setp(nm, 'Width', '=Min(140,(Min(1160,Parent.Width-16)-52)*0.15)')
setp('V97Min', 'Width', '=Min(105,(Min(1160,Parent.Width-16)-52)*0.15)')
setp('V97Pct', 'Width', '=Min(105,(Min(1160,Parent.Width-16)-52)*0.15)')
clone('V97EvidenceSortButton', 'V97DrillSort', {'Text': U.DRILL_SORT_TEXT, 'OnSelect': U.DRILL_SORT_SELECT,
      'X': '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+(Min(1160,Parent.Width-16)-52)*0.84', 'Y': '=86',
      'Width': '=(Min(1160,Parent.Width-16)-52)*0.16+20', 'Height': '=34',
      'Visible': '=varV97Ready && varV97Modal="drill"'}, after='V97Pct')
for nm in ('V97RowCurrent', 'V97RowPrior', 'V97RowDiff'):
    o = getp(nm, 'OnSelect')
    setp(nm, 'OnSelect', o + ';Set(varV97DrillSort,"original")')
setp('V97NoteTarget', 'Text', U.NOTE_TARGET)
setp('V97NotesRow', 'Text', U.NOTES_ROW)
setp('V97Notes', 'Items', U.NOTES_ITEMS)
setp('V97NoteApply', 'OnSelect', U.NOTE_APPLY)
an = getp('V97Analysis', 'Items')
an2 = an.replace('NoteKey:If(e.Source="manual_entry",e.Section,e.Key)', 'NoteKey:e.Key')
assert an2 != an
setp('V97Analysis', 'Items', an2)
setp('V97Empty', 'Visible', '=varV97Ready && ((varV97Modal in ["exec","exceptions","unchanged"] && IsEmpty(V97Analysis.AllItems)) || (varV97Modal="notes" && IsEmpty(V97Notes.AllItems)) || (varV97Modal="drill" && IsEmpty(V97Drill.AllItems)) || (varV97Modal="evidence" && IsEmpty(V97Evidence.AllItems)))')

# ----------------------------------------------------- manual entries (A05/B03)
setp('V97Post', 'OnSelect', U.POST)
setp('V97ConfirmYesdeleteconfirm', 'OnSelect', U.DELETE_ENTRY)
setp('V97Confirmdeleteconfirm', 'Text', '="למחוק את הפקודה הנבחרת, יחד עם ההערות, שיוכי הראיות והסטטוסים התלויים בה, ולחשב מחדש?"')
setp('V97SourceEntries', 'Items', U.SOURCE_ENTRIES_ITEMS)
setp('V97SourceEntryText', 'Text', U.SOURCE_ENTRY_TEXT)
setp('V97Journal', 'Items', U.JOURNAL_ITEMS)
setp('V97JournalText', 'Text', U.JOURNAL_TEXT)
setp('V97JournalCount', 'Text', U.JOURNAL_COUNT)

# ----------------------------------------------------------- evidence (B05/B07)
setp('V97Evidence', 'Items', U.EVIDENCE_ITEMS)
setp('V97EvidenceRow', 'Text', U.EVIDENCE_ROW)
setp('V97EvidenceRow', 'OnSelect', U.EVIDENCE_ROW_SELECT)
setp('V97Evidence', 'TemplateSize', '=78')
setp('V97EvidenceSelected', 'Text', U.EVIDENCE_SELECTED)
setp('V97EvidenceNote', 'Default', U.EVIDENCE_NOTE_DEFAULT)
for nm, (txt, f) in U.REVIEW.items():
    setp(nm, 'Text', txt)
    setp(nm, 'OnSelect', f)
setp('V97EvidenceUrl', 'Default', U.URL_DEFAULT)
setp('V97SetUrl', 'OnSelect', U.SET_URL)
setp('V97OpenDoc', 'OnSelect', U.OPEN_DOC)
setp('V97EvidenceRaw', 'Default', U.EVIDENCE_RAW)
setp('V97Documents', 'Items', U.DOCUMENTS_ITEMS)
setp('V97DocumentRow', 'Text', U.DOCUMENT_ROW)
setp('V97DocumentRow', 'OnSelect', U.DOCUMENT_ROW_SELECT)
setp('V97DocumentRow', 'Width', '=Parent.TemplateWidth-If(StartsWith(ThisItem.DocId,"EXT-"),64,0)')
clone('V97LinkDelete', 'V97DocumentDelete', {'Text': '="הסר"', 'X': '=Parent.TemplateWidth-60', 'Y': '=2', 'Width': '=58', 'Height': '=31',
      'OnSelect': U.DOCUMENT_DELETE, 'Visible': '=StartsWith(ThisItem.DocId,"EXT-")'}, after='V97DocumentRow')
setp('V97EvidenceHistory', 'OnSelect', U.EVIDENCE_HISTORY)
setp('V97EvidenceReadable', 'OnSelect', U.EVIDENCE_READABLE)
setp('V97EvidenceDetailCard', 'OnSelect', '=Set(varV97ExportText,ThisItem.Heading&Char(10)&ThisItem.Body);Reset(V97Export);Set(varV97BackModal,"evidencedetail");Set(varV97Modal,"copy")')
setp('V97EvidenceDetails', 'TemplateSize', '=170')
setp('V97EvidenceDetailCard', 'Height', '=162')
setp('V97EvidenceSortButton', 'Text', U.EVIDENCE_SORT_TEXT)
setp('V97EvidenceSortButton', 'OnSelect', U.EVIDENCE_SORT_SELECT)
setp('V97EvidenceAdjustment', 'Text', U.EVIDENCE_ADJ)
setp('V97EvidenceFilterattention', 'Text', '="דורש תשומת לב"')
setp('V97EvidenceBaseNote', 'X', '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+215')
setp('V97EvidenceBaseNote', 'Width', '=Max(0,(Min(1160,Parent.Width-16)-52)*0.55-195)')
setp('V97EvidenceBaseNote', 'Visible', '=varV97Ready && !IsBlank(varV97Modal) && varV97Modal="evidence" && Parent.Width>=600')
setp('V97EvidenceBaseNote', 'Text', '="בדיקות המסמך הן מהמקור, לפני התאמות. סימון ידני ושיוך ידני אינם בדיקה מספרית."')

# ------------------------------------------------- links / external docs (B06/B16)
setp('V97ManualLink', 'OnSelect', '=Set(varV97LinkTarget,If(IsBlank(varV97EvidenceKey),"",varV97EvidenceKey));Set(varV97Modal,"links");Reset(V97LinkAccount)')
setp('V97ManualLink', 'Text', '="שיוכים ידניים ומסמכים"')
setp('V97LinkIntro', 'Text', U.LINK_INTRO)
setp('V97LinkAccount', 'Default', '=""')
setp('V97LinkAccount', 'HintText', '="חיפוש יעד: סעיף, מספר חשבון או תיאור"')
setp('V97LinkAccount', 'Width', '=(Min(1160,Parent.Width-16)-52)*0.38')
setp('V97LinkAccount', 'X', '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+20+(Min(1160,Parent.Width-16)-52)*0.62')
setp('V97LinkAccount', 'Y', '=226')
setp('V97LinkAdd', 'OnSelect', U.LINK_ADD)
setp('V97LinkAdd', 'Text', '="שייך מסמך ליעד"')
setp('V97LinkAdd', 'Y', '=164')
setp('V97LinkTargets', 'Items', U.LINK_TARGETS)
setp('V97LinkTargetRow', 'Text', U.LINK_TARGET_ROW)
setp('V97LinkTargetRow', 'OnSelect', U.LINK_TARGET_SELECT)
setp('V97Links', 'Items', U.LINKS_ITEMS)
setp('V97LinkText', 'Text', U.LINK_TEXT)
setp('V97LinkDelete', 'OnSelect', U.LINK_DELETE)
inp = dict(props('V97LinkAccount'))
clone('V97LinkAccount', 'V97ExtDocName', {'X': '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+20', 'Y': '=210', 'Width': '=(Min(1160,Parent.Width-16)-52)*0.28',
      'HintText': '="שם מסמך חיצוני חדש"', 'Default': '=""', 'AccessibleLabel': '="שם מסמך חיצוני חדש"'}, after='V97LinkAdd')
clone('V97LinkAccount', 'V97ExtDocUrl', {'X': '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+26+(Min(1160,Parent.Width-16)-52)*0.28', 'Y': '=210', 'Width': '=(Min(1160,Parent.Width-16)-52)*0.30',
      'HintText': '="כתובת HTTPS של המסמך"', 'Default': '=""', 'AccessibleLabel': '="כתובת HTTPS של המסמך"'}, after='V97ExtDocName')
clone('V97LinkAdd', 'V97ExtDocAdd', {'Text': '="הוסף מסמך חיצוני (ושייך ליעד הנבחר)"', 'X': '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+20+(Min(1160,Parent.Width-16)-52)*0.38',
      'Y': '=164', 'Width': '=(Min(1160,Parent.Width-16)-52)*0.20', 'OnSelect': U.EXT_DOC_ADD}, after='V97ExtDocUrl')
setp('V97LinkAdd', 'Width', '=(Min(1160,Parent.Width-16)-52)*0.20')
setp('V97Links', 'Y', '=256'); setp('V97Links', 'Height', '=Max(60,Parent.Height-320)')
setp('V97LinkTargets', 'Y', '=266'); setp('V97LinkTargets', 'Height', '=Max(60,Parent.Height-330)')
setp('V97LinkText', 'Height', '=42')

# --------------------------------------------------------------- drivers (A01)
setp('V97Drivers', 'Items', U.DRIVERS_ITEMS)
setp('V97DriverText', 'Text', U.DRIVER_TEXT)
setp('V97DriverText', 'OnSelect', U.DRIVER_SELECT)

# ---------------------------------------------------------------- exports
setp('V97ExportView', 'OnSelect', U.EXPORT_VIEW)
setp('V97ExportView', 'Text', '="העתק לאקסל"')
setp('V97Actionbackup', 'OnSelect', '=Set(varV97ExportText,JSON({Version:9,Dataset:varV97Dataset,Entries:colV97Entries,Notes:colV97Notes,Reviews:colV97Reviews,Links:colV97Links,Urls:colV97Urls,Docs:colV97Docs,History:colV97History,Materiality:varV97Materiality,Market:varV97Market},JSONFormat.Compact));Reset(V97Export);Set(varV97Modal,"backup")')
setp('V97ImportConfirmText', 'Text', '="השחזור יחליף את המצב המשותף לכל הצוות (פקודות, הערות, סטטוסים, שיוכים ומסמכים חיצוניים) ויוצר דור מצב חדש. שינויים שנכתבו על בסיס המצב הקודם לא יגברו עליו. האירועים הקודמים נשמרים ביומן. להמשיך?"')

# ------------------------------------------------------------------ FX (B14)
setp('V97Fx', 'Items', U.FX_ITEMS)
setp('V97FxRow', 'Text', U.FX_ROW)

# ------------------------------------------------------ small-screen fixes (B17)
setp('V97AuditChecks', 'X', '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+20+Min(210,(Min(1160,Parent.Width-16)-52)*0.5)+10')
setp('V97AuditChecks', 'Width', '=Min(210,(Min(1160,Parent.Width-16)-52)*0.5)')
setp('V97ExceptionType', 'Width', '=Min(200,(Min(1160,Parent.Width-16)-52)*0.5)')
setp('V97ModalTitle', 'X', '=Max(8,(Parent.Width-Min(1160,Parent.Width-16))/2)+If(Parent.Width>=600,300,60)')
setp('V97ModalTitle', 'Width', '=Min(1160,Parent.Width-16)-If(Parent.Width>=600,328,72)')
setp('V97ModalTitle', 'Y', '=If(Parent.Width>=600,32,26)')
setp('V97ExportView', 'Y', '=If(Parent.Width>=600,32,62)')

# hidden builders for HTML save and all-pages export (B15)
import f_extra as X
clone('V97Checkpoint', 'V97BuildHtml', {'OnSelect': X.BUILD_HTML}, after='V97AuditLogLoad')
clone('V97Checkpoint', 'V97BuildExportAll', {'OnSelect': X.BUILD_EXPORT_ALL}, after='V97BuildHtml')

out = emit.emit(doc)
open(OUT, 'w', encoding='utf-8').write(out)
print('written', OUT, len(out), 'chars', sum(1 for _ in all_ctrls()), 'controls')
