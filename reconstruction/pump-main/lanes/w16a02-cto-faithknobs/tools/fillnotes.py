#!/usr/bin/env python3
"""fillnotes.py: replace the 1f4e396 knob rows in NOTES.md with ktable.py output (bookkeeping)."""
import os,subprocess,re
T=os.path.dirname(os.path.abspath(__file__)); N=os.path.join(os.path.dirname(T),'NOTES.md')
rows=subprocess.run(['python3',T+'/ktable.py'],capture_output=True,text=True).stdout.strip().split('\n')
s=open(N).read()
lines=s.split('\n')
out=[l for l in lines if not re.match(r'^\| k_\w+ .*\(on 1f4e396\)',l)]
i=max(k for k,l in enumerate(out) if l.startswith('| k_hkpid'))
out=out[:i+1]+rows+out[i+1:]
open(N,'w').write('\n'.join(out))
print(len(rows),'rows')
