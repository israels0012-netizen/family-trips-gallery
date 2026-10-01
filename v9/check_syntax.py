import sys,time
from parse import load,walk
import pfx
def run(path):
    c=walk(load(path)); n=0; errs=[]
    t=time.time()
    for name,_,_,p in c:
        for k,v in p.items():
            v=str(v)
            if not v.startswith('='): continue
            n+=1
            try: pfx.parse(v)
            except Exception as e: errs.append((name,k,str(e)[:200]))
    print(path,'formulas',n,'errors',len(errs),'%.1fs'%(time.time()-t))
    for e in errs[:30]: print('  ',e)
for p in sys.argv[1:]: run(p)
