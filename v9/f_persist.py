# -*- coding: utf-8 -*-
"""v9 persistence formulas (SharePoint list DashboardPOC_Data).

Record types written by v9:
  V97Event9     field_10=Seq (own ID, -1 until stamped), field_11=Gen, AuditNote=envelope
  V97Snapshot9  field_10=Through, field_11=Gen, field_17=SnapId, AuditNote=header JSON
  V97SnapPart9  field_10=part index (1..n), field_11=Gen, field_17=SnapId, AuditNote=chunk
Only Number columns field_10/field_11 (already used as numbers by v7) and the text
columns already used by v7/v8 are referenced. field_13 is no longer used.
"""

# common delegable scope predicate
P = 'field_1=varV97CompanyID && field_2=varV97PeriodID && field_14=varV97Dataset'

def sub(s, **kw):
    s = s.replace('%P%', P)
    for k, v in kw.items():
        s = s.replace('%' + k + '%', v)
    return s

ENTITY_LIST = '["Entries","Notes","Reviews","Links","Urls","Docs","History","Settings"]'

# key carried inside an entity payload (B10)
PKEY = ('Switch(%ENT%,"Entries",Text(%PL%.Id),"Notes",Text(%PL%.Key),"Reviews",Text(%PL%.Key),'
        '"Links",Text(%PL%.Key),"Urls",Text(%PL%.DocId),"Docs",Text(%PL%.DocId),"History",Text(%PL%.Id),'
        '"Settings","settings","")')

def pkey(ent, pl):
    return PKEY.replace('%ENT%', ent).replace('%PL%', pl)

EVENT_PAGE = ('If(varV97More,ClearCollect(colV97EvPage,ShowColumns(SortByColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Event9" && field_11=varV97Gen && field_10>varV97Cursor),"field_10",SortOrder.Ascending),ID,field_10,field_11,AuditNote,Created));'
              'Collect(colV97EvRaw,colV97EvPage);Set(varV97More,!IsEmpty(colV97EvPage));If(!IsEmpty(colV97EvPage),Set(varV97Cursor,Max(colV97EvPage,field_10))));')

PAGES = 10

LOAD_SHARED = sub(r'''=Set(varV97Syncing,true);
Set(varV97LoadOk,true);
Set(varV97Legacy,false);
Set(varV97LoadWarn,"");
Set(varV97SaveMessage,"טוען מצב משותף מ-SharePoint...");
IfError(
  Refresh(DashboardPOC_Data);
  Set(varV97SnapHead,First(SortByColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Snapshot9"),"field_11",SortOrder.Descending,"field_10",SortOrder.Descending)));
  Set(varV97Legacy,IsBlank(varV97SnapHead.ID));
  true,
  Set(varV97LoadOk,false);Set(varV97SaveMessage,"טעינת המצב המשותף נכשלה: "&FirstError.Message);false
);
If(varV97LoadOk && !varV97Legacy,IfError(
  Set(varV97SnapMeta,ParseJSON(varV97SnapHead.AuditNote));
  If(IfError(Text(varV97SnapMeta.Dataset),"")<>varV97Dataset || IfError(Value(varV97SnapMeta.V),0)<>9 || IfError(Value(varV97SnapMeta.Gen),-1)<>varV97SnapHead.field_11 || IfError(Value(varV97SnapMeta.Through),-1)<>varV97SnapHead.field_10 || IsBlank(varV97SnapHead.field_17) || IfError(Text(varV97SnapMeta.SnapId),"")<>varV97SnapHead.field_17,
    Set(varV97LoadOk,false);Set(varV97SaveMessage,"כותרת נקודת השחזור האחרונה אינה תואמת לעמודות הרשומה (ID "&Text(varV97SnapHead.ID)&"); הטעינה נעצרה והמצב הפעיל לא הוחלף"),
    If(varV97SnapHead.field_17<>varV97CachedSnapId || IsBlank(varV97CachedSnapText),
      ClearCollect(colV97SnapParts,ShowColumns(SortByColumns(Filter(DashboardPOC_Data,%P% && field_3="V97SnapPart9" && field_17=varV97SnapHead.field_17),"field_10",SortOrder.Ascending),ID,field_10,AuditNote));
      Set(varV97PartText,Concat(colV97SnapParts,AuditNote));
      If(CountRows(colV97SnapParts)<>Value(varV97SnapMeta.Parts) || CountRows(Distinct(colV97SnapParts,field_10))<>CountRows(colV97SnapParts) || Min(colV97SnapParts,field_10)<>1 || Max(colV97SnapParts,field_10)<>Value(varV97SnapMeta.Parts) || Len(varV97PartText)<>Value(varV97SnapMeta.Length),
        Set(varV97LoadOk,false);Set(varV97SaveMessage,"נקודת השחזור האחרונה חסרה חלקים או שאורכה שגוי; הטעינה נעצרה והמצב הפעיל לא הוחלף"),
        Set(varV97CachedSnapText,varV97PartText);Set(varV97CachedSnapId,varV97SnapHead.field_17)
      )
    );
    If(varV97LoadOk,
      Set(varV97SharedBase,ParseJSON(varV97CachedSnapText));
      If(IfError(Text(varV97SharedBase.Dataset),"")<>varV97Dataset || IfError(Value(varV97SharedBase.V),0)<>9 || IfError(Value(varV97SharedBase.Gen),-1)<>varV97SnapHead.field_11 || IfError(Value(varV97SharedBase.Through),-1)<>varV97SnapHead.field_10 || IfError(Text(varV97SharedBase.SnapId),"")<>varV97SnapHead.field_17,
        Set(varV97LoadOk,false);Set(varV97CachedSnapId,"");Set(varV97SaveMessage,"תוכן נקודת השחזור אינו תואם לזהות הרשומה; הטעינה נעצרה והמצב הפעיל לא הוחלף"),
        Set(varV97Gen,varV97SnapHead.field_11);Set(varV97Through,varV97SnapHead.field_10);Set(varV97SnapId,varV97SnapHead.field_17)
      )
    )
  );
  true,
  Set(varV97LoadOk,false);Set(varV97CachedSnapId,"");Set(varV97SaveMessage,"קריאת נקודת השחזור נכשלה: "&FirstError.Message);false
));
If(varV97LoadOk && !varV97Legacy,IfError(
  Clear(colV97EvRaw);Set(varV97Cursor,varV97Through);Set(varV97More,true);
  %PAGES%
  Set(varV97EventsComplete,!varV97More);
  ClearCollect(colV97EvPending,ShowColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Event9" && field_11=varV97Gen && field_10=-1),ID,field_10,field_11,AuditNote,Created));
  If(!varV97EventsComplete || CountRows(colV97EvPending)>=500,
    Set(varV97LoadOk,false);Set(varV97SaveMessage,"הטעינה נעצרה: מספר השינויים מאז נקודת השחזור האחרונה חורג מיכולת הטעינה המוכחת. המצב הפעיל לא הוחלף; פנה למנהל לפי הוראות ההתקנה."),
    Collect(colV97EvRaw,Filter(colV97EvPending As p,IsBlank(LookUp(colV97EvRaw,ID=p.ID))));
    ForAll(Filter(colV97EvPending As p,p.Created<DateAdd(Now(),-2,TimeUnit.Minutes)) As p,IfError(Patch(DashboardPOC_Data,LookUp(DashboardPOC_Data,ID=p.ID),{field_10:p.ID});true,false))
  );
  true,
  Set(varV97LoadOk,false);Set(varV97SaveMessage,"טעינת השינויים המשותפים נכשלה: "&FirstError.Message);false
));
If(varV97LoadOk && !varV97Legacy,IfError(
  ClearCollect(colV97Events,ForAll(colV97EvRaw As e,With({j:IfError(ParseJSON(e.AuditNote),ParseJSON("{}"))},With({ent:IfError(Text(j.Entity),""),k:IfError(Text(j.Key),""),pl:IfError(Text(j.Payload),""),del:IfError(Boolean(j.Deleted),false)},{EventId:e.ID,Created:e.Created,Entity:ent,Key:k,Deleted:del,Payload:pl,At:IfError(Text(j.At),""),Author:IfError(Text(j.Author),""),Valid:(ent in %ENTITIES%) && !IsBlank(k) && e.field_11=varV97Gen && IfError(Value(j.Gen),-1)=varV97Gen && IfError(Text(j.Dataset),"")=varV97Dataset && IfError(Value(j.V),0)=9 && IfError(With({p:ParseJSON(pl)},%PKEY%)=k,false)}))));
  Set(varV97BadEvents,CountIf(colV97Events,!Valid));
  ClearCollect(colV97Merge,ForAll(Table(varV97SharedBase.Items) As b,{Entity:Text(b.Value.Entity),Key:Text(b.Value.Key),EventId:Value(b.Value.EventId),Deleted:Boolean(b.Value.Deleted),Payload:Text(b.Value.Payload)}));
  Collect(colV97Merge,ForAll(Filter(colV97Events,Valid) As e,{Entity:e.Entity,Key:e.Key,EventId:e.EventId,Deleted:e.Deleted,Payload:e.Payload}));
  ClearCollect(colV97Win,ForAll(Distinct(colV97Merge,Entity&"|"&Key) As g,First(SortByColumns(Filter(colV97Merge,Entity&"|"&Key=g.Value),"EventId",SortOrder.Descending))));
  Set(varV97MaxEventId,Max(varV97Through,Coalesce(Max(colV97Events,EventId),0)));
  Set(varV97CheckpointNeeded,CountRows(colV97Events)>=50);
  If(varV97BadEvents>0,Set(varV97LoadWarn,varV97LoadWarn&" · "&Text(varV97BadEvents)&" רשומות שינוי לא תקינות נדחו"));
  true,
  Set(varV97LoadOk,false);Set(varV97SaveMessage,"מיזוג השינויים נכשל: "&FirstError.Message);false
));
If(varV97LoadOk && varV97Legacy,IfError(
  Set(varV97Gen,0);Set(varV97Through,0);Set(varV97SnapId,"");Set(varV97CachedSnapId,"");
  ClearCollect(colV97Snap8,ForAll(Filter(DashboardPOC_Data,%P% && field_3="V97Snapshot8") As s,With({j:IfError(ParseJSON(s.AuditNote),ParseJSON("{}"))},{ID:s.ID,Title:s.Title,AuditNote:s.AuditNote,Through:IfError(Value(j.ThroughEventId),-1),Ok:IfError(Text(j.Dataset)=varV97Dataset && (Value(j.Version) in [1,2]),false)})));
  If(CountRows(colV97Snap8)>=500,Error({Kind:ErrorKind.Custom,Message:"יותר מ-500 נקודות שחזור של v8; נדרשת הגדלת מגבלת השורות לפני מיגרציה"}));
  Set(varV97Snap8,First(SortByColumns(AddColumns(Filter(colV97Snap8,Ok && Through>=0) As s,Prio,s.Through*10+If(StartsWith(s.Title,"V97-SNAPSHOT8-RESTORE-"),5,0)),"Prio",SortOrder.Descending,"ID",SortOrder.Descending)));
  ClearCollect(colV97Snap7,ShowColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Snapshot7"),ID,AuditNote));
  If(CountRows(colV97Snap7)>=500,Error({Kind:ErrorKind.Custom,Message:"יותר מ-500 נקודות שחזור של v7; נדרשת מיגרציה מבוקרת"}));
  Set(varV97Snap7,If(IsBlank(varV97Snap8.ID),First(SortByColumns(Filter(colV97Snap7 As s,IfError(Text(ParseJSON(s.AuditNote).Dataset)=varV97Dataset,false)),"ID",SortOrder.Descending)),Blank()));
  Set(varV97LegacyThrough,If(!IsBlank(varV97Snap8.ID),varV97Snap8.Through,If(!IsBlank(varV97Snap7.ID),Coalesce(IfError(Value(ParseJSON(varV97Snap7.AuditNote).ThroughEventId),Blank()),varV97Snap7.ID),0)));
  If(IsBlank(varV97Snap8.ID) && IsBlank(varV97Snap7.ID),
    ClearCollect(colV97LegacyEntries,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97ManualEntry"));
    ClearCollect(colV97LegacyNotes,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97Note"));
    ClearCollect(colV97LegacyReviews,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97Review"));
    ClearCollect(colV97LegacyLinks,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97Link"));
    ClearCollect(colV97LegacyUrls,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97Url"));
    ClearCollect(colV97LegacyHistory,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97History"));
    ClearCollect(colV97LegacySettings,Filter(DashboardPOC_Data,field_1=varV97CompanyID && field_2=varV97PeriodID && field_3="V97Settings"));
    If(Max(CountRows(colV97LegacyEntries),CountRows(colV97LegacyNotes),CountRows(colV97LegacyReviews),CountRows(colV97LegacyLinks),CountRows(colV97LegacyUrls),CountRows(colV97LegacyHistory),CountRows(colV97LegacySettings))>=500,Error({Kind:ErrorKind.Custom,Message:"אחת מאוכלוסיות המצב הישנות הגיעה למגבלת 500; נדרשת מיגרציה מבוקרת"}));
    Set(varV97LegacyBaseText,JSON({Version:2,Dataset:varV97Dataset,ThroughEventId:0,Entries:ForAll(colV97LegacyEntries As s,{Id:s.field_14,Debit:s.field_5,Credit:s.field_6,Amount:s.field_10,Description:s.field_9,Reference:s.field_21,Flow:s.field_20,CashDelta:s.field_11,At:s.AuditNote}),Notes:ForAll(colV97LegacyNotes As s,{Key:s.field_14,Text:s.AuditNote,At:s.field_21}),Reviews:ForAll(colV97LegacyReviews As s,{Key:s.field_14,Status:s.AuditStatus,Note:s.AuditNote,At:s.field_21}),Links:ForAll(colV97LegacyLinks As s,{Key:s.field_14,DocId:s.field_17,Section:s.field_5,Account:s.field_21,Name:s.field_9}),Urls:ForAll(colV97LegacyUrls As s,{DocId:s.field_17,Url:s.EvidenceUrl}),History:ForAll(colV97LegacyHistory As s,{Id:s.Title,Key:s.field_14,Action:s.AuditStatus,At:s.field_21,User:s.AuditNote}),Materiality:Coalesce(First(colV97LegacySettings).field_10,50),Market:Coalesce(First(colV97LegacySettings).field_11,0)},JSONFormat.Compact)),
    Set(varV97LegacyBaseText,If(!IsBlank(varV97Snap8.ID),varV97Snap8.AuditNote,varV97Snap7.AuditNote))
  );
  Set(varV97SharedBase,ParseJSON(varV97LegacyBaseText));
  ClearCollect(colV97LegEv8,ShowColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Event8"),ID,AuditNote));
  ClearCollect(colV97LegEv7,ShowColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Event7"),ID,AuditNote));
  If(CountRows(colV97LegEv8)>=500 || CountRows(colV97LegEv7)>=500,Error({Kind:ErrorKind.Custom,Message:"יותר מ-500 אירועי v7/v8; לא ניתן להוכיח טעינה מלאה לצורך מיגרציה"}));
  ClearCollect(colV97Events,ForAll(Filter(colV97LegEv8,ID>varV97LegacyThrough) As e,With({j:IfError(ParseJSON(e.AuditNote),ParseJSON("{}"))},With({ent:IfError(Text(j.Entity),""),k:IfError(Text(j.Key),""),pl:IfError(Text(j.Payload),""),del:IfError(Boolean(j.Deleted),false)},{EventId:e.ID,Created:Now(),Entity:ent,Key:k,Deleted:del,Payload:pl,At:IfError(Text(j.At),""),Author:IfError(Text(j.Author),""),Valid:(ent in ["Entries","Notes","Reviews","Links","Urls","Settings"]) && !IsBlank(k) && (del || IfError(With({p:ParseJSON(pl)},Switch(ent,"Entries",Text(p.Id),"Notes",Text(p.Key),"Reviews",Text(p.Key),"Links",Text(p.Key),"Urls",Text(p.DocId),"Settings","settings",""))=k,false))}))));
  Collect(colV97Events,ForAll(Filter(colV97LegEv7,ID>varV97LegacyThrough) As e,With({j:IfError(ParseJSON(e.AuditNote),ParseJSON("{}"))},With({ent:IfError(Text(j.Entity),""),k:IfError(Text(j.Key),""),pl:IfError(Text(j.Payload),""),del:IfError(Boolean(j.Deleted),false)},{EventId:e.ID,Created:Now(),Entity:ent,Key:k,Deleted:del,Payload:pl,At:IfError(Text(j.At),""),Author:IfError(Text(j.Author),""),Valid:(ent in ["Entries","Notes","Reviews","Links","Urls","Settings"]) && !IsBlank(k) && (del || IfError(With({p:ParseJSON(pl)},Switch(ent,"Entries",Text(p.Id),"Notes",Text(p.Key),"Reviews",Text(p.Key),"Links",Text(p.Key),"Urls",Text(p.DocId),"Settings","settings",""))=k,false))}))));
  Set(varV97BadEvents,CountIf(colV97Events,!Valid));
  ClearCollect(colV97Merge,ForAll(Table(varV97SharedBase.Entries) As b,{Entity:"Entries",Key:Text(b.Value.Id),EventId:0,Deleted:false,Payload:JSON(b.Value,JSONFormat.Compact)}));
  Collect(colV97Merge,ForAll(Table(varV97SharedBase.Notes) As b,{Entity:"Notes",Key:Text(b.Value.Key),EventId:0,Deleted:false,Payload:JSON(b.Value,JSONFormat.Compact)}));
  Collect(colV97Merge,ForAll(Table(varV97SharedBase.Reviews) As b,{Entity:"Reviews",Key:Text(b.Value.Key),EventId:0,Deleted:false,Payload:JSON(b.Value,JSONFormat.Compact)}));
  Collect(colV97Merge,ForAll(Table(varV97SharedBase.Links) As b,{Entity:"Links",Key:Text(b.Value.Key),EventId:0,Deleted:false,Payload:JSON(b.Value,JSONFormat.Compact)}));
  Collect(colV97Merge,ForAll(Table(varV97SharedBase.Urls) As b,{Entity:"Urls",Key:Text(b.Value.DocId),EventId:0,Deleted:false,Payload:JSON(b.Value,JSONFormat.Compact)}));
  Collect(colV97Merge,ForAll(Table(varV97SharedBase.History) As b,{Entity:"History",Key:Text(b.Value.Id),EventId:0,Deleted:false,Payload:JSON(b.Value,JSONFormat.Compact)}));
  Collect(colV97Merge,{Entity:"Settings",Key:"settings",EventId:0,Deleted:false,Payload:JSON({Materiality:IfError(Value(varV97SharedBase.Materiality),50),Market:IfError(Value(varV97SharedBase.Market),0)},JSONFormat.Compact)});
  Collect(colV97Merge,ForAll(Filter(colV97Events,Valid) As e,{Entity:e.Entity,Key:e.Key,EventId:e.EventId,Deleted:e.Deleted,Payload:e.Payload}));
  ClearCollect(colV97Win,ForAll(Distinct(colV97Merge,Entity&"|"&Key) As g,First(SortByColumns(Filter(colV97Merge,Entity&"|"&Key=g.Value),"EventId",SortOrder.Descending))));
  If(varV97BadEvents>0,Set(varV97LoadWarn,varV97LoadWarn&" · "&Text(varV97BadEvents)&" רשומות v7/v8 לא תקינות לא הועברו"));
  true,
  Set(varV97LoadOk,false);Set(varV97SaveMessage,"קריאת המצב של גרסה קודמת נכשלה: "&FirstError.Message);false
));
If(varV97LoadOk,
  Select(V97Materialize),
  Set(varV97Syncing,false);Set(varV97Starting,false);Set(varV97RemoteReady,false);Set(varV97SaveMessage,varV97SaveMessage&" · השמירה מושבתת עד רענון תקין");Notify(varV97SaveMessage,NotificationType.Error)
)''').replace('%PAGES%', '\n  '.join([sub(EVENT_PAGE)] * PAGES)).replace('%ENTITIES%', ENTITY_LIST).replace('%PKEY%', pkey('ent', 'p'))

# ---------------------------------------------------------------------------
# Materialize: winners -> stage collections (v9 shapes); legacy shapes are
# converted (reviews keyed by evidence target, statuses, link target keys).
MATERIALIZE = r'''=IfError(
  ClearCollect(colV97StageEntries,ForAll(Filter(colV97Win,Entity="Entries" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{Id:Text(j.Id),Debit:Text(j.Debit),Credit:Text(j.Credit),Amount:Value(j.Amount),Description:Text(j.Description),Reference:Text(j.Reference),Flow:Text(j.Flow),CashDelta:Value(j.CashDelta),At:Text(j.At)})));
  ClearCollect(colV97StageNotes,ForAll(Filter(colV97Win,Entity="Notes" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{Key:Text(j.Key),Text:Text(j.Text),At:Text(j.At)})));
  ClearCollect(colV97StageReviews,ForAll(Filter(colV97Win,Entity="Reviews" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{Key:Text(j.Key),Status:Text(j.Status),Note:Text(j.Note),At:Text(j.At)})));
  ClearCollect(colV97StageLinks,ForAll(Filter(colV97Win,Entity="Links" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{Key:Text(j.Key),TargetKey:Text(j.TargetKey),DocId:Text(j.DocId),Section:Text(j.Section),Account:Text(j.Account),Name:Text(j.Name)})));
  ClearCollect(colV97StageUrls,ForAll(Filter(colV97Win,Entity="Urls" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{DocId:Text(j.DocId),Url:Text(j.Url)})));
  ClearCollect(colV97StageDocs,ForAll(Filter(colV97Win,Entity="Docs" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{DocId:Text(j.DocId),Name:Text(j.Name),Url:Text(j.Url),At:Text(j.At)})));
  ClearCollect(colV97StageHistory,ForAll(Filter(colV97Win,Entity="History" && !Deleted) As z,With({j:ParseJSON(z.Payload)},{Id:Text(j.Id),Key:Text(j.Key),Action:Text(j.Action),At:Text(j.At),User:Text(j.User)})));
  With({s:LookUp(colV97Win,Entity="Settings" && Key="settings" && !Deleted)},If(IsBlank(s.Payload),Set(varV97StageMateriality,50);Set(varV97StageMarket,0),With({j:ParseJSON(s.Payload)},Set(varV97StageMateriality,IfError(Value(j.Materiality),-1));Set(varV97StageMarket,IfError(Value(j.Market),-1)))));
  Set(varV97StageVersion,If(varV97Legacy,2,9));
  true,
  Set(varV97LoadOk,false);Set(varV97SaveMessage,"פענוח המצב המשותף נכשל: "&FirstError.Message);false
);
If(varV97LoadOk,
  Set(varV97ApplyMode,If(varV97Legacy,"migrate","load"));
  If(varV97StageVersion<9,Select(V97ConvertStage),Select(V97ApplyState)),
  Set(varV97Syncing,false);Set(varV97Starting,false);Notify(varV97SaveMessage,NotificationType.Error)
)'''

# Converts v7/v8 (Version 1/2) stage content to v9 semantics.
CONVERT_STAGE = r'''=IfError(
  ClearCollect(colV97StageLinks,ForAll(colV97StageLinks As l,With({tk:If(IsBlank(l.TargetKey),If(IsBlank(Trim(l.Account)),"general:"&l.Section&":","drill:"&l.Section&":"&Trim(l.Account)),l.TargetKey)},{Key:tk&"|"&l.DocId,TargetKey:tk,DocId:l.DocId,Section:l.Section,Account:Trim(l.Account),Name:l.Name})));
  ClearCollect(colV97ConvReviews,ForAll(colV97StageReviews As r,{Key:If(StartsWith(r.Key,"LINK|"),With({parts:Split(Mid(r.Key,6),"|")},If(CountRows(parts)>=3,If(IsBlank(Trim(Index(parts,3).Value)),"general:"&Index(parts,2).Value&":","drill:"&Index(parts,2).Value&":"&Trim(Index(parts,3).Value)),"")),Coalesce(LookUp(colV97MatchesX,Key=r.Key,TargetKey),If(StartsWith(r.Key,"drill:") || StartsWith(r.Key,"general:"),r.Key,""))),Status:Switch(r.Status,"טופל","handled","דורש בדיקה","needsAction","דורש טיפול","needsAction","handled","handled","needsAction","needsAction",""),Note:r.Note,At:r.At,Orig:r.Key,OrigStatus:r.Status}));
  ClearCollect(colV97ConvReviews,ForAll(colV97ConvReviews As r,{Key:If(IsBlank(r.Key),"unmapped:"&r.Orig,r.Key),Status:If(IsBlank(r.Status),r.OrigStatus,r.Status),Note:r.Note,At:r.At,Orig:r.Orig,OrigStatus:r.OrigStatus}));
  ClearCollect(colV97StageReviews,ForAll(Distinct(Filter(colV97ConvReviews,OrigStatus<>"אוטומטי"),Key) As g,First(ShowColumns(SortByColumns(Filter(colV97ConvReviews,Key=g.Value),"At",SortOrder.Descending),Key,Status,Note,At))));
  ClearCollect(colV97StageHistory,Filter(colV97StageHistory,!StartsWith(Id,"EVENT-")));
  Set(varV97StageVersion,9);
  true,
  Set(varV97LoadOk,false);Set(varV97SaveMessage,"המרת מצב מגרסה קודמת נכשלה: "&FirstError.Message);false
);
If(varV97LoadOk,Select(V97ApplyState),Set(varV97Syncing,false);Set(varV97Starting,false);Notify(varV97SaveMessage,NotificationType.Error))'''

# validity predicates over stage collections (shared by strict and lenient modes)
ENTRY_OK = ('!IsBlank(%e%.Id) && !IsBlank(Trim(%e%.Description)) && !IsBlank(%e%.Amount) && %e%.Amount>0 && %e%.Amount<=1000000000000 && %e%.Debit<>%e%.Credit'
            ' && !IsBlank(LookUp(colV97Base,RowId=%e%.Debit && CanPost).RowId) && !IsBlank(LookUp(colV97Base,RowId=%e%.Credit && CanPost).RowId)'
            ' && (%e%.Flow in ["operating","investing","financing","noncash"]) && !IsBlank(%e%.CashDelta)'
            ' && !(%e%.Flow="noncash" && Abs(%e%.CashDelta)>0.000001)'
            ' && Abs(%e%.CashDelta-%e%.Amount*(If(LookUp(colV97Base,RowId=%e%.Debit,Cash),1,0)-If(LookUp(colV97Base,RowId=%e%.Credit,Cash),1,0)))<=0.000001')
DOC_OK = ('StartsWith(%d%.DocId,"EXT-") && !IsBlank(Trim(%d%.Name)) && StartsWith(Lower(Trim(%d%.Url)),"https://") && IsBlank(LookUp(colV97Documents,DocId=%d%.DocId).DocId)')
DOC_EXISTS = '(!IsBlank(LookUp(colV97Documents,DocId=%x%).DocId) || !IsBlank(LookUp(colV97StageDocs,DocId=%x%).DocId))'
TARGET_OK = ('(If(StartsWith(%l%.TargetKey,"drill:"),%l%.TargetKey="drill:"&%l%.Section&":"&%l%.Account && !IsBlank(%l%.Account)'
             ' && (!IsBlank(LookUp(colV97Drill,Section=%l%.Section && Trim(Account)=%l%.Account).Key) || (StartsWith(%l%.Account,"MANUAL-") && !IsBlank(LookUp(colV97StageEntries As me,"MANUAL-"&me.Id=%l%.Account && (me.Debit=%l%.Section || me.Credit=%l%.Section)).Id))),'
             'StartsWith(%l%.TargetKey,"general:") && %l%.TargetKey="general:"&%l%.Section&":"&%l%.Account && !IsBlank(LookUp(colV97Base,RowId=%l%.Section).RowId)))')
LINK_OK = ('!IsBlank(%l%.DocId) && ' + DOC_EXISTS.replace('%x%', '%l%.DocId') + ' && %l%.Key=%l%.TargetKey&"|"&%l%.DocId && ' + TARGET_OK)
NOTE_OK = ('!IsBlank(%n%.Key) && !IsBlank(Trim(%n%.Text)) && (!IsBlank(LookUp(colV97Base,RowId=%n%.Key).RowId) || !IsBlank(LookUp(colV97Drill,Key=%n%.Key).Key)'
           ' || !IsBlank(LookUp(colV97StageEntries As me,%n%.Key="MANUAL|"&me.Id&"|D" || %n%.Key="MANUAL|"&me.Id&"|C").Id))')
URL_OK = (DOC_EXISTS.replace('%x%', '%u%.DocId') + ' && StartsWith(Lower(Trim(%u%.Url)),"https://")')
REVIEW_OK = ('(%r%.Status in ["handled","needsAction"]) && (!IsBlank(LookUp(colV97MatchesX,TargetKey=%r%.Key).Key) || !IsBlank(LookUp(colV97StageLinks,TargetKey=%r%.Key).Key))')
HIST_OK = '!IsBlank(%h%.Id) && !IsBlank(%h%.Key)'

def P_(t, var, s):
    return t.replace(var, s)

APPLY_STATE = r'''=Set(varV97ApplyOk,true);Clear(colV97StageErrors);
IfError(
  If(varV97ApplyMode="restore",
    If(CountRows(colV97StageEntries)<>CountRows(Distinct(colV97StageEntries,Id)),Collect(colV97StageErrors,{Msg:"מזהה פקודה כפול"}));
    If(CountRows(colV97StageNotes)<>CountRows(Distinct(colV97StageNotes,Key)),Collect(colV97StageErrors,{Msg:"הערה כפולה לאותו יעד"}));
    If(CountRows(colV97StageReviews)<>CountRows(Distinct(colV97StageReviews,Key)),Collect(colV97StageErrors,{Msg:"סטטוס ראיה כפול לאותו יעד"}));
    If(CountRows(colV97StageLinks)<>CountRows(Distinct(colV97StageLinks,Key)),Collect(colV97StageErrors,{Msg:"שיוך ראיה כפול"}));
    If(CountRows(colV97StageUrls)<>CountRows(Distinct(colV97StageUrls,DocId)),Collect(colV97StageErrors,{Msg:"קישור כפול למסמך"}));
    If(CountRows(colV97StageDocs)<>CountRows(Distinct(colV97StageDocs,DocId)),Collect(colV97StageErrors,{Msg:"מסמך חיצוני כפול"}));
    If(CountRows(colV97StageHistory)<>CountRows(Distinct(colV97StageHistory,Id)),Collect(colV97StageErrors,{Msg:"רשומת היסטוריה כפולה"}));
    ForAll(Filter(colV97StageEntries As e,!(%ENTRY_e%)) As e,Collect(colV97StageErrors,{Msg:"פקודה לא תקינה: "&e.Id}));
    ForAll(Filter(colV97StageDocs As d,!(%DOC_d%)) As d,Collect(colV97StageErrors,{Msg:"מסמך חיצוני לא תקין: "&d.DocId}));
    ForAll(Filter(colV97StageLinks As l,!(%LINK_l%)) As l,Collect(colV97StageErrors,{Msg:"שיוך ראיה ליעד שאינו קיים: "&l.Key}));
    ForAll(Filter(colV97StageNotes As n,!(%NOTE_n%)) As n,Collect(colV97StageErrors,{Msg:"הערה ליעד שאינו קיים: "&n.Key}));
    ForAll(Filter(colV97StageUrls As u,!(%URL_u%)) As u,Collect(colV97StageErrors,{Msg:"קישור למסמך שאינו קיים או שאינו HTTPS: "&u.DocId}));
    ForAll(Filter(colV97StageReviews As r,!(%REVIEW_r%)) As r,Collect(colV97StageErrors,{Msg:"סטטוס ראיה ליעד ללא ראיות: "&r.Key}));
    ForAll(Filter(colV97StageHistory As h,!(%HIST_h%)) As h,Collect(colV97StageErrors,{Msg:"רשומת היסטוריה לא תקינה"}));
    If(IsBlank(varV97StageMateriality) || varV97StageMateriality<0 || IsBlank(varV97StageMarket) || varV97StageMarket<0,Collect(colV97StageErrors,{Msg:"מהותיות או שווי שוק לא תקינים"}));
    Set(varV97ApplyOk,IsEmpty(colV97StageErrors)),
    Set(varV97DropCount,CountRows(colV97StageEntries)+CountRows(colV97StageDocs)+CountRows(colV97StageLinks)+CountRows(colV97StageNotes)+CountRows(colV97StageUrls)+CountRows(colV97StageReviews));
    ClearCollect(colV97StageEntries,Filter(colV97StageEntries As e,%ENTRY_e%));
    ClearCollect(colV97StageDocs,Filter(colV97StageDocs As d,%DOC_d%));
    ClearCollect(colV97StageLinks,Filter(colV97StageLinks As l,%LINK_l%));
    ClearCollect(colV97StageNotes,Filter(colV97StageNotes As n,%NOTE_n%));
    ClearCollect(colV97StageUrls,Filter(colV97StageUrls As u,%URL_u%));
    ClearCollect(colV97StageReviews,Filter(colV97StageReviews As r,%REVIEW_r%));
    ClearCollect(colV97StageHistory,Filter(colV97StageHistory As h,%HIST_h%));
    Set(varV97DropCount,varV97DropCount-(CountRows(colV97StageEntries)+CountRows(colV97StageDocs)+CountRows(colV97StageLinks)+CountRows(colV97StageNotes)+CountRows(colV97StageUrls)+CountRows(colV97StageReviews)));
    If(varV97DropCount>0,Set(varV97LoadWarn,varV97LoadWarn&" · "&Text(varV97DropCount)&" פריטים תלויים ביעד שאינו קיים לא הוחלו"));
    If(IsBlank(varV97StageMateriality) || varV97StageMateriality<0,Set(varV97StageMateriality,50));
    If(IsBlank(varV97StageMarket) || varV97StageMarket<0,Set(varV97StageMarket,0))
  );
  true,
  Set(varV97ApplyOk,false);Collect(colV97StageErrors,{Msg:"בדיקת התקינות נכשלה: "&FirstError.Message});false
);
If(varV97ApplyOk,
  If(varV97ApplyMode="load",
    ClearCollect(colV97Entries,colV97StageEntries);ClearCollect(colV97Notes,colV97StageNotes);ClearCollect(colV97Reviews,colV97StageReviews);ClearCollect(colV97Links,colV97StageLinks);ClearCollect(colV97Urls,colV97StageUrls);ClearCollect(colV97Docs,colV97StageDocs);ClearCollect(colV97History,colV97StageHistory);
    Set(varV97Materiality,varV97StageMateriality);Set(varV97Market,varV97StageMarket);Reset(V97Materiality);Reset(V97Market);
    Set(varV97RemoteReady,true);Set(varV97Dirty,false);Set(varV97Starting,false);
    Set(varV97SaveMessage,"מסונכרן עם הצוות · "&Text(Now(),"hh:mm")&varV97LoadWarn);
    If(varV97PendingWriteCheck && varV97Gen<>varV97WriteGen,Set(varV97PendingWriteCheck,false);Notify("השינוי האחרון נכתב לפני שחזור מקביל של משתמש אחר ולכן אינו חלק מהמצב המשוחזר. בצע אותו שוב אם הוא עדיין נדרש.",NotificationType.Warning));
    Set(varV97PendingWriteCheck,false);
    If(!varV97CheckpointNeeded,Set(varV97Syncing,false));
    Select(V97Recalculate),
    ClearCollect(colV97SnapItems,ForAll(colV97StageEntries As x,{Entity:"Entries",Key:x.Id,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,ForAll(colV97StageNotes As x,{Entity:"Notes",Key:x.Key,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,ForAll(colV97StageReviews As x,{Entity:"Reviews",Key:x.Key,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,ForAll(colV97StageLinks As x,{Entity:"Links",Key:x.Key,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,ForAll(colV97StageUrls As x,{Entity:"Urls",Key:x.DocId,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,ForAll(colV97StageDocs As x,{Entity:"Docs",Key:x.DocId,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,ForAll(colV97StageHistory As x,{Entity:"History",Key:x.Id,EventId:0,Deleted:false,Payload:JSON(x,JSONFormat.Compact)}));
    Collect(colV97SnapItems,{Entity:"Settings",Key:"settings",EventId:0,Deleted:false,Payload:JSON({Materiality:varV97StageMateriality,Market:varV97StageMarket},JSONFormat.Compact)});
    Set(varV97SnapKind,varV97ApplyMode);Set(varV97SnapThroughTarget,0);
    Select(V97WriteSnapshot)
  ),
  Set(varV97Syncing,false);Set(varV97Starting,false);
  If(varV97ApplyMode="restore",
    Set(varV97SaveMessage,"הגיבוי נדחה בבדיקת תקינות; המצב המשותף לא הוחלף: "&Concat(FirstN(colV97StageErrors,3),Msg,"; ")),
    Set(varV97RemoteReady,false);Set(varV97SaveMessage,"המצב המשותף נדחה בבדיקת תקינות; המצב הפעיל לא הוחלף: "&Concat(FirstN(colV97StageErrors,3),Msg,"; "))
  );
  Notify(varV97SaveMessage,NotificationType.Error)
)'''
APPLY_STATE = (APPLY_STATE
    .replace('%ENTRY_e%', ENTRY_OK.replace('%e%', 'e'))
    .replace('%DOC_d%', DOC_OK.replace('%d%', 'd'))
    .replace('%LINK_l%', LINK_OK.replace('%l%', 'l'))
    .replace('%NOTE_n%', NOTE_OK.replace('%n%', 'n'))
    .replace('%URL_u%', URL_OK.replace('%u%', 'u'))
    .replace('%REVIEW_r%', REVIEW_OK.replace('%r%', 'r'))
    .replace('%HIST_h%', HIST_OK.replace('%h%', 'h')))

# ---------------------------------------------------------------------------
CHECKPOINT = r'''=If(varV97RemoteReady && varV97CheckpointNeeded,
  Set(varV97CheckpointNeeded,false);
  Set(varV97NewThrough,Max(varV97Through,Coalesce(Max(Filter(colV97Events,Created<DateAdd(Now(),-10,TimeUnit.Minutes)),EventId),0)));
  If(varV97NewThrough>varV97Through,
    ClearCollect(colV97SnapItems,ShowColumns(Filter(colV97Win,!Deleted || EventId>varV97NewThrough),Entity,Key,EventId,Deleted,Payload));
    Set(varV97SnapKind,"checkpoint");Set(varV97SnapThroughTarget,varV97NewThrough);
    Select(V97WriteSnapshot),
    Set(varV97Syncing,false)
  ),
  Set(varV97Syncing,false)
)'''

WRITE_SNAPSHOT = sub(r'''=Set(varV97SnapOk,true);Set(varV97SnapBlocked,false);
IfError(
  Refresh(DashboardPOC_Data);
  Set(varV97SnapGenTarget,If(varV97SnapKind="checkpoint",varV97Gen,Coalesce(First(SortByColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Snapshot9"),"field_11",SortOrder.Descending)).field_11,0)+1));
  If(varV97SnapKind="checkpoint",Set(varV97SnapBlocked,!IsBlank(LookUp(DashboardPOC_Data,%P% && field_3="V97Snapshot9" && (field_11>varV97SnapGenTarget || (field_11=varV97SnapGenTarget && field_10>=varV97SnapThroughTarget))).ID)));
  If(!varV97SnapBlocked,
    Set(varV97NewSnapId,Text(GUID()));
    Set(varV97SnapText,JSON({V:9,Dataset:varV97Dataset,Gen:varV97SnapGenTarget,Through:varV97SnapThroughTarget,SnapId:varV97NewSnapId,Kind:varV97SnapKind,Items:colV97SnapItems},JSONFormat.Compact));
    Set(varV97SnapParts,Max(1,RoundUp(Len(varV97SnapText)/30000,0)));
    If(varV97SnapParts>60,Error({Kind:ErrorKind.Custom,Message:"המצב המשותף גדול מ-1.8 מיליון תווים"}));
    ForAll(Sequence(varV97SnapParts) As i,Patch(DashboardPOC_Data,Defaults(DashboardPOC_Data),{Title:"V97-SNAPPART9-"&varV97NewSnapId&"-"&Text(i.Value),field_1:varV97CompanyID,field_2:varV97PeriodID,field_3:"V97SnapPart9",field_10:i.Value,field_11:varV97SnapGenTarget,field_14:varV97Dataset,field_17:varV97NewSnapId,AuditNote:Mid(varV97SnapText,(i.Value-1)*30000+1,30000)}));
    ClearCollect(colV97PartCheck,ShowColumns(Filter(DashboardPOC_Data,%P% && field_3="V97SnapPart9" && field_17=varV97NewSnapId),ID,field_10));
    If(CountRows(colV97PartCheck)<>varV97SnapParts,Error({Kind:ErrorKind.Custom,Message:"לא כל חלקי נקודת השחזור נשמרו"}));
    Patch(DashboardPOC_Data,Defaults(DashboardPOC_Data),{Title:"V97-SNAP9-"&varV97NewSnapId,field_1:varV97CompanyID,field_2:varV97PeriodID,field_3:"V97Snapshot9",field_10:varV97SnapThroughTarget,field_11:varV97SnapGenTarget,field_14:varV97Dataset,field_17:varV97NewSnapId,AuditNote:JSON({V:9,Dataset:varV97Dataset,Gen:varV97SnapGenTarget,Through:varV97SnapThroughTarget,SnapId:varV97NewSnapId,Kind:varV97SnapKind,Parts:varV97SnapParts,Length:Len(varV97SnapText)},JSONFormat.Compact)})
  );
  true,
  Set(varV97SnapOk,false);Set(varV97SnapError,FirstError.Message);false
);
If(varV97SnapKind="checkpoint",
  If(varV97SnapOk && !varV97SnapBlocked,Set(varV97CachedSnapText,varV97SnapText);Set(varV97CachedSnapId,varV97NewSnapId);Set(varV97SnapId,varV97NewSnapId);Set(varV97Through,varV97SnapThroughTarget);Set(varV97SaveMessage,"מסונכרן עם הצוות · נקודת שחזור נשמרה "&Text(Now(),"hh:mm")&varV97LoadWarn));
  If(!varV97SnapOk,Set(varV97SaveMessage,"מסונכרן עם הצוות; יצירת נקודת שחזור נכשלה ותנוסה שוב בטעינה הבאה: "&varV97SnapError));
  Set(varV97Syncing,false),
  If(varV97SnapOk,
    Set(varV97Modal,"");Set(varV97SaveMessage,If(varV97SnapKind="restore","הגיבוי נשמר כדור מצב חדש; מרענן את המצב המשותף…","המצב מגרסה קודמת הועבר למבנה v9; מרענן…"));Set(varV97CachedSnapId,"");Select(V97LoadShared),
    Set(varV97Syncing,false);Set(varV97Starting,false);
    If(varV97SnapKind="migrate",Set(varV97RemoteReady,false));
    Set(varV97SaveMessage,If(varV97SnapKind="restore","השחזור לא נשמר: ","העברת המצב למבנה v9 נכשלה; השמירה המשותפת מושבתת: ")&varV97SnapError);
    Notify(varV97SaveMessage,NotificationType.Error)
  )
)''')

WRITE_EVENT = sub(r'''=If(varV97RemoteReady && varV97Syncing && !IsEmpty(colV97Batch),
  Set(varV97WriteOk,true);
  IfError(
    Set(varV97NewerGen,LookUp(DashboardPOC_Data,%P% && field_3="V97Snapshot9" && field_11>varV97Gen));
    If(!IsBlank(varV97NewerGen.ID),Error({Kind:ErrorKind.Custom,Message:"STALE"}));
    ClearCollect(colV97Envelopes,ForAll(colV97Batch As b,{Entity:b.Entity,Key:b.Key,Env:JSON({V:9,Dataset:varV97Dataset,Gen:varV97Gen,Entity:b.Entity,Key:b.Key,Deleted:b.Deleted,Payload:b.Payload,At:Text(Now(),DateTimeFormat.UTC),Author:User().FullName,AuthorEmail:User().Email},JSONFormat.Compact)}));
    If(CountIf(colV97Envelopes,Len(Env)>30000)>0,Error({Kind:ErrorKind.Custom,Message:"השינוי ארוך מדי לשמירה ברשומה אחת (מעל 30,000 תווים)"}));
    ClearCollect(colV97Written,ForAll(colV97Envelopes As v,Patch(DashboardPOC_Data,Defaults(DashboardPOC_Data),{Title:"V97-EVENT9-"&Text(GUID()),field_1:varV97CompanyID,field_2:varV97PeriodID,field_3:"V97Event9",field_10:-1,field_11:varV97Gen,field_14:varV97Dataset,AuditNote:v.Env})));
    ForAll(colV97Written As w,IfError(Patch(DashboardPOC_Data,LookUp(DashboardPOC_Data,ID=w.ID),{field_10:w.ID});true,false));
    true,
    Set(varV97WriteOk,false);Set(varV97WriteError,FirstError.Message);false
  );
  If(varV97WriteOk,
    Set(varV97SaveMessage,"השינוי נשמר; מרענן את המצב המשותף…");Set(varV97WriteGen,varV97Gen);Set(varV97PendingWriteCheck,true);
    If(LookUp(colV97Batch,Entity="Entries" && !Deleted,true),Reset(V97Amount);Reset(V97Description);Reset(V97Reference));
    If(LookUp(colV97Batch,Entity="Docs" && !Deleted,true),Reset(V97ExtDocName);Reset(V97ExtDocUrl));
    Clear(colV97Batch);Select(V97LoadShared),
    If(varV97WriteError="STALE",
      Set(varV97SaveMessage,"משתמש אחר שחזר גיבוי; המצב נטען מחדש והשינוי לא נשמר. בצע אותו שוב לאחר הטעינה.");Notify(varV97SaveMessage,NotificationType.Warning);Clear(colV97Batch);Select(V97LoadShared),
      Set(varV97Syncing,false);Set(varV97SaveMessage,"השינוי לא נשמר: "&varV97WriteError&If(CountRows(colV97Written)>0," (חלק מהרשומות נשמרו; רענן מהצוות)",""));Notify(varV97SaveMessage,NotificationType.Error)
    )
  ),
  Set(varV97Syncing,false);Notify("יש לרענן את המצב המשותף לפני שמירה",NotificationType.Warning)
)''')

IMPORT_STATE = r'''=Set(varV97ImportOk,true);
IfError(Set(varV97Incoming,ParseJSON(varV97ImportText));true,Set(varV97ImportOk,false);false);
If(varV97ImportOk,IfError(If(IsBlank(varV97Incoming.Entries) || IsBlank(varV97Incoming.Notes) || IsBlank(varV97Incoming.Reviews) || IsBlank(varV97Incoming.Links) || IsBlank(varV97Incoming.Urls) || IsBlank(varV97Incoming.History) || !(Value(varV97Incoming.Version) in [1,2,9]) || Text(varV97Incoming.Dataset)<>varV97Dataset,Set(varV97ImportOk,false));true,Set(varV97ImportOk,false);false));
If(varV97ImportOk,IfError(
  ClearCollect(colV97StageEntries,ForAll(Table(varV97Incoming.Entries) As j,{Id:Text(j.Value.Id),Debit:Text(j.Value.Debit),Credit:Text(j.Value.Credit),Amount:Value(j.Value.Amount),Description:Text(j.Value.Description),Reference:Text(j.Value.Reference),Flow:Text(j.Value.Flow),CashDelta:Value(j.Value.CashDelta),At:Text(j.Value.At)}));
  ClearCollect(colV97StageNotes,ForAll(Table(varV97Incoming.Notes) As j,{Key:Text(j.Value.Key),Text:Text(j.Value.Text),At:Text(j.Value.At)}));
  ClearCollect(colV97StageReviews,ForAll(Table(varV97Incoming.Reviews) As j,{Key:Text(j.Value.Key),Status:Text(j.Value.Status),Note:Text(j.Value.Note),At:Text(j.Value.At)}));
  ClearCollect(colV97StageLinks,ForAll(Table(varV97Incoming.Links) As j,{Key:Text(j.Value.Key),TargetKey:Text(j.Value.TargetKey),DocId:Text(j.Value.DocId),Section:Text(j.Value.Section),Account:Text(j.Value.Account),Name:Text(j.Value.Name)}));
  ClearCollect(colV97StageUrls,ForAll(Table(varV97Incoming.Urls) As j,{DocId:Text(j.Value.DocId),Url:Text(j.Value.Url)}));
  Clear(colV97StageDocs);If(!IsBlank(varV97Incoming.Docs),Collect(colV97StageDocs,ForAll(Table(varV97Incoming.Docs) As j,{DocId:Text(j.Value.DocId),Name:Text(j.Value.Name),Url:Text(j.Value.Url),At:Text(j.Value.At)})));
  ClearCollect(colV97StageHistory,ForAll(Table(varV97Incoming.History) As j,{Id:Text(j.Value.Id),Key:Text(j.Value.Key),Action:Text(j.Value.Action),At:Text(j.Value.At),User:Text(j.Value.User)}));
  Set(varV97StageMateriality,Value(varV97Incoming.Materiality));Set(varV97StageMarket,Value(varV97Incoming.Market));
  Set(varV97StageVersion,Value(varV97Incoming.Version));
  true,Set(varV97ImportOk,false);false));
If(varV97ImportOk,
  Set(varV97ApplyMode,"restore");Set(varV97Legacy,false);Set(varV97LoadOk,true);
  If(varV97StageVersion<9,Select(V97ConvertStage),Select(V97ApplyState)),
  Set(varV97Syncing,false);Set(varV97SaveMessage,"הגיבוי אינו JSON תקין של דשבורד זה; המצב לא הוחלף");Notify(varV97SaveMessage,NotificationType.Error)
)'''

# full change log (B12): every Event9 of every generation, paged on field_10
AUDIT_PAGE = ('If(varV97More,ClearCollect(colV97EvPage,ShowColumns(SortByColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Event9" && field_10>varV97Cursor),"field_10",SortOrder.Ascending),ID,field_10,field_11,AuditNote,Created));'
              'Collect(colV97AuditRaw,colV97EvPage);Set(varV97More,!IsEmpty(colV97EvPage));If(!IsEmpty(colV97EvPage),Set(varV97Cursor,Max(colV97EvPage,field_10))));')
AUDIT_LOG = sub(r'''=IfError(
  Clear(colV97AuditRaw);Set(varV97Cursor,0);Set(varV97More,true);
  %PAGES%
  Collect(colV97AuditRaw,ShowColumns(Filter(DashboardPOC_Data,%P% && field_3="V97Event9" && field_10=-1),ID,field_10,field_11,AuditNote,Created));
  ClearCollect(colV97AuditLog,SortByColumns(ForAll(colV97AuditRaw As e,With({j:IfError(ParseJSON(e.AuditNote),ParseJSON("{}"))},{EventId:e.ID,Gen:e.field_11,Entity:IfError(Text(j.Entity),"?"),Key:IfError(Text(j.Key),""),Deleted:IfError(Boolean(j.Deleted),false),At:IfError(Text(j.At),""),Author:IfError(Text(j.Author),""),Payload:IfError(Text(j.Payload),"")})),"EventId",SortOrder.Ascending));
  Set(varV97ExportText,"יומן שינויים מלא · "&varV97Company&" · "&Text(CountRows(colV97AuditLog))&" רשומות"&If(varV97More," · היומן חלקי: קיימות רשומות נוספות מעבר ל-"&Text(%PAGES_N%)&" עמודים","")&Char(10)&"מזהה"&Char(9)&"דור"&Char(9)&"זמן"&Char(9)&"משתמש"&Char(9)&"ישות"&Char(9)&"מפתח"&Char(9)&"פעולה"&Char(9)&"תוכן"&Char(10)&Concat(colV97AuditLog,Text(EventId)&Char(9)&Text(Gen)&Char(9)&%CL_At%&Char(9)&%CL_Author%&Char(9)&Entity&Char(9)&%CL_Key%&Char(9)&If(Deleted,"הוסר","עודכן")&Char(9)&%CL_Payload%,Char(10)));
  Reset(V97Export);Set(varV97BackModal,"");Set(varV97Modal,"copy");
  true,
  Notify("טעינת היומן נכשלה: "&FirstError.Message,NotificationType.Error);false
)''').replace('%PAGES%', '\n  '.join([sub(AUDIT_PAGE)] * 20)).replace('%PAGES_N%', '20')


def cl(x):
    """TSV-safe text (B20)."""
    return 'Substitute(Substitute(Substitute(' + x + ',Char(9)," "),Char(13)," "),Char(10)," ")'

AUDIT_LOG = (AUDIT_LOG.replace('%CL_At%', cl('At')).replace('%CL_Author%', cl('Author'))
             .replace('%CL_Key%', cl('Key')).replace('%CL_Payload%', cl('Payload')))
