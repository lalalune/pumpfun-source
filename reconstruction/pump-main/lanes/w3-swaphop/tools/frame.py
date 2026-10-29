# frame.py sh.mir : list frame objects (id, type, offset, size)
import sys,re
t=open(sys.argv[1]).read()
st=t[t.index('\nstack:'):]; st=st[:st.index('\ncallSites') if '\ncallSites' in st else len(st)]
for m in re.finditer(r"id: (\d+), name: ([^,]*), type: ([\w-]+), offset: (-?\d+), size: (\d+)",st):
    i,n,ty,off,sz=m.groups(); print(i,ty,hex(-int(off)),sz,n)
