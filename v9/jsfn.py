import re,sys
js=open('template.js',encoding='utf-8').read()
def get(name):
    m=re.search(r'function\s+'+name+r'\s*\(',js)
    if not m: return None
    i=js.index('{',m.end()); d=0
    for j in range(i,len(js)):
        if js[j]=='{': d+=1
        elif js[j]=='}':
            d-=1
            if d==0: return js[m.start():j+1]
for n in sys.argv[1:]:
    print('//////',n); print(get(n))
