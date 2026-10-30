#!/usr/bin/env python3
"""getfn.py <ll> <regex> : print the first function definition whose name matches regex (metadata refs stripped)."""
import re,sys
t=open(sys.argv[1]).read()
m=re.search(r'\ndefine [^\n]*@"?[^\n(]*'+sys.argv[2]+r'[^\n(]*"?\([^\n]*\n',t)
s=m.start()+1; e=t.find('\n}\n',s)+3
body=t[s:e]
if len(sys.argv)>3 and sys.argv[3]=='--strip':
    body=re.sub(r', ![\w.]+ ![0-9]+','',body); body=re.sub(r' #[0-9]+','',body)
print(body,end='')
