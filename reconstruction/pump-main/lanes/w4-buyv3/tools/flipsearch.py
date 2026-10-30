import sys,subprocess,itertools,re
f=sys.argv[1]
src=open('rpo.py').read()
blocks=[l.split(':')[0] for l in open(f) if re.match(r'^bb\d+:',l)]
def created(flips):
    r=subprocess.run(['python3','rpo.py',f]+['flip:'+x for x in flips],capture_output=True,text=True).stdout.split('\n')[1].split()[1:]
    return r
def good(c):
    i=c.index
    return (i('bb76')>i('bb83') and i('bb76')<i('bb50')) or (i('bb50')==i('bb76')+1)
for b in blocks:
    c=created([b])
    if good(c): print('single',b)
