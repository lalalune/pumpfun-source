"""Parse the line-table asm (rustc --emit=asm -C debuginfo=line-tables-only) into per-function instruction->(file,line,col)."""
import re,sys,os,pickle,json
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom'
S=OUT+'/lines/cap/lines.s'
def parse():
    files={}; funcs={}; cur=None; loc=None; pending=None
    for line in open(S):
        if line.startswith('\t.file\t'):
            m=re.match(r'\t\.file\t(\d+)\s+"([^"]*)"(?:\s+"([^"]*)")?',line)
            if m: files[int(m.group(1))]=(m.group(2)+'/'+m.group(3)) if m.group(3) else m.group(2)
            continue
        if line.startswith('\t.type\t') and '@function' in line:
            pending=line.split('\t')[2].split(',')[0].strip(); continue
        if not line.startswith(('\t',' ')) and line.rstrip().endswith(':'):
            name=line.rstrip()[:-1]
            if name==globals().get('pending_name') or name==locals().get('pending'):
                cur=name; funcs.setdefault(cur,[]); loc=None
            continue
        if cur is None: continue
        s=line.strip()
        if s.startswith('.loc'):
            m=re.match(r'\.loc\s+(\d+)\s+(\d+)\s+(\d+)',s)
            if m: loc=(int(m.group(1)),int(m.group(2)),int(m.group(3)))
            continue
        if not s or s.startswith(('.','#')) or s.endswith(':'): 
            if s.startswith('.Lfunc_end'): cur=None
            continue
        # instruction line
        funcs[cur].append((s,loc))
    return files,funcs
if __name__=='__main__':
    files,funcs=parse()
    pickle.dump((files,funcs),open(OUT+'/lines/asm.pkl','wb'))
    print(len(files),len(funcs))
    k=[f for f in funcs if 'admin_cto7execute' in f][0]
    print(k,len(funcs[k]))
