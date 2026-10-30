import re
def slim(t,keep=r'create_v27execute'):
    out=[];i=0;n=len(t)
    lines=t.split('\n'); res=[]; skip=False
    for l in lines:
        if skip:
            if l=='}': skip=False
            continue
        if l.startswith('define '):
            m=re.match(r'define (.*?)@("[^"]+"|[\w.$]+)\(',l)
            if not re.search(keep,m.group(2)):
                d=l[len('define '):].rstrip()
                assert d.endswith('{'); d=d[:-1].rstrip()
                d=re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local)\s+','',d)
                d=re.sub(r'\s+comdat(\([^)]*\))?','',d)
                d=re.sub(r'\s+personality\s+ptr\s+@\S+','',d)
                d=re.sub(r' (%[\w.$"]+)(?=[,)])','',d)  # drop arg names
                res.append('declare '+d); skip=True; continue
        if re.match(r'^@\S+ = .*\balias\b',l): continue
        res.append(l)
    return '\n'.join(res)
if __name__=='__main__':
    import sys; open(sys.argv[2],'w').write(slim(open(sys.argv[1]).read()))
