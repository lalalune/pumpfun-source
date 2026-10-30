"""combo.py name=a+b+c ... : write e/<name>.py concatenating edits of e/a.py, e/b.py ..."""
import sys,os,json
D=os.path.dirname(os.path.abspath(__file__))
for spec in sys.argv[1:]:
    n,parts=spec.split('=')
    E=[]
    for p in parts.split('+'):
        g={};exec(open(f'{D}/{p}.py').read(),g); E+= [list(x) for x in g['EDITS']]
    open(f'{D}/{n}.py','w').write('EDITS='+json.dumps(E)+'\n'); print(n)
