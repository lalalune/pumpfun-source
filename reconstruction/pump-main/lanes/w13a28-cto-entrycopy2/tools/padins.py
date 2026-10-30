import sys,re
# padins.py in.ll out.ll NAME SIZE BEFORE : add alloca %NAME [SIZE x i8] align 8 just before alloca %BEFORE in execute, kept alive by a volatile store at entry
src,dst,name,size,before=sys.argv[1:6]
t=open(src).read()
i=t.index('admin_cto7execute'); i=t.index('\n',t.rfind('define',0,i+200))
pat='  %'+before+' = alloca'
j=t.index(pat,i)
t=t[:j]+'  %'+name+' = alloca ['+size+' x i8], align 8\n'+t[j:]
# volatile store after last alloca of the entry block
k=t.index('\n',t.index(pat,j))+1
# find end of consecutive alloca lines
while t[k:].startswith('  %') and ' = alloca ' in t[k:t.index('\n',k)]: k=t.index('\n',k)+1
t=t[:k]+'  store volatile i8 0, ptr %'+name+', align 1\n'+t[k:]
open(dst,'w').write(t)
