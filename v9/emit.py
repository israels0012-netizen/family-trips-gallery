import yaml,re,json
from parse import load,walk
SRC='v8_src.txt'
def raw_props(path):
    """map (ctrl,prop)->(value, raw_lines)"""
    lines=open(path,encoding='utf-8').read().split('\n')
    res={};cur=None;i=0
    while i<len(lines):
        L=lines[i]
        m=re.match(r'^(\s*)- (\w+):\s*$',L)
        if m: cur=m.group(2); i+=1; continue
        m=re.match(r'^(\s+)(\w+): (.*)$',L)
        if m and cur and m.group(2) not in ('Control','Variant'):
            ind=len(m.group(1)); raw=[L]; j=i+1
            while j<len(lines) and (lines[j]=='' or len(lines[j])-len(lines[j].lstrip())>ind) and not re.match(r'^\s*- \w+:\s*$',lines[j]):
                raw.append(lines[j]); j+=1
            # trailing blank lines belong to block only if inside
            while raw and raw[-1]=='' : raw.pop(); j-=1
            res[(cur,m.group(2))]=raw; i=j; continue
        i+=1
    return res
RAW=raw_props(SRC)
ORIG={}
for n,_,_,p in walk(load(SRC)):
    for k,v in p.items(): ORIG[(n,k)]=str(v)
def needs_block(v):
    if '\n' in v: return True
    try:
        r=yaml.safe_load('k: '+v)
        return not (isinstance(r,dict) and r.get('k')==v)
    except Exception: return True
def emit_ctrl(node,ind=0):
    (name,body),=node.items()
    p=' '*ind
    out=[f"{p}- {name}:"]
    for k,v in body.items():
        if k=='Properties':
            out.append(f"{p}    Properties:")
            for pk,pv in v.items():
                pv=str(pv)
                if ORIG.get((name,pk))==pv and (name,pk) in RAW:
                    out.extend(RAW[(name,pk)])
                elif needs_block(pv) or len(pv)>120:
                    out.append(f"{p}      {pk}: |-")
                    for line in pv.split('\n'):
                        out.append((f"{p}        {line}") if line else "")
                else:
                    out.append(f"{p}      {pk}: {pv}")
        elif k=='Children':
            out.append(f"{p}    Children:")
            for ch in v: out.extend(emit_ctrl(ch,ind+4))
        else:
            out.append(f"{p}    {k}: {v}")
    return out
def emit(doc):
    lines=[]
    for n in doc: lines.extend(emit_ctrl(n))
    return '\n'.join(lines)+'\n'
if __name__=='__main__':
    import sys
    d=load(sys.argv[1]); s=emit(d)
    o=open(sys.argv[1],encoding='utf-8').read()
    print(s==o, len(s),len(o))
    if s!=o:
        a=s.split('\n'); b=o.split('\n')
        for i,(x,y) in enumerate(zip(a,b)):
            if x!=y: print(i+1,repr(x[:200]),'\n   ',repr(y[:200])); break
