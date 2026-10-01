# -*- coding: utf-8 -*-
"""v9 UI / functional formulas."""
from f_persist import cl

NF = '"#,##0.#"'          # template fmt(): maximumFractionDigits 1
XN = '"0.######"'          # export numbers (raw, invariant)
W = 'V97Background.Width'

def pct_change(c, p):
    # template pctChange()
    return ('With({pc_c:Coalesce(' + c + ',0),pc_p:Coalesce(' + p + ',0)},If(pc_p=0 && pc_c=0,"—",If(pc_p=0,"N/A",'
            'If(pc_c=0,"-100.0%",Text(Round((pc_c-pc_p)/Abs(pc_p)*100,1),"0.0","en-US")&"%"))))')

def fmt(x):
    return 'If(IsBlank(' + x + '),"—",Text(' + x + ',' + NF + ',"he-IL"))'

def xnum(x):
    return 'If(IsBlank(' + x + '),"",Text(' + x + ',' + XN + ',"en-US"))'

REV_SIGN_C = 'With({rs:LookUp(colV97Rows,RowId="pnl_metric_sales")},If(rs.Current>0,1,If(rs.Current<0,-1,If(rs.Prior>0,1,-1))))'
REV_SIGN_P = 'With({rs:LookUp(colV97Rows,RowId="pnl_metric_sales")},If(rs.Prior>0,1,If(rs.Prior<0,-1,If(rs.Current>0,1,-1))))'

# economic change score, template economicChangeClass()
def score(item):
    i = item
    return ('If(' + i + '.Page="pnl",If(' + i + '.RowId="pnl_metric_gross_margin_pct",Coalesce(' + i + '.Current,0)-Coalesce(' + i + '.Prior,0),'
            'If(' + i + '.RowId in ["pnl_r236","pnl_r270","pnl_r289"],With({rr:LookUp(colV97Rows,RowId=Switch(' + i + '.RowId,"pnl_r236","ratios_R01","pnl_r270","ratios_R06","ratios_R07"))},Coalesce(rr.Current,0)-Coalesce(rr.Prior,0)),'
            + REV_SIGN_C + '*Coalesce(' + i + '.Current,0)-' + REV_SIGN_P + '*Coalesce(' + i + '.Prior,0))),Coalesce(' + i + '.Current,0)-Coalesce(' + i + '.Prior,0))')

ROW_COLOR = ('If(ThisItem.RowId="pnl_r205",RGBA(219,227,238,1),If(ThisItem.Page="balance",If(Coalesce(ThisItem.Current,0)>Coalesce(ThisItem.Prior,0),RGBA(111,147,173,1),If(Coalesce(ThisItem.Current,0)<Coalesce(ThisItem.Prior,0),RGBA(196,111,59,1),RGBA(219,227,238,1))),'
             'With({sc:' + score('ThisItem') + '},If(sc>0,RGBA(123,220,84,1),If(sc<0,RGBA(225,107,134,1),RGBA(219,227,238,1))))))')

def kpi(rid, label_expr, idx):
    return ('=' + label_expr + ' & Char(10) & ' + fmt('LookUp(colV97Rows,RowId="' + rid + '",Current)') + ' & Char(10) & '
            + pct_change('LookUp(colV97Rows,RowId="' + rid + '",Current)', 'LookUp(colV97Rows,RowId="' + rid + '",Prior)')
            + ' & With({kc:Coalesce(LookUp(colV97Rows,RowId="' + rid + '",Current),0)-Coalesce(LookUp(colV97Rows,RowId="' + rid + '",Prior),0)},If(kc>0," ↗",If(kc<0," ↘","")))')

def loss_label(rid, profit, loss):
    return 'If(LookUp(colV97Rows,RowId="' + rid + '",Current)<0,"' + loss + '","' + profit + '")'

KPI_TEXT = {
    'V97Kpi0': kpi('ratios_R01', loss_label('ratios_R01', 'רווח גולמי', 'הפסד גולמי'), 0),
    'V97Kpi1': kpi('ratios_R03', '"EBITDA"', 1),
    'V97Kpi2': kpi('ratios_R05', '"הון חוזר"', 2),
    'V97Kpi3': kpi('ratios_R06', loss_label('ratios_R06', 'רווח תפעולי', 'הפסד תפעולי'), 3),
    'V97Kpi4': kpi('ratios_R07', loss_label('ratios_R07', 'רווח נקי', 'הפסד נקי'), 4),
}

ROW_NAME = ('=If(ThisItem.HasChildren,If(ThisItem.RowId in colV97Closed.RowId,"+ ","− "),"• ") & '
            'Switch(ThisItem.RowId,"ratios_R01",' + loss_label('ratios_R01', 'רווח גולמי', 'הפסד גולמי') + ',"ratios_R02","שיעור "&' + loss_label('ratios_R01', 'רווח גולמי', 'הפסד גולמי') +
            ',"ratios_R06",' + loss_label('ratios_R06', 'רווח תפעולי', 'הפסד תפעולי') + ',"ratios_R08","שיעור "&' + loss_label('ratios_R06', 'רווח תפעולי', 'הפסד תפעולי') +
            ',"ratios_R07",' + loss_label('ratios_R07', 'רווח נקי', 'הפסד נקי') + ',"ratios_R09","שיעור "&' + loss_label('ratios_R07', 'רווח נקי', 'הפסד נקי') + ',ThisItem.Name)'
            ' & If(IsBlank(ThisItem.Code),"","  [" & ThisItem.Code & "]") & If(!IsBlank(LookUp(colV97Notes,Key=ThisItem.RowId).Key),"  📝","")'
            ' & If(CountIf(colV97EvidenceItems,Section=ThisItem.RowId)>0,"  ●","")')
ROW_CURRENT = '=If(ThisItem.RowId="pnl_r205","",' + fmt('ThisItem.Current') + ' & If(ThisItem.Unit="%" && !IsBlank(ThisItem.Current),"%",""))'
ROW_PRIOR = '=If(ThisItem.RowId="pnl_r205","",' + fmt('ThisItem.Prior') + ' & If(ThisItem.Unit="%" && !IsBlank(ThisItem.Prior),"%",""))'
ROW_DIFF = ('=If(ThisItem.RowId="pnl_r205","",If(IsBlank(ThisItem.Current) && IsBlank(ThisItem.Prior),"—",Text(Coalesce(ThisItem.Current,0)-Coalesce(ThisItem.Prior,0),' + NF + ',"he-IL"))'
            ' & If(Abs(Coalesce(ThisItem.Current,0)-Coalesce(ThisItem.Prior,0))>=varV97Materiality && !(IsBlank(ThisItem.Current) && IsBlank(ThisItem.Prior))," !",""))')
ROW_PCT = '=If(ThisItem.RowId="pnl_r205","",' + pct_change('ThisItem.Current', 'ThisItem.Prior') + ')'

# B04: copy the population that is on screen
COPY_TABLE = ('=Set(varV97ExportText,If(varV97Page="comparisons",'
              '"יחס"&Char(9)&"קוד"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"שינוי %"&Char(9)&"מטבע"&Char(10)&Concat(V97Comparison.AllItems,'
              + cl('Name') + '&Char(9)&' + cl('Code') + '&Char(9)&' + xnum('Current') + '&Char(9)&' + xnum('Prior') + '&Char(9)&If(IsBlank(Current) && IsBlank(Prior),"",Text(Coalesce(Current,0)-Coalesce(Prior,0),' + XN + ',"en-US"))&Char(9)&' + pct_change('Current', 'Prior') + '&Char(9)&' + cl('Unit') + ',Char(10)),'
              '"סעיף"&Char(9)&"קוד"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"שינוי %"&Char(9)&"מטבע"&Char(10)&Concat(V97Main.AllItems,'
              + cl('Name') + '&Char(9)&' + cl('Code') + '&Char(9)&' + xnum('Current') + '&Char(9)&' + xnum('Prior') + '&Char(9)&If(IsBlank(Current) && IsBlank(Prior),"",Text(Coalesce(Current,0)-Coalesce(Prior,0),' + XN + ',"en-US"))&Char(9)&' + pct_change('Current', 'Prior') + '&Char(9)&' + cl('Unit') + ',Char(10))));'
              'IfError(Copy(varV97ExportText);true,Set(varV97BackModal,"");Set(varV97Modal,"copy");Reset(V97Export);false,Notify("הטבלה הועתקה",NotificationType.Success);true)')

FOOTER = '="שורות בתצוגה: "&CountRows(V97Main.AllItems)&If(!IsBlank(V97Search.Text)," | חיפוש בכל דפי הדוח","")'

COMPARE_NUMBERS = ('="נוכחי: " & ' + fmt('ThisItem.Current') + ' & " | השוואתי: " & ' + fmt('ThisItem.Prior') + ' & " | שינוי: " & ' + pct_change('ThisItem.Current', 'ThisItem.Prior') + ' & " " & ThisItem.Unit')

SETTINGS_TEXT = ('="גמידה פור לייף • 2025 מול 2024"&Char(10)&"השינויים נשמרים לצוות ב-DashboardPOC_Data כאירועים (V97Event9). בשינוי של אותו פריט, השינוי האחרון שנשמר בשרת קובע."&Char(10)&'
                 '"נקודת שחזור (V97Snapshot9) נשמרת בחלקים ונטענת במלואה או נדחית; השינויים שאחריה נטענים בעמודים עד אישור שאין עוד רשומות. אם השלמות אינה מוכחת — הטעינה נעצרת והמצב הפעיל לא מוחלף."&Char(10)&'
                 '"שחזור גיבוי יוצר דור מצב חדש לכל הצוות; שינויים שנכתבו על בסיס דור קודם אינם גוברים עליו. היומן המלא נשמר ברשימה וזמין בכפתור \'יומן שינויים מלא\'."')

# --- drill-down (B01, B18, B19) -------------------------------------------
DRILL_SCOPE = '(d.Section=varV97Section || CountIf(colV97Edges,RowId=d.Section && Ancestor=varV97Section)>0)'
DRILL_ITEMS = ('=With({dr_b:LookUp(colV97Rows,RowId=varV97Section),dr_a:Max(0,IfError(Value(V97Min.Text),0)),dr_p:Max(0,IfError(Value(V97Pct.Text),0)),dr_q:Lower(Trim(V97ModalSearch.Text))},'
               'With({dr_abs:Max(Abs(Coalesce(dr_b.Current,0)),Abs(Coalesce(dr_b.Prior,0)),0.000001)},'
               'With({dr_t:AddColumns(Filter(colV97AllDrill As d,' + DRILL_SCOPE + ' && ((dr_a=0 && dr_p=0) || (dr_a>0 && Max(Abs(Coalesce(d.Current,0)),Abs(Coalesce(d.Prior,0)))>=dr_a) || (dr_p>0 && Max(Abs(Coalesce(d.Current,0)),Abs(Coalesce(d.Prior,0)))/dr_abs*100>=dr_p))'
               ' && (IsBlank(dr_q) || dr_q in Lower(d.Name&" "&d.Account&" "&d.Code&" "&d.Source&" "&If(d.Source="manual_entry",LookUp(colV97Entries,"MANUAL-"&Id=d.Account,Reference),"")))) As d,'
               'SortGroup,If(d.Source="additional_entry",1,0),CurrentSort,Coalesce(d.Current,0))},'
               'Switch(varV97DrillSort,"desc",SortByColumns(dr_t,"SortGroup",SortOrder.Ascending,"CurrentSort",SortOrder.Descending,"Ord",SortOrder.Ascending),'
               '"asc",SortByColumns(dr_t,"SortGroup",SortOrder.Ascending,"CurrentSort",SortOrder.Ascending,"Ord",SortOrder.Ascending),'
               'SortByColumns(dr_t,"SortGroup",SortOrder.Ascending,"Ord",SortOrder.Ascending)))))')

DRILL_ROW = ('=If(ThisItem.Source="manual_entry",Coalesce(LookUp(colV97Entries,"MANUAL-"&Id=ThisItem.Account,Reference),"פקודה ידנית"),ThisItem.Account) & " | " & ThisItem.Name'
             ' & If(ThisItem.Source="manual_entry","  [הוזן ידנית]",If(ThisItem.Source="additional_entry","  [פקודה נוספת]",""))'
             ' & If(!IsBlank(LookUp(colV97Notes,Key=ThisItem.Key).Key),"  📝","") & If(CountIf(colV97EvidenceItems,TargetKey="drill:"&ThisItem.Section&":"&Trim(ThisItem.Account))>0,"  ●","") & Char(10)'
             ' & ' + fmt('ThisItem.Current') + ' & "  מול  " & ' + fmt('ThisItem.Prior') + ' & " | הפרש: " & Text(Coalesce(ThisItem.Current,0)-Coalesce(ThisItem.Prior,0),' + NF + ',"he-IL") & " | " & ' + pct_change('ThisItem.Current', 'ThisItem.Prior'))
DRILL_ROW_SELECT = '=Set(varV97NoteKey,ThisItem.Key);Reset(V97Note);Set(varV97DetailText,ThisItem.Detail);Set(varV97SelectedAccount,ThisItem.Account)'

DRILL_RECON = ('=With({r:LookUp(colV97Rows,RowId=varV97Section),all:Filter(colV97AllDrill As d,' + DRILL_SCOPE + '),shown:V97Drill.AllItems},'
               'With({sc:Sum(all,Coalesce(Current,0)),sp:Sum(all,Coalesce(Prior,0))},'
               'If(IsEmpty(all),"אין פירוט זמין לסעיף "&r.Name,'
               'varV97Date&": יתרת הסעיף "&Text(Coalesce(r.Current,0),' + NF + ',"he-IL")&" | סה״כ Drill-down "&Text(sc,' + NF + ',"he-IL")&" | "&If(Abs(Coalesce(r.Current,0)-sc)<=0.005,"✓ תקין","⚠ הפרש לא מוסבר: "&Text(Coalesce(r.Current,0)-sc,' + NF + ',"he-IL"))&Char(10)&'
               'varV97PriorDate&": יתרת הסעיף "&Text(Coalesce(r.Prior,0),' + NF + ',"he-IL")&" | סה״כ Drill-down "&Text(sp,' + NF + ',"he-IL")&" | "&If(Abs(Coalesce(r.Prior,0)-sp)<=0.005,"✓ תקין","⚠ הפרש לא מוסבר: "&Text(Coalesce(r.Prior,0)-sp,' + NF + ',"he-IL"))&Char(10)&'
               'CountRows(shown)&" מתוך "&CountRows(all)&" שורות | סה״כ מוצג: "&Text(Sum(shown,Coalesce(Current,0)),' + NF + ',"he-IL")&" מול "&Text(Sum(shown,Coalesce(Prior,0)),' + NF + ',"he-IL"))))')

DRILL_SORT_TEXT = '="מיון: "&Switch(varV97DrillSort,"desc","מסכום גבוה לנמוך","asc","מסכום נמוך לגבוה","סדר מקורי")'
DRILL_SORT_SELECT = '=Set(varV97DrillSort,Switch(varV97DrillSort,"original","desc","desc","asc","original"))'

MIN_LABEL = '=If(varV97Modal="drill","הצג שורות מסכום של","שינוי מזערי")'
PCT_LABEL = '=If(varV97Modal="drill","או מאחוז מתוך הסעיף","אחוז מזערי")'

NOTE_LABEL = ('With({nk:%K%},If(StartsWith(nk,"MANUAL|"),"פקודה ידנית: "&Coalesce(LookUp(colV97Entries,Id=Mid(nk,8,Find("|",nk,8)-8),Description),nk)&If(EndsWith(nk,"|D")," (חובה)"," (זכות)"),'
              'If(!IsBlank(LookUp(colV97Rows,RowId=nk).RowId),"סעיף: "&LookUp(colV97Rows,RowId=nk,Name),If(!IsBlank(LookUp(colV97Drill,Key=nk).Key),"שורת Drill-down: "&LookUp(colV97Drill,Key=nk,Account)&" — "&LookUp(colV97Drill,Key=nk,Name)&" ("&LookUp(colV97Rows,RowId=LookUp(colV97Drill,Key=nk,Section),Name)&")",nk))))')
NOTE_TARGET = '="יעד הערה: " & If(IsBlank(varV97NoteKey),"בחר שורה",' + NOTE_LABEL.replace('%K%', 'varV97NoteKey') + ')'
NOTES_ROW = '=' + NOTE_LABEL.replace('%K%', 'ThisItem.Key') + ' & Char(10) & ThisItem.Text'
NOTES_ITEMS = '=Filter(colV97Notes As n,IsBlank(V97ModalSearch.Text) || Lower(V97ModalSearch.Text) in Lower(n.Key & " " & n.Text & " " & ' + NOTE_LABEL.replace('%K%', 'n.Key') + '))'

BUSY = 'Notify("המתן לסיום הסנכרון או רענן מהצוות",NotificationType.Warning)'

NOTE_APPLY = ('=If(varV97RemoteReady && !varV97Syncing,If(IsBlank(varV97NoteKey),Notify("בחר יעד להערה",NotificationType.Warning),'
              'Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Notes",Key:varV97NoteKey,Deleted:IsBlank(Trim(V97Note.Text)),Payload:JSON({Key:varV97NoteKey,Text:V97Note.Text,At:Text(Now(),DateTimeFormat.UTC)},JSONFormat.Compact)});Select(V97WriteEvent)),' + BUSY + ')')

PERSIST_ALL = ('=If(varV97RemoteReady && !varV97Syncing,Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Settings",Key:"settings",Deleted:false,Payload:JSON({Materiality:varV97Materiality,Market:varV97Market},JSONFormat.Compact)});Select(V97WriteEvent),' + BUSY + ')')

POST = ('=If(varV97RemoteReady && !varV97Syncing,With({a:IfError(Value(V97Amount.Text),Blank()),de:LookUp(colV97Base,RowId=varV97Debit),cr:LookUp(colV97Base,RowId=varV97Credit)},If(IsBlank(a) || a<=0 || a>1000000000000 || IsBlank(Trim(V97Description.Text)) || !de.CanPost || !cr.CanPost || IsBlank(varV97Debit) || IsBlank(varV97Credit) || varV97Debit=varV97Credit,Notify("נדרשים סכום חיובי, תיאור ושני סעיפים שונים",NotificationType.Error),'
        'With({cash:a*(If(de.Cash,1,0)-If(cr.Cash,1,0))},If(cash<>0 && varV97Flow="noncash",Notify("פקודה המשנה מזומן חייבת סיווג פעילות",NotificationType.Error),'
        'With({id:Text(GUID()),at:Text(Now(),DateTimeFormat.UTC)},Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Entries",Key:id,Deleted:false,Payload:JSON({Id:id,Debit:varV97Debit,Credit:varV97Credit,Amount:a,Description:Trim(V97Description.Text),Reference:Trim(V97Reference.Text),Flow:varV97Flow,CashDelta:cash,At:at},JSONFormat.Compact)});Select(V97WriteEvent)))))),' + BUSY + ')')

# A05: delete entry together with everything that depends on it (one logical operation)
DELETE_ENTRY = ('=If(varV97RemoteReady && !varV97Syncing,If(IsBlank(LookUp(colV97Entries,Id=varV97DeleteId).Id),Notify("הפקודה כבר אינה קיימת",NotificationType.Warning);Set(varV97Modal,"additional"),'
                'Set(varV97Syncing,true);'
                'ClearCollect(colV97Batch,{Entity:"Entries",Key:varV97DeleteId,Deleted:true,Payload:JSON({Id:varV97DeleteId},JSONFormat.Compact)});'
                'Collect(colV97Batch,ForAll(Filter(colV97Links,Account="MANUAL-"&varV97DeleteId) As l,{Entity:"Links",Key:l.Key,Deleted:true,Payload:JSON({Key:l.Key},JSONFormat.Compact)}));'
                'Collect(colV97Batch,ForAll(Filter(colV97Notes,Key="MANUAL|"&varV97DeleteId&"|D" || Key="MANUAL|"&varV97DeleteId&"|C") As n,{Entity:"Notes",Key:n.Key,Deleted:true,Payload:JSON({Key:n.Key},JSONFormat.Compact)}));'
                'Collect(colV97Batch,ForAll(Filter(colV97Reviews,EndsWith(Key,":MANUAL-"&varV97DeleteId)) As r,{Entity:"Reviews",Key:r.Key,Deleted:true,Payload:JSON({Key:r.Key},JSONFormat.Compact)}));'
                'Set(varV97Modal,"additional");Select(V97WriteEvent)),' + BUSY + ')')

# --- evidence center (B05, B07) --------------------------------------------
STATUS_LABEL = 'Switch(%S%,"match","תואם","gap","פער","unable","לא ניתן לבדוק","activity","ראיה לפעילות","manualAssigned","שויך ידנית","handled","טופל","needsAction","דורש טיפול","—")'
STATUS_ICON = 'Switch(%S%,"handled","✓","needsAction","⬢","manualAssigned","+","●")'
def status_label(s):
    return STATUS_LABEL.replace('%S%', s)

EVIDENCE_ITEMS = ('=With({ev_q:Lower(Trim(V97ModalSearch.Text))},With({ev_t:Filter(AddColumns(colV97EvidenceTargets As m,EffectiveStatus,Coalesce(LookUp(colV97Reviews,Key=m.TargetKey,Status),m.AutoStatus)) As e,'
                  '(IsBlank(ev_q) || ev_q in Lower(e.Hay)) && Switch(varV97EvidenceFilter,"attention",e.EffectiveStatus in ["gap","unable","needsAction"],"handled",e.EffectiveStatus="handled","section",e.Section=varV97Section,true))},'
                  'Switch(varV97EvidenceSort,"desc",SortByColumns(ev_t,"SortAmount",SortOrder.Descending,"Ord",SortOrder.Ascending),"asc",SortByColumns(ev_t,"SortAmount",SortOrder.Ascending,"Ord",SortOrder.Ascending),SortByColumns(ev_t,"Ord",SortOrder.Ascending))))')
EVIDENCE_ROW = ('=ThisItem.SectionLabel & " | " & ThisItem.Desc & " | " & ThisItem.Code & Char(10) & ' + fmt('ThisItem.Current') + ' & " מול " & ' + fmt('ThisItem.Prior')
                + ' & " | הפרש " & Text(Coalesce(ThisItem.Current,0)-Coalesce(ThisItem.Prior,0),' + NF + ',"he-IL") & " | " & ' + pct_change('ThisItem.Current', 'ThisItem.Prior')
                + ' & Char(10) & ' + STATUS_ICON.replace('%S%', 'ThisItem.EffectiveStatus') + ' & " " & ' + status_label('ThisItem.EffectiveStatus') + ' & " · " & ThisItem.Count & If(ThisItem.Count=1," ראיה"," ראיות") & " · " & ThisItem.Level')
EVIDENCE_ROW_SELECT = ('=Set(varV97EvidenceKey,ThisItem.TargetKey);Set(varV97Doc,First(SortByColumns(Filter(colV97EvidenceItems,TargetKey=ThisItem.TargetKey),"Ord",SortOrder.Ascending)).DocId);'
                       'Set(varV97Section,ThisItem.Section);Set(varV97EvidenceDetail,"");Reset(V97EvidenceNote);Reset(V97EvidenceUrl);Reset(V97EvidenceRaw)')
EVIDENCE_SELECTED = ('=If(IsBlank(varV97EvidenceKey),Coalesce(LookUp(colV97AllDocs,DocId=varV97Doc,Name),"בחר יעד ראיה או מסמך"),'
                     'With({t:LookUp(colV97EvidenceTargets,TargetKey=varV97EvidenceKey)},t.SectionLabel&" | "&t.Desc&" | "&t.Code&Char(10)&"סטטוס: "&' + status_label('Coalesce(LookUp(colV97Reviews,Key=varV97EvidenceKey,Status),t.AutoStatus)') + '&If(IsBlank(LookUp(colV97Reviews,Key=varV97EvidenceKey).Key),""," (סומן ידנית)")&" · מסמך פעיל: "&Coalesce(LookUp(colV97AllDocs,DocId=varV97Doc,Name),"—")))')
EVIDENCE_NOTE_DEFAULT = '=Coalesce(LookUp(colV97Reviews,Key=varV97EvidenceKey,Note),"")'

def review(status, label):
    if status == 'auto':
        guard = 'IsBlank(LookUp(colV97Reviews,Key=varV97EvidenceKey).Key)'
        guard_msg = 'Notify("אין סימון ידני ליעד זה",NotificationType.Information)'
        action = ('ClearCollect(colV97Batch,{Entity:"Reviews",Key:varV97EvidenceKey,Deleted:true,Payload:JSON({Key:varV97EvidenceKey},JSONFormat.Compact)});')
    else:
        guard = 'false'
        guard_msg = 'false'
        action = ('ClearCollect(colV97Batch,{Entity:"Reviews",Key:varV97EvidenceKey,Deleted:false,Payload:JSON({Key:varV97EvidenceKey,Status:"' + status + '",Note:V97EvidenceNote.Text,At:Text(Now(),DateTimeFormat.UTC)},JSONFormat.Compact)});')
    return ('=If(varV97RemoteReady && !varV97Syncing,If(IsBlank(LookUp(colV97EvidenceTargets,TargetKey=varV97EvidenceKey).TargetKey),Notify("בחר יעד ראיה ברשימה",NotificationType.Warning),If(' + guard + ',' + guard_msg + ','
            'Set(varV97Syncing,true);' + action +
            'With({hid:Text(GUID())},Collect(colV97Batch,{Entity:"History",Key:hid,Deleted:false,Payload:JSON({Id:hid,Key:varV97EvidenceKey,Action:"' + label + '"&If(IsBlank(Trim(V97EvidenceNote.Text)),""," · "&Trim(V97EvidenceNote.Text)),At:Text(Now(),DateTimeFormat.UTC),User:User().FullName},JSONFormat.Compact)}));'
            'Select(V97WriteEvent))),' + BUSY + ')')

REVIEW = {
    'V97Review0': ('="✓ סמן כטופל"', review('handled', 'טופל')),
    'V97Review1': ('="⬢ דורש טיפול"', review('needsAction', 'דורש טיפול')),
    'V97Review2': ('="↩ חזרה לאוטומטי"', review('auto', 'בוטל הסימון הידני — חזרה לסטטוס האוטומטי')),
}

URL_DEFAULT = '=Coalesce(LookUp(colV97Urls,DocId=varV97Doc,Url),LookUp(colV97AllDocs,DocId=varV97Doc,Url),"")'
SET_URL = ('=If(varV97RemoteReady && !varV97Syncing,If(IsBlank(LookUp(colV97AllDocs,DocId=varV97Doc).DocId) || !StartsWith(Lower(Trim(V97EvidenceUrl.Text)),"https://"),Notify("בחר מסמך והזן כתובת HTTPS מלאה",NotificationType.Error),'
           'Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Urls",Key:varV97Doc,Deleted:false,Payload:JSON({DocId:varV97Doc,Url:Trim(V97EvidenceUrl.Text)},JSONFormat.Compact)});Select(V97WriteEvent)),' + BUSY + ')')
OPEN_DOC = ('=With({u:Coalesce(LookUp(colV97Urls,DocId=varV97Doc,Url),LookUp(colV97AllDocs,DocId=varV97Doc,Url))},If(StartsWith(Lower(u),"https://"),IfError(Launch(u),Notify("לא ניתן לפתוח את הקישור",NotificationType.Error)),Notify("לא הוגדר קישור HTTPS למסמך הזה",NotificationType.Warning)))')

def amt(x, cur):
    return 'If(IsBlank(' + x + '),"—",Text(' + x + ',' + NF + ',"he-IL")&If(IsBlank(' + cur + '),""," "&' + cur + '))'

EVIDENCE_RAW = ('=If(IsBlank(varV97EvidenceKey),If(IsBlank(varV97Doc),"","מסמך: "&LookUp(colV97AllDocs,DocId=varV97Doc,Name)&Char(10)&LookUp(colV97AllDocs,DocId=varV97Doc,Type)&Char(10)&"יעדים: "&Coalesce(Concat(Distinct(Filter(colV97EvidenceItems,DocId=varV97Doc),TargetKey),Value,", "),"אין")&Char(10)&"לפרטים מלאים: \'פרטי ראיה מסודרים\'"),'
                'Concat(SortByColumns(Filter(colV97EvidenceItems,TargetKey=varV97EvidenceKey),"Ord",SortOrder.Ascending) As i,'
                '"▸ "&i.FileName&If(IsBlank(i.Meta),""," | "&i.Meta)&Char(10)&"סטטוס: "&' + status_label('i.StatusKey') + '&Char(10)&"ראיה: "&' + amt('i.DocAmount', 'i.Currency') + '&" | דשבורד: "&' + amt('i.BookAmount', 'i.Currency') + '&" | פער: "&' + amt('i.Difference', 'i.Currency') +
                '&If(IsBlank(i.Reason),"",Char(10)&i.Reason)&If(IsBlank(i.Note),"",Char(10)&i.Note)&If(IsBlank(i.Evidence),"",Char(10)&i.Evidence),Char(10)&Char(10))'
                '&With({hh:Filter(colV97History,Key=varV97EvidenceKey)},If(IsEmpty(hh),"",Char(10)&Char(10)&"היסטוריית טיפול:"&Char(10)&Concat(SortByColumns(hh,"At",SortOrder.Ascending),At&" — "&Action&If(IsBlank(User),""," · "&User),Char(10)))))')

DOCUMENTS_ITEMS = ('=SortByColumns(AddColumns(Filter(colV97AllDocs As x,IsBlank(V97ModalSearch.Text) || Lower(V97ModalSearch.Text) in Lower(x.Name & " " & x.DocId & " " & x.Type)) As x,InTarget,If(!IsBlank(varV97EvidenceKey) && !IsBlank(LookUp(colV97EvidenceItems,TargetKey=varV97EvidenceKey && DocId=x.DocId).DocId),0,1)),"InTarget",SortOrder.Ascending)')
DOCUMENT_ROW = '=If(ThisItem.InTarget=0,"● ","") & ThisItem.DocId & " | " & ThisItem.Name & If(StartsWith(ThisItem.DocId,"EXT-"),"  [צורף ידנית]","")'
DOCUMENT_ROW_SELECT = '=Set(varV97Doc,ThisItem.DocId);Set(varV97EvidenceDetail,ThisItem.Detail);Reset(V97EvidenceRaw);Reset(V97EvidenceUrl);Reset(V97EvidenceNote)'
DOCUMENT_DELETE = ('=If(varV97RemoteReady && !varV97Syncing,Set(varV97Syncing,true);'
                   'ClearCollect(colV97Batch,{Entity:"Docs",Key:ThisItem.DocId,Deleted:true,Payload:JSON({DocId:ThisItem.DocId},JSONFormat.Compact)});'
                   'Collect(colV97Batch,ForAll(Filter(colV97Links,DocId=ThisItem.DocId) As l,{Entity:"Links",Key:l.Key,Deleted:true,Payload:JSON({Key:l.Key},JSONFormat.Compact)}));'
                   'If(!IsBlank(LookUp(colV97Urls,DocId=ThisItem.DocId).DocId),Collect(colV97Batch,{Entity:"Urls",Key:ThisItem.DocId,Deleted:true,Payload:JSON({DocId:ThisItem.DocId},JSONFormat.Compact)}));'
                   'If(varV97Doc=ThisItem.DocId,Set(varV97Doc,""));Select(V97WriteEvent),' + BUSY + ')')

EVIDENCE_HISTORY = ('=Set(varV97ExportText,"זמן"&Char(9)&"משתמש"&Char(9)&"יעד"&Char(9)&"פעולה"&Char(10)&Concat(SortByColumns(Filter(colV97History,IsBlank(varV97EvidenceKey) || Key=varV97EvidenceKey),"At",SortOrder.Ascending),'
                    + cl('At') + '&Char(9)&' + cl('User') + '&Char(9)&' + cl('Key') + '&Char(9)&' + cl('Action') + ',Char(10)));Reset(V97Export);Set(varV97BackModal,"evidence");Set(varV97Modal,"copy")')

def kv(label, expr):
    return 'If(IsBlank(' + expr + '),"",Char(10)&"' + label + ': "&' + expr + ')'

def t(x):
    return 'IfError(Text(' + x + '),"")'

DETAIL_ITEM = ('t_i.Value', )
EVIDENCE_READABLE = ('=If(IsBlank(varV97Doc) && IsBlank(varV97EvidenceKey),Notify("בחר מסמך או יעד ראיה",NotificationType.Warning),'
    'With({d:IfError(ParseJSON(LookUp(colV97AllDocs,DocId=varV97Doc,Detail)),ParseJSON("{}"))},'
    'ClearCollect(colV97EvidenceDetails,{Heading:"מסמך וסיווג",Body:' + t('d.fileName') + '&' + kv('סוג', t('d.documentType')) + '&' + kv('תאריך', t('d.documentDate')) + '&' + kv('קטגוריה', t('d.documentCategory')) + '&' + kv('סטטוס סיווג', t('d.classificationStatus')) + '&' + kv('הערת סיווג', t('d.classificationNote')) + '&' + kv('קישור', 'Coalesce(LookUp(colV97Urls,DocId=varV97Doc,Url),' + t('d.documentUrl') + ')') + '});'
    'Collect(colV97EvidenceDetails,{Heading:"נתונים שחולצו מהמסמך",Body:"ישות: "&' + t('d.extractedData.entityName') + '&' + kv('מזהה', t('d.extractedData.identifier')) + '&' + kv('חשבון', t('d.extractedData.accountNumber')) + '&' + kv('הלוואה', t('d.extractedData.loanNumber')) + '&' + kv('מטבע', t('d.extractedData.currency')) + '&' + kv('תיאור', t('d.extractedData.description')) + '&Char(10)&"פריטים שחולצו: "&IfError(Text(CountRows(Table(d.extractedItems))),"0")});'
    'IfError(Collect(colV97EvidenceDetails,ForAll(Table(d.extractedItems) As x,{Heading:"פריט שחולץ · "&' + t('x.Value.extractedItemId') + ',Body:' + t('x.Value.description') + '&Char(10)&"סכום: "&Coalesce(' + t('x.Value.sourceAmount') + ',' + t('x.Value.amount') + ')&" "&Coalesce(' + t('x.Value.sourceCurrency') + ',' + t('x.Value.currency') + ')&' + kv('תאריך', t('x.Value.date')) + '&' + kv('מזהה', t('x.Value.identifier')) + '}));true,false);'
    'If(IsBlank(d.unmatchedExtractedItems) || IfError(CountRows(Table(d.unmatchedExtractedItems)),0)=0,Collect(colV97EvidenceDetails,{Heading:"פריטים שלא נמצאה להם התאמה",Body:"אין"}),'
    'Collect(colV97EvidenceDetails,ForAll(Table(d.unmatchedExtractedItems) As x,{Heading:"פריט ללא התאמה · "&' + t('x.Value.extractedItemId') + ',Body:' + t('x.Value.description') + '&Char(10)&"סכום: "&' + t('x.Value.amount') + '&" "&' + t('x.Value.currency') + '&' + kv('תאריך', t('x.Value.date')) + '&' + kv('מזהה', t('x.Value.identifier')) + '&' + kv('סיבה', t('x.Value.reasonNotMatched')) + '})));'
    'If(IsBlank(d.groupChecks) || IfError(CountRows(Table(d.groupChecks)),0)=0,Collect(colV97EvidenceDetails,{Heading:"בדיקות קבוצתיות",Body:"לא סופקו בדיקות קבוצתיות"}),'
    'Collect(colV97EvidenceDetails,ForAll(Table(d.groupChecks) As x,{Heading:"בדיקה קבוצתית · "&' + t('x.Value.groupCheckId') + ',Body:' + t('x.Value.description') + '&' + kv('מטרה', t('x.Value.checkPurpose')) + '&' + kv('סטטוס', t('x.Value.status')) + '&' + kv('סכום מסמך', t('x.Value.documentAmount')) + '&' + kv('סכום דשבורד', t('x.Value.jsonAmount')) + '&' + kv('הפרש', t('x.Value.difference')) + '&' + kv('שלמות', t('x.Value.completenessStatus')) + '&' + kv('הערת שלמות', t('x.Value.completenessNote')) + '&' + kv('הערה', t('x.Value.note')) + '&' + kv('סיבה שלא ניתן לאמת', t('x.Value.notVerifiableReason')) + '})));'
    'Collect(colV97EvidenceDetails,{Heading:"פירוט היעד הנבחר",Body:If(IsBlank(varV97EvidenceKey),"בחר יעד במרכז הראיות",V97EvidenceRaw.Text)});'
    'Collect(colV97EvidenceDetails,{Heading:"כל הנתונים שנשמרו (JSON) — לחיצה מעתיקה",Body:LookUp(colV97AllDocs,DocId=varV97Doc,Detail)}));'
    'Set(varV97BackModal,"evidence");Set(varV97Modal,"evidencedetail"))')

EVIDENCE_SORT_TEXT = '="מיון: "&Switch(varV97EvidenceSort,"desc","מסכום גבוה לנמוך","asc","מסכום נמוך לגבוה","סדר מקורי")'
EVIDENCE_SORT_SELECT = '=Set(varV97EvidenceSort,Switch(varV97EvidenceSort,"original","desc","desc","asc","original"))'
EVIDENCE_ADJ = '="התאמות לסעיף מאז מקור הראיה: " & With({adj:Sum(Filter(colV97Rows,RowId=varV97Section),Current-Base)},If(IsBlank(adj),"—",Text(adj,' + NF + ',"he-IL")))'

# --- manual links / external documents (B06, B16) ---------------------------
LINK_TARGETS = ('=Filter(colV97LinkTargetsAll As x,IsBlank(Trim(V97LinkAccount.Text)) || Lower(Trim(V97LinkAccount.Text)) in Lower(x.Label))')
LINK_TARGET_ROW = '=ThisItem.Label & If(ThisItem.TargetKey=varV97LinkTarget,"  ✓","")'
LINK_TARGET_SELECT = '=Set(varV97LinkTarget,ThisItem.TargetKey)'
LINK_INTRO = ('="מסמך: "&Coalesce(LookUp(colV97AllDocs,DocId=varV97Doc,Name),"לא נבחר")&Char(10)&"יעד: "&Coalesce(LookUp(colV97LinkTargetsAll,TargetKey=varV97LinkTarget,Label),"בחר חשבון / סעיף מהרשימה")&Char(10)&"שיוך ידני אינו בדיקה מספרית וניתן להסרה בכל עת."')
LINK_ADD = ('=If(varV97RemoteReady && !varV97Syncing,With({tg:LookUp(colV97LinkTargetsAll,TargetKey=varV97LinkTarget)},'
            'If(IsBlank(LookUp(colV97AllDocs,DocId=varV97Doc).DocId) || IsBlank(tg.TargetKey),Notify("בחר מסמך ויעד שיוך מהרשימה",NotificationType.Error),'
            'If(!IsBlank(LookUp(colV97EvidenceItems,TargetKey=tg.TargetKey && DocId=varV97Doc).DocId),Notify("המסמך כבר משויך ליעד זה",NotificationType.Information),'
            'Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Links",Key:tg.TargetKey&"|"&varV97Doc,Deleted:false,Payload:JSON({Key:tg.TargetKey&"|"&varV97Doc,TargetKey:tg.TargetKey,DocId:varV97Doc,Section:tg.Section,Account:tg.Account,Name:tg.Name},JSONFormat.Compact)});Select(V97WriteEvent)))),' + BUSY + ')')
LINKS_ITEMS = '=Filter(colV97Links,IsBlank(varV97Doc) || DocId=varV97Doc || TargetKey=varV97LinkTarget)'
LINK_TEXT = '=ThisItem.DocId & " | " & Coalesce(LookUp(colV97AllDocs,DocId=ThisItem.DocId,Name),"") & Char(10) & Coalesce(LookUp(colV97LinkTargetsAll,TargetKey=ThisItem.TargetKey,Label),ThisItem.TargetKey)'
LINK_DELETE = ('=If(varV97RemoteReady && !varV97Syncing,Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Links",Key:ThisItem.Key,Deleted:true,Payload:JSON({Key:ThisItem.Key},JSONFormat.Compact)});Select(V97WriteEvent),' + BUSY + ')')
EXT_DOC_ADD = ('=If(varV97RemoteReady && !varV97Syncing,With({nm:Trim(V97ExtDocName.Text),u:Trim(V97ExtDocUrl.Text),id:"EXT-"&Text(GUID())},'
               'If(IsBlank(nm) || !StartsWith(Lower(u),"https://"),Notify("הזן שם מסמך וכתובת HTTPS מלאה",NotificationType.Error),'
               'If(!IsBlank(LookUp(colV97AllDocs,Lower(Url)=Lower(u)).DocId),Notify("מסמך עם כתובת זו כבר קיים",NotificationType.Warning),'
               'Set(varV97Syncing,true);ClearCollect(colV97Batch,{Entity:"Docs",Key:id,Deleted:false,Payload:JSON({DocId:id,Name:nm,Url:u,At:Text(Now(),DateTimeFormat.UTC)},JSONFormat.Compact)});'
               'With({tg:LookUp(colV97LinkTargetsAll,TargetKey=varV97LinkTarget)},If(!IsBlank(tg.TargetKey),Collect(colV97Batch,{Entity:"Links",Key:tg.TargetKey&"|"&id,Deleted:false,Payload:JSON({Key:tg.TargetKey&"|"&id,TargetKey:tg.TargetKey,DocId:id,Section:tg.Section,Account:tg.Account,Name:tg.Name},JSONFormat.Compact)})));'
               'Set(varV97Doc,id);Select(V97WriteEvent)))),' + BUSY + ')')

# --- profit drivers (A01) ---------------------------------------------------
DRIVERS_ITEMS = ('=FirstN(SortByColumns(AddColumns(Filter(AddColumns(Filter(colV97AllDrill As d,CountIf(colV97Effects,Target=varV97DriverTarget && Source=d.Section)>0 && !LookUp(colV97Base,RowId=d.Section,HasChildren)) As d,'
                 'Impact,With({c:Upper(Coalesce(LookUp(colV97Rows,RowId=d.Section,Code),"")),n:Coalesce(LookUp(colV97Rows,RowId=d.Section,Name),""),mult:' + REV_SIGN_C + ',cur:Coalesce(d.Current,0),cmp:Coalesce(d.Prior,0)},'
                 'If(StartsWith(c,"T") || (IsMatch(n,"הכנס",MatchOptions.Contains) && !IsMatch(n,"הוצא",MatchOptions.Contains)),Abs(cur)-Abs(cmp),'
                 'If(StartsWith(c,"U") || StartsWith(c,"V") || StartsWith(c,"W") || IsMatch(n,"עלות|הוצא|מסים על ההכנסה",MatchOptions.Contains),-(Abs(cur)-Abs(cmp)),mult*(cur-cmp)))),'
                 'ParentName,Coalesce(LookUp(colV97Rows,RowId=d.Section,Name),d.Section)),Abs(Impact)>=0.005) As x,Magnitude,Abs(x.Impact)),"Magnitude",SortOrder.Descending),5)')
DRIVER_TEXT = '=If(IsBlank(ThisItem.Account),"",ThisItem.Account&" — ")&ThisItem.Name&Char(10)&ThisItem.ParentName&" | "&If(ThisItem.Impact>0,"שיפור ","פגיעה ")&Text(Abs(ThisItem.Impact),' + NF + ',"he-IL")'
DRIVER_SELECT = '=Set(varV97Section,ThisItem.Section);Set(varV97NoteKey,ThisItem.Key);Set(varV97DetailText,ThisItem.Detail);Reset(V97Note);Set(varV97BackModal,"drivers");Set(varV97Modal,"drill");Reset(V97Min);Reset(V97Pct)'

# --- exports (A02, B02, B03, B20) -------------------------------------------
def tsv(*cols):
    return '&Char(9)&'.join(cols)

EXPORT_VIEW = ('=Set(varV97ExportText,Switch(varV97Modal,\n'
  '  "drill",' + cl('LookUp(colV97Rows,RowId=varV97Section,Name)') + '&Char(10)&"תיאור חשבון"&Char(9)&"קוד חשבון"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"שינוי %"&Char(9)&"מטבע"&Char(9)&"מקור"&Char(10)&Concat(V97Drill.AllItems,'
  + tsv(cl('Name'), cl('If(Source="manual_entry",Coalesce(LookUp(colV97Entries,"MANUAL-"&Id=Account,Reference),"פקודה ידנית"),Account)'), xnum('Current'), xnum('Prior'), 'Text(Coalesce(Current,0)-Coalesce(Prior,0),' + XN + ',"en-US")', pct_change('Current', 'Prior'), 'varV97Unit', 'Switch(Source,"trial_balance","מאזן בוחן","additional_entry","פקודה נוספת","manual_entry","פקודה ידנית",Source)')
  + ',Char(10))&Char(10)&With({tc:Sum(V97Drill.AllItems,Coalesce(Current,0)),tp:Sum(V97Drill.AllItems,Coalesce(Prior,0))},"סה״כ"&Char(9)&""&Char(9)&Text(tc,' + XN + ',"en-US")&Char(9)&Text(tp,' + XN + ',"en-US")&Char(9)&Text(tc-tp,' + XN + ',"en-US")&Char(9)&' + pct_change('tc', 'tp') + '&Char(9)&varV97Unit&Char(9)&""),\n'
  '  "evidence","סעיף"&Char(9)&"תיאור חשבון"&Char(9)&"קוד חשבון"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"שינוי %"&Char(9)&"מטבע"&Char(9)&"סטטוס ראיות"&Char(9)&"מספר ראיות"&Char(9)&"רמת שיוך"&Char(9)&"מסמכים"&Char(10)&Concat(V97Evidence.AllItems,'
  + tsv(cl('SectionLabel'), cl('Desc'), cl('Code'), xnum('Current'), xnum('Prior'), 'Text(Coalesce(Current,0)-Coalesce(Prior,0),' + XN + ',"en-US")', pct_change('Current', 'Prior'), cl('Currency'), status_label('EffectiveStatus'), 'Text(Count)', cl('Level'), cl('Files'))
  + ',Char(10)),\n'
  '  "additional","סוג"&Char(9)&"סעיף"&Char(9)&"פקודה"&Char(9)&"חשבון / אסמכתא"&Char(9)&varV97Date&Char(9)&"צד"&Char(9)&"מול מה נרשם"&Char(9)&"סיווג תזרים"&Char(9)&"תאריך"&Char(9)&"סטטוס"&Char(10)&'
  'Concat(V97Journal.AllItems,' + tsv('"הוזן ידנית"', cl('LookUp(colV97Rows,RowId=Debit,Name)&" / "&LookUp(colV97Rows,RowId=Credit,Name)'), cl('Description'), cl('Coalesce(Reference,"פקודה ידנית")'), xnum('Amount'), '"חובה/זכות"', cl('"חובה: "&LookUp(colV97Rows,RowId=Debit,Name)&" | זכות: "&LookUp(colV97Rows,RowId=Credit,Name)'), 'Switch(Flow,"operating","שוטפת","investing","השקעה","financing","מימון","noncash","ללא מזומן",Flow)', cl('At'), '"הוזן ידנית"') + ',Char(10))'
  '&If(varV97EntryFilter="all" && !IsEmpty(V97Journal.AllItems) && !IsEmpty(V97SourceEntries.AllItems),Char(10),"")'
  '&If(varV97EntryFilter="all",Concat(V97SourceEntries.AllItems,' + tsv('"פקודה נוספת"', cl('LookUp(colV97Rows,RowId=Section,Name)'), cl('Name'), cl('Account'), xnum('Current'), 'Switch(Side,"debit","חובה","credit","זכות",Side)', cl('IfError(Concat(Table(ParseJSON(Detail).counterparties),Coalesce(Text(ThisRecord.Value.desc),Text(ThisRecord.Value.name),"")&" "&Coalesce(Text(ThisRecord.Value.account),Text(ThisRecord.Value.code),"")&" "&Text(ThisRecord.Value.amount)," ; "),"")'), '""', '""', 'IfError(If(Text(ParseJSON(Detail).counterpartyStatus)="not_identified","צד נגדי לא זוהה",If(Text(ParseJSON(Detail).counterpartyStatus)="unbalanced","זוהה — דורש בדיקת איזון","זוהה")),"")') + ',Char(10)),""),\n'
  '  "exceptions","סעיף"&Char(9)&"חשבון"&Char(9)&"תיאור"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"סוגי חריגה"&Char(10)&Concat(V97Analysis.AllItems,'
  + tsv(cl('Section'), cl('Account'), cl('Name'), xnum('Current'), xnum('Prior'), xnum('Delta'), cl('Tags')) + ',Char(10)),\n'
  '  "unchanged","סעיף"&Char(9)&"חשבון"&Char(9)&"תיאור"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"סיבה"&Char(10)&Concat(V97Analysis.AllItems,'
  + tsv(cl('Section'), cl('Account'), cl('Name'), xnum('Current'), xnum('Prior'), cl('Tags')) + ',Char(10)),\n'
  '  "exec","סעיף"&Char(9)&"קוד"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"שינוי %"&Char(10)&Concat(V97Analysis.AllItems,'
  + tsv(cl('Name'), cl('Account'), xnum('Current'), xnum('Prior'), xnum('Delta'), pct_change('Current', 'Prior')) + ',Char(10)),\n'
  '  ""\n'
  '));Reset(V97Export);Set(varV97BackModal,varV97Modal);Set(varV97Modal,"copy")')

# --- additional entries modal (B03) ---------------------------------------
SOURCE_ENTRIES_ITEMS = '=Filter(colV97Drill,Source="additional_entry" && (IsBlank(V97ModalSearch.Text) || Lower(V97ModalSearch.Text) in Lower(Name & " " & Account & " " & LookUp(colV97Rows,RowId=Section,Name))))'
SOURCE_ENTRY_TEXT = ('="פקודה נוספת | " & LookUp(colV97Rows,RowId=ThisItem.Section,Name) & " | " & ThisItem.Account & " | " & ThisItem.Name & Char(10) & '
                     + fmt('ThisItem.Current') + ' & " " & Switch(ThisItem.Side,"debit","חובה","credit","זכות","") & " | " & IfError(If(Text(ParseJSON(ThisItem.Detail).counterpartyStatus)="not_identified","צד נגדי לא זוהה","צד נגדי זוהה"),"")')
JOURNAL_ITEMS = '=Filter(colV97Entries,IsBlank(V97ModalSearch.Text) || Lower(V97ModalSearch.Text) in Lower(Description & " " & Reference & " " & LookUp(colV97Rows,RowId=Debit,Name) & " " & LookUp(colV97Rows,RowId=Credit,Name)))'
JOURNAL_TEXT = ('=ThisItem.Description & " | " & ' + fmt('ThisItem.Amount') + ' & "  [הוזן ידנית]" & Char(10) & "חובה: " & LookUp(colV97Base,RowId=ThisItem.Debit,Name) & " ← זכות: " & LookUp(colV97Base,RowId=ThisItem.Credit,Name) & " | " & Switch(ThisItem.Flow,"operating","שוטפת","investing","השקעה","financing","מימון","ללא מזומן") & If(IsBlank(ThisItem.Reference),""," | "&ThisItem.Reference)')
JOURNAL_COUNT = '="פקודות ידניות: " & CountRows(colV97Entries) & " | פקודות נוספות מהמקור: " & CountIf(colV97Drill,Source="additional_entry")'

# --- FX (B14) ----------------------------------------------------------------
FX_ITEMS = ('=With({fa:IfError(Value(V97FxMin.Text),Blank()),fb:IfError(Value(V97FxMax.Text),Blank())},'
            'With({lo0:If(IsBlank(Trim(V97FxMin.Text)),Blank(),fa),hi0:If(IsBlank(Trim(V97FxMax.Text)),Blank(),fb)},'
            'With({lo1:If(IsBlank(lo0) && IsBlank(hi0),0,Coalesce(lo0,hi0)),hi1:If(IsBlank(lo0) && IsBlank(hi0),1000000000000,Coalesce(hi0,lo0))},'
            'SortByColumns(Filter(colV97Drill,HasFx && Coalesce(OtherCurrent,0)<>0 && Rate>0 && (IsBlank(V97ModalSearch.Text) || Lower(V97ModalSearch.Text) in Lower(Name & " " & Account)) && Rate>=Min(lo1,hi1) && Rate<=Max(lo1,hi1)),"Rate",SortOrder.Ascending))))')
FX_ROW = '=LookUp(colV97Rows,RowId=ThisItem.Section,Name) & " | " & ThisItem.Account & " — " & ThisItem.Name & Char(10) & ThisItem.OtherCurrency & " " & ' + fmt('ThisItem.OtherCurrent') + ' & " | ש״ח: " & ' + fmt('ThisItem.Current') + ' & " | שער: " & If(IsBlank(ThisItem.Rate),"—",Text(ThisItem.Rate,"0.0000","en-US"))'

# --- market ratios (B17, B21) -----------------------------------------------
L = 'If(' + W + '>=900,166,12)'
MK = {
  'V97MarketLabel': {'Y': '=Parent.Height-If(' + W + '>=600,142,222)'},
  'V97Market': {'X': '=' + L, 'Y': '=Parent.Height-If(' + W + '>=600,112,196)', 'Width': '=If(' + W + '>=600,180,(' + W + '-' + L + '-22)/2)'},
  'V97Valuation': {'X': '=If(' + W + '>=600,' + L + '+190,' + L + '+(' + W + '-' + L + '-22)/2+6)', 'Y': '=Parent.Height-If(' + W + '>=600,112,196)',
                   'Width': '=If(' + W + '>=600,Max(110,(' + W + '-' + L + '-216)/3-6),(' + W + '-' + L + '-22)/2)',
                   'Text': '="יחס הון לשווי שוק"&Char(10)&With({eq:LookUp(colV97Rows,RowId="balance_total_equity",Current)},If(!(varV97Market>0) || Coalesce(eq,0)=0,"—",Text(100*eq/varV97Market,"#,##0.#","he-IL")&"%"))'},
  'V97PriceToBook': {'X': '=If(' + W + '>=600,V97Valuation.X+V97Valuation.Width+6,' + L + ')', 'Y': '=Parent.Height-If(' + W + '>=600,112,118)',
                     'Text': '="מכפיל הון"&Char(10)&With({eq:LookUp(colV97Rows,RowId="balance_total_equity",Current)},If(!(varV97Market>0) || Coalesce(eq,0)=0,"—",Text(varV97Market/eq,"#,##0.##","he-IL")&"x"))'},
  'V97PriceEarnings': {'X': '=If(' + W + '>=600,V97PriceToBook.X+V97PriceToBook.Width+6,' + L + '+(' + W + '-' + L + '-22)/2+6)', 'Y': '=Parent.Height-If(' + W + '>=600,112,118)',
                       'Text': '="מכפיל רווח"&Char(10)&With({np:Coalesce(LookUp(colV97Rows,RowId="ratios_R07",Current),0)},If(!(varV97Market>0),"—",If(np>0,Text(varV97Market/np,"#,##0.##","he-IL")&"x",If(np<0,"לא רלוונטי (הפסד)","—"))))'},
}
MAIN_HEIGHT_RATIOS = 'If(varV97Page="ratios",If(' + W + '>=600,150,230),0)'
