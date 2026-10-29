# fnloc.py file fnname -> prints line range (1-based, incl. preceding attrs/doc lines) of `fn name`
import sys,re
def locate(path,name,nth=0):
    L=open(path).read().split('\n')
    hits=[i for i,l in enumerate(L) if re.search(r'\bfn\s+'+re.escape(name)+r'\b\s*[<(]',l)]
    i=hits[nth]
    # brace match from the fn line
    depth=0; started=False; j=i; col0=L[i].find('fn '+name)
    k=col0
    while True:
        line=L[j]
        rng=line[k:] if j==i else line
        for ch in rng:
            if ch=='{': depth+=1; started=True
            elif ch=='}':
                depth-=1
                if started and depth==0: return i,j,L
        j+=1
        if j>=len(L): raise SystemExit('no end')
if __name__=='__main__':
    i,j,L=locate(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 0)
    s=i
    while s>0 and (L[s-1].strip().startswith('#[') or L[s-1].strip().startswith('///')): s-=1
    print(s+1,i+1,j+1)
    for x in range(s,j+1): print(f'{x+1}: {L[x][:150]}')
