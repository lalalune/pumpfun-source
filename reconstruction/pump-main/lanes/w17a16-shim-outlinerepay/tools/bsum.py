#!/usr/bin/env python3
"""bsum.py <m.ll> [from] [count]: summarize execute's post-opt blocks: name, error codes, calls, terminator."""
import sys,re
t=open(sys.argv[1]).read()
m=re.search(r'^define [^\n]*admin_cto7execute[^\n]*\{\n(.*?)\n\}\n',t,re.M|re.S)
body=m.group(1)
blocks=re.split(r'\n(?=[\w.$-]+:)',body)
CODE={6088:284,6083:289,6084:296,6090:298,6089:306,6030:307,6019:312,6091:326,6080:330,6077:334,6078:338,6095:410}
start=sys.argv[2] if len(sys.argv)>2 else 'bb6.i'; cnt=int(sys.argv[3]) if len(sys.argv)>3 else 40
names=[re.match(r'([\w.$-]+):',b).group(1) if re.match(r'([\w.$-]+):',b) else 'start' for b in blocks]
i=names.index(start)
for b,n in list(zip(blocks,names))[i:i+cnt]:
    codes=[CODE[int(c)] for c in re.findall(r'store i32 (\d+)',b) if int(c) in CODE]
    lines=[int(c) for c in re.findall(r'store i32 (\d+)',b) if 250<int(c)<800]
    calls=[re.sub(r'17h[0-9a-f]+E','',x)[-40:] for x in re.findall(r'call [^@]*@"?([^"(]+)',b) if 'lifetime' not in x and 'memcpy' not in x]
    term=b.strip().split('\n')[-1].strip()[:110]
    print(f'{n:14s} codes={codes} lines={lines} calls={[c.split("$")[-1][-28:] for c in calls][:4]} | {term}')
