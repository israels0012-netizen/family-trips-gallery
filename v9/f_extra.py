# -*- coding: utf-8 -*-
"""B15: Canvas substitutes for 'save dashboard with notes' and Excel export."""
from f_persist import cl
from f_ui import pct_change, NF, XN

def esc(x):
    return 'Substitute(Substitute(Substitute(Substitute(' + x + ',"&","&amp;"),"<","&lt;"),">","&gt;"),Char(34),"&quot;")'

def num(x):
    return 'If(IsBlank(' + x + '),"—",Text(' + x + ',' + NF + ',"he-IL"))'

PAGE_TABLE = ('"<h2>"&%T%&"</h2><table><thead><tr><th>סעיף</th><th>קוד</th><th>"&varV97Date&"</th><th>"&varV97PriorDate&"</th><th>הפרש</th><th>שינוי %</th><th>הערה</th></tr></thead><tbody>"'
              '&Concat(SortByColumns(Filter(colV97Rows,Page="%P%"),"Order",SortOrder.Ascending),"<tr class=\'"&Kind&"\'><td style=\'padding-right:"&Text(Depth*14)&"px\'>"&' + esc('Name') + '&"</td><td>"&' + esc('Code') + '&"</td><td class=n>"&' + num('Current') + '&"</td><td class=n>"&' + num('Prior') + '&"</td><td class=n>"&If(IsBlank(Current) && IsBlank(Prior),"—",Text(Coalesce(Current,0)-Coalesce(Prior,0),' + NF + ',"he-IL"))&"</td><td class=n>"&' + pct_change('Current', 'Prior') + '&"</td><td>"&' + esc('Coalesce(LookUp(colV97Notes,Key=RowId,Text),"")') + '&"</td></tr>")&"</tbody></table>"')

def page(title, pg):
    return PAGE_TABLE.replace('%T%', '"' + title + '"').replace('%P%', pg)

BUILD_HTML = ('=Set(varV97ExportText,"<!DOCTYPE html><html dir=\'rtl\' lang=\'he\'><head><meta charset=\'utf-8\'><title>"&' + esc('varV97Company') + '&" — דשבורד עם הערות</title>'
              '<style>body{font-family:Arial,sans-serif;background:#07111d;color:#dbe3ee;margin:24px}h1,h2{color:#f0c05a}table{border-collapse:collapse;width:100%;margin-bottom:24px}th,td{border:1px solid rgba(218,173,82,.28);padding:6px 8px;font-size:12px}th{background:#102238;color:#f0c05a}.n{text-align:left;direction:ltr}.section,.metric{font-weight:700;background:#102238}@media print{body{background:#fff;color:#000}th{background:#eee;color:#000}}</style></head><body>'
              '<h1>"&' + esc('varV97Company') + '&"</h1><p>"&varV97Date&" מול "&varV97PriorDate&" | "&' + esc('varV97Unit') + '&" | הופק מ-Power Apps "&Text(Now(),"dd/mm/yyyy hh:mm")&" | הנתונים כוללים פקודות ידניות</p>"'
              '&' + page('מאזן', 'balance') + '&' + page('רווח והפסד', 'pnl') + '&' + page('תזרים מזומנים', 'cashflow') + '&' + page('יחסים פיננסיים', 'ratios') +
              '&"<h2>פקודות ידניות</h2><table><thead><tr><th>תיאור</th><th>אסמכתא</th><th>חובה</th><th>זכות</th><th>סכום</th><th>סיווג תזרים</th><th>תאריך</th></tr></thead><tbody>"&Concat(colV97Entries,"<tr><td>"&' + esc('Description') + '&"</td><td>"&' + esc('Reference') + '&"</td><td>"&' + esc('LookUp(colV97Base,RowId=Debit,Name)') + '&"</td><td>"&' + esc('LookUp(colV97Base,RowId=Credit,Name)') + '&"</td><td class=n>"&' + num('Amount') + '&"</td><td>"&Flow&"</td><td>"&' + esc('At') + '&"</td></tr>")&"</tbody></table>"'
              '&"<h2>הערות ביקורת</h2><table><thead><tr><th>יעד</th><th>הערה</th><th>עודכן</th></tr></thead><tbody>"&Concat(colV97Notes,"<tr><td>"&' + esc('Key') + '&"</td><td>"&' + esc('Text') + '&"</td><td>"&' + esc('At') + '&"</td></tr>")&"</tbody></table>"'
              '&"<h2>סטטוס ראיות</h2><table><thead><tr><th>סעיף</th><th>תיאור</th><th>קוד</th><th>סטטוס</th><th>ראיות</th><th>מסמכים</th></tr></thead><tbody>"&Concat(AddColumns(colV97EvidenceTargets As m,St,Coalesce(LookUp(colV97Reviews,Key=m.TargetKey,Status),m.AutoStatus)),"<tr><td>"&' + esc('SectionLabel') + '&"</td><td>"&' + esc('Desc') + '&"</td><td>"&' + esc('Code') + '&"</td><td>"&Switch(St,"match","תואם","gap","פער","unable","לא ניתן לבדוק","activity","ראיה לפעילות","manualAssigned","שויך ידנית","handled","טופל","needsAction","דורש טיפול",St)&"</td><td class=n>"&Text(Count)&"</td><td>"&' + esc('Files') + '&"</td></tr>")&"</tbody></table>"'
              '&"<p>מהותיות: "&Text(varV97Materiality)&" | שווי שוק: "&Text(varV97Market)&"</p></body></html>");'
              'Reset(V97Export);Set(varV97BackModal,"");Set(varV97Modal,"copy");Notify("קוד HTML הוכן. העתק ושמור כקובץ ‎.html",NotificationType.Information)')

ALL_PAGE = ('"%T%"&Char(10)&"סעיף"&Char(9)&"קוד"&Char(9)&varV97Date&Char(9)&varV97PriorDate&Char(9)&"הפרש"&Char(9)&"שינוי %"&Char(9)&"מטבע"&Char(10)&Concat(SortByColumns(Filter(colV97Rows,Page="%P%"),"Order",SortOrder.Ascending),'
            + cl('Name') + '&Char(9)&' + cl('Code') + '&Char(9)&If(IsBlank(Current),"",Text(Current,' + XN + ',"en-US"))&Char(9)&If(IsBlank(Prior),"",Text(Prior,' + XN + ',"en-US"))&Char(9)&If(IsBlank(Current) && IsBlank(Prior),"",Text(Coalesce(Current,0)-Coalesce(Prior,0),' + XN + ',"en-US"))&Char(9)&' + pct_change('Current', 'Prior') + '&Char(9)&' + cl('Unit') + ',Char(10))')

BUILD_EXPORT_ALL = ('=Set(varV97ExportText,' + '&Char(10)&Char(10)&'.join(ALL_PAGE.replace('%T%', t).replace('%P%', p) for t, p in [('מאזן', 'balance'), ('רווח והפסד', 'pnl'), ('תזרים מזומנים', 'cashflow'), ('יחסים פיננסיים', 'ratios')]) + ');'
                    'IfError(Copy(varV97ExportText);Notify("כל הדוחות הועתקו — הדבק באקסל",NotificationType.Success),Notify("ההעתקה חסומה; העתק מהתיבה",NotificationType.Warning));Reset(V97Export);Set(varV97BackModal,"");Set(varV97Modal,"copy")')
