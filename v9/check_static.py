import sys,re
from parse import load,walk
import pfx
ROWFUNCS={'Filter':1,'LookUp':1,'ForAll':1,'AddColumns':1,'CountIf':1,'Sum':1,'Max':1,'Min':1,'Concat':1,'Sort':1,'Distinct':1,'RemoveIf':1,'UpdateIf':1,'Average':1}
KNOWN_FUNCS=set(n[2:] for n in dir(pfx.App) if n.startswith('f_'))
def analyze(path):
    c=walk(load(path)); ctrls={n for n,_,_,_ in c}
    issues=[]
    for name,par,_,p in c:
        for k,v in p.items():
            v=str(v)
            if not v.startswith('='): continue
            ast=pfx.parse(v)
            def walkn(n,scope):
                kind=n[0]
                if kind=='id':
                    nm=n[1]
                    if nm.startswith('V97') and nm not in ctrls: issues.append((name,k,'unknown control '+nm))
                    return
                if kind=='dot':
                    b=n[1]
                    if b[0]=='id' and re.fullmatch(r'[a-z][a-zA-Z0-9_]{0,8}',b[1]) and b[1] not in ('var',) and not b[1].startswith(('var','col')):
                        if b[1] not in scope: issues.append((name,k,'UNBOUND alias/name '+b[1]+'.'+n[2]))
                    walkn(b,scope); return
                if kind=='call':
                    fn,args=n[1],n[2]
                    if fn not in KNOWN_FUNCS: issues.append((name,k,'unknown function '+fn))
                    if fn=='With':
                        walkn(args[0],scope)
                        names=set(f for f,_ in args[0][1]) if args[0][0]=='rec' else set()
                        for a in args[1:]: walkn(a,scope|names)
                        return
                    if fn in ROWFUNCS and args:
                        a0=args[0]; alias=None
                        if a0[0]=='as': alias=a0[2]; walkn(a0[1],scope)
                        else: walkn(a0,scope)
                        inner=scope|({alias} if alias else set())
                        for a in args[1:]: walkn(a,inner)
                        return
                    for a in args:
                        if a[0]=='as': walkn(a[1],scope); issues.append((name,k,'As in non-row function '+fn))
                        else: walkn(a,scope)
                    return
                if kind in('bin',): walkn(n[2],scope);walkn(n[3],scope);return
                if kind in('and','or'): walkn(n[1],scope);walkn(n[2],scope);return
                if kind in('not','neg'): walkn(n[1],scope);return
                if kind=='chain':
                    for x in n[1]: walkn(x,scope)
                    return
                if kind=='rec':
                    for _,e in n[1]: walkn(e,scope)
                    return
                if kind=='arr':
                    for e in n[1]: walkn(e,scope)
                    return
            walkn(ast,set())
    print(path,'issues',len(issues))
    for i in issues: print('  ',i)
for p in sys.argv[1:]: analyze(p)
