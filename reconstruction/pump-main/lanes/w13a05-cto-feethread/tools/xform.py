import sys,runpy
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g=runpy.run_path(p)
n0=s.count('\n'); s=g['transform'](s); assert s.count('\n')==n0,'newline count changed'
open(f,'w').write(s)
