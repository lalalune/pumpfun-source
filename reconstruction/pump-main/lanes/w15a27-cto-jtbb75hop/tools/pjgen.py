# EDITS generator for mbp.sh: in rx/$PJN/sbp.mir, if the block 'bb.N.bb88' ends with a conditional jump and falls through
# to 'bb.M.bb37', add an explicit 'JMP %bb.M' (keeps main's layout: bb37 after the sharing CPI arm)
import os,re
s=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop/rx/'+os.environ['PJN']+'/sbp.mir')).read()
m=re.search(r'\n(    J\w+ [^\n]*%bb\.\d+)\n  \n  bb\.(\d+)\.bb37:',s)
i=s.rfind('\n  bb.',0,m.start()+1); hdr=s[i:i+40]
assert '.bb88:' in hdr,(hdr)
EDITS=[(m.group(0),'\n'+m.group(1)+'\n    JMP %bb.'+m.group(2)+'\n  \n  bb.'+m.group(2)+'.bb37:')]
