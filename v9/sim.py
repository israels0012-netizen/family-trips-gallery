import time,sys
from parse import load
import pfx
V9='PowerApps_V97_CANVAS_SHARED_v9_ONE_PASTE.txt'
_DOC={}
def doc(path=V9):
    if path not in _DOC: _DOC[path]=load(path)
    return _DOC[path]
def start(sp=None,path=V9,user='User A',width=1440,height=900):
    app=pfx.App(doc(path),sp=sp,width=width,height=height,user=user)
    app.select('V97Start')
    return app
def state(app):
    g=app.globals
    return dict(ready=g.get('varV97Ready'),remote=g.get('varV97RemoteReady'),sync=g.get('varV97Syncing'),msg=g.get('varV97SaveMessage'),gen=g.get('varV97Gen'),through=g.get('varV97Through'))
def unhandled(app): return [n for n in app.notes if n[0]=='UNHANDLED']
if __name__=='__main__':
    t=time.time()
    sp=pfx.SPList()
    a=start(sp)
    print('%.1fs'%(time.time()-t), state(a))
    print({k:len(v) for k,v in a.cols.items() if k in('colV97Base','colV97Drill','colV97Documents','colV97Matches','colV97Components','colV97Charts','colV97Rows','colV97AllDrill','colV97EvidenceTargets','colV97EvidenceItems','colV97LinkTargetsAll','colV97MatchesX')})
    print('notes',a.notes[-8:]); print('sp rows',len(sp.rows),[ (r['field_3'],r['field_10'],r['field_11']) for r in sp.rows])
    print('warn',a.warnings[:5])
