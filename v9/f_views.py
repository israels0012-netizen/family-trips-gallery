# -*- coding: utf-8 -*-
"""v9 Initialize / RebuildViews additions."""

SCHEMAS = r'''ClearCollect(colV97Entries,Table({Id:"",Debit:"",Credit:"",Amount:0.0,Description:"",Reference:"",Flow:"",CashDelta:0.0,At:""}));Clear(colV97Entries);
ClearCollect(colV97Notes,Table({Key:"",Text:"",At:""}));Clear(colV97Notes);
ClearCollect(colV97Reviews,Table({Key:"",Status:"",Note:"",At:""}));Clear(colV97Reviews);
ClearCollect(colV97Links,Table({Key:"",TargetKey:"",DocId:"",Section:"",Account:"",Name:""}));Clear(colV97Links);
ClearCollect(colV97Urls,Table({DocId:"",Url:""}));Clear(colV97Urls);
ClearCollect(colV97Docs,Table({DocId:"",Name:"",Url:"",At:""}));Clear(colV97Docs);
ClearCollect(colV97History,Table({Id:"",Key:"",Action:"",At:"",User:""}));Clear(colV97History);
ClearCollect(colV97StageEntries,colV97Entries);ClearCollect(colV97StageNotes,colV97Notes);ClearCollect(colV97StageReviews,colV97Reviews);ClearCollect(colV97StageLinks,colV97Links);ClearCollect(colV97StageUrls,colV97Urls);ClearCollect(colV97StageDocs,colV97Docs);ClearCollect(colV97StageHistory,colV97History);
ClearCollect(colV97ConvReviews,colV97Reviews);
ClearCollect(colV97StageErrors,Table({Msg:""}));Clear(colV97StageErrors);
ClearCollect(colV97Batch,Table({Entity:"",Key:"",Deleted:false,Payload:""}));Clear(colV97Batch);
ClearCollect(colV97Merge,Table({Entity:"",Key:"",EventId:0,Deleted:false,Payload:""}));Clear(colV97Merge);
ClearCollect(colV97Win,colV97Merge);ClearCollect(colV97SnapItems,colV97Merge);
ClearCollect(colV97Events,Table({EventId:0,Created:Now(),Entity:"",Key:"",Deleted:false,Payload:"",At:"",Author:"",Valid:false}));Clear(colV97Events);
ClearCollect(colV97Closed,Table({RowId:""}));Clear(colV97Closed);
ClearCollect(colV97Store,Table({Payload:""}));Clear(colV97Store);'''

def matches_x():
    status = ('If(IsMatch(m.AutoStatus,"פער",MatchOptions.Contains),"gap",If(IsMatch(m.AutoStatus,"לא ניתן",MatchOptions.Contains),"unable",'
              'If(IsMatch(m.AutoStatus,"לא רלוונטי",MatchOptions.Contains),"activity",If(IsMatch(m.AutoStatus,"תואם|תקין",MatchOptions.Contains),"match","unable"))))')
    return ('ClearCollect(colV97MatchesX,ForAll(Sequence(CountRows(colV97Matches)) As i,With({m:Index(colV97Matches,i.Value)},With({j:IfError(ParseJSON(m.Detail),ParseJSON("{}")),dc:LookUp(colV97Documents,DocId=m.DocId)},'
            'With({lvl:IfError(Text(j.matchLevel),"")},{Key:m.Key,ItemKey:m.Key,DocId:m.DocId,FileName:dc.Name,Section:m.Section,Account:Trim(m.Account),AccountName:m.Name,'
            'Level:If(lvl="Drill-down","Drill-down",Coalesce(lvl,"General")),TargetKey:If(lvl="Drill-down","drill:","general:")&m.Section&":"&Trim(m.Account),'
            'StatusKey:' + status + ',DocAmount:m.DocAmount,BookAmount:m.BookAmount,Difference:m.Difference,Reason:m.Reason,Detail:m.Detail,'
            'SectionLabel:Coalesce(IfError(Text(j.target.subSection),""),IfError(Text(j.target.mainSection),""),IfError(Text(j.target.code),""),LookUp(colV97Base,RowId=m.Section,Name)),'
            'TargetCode:IfError(Text(j.target.code),""),'
            'Meta:Concat(Filter(Table({v:dc.Type},{v:dc.Date},{v:IfError(Text(j.confidence),"")}),!IsBlank(v)),v," | "),'
            'Note:IfError(Text(j.numericCheck.note),""),'
            'Evidence:IfError(Concat(Table(j.evidenceForMatch),"• "&Text(ThisRecord.Value),Char(10)),""),'
            'Currency:IfError(Text(j.numericCheck.documentCurrency),""),JsonAmount:IfError(Value(j.numericCheck.jsonAmount),Blank()),'
            'Ord:i.Value,Manual:false,LinkKey:""})))));')

INIT_EXTRA = matches_x() + r'''
ClearCollect(colV97Closed,ShowColumns(Filter(colV97Base,HasChildren && Depth>=1),RowId));'''

# RebuildViews: drill with stable order, manual rows (B19 keys), evidence model (B05)
ALLDRILL = r'''ClearCollect(colV97AllDrill,ForAll(Sequence(CountRows(colV97Drill)) As i,Patch(Index(colV97Drill,i.Value),{Ord:i.Value})));
Collect(colV97AllDrill,ForAll(colV97Entries As e,With({r:LookUp(colV97Base,RowId=e.Debit)},{Key:"MANUAL|"&e.Id&"|D",Section:e.Debit,Page:r.Page,Name:e.Description,Account:"MANUAL-"&e.Id,Code:r.Code,Current:e.Amount*r.DebitSign,Prior:0,Source:"manual_entry",Side:"debit",OtherCurrency:"",OtherCurrent:Blank(),OtherPrior:Blank(),Rate:Blank(),HasFx:false,Detail:JSON(e,JSONFormat.Compact),Ord:100000+CountRows(colV97AllDrill)})));
Collect(colV97AllDrill,ForAll(colV97Entries As e,With({r:LookUp(colV97Base,RowId=e.Credit)},{Key:"MANUAL|"&e.Id&"|C",Section:e.Credit,Page:r.Page,Name:e.Description,Account:"MANUAL-"&e.Id,Code:r.Code,Current:-e.Amount*r.DebitSign,Prior:0,Source:"manual_entry",Side:"credit",OtherCurrency:"",OtherCurrent:Blank(),OtherPrior:Blank(),Rate:Blank(),HasFx:false,Detail:JSON(e,JSONFormat.Compact),Ord:200000+CountRows(colV97AllDrill)})));'''

EVIDENCE = r'''ClearCollect(colV97AllDocs,colV97Documents);
Collect(colV97AllDocs,ForAll(colV97Docs As x,{DocId:x.DocId,Name:x.Name,Type:"מסמך חיצוני",Category:"external",Date:x.At,Url:x.Url,Detail:JSON({documentId:x.DocId,fileName:x.Name,documentType:"מסמך חיצוני",documentDate:x.At,documentUrl:x.Url,manualExternal:true},JSONFormat.Compact)}));
ClearCollect(colV97EvidenceItems,ShowColumns(colV97MatchesX,ItemKey,TargetKey,DocId,FileName,Section,Account,AccountName,Level,StatusKey,DocAmount,BookAmount,Difference,Reason,Detail,SectionLabel,TargetCode,Meta,Note,Evidence,Currency,JsonAmount,Ord,Manual,LinkKey));
Collect(colV97EvidenceItems,ForAll(Filter(colV97Links As l,IsBlank(LookUp(colV97MatchesX,TargetKey=l.TargetKey && DocId=l.DocId).Key)) As l,With({dc:LookUp(colV97AllDocs,DocId=l.DocId)},{ItemKey:"LINK|"&l.Key,TargetKey:l.TargetKey,DocId:l.DocId,FileName:dc.Name,Section:l.Section,Account:l.Account,AccountName:"",Level:If(StartsWith(l.TargetKey,"drill:"),"Drill-down","שיוך לסעיף"),StatusKey:"manualAssigned",DocAmount:Blank(),BookAmount:Blank(),Difference:Blank(),Reason:If(StartsWith(l.DocId,"EXT-"),"צורף ידנית","שויך ידנית"),Detail:JSON(l,JSONFormat.Compact),SectionLabel:LookUp(colV97Rows,RowId=l.Section,Name),TargetCode:LookUp(colV97Rows,RowId=l.Section,Code),Meta:dc.Type,Note:"",Evidence:"",Currency:"",JsonAmount:Blank(),Ord:1000000,Manual:true,LinkKey:l.Key})));
ClearCollect(colV97EvidenceView,colV97EvidenceItems);
ClearCollect(colV97EvidenceTargets,ForAll(Distinct(colV97EvidenceItems,TargetKey) As g,With({its:Filter(colV97EvidenceItems,TargetKey=g.Value)},With({f:First(SortByColumns(its,"Ord",SortOrder.Ascending)),pr:Max(its,Switch(StatusKey,"gap",5,"unable",4,"activity",3,"match",2,"manualAssigned",1,0))},With({dr:LookUp(colV97AllDrill,Section=f.Section && Trim(Account)=f.Account),sr:LookUp(colV97Rows,RowId=f.Section),isd:StartsWith(g.Value,"drill:")},
{TargetKey:g.Value,Section:f.Section,Account:f.Account,IsDrill:isd,Level:If(isd,"Drill-down",f.Level),SectionLabel:Coalesce(f.SectionLabel,sr.Name),
Desc:If(isd,Coalesce(dr.Name,f.AccountName),Coalesce(f.SectionLabel,sr.Name)),Code:If(isd,Coalesce(dr.Account,f.Account),Coalesce(f.TargetCode,sr.Code)),
Current:If(isd,dr.Current,sr.Current),Prior:If(isd,dr.Prior,sr.Prior),Currency:Coalesce(sr.Unit,varV97Unit),
AutoStatus:Switch(pr,5,"gap",4,"unable",3,"activity",2,"match",1,"manualAssigned","match"),Count:CountRows(its),
Files:Concat(Distinct(its,FileName),Value," | "),Ord:f.Ord,SortAmount:If(isd,Coalesce(dr.Current,0),Coalesce(f.JsonAmount,f.BookAmount,f.DocAmount,0)),
Hay:Concat(its,FileName&" "&Reason&" "&Account&" "&AccountName&" "&SectionLabel&" "&Meta," ")&" "&Coalesce(dr.Name,"")&" "&Coalesce(dr.Account,"")&" "&sr.Name})))));
ClearCollect(colV97LinkTargetsAll,ForAll(Distinct(Filter(colV97AllDrill,!IsBlank(Trim(Account))),Section&"|"&Trim(Account)) As g,With({x:LookUp(colV97AllDrill,Section&"|"&Trim(Account)=g.Value)},{TargetKey:"drill:"&x.Section&":"&Trim(x.Account),Section:x.Section,Account:Trim(x.Account),Name:LookUp(colV97Rows,RowId=x.Section,Name),Label:LookUp(colV97Rows,RowId=x.Section,Name)&" — "&Trim(x.Account)&" — "&x.Name&If(x.Source="manual_entry"," (פקודה ידנית)","")})));
Collect(colV97LinkTargetsAll,ForAll(Filter(colV97Base,Kind="item" && !HasChildren && Page<>"ratios") As r,{TargetKey:"general:"&r.RowId&":",Section:r.RowId,Account:"",Name:r.Name,Label:r.Name&If(IsBlank(r.Code),""," ["&r.Code&"]")&" — כל הסעיף"}));'''

REBUILD_TAIL = r'''If(varV97InitPending,Set(varV97InitPending,false);Select(V97LoadShared),If(varV97CheckpointNeeded && varV97RemoteReady,Select(V97Checkpoint)))'''
