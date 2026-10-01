import yaml,sys,json
def load(p):
    return yaml.safe_load(open(p,encoding='utf-8'))
def walk(nodes,parent=None,out=None):
    if out is None: out=[]
    for n in nodes:
        (name,body),=n.items()
        out.append((name,parent,body.get('Control'),body.get('Properties',{})))
        if 'Children' in body and body['Children']:
            walk(body['Children'],name,out)
    return out
if __name__=='__main__':
    d=load(sys.argv[1]); ctr=walk(d)
    print(len(ctr))
    skip=set(sys.argv[2].split(',')) if len(sys.argv)>2 else set()
    for name,par,c,p in ctr:
        if name.startswith('V97Load') and name not in ('V97LoadShared','V97LoadLocal'): continue
        print(f"### {name} [{c}] parent={par}")
        for k,v in p.items():
            v=str(v)
            if k in skip: continue
            if len(v)>1500: v=v[:1500]+f"...[+{len(v)-1500}]"
            print(f"  {k}: {v}")
