import json,sys,re,subprocess
ck=sys.argv[1]
for l in open('results.jsonl'):
    r=json.loads(l)
    if r['ckey']==ck: D=r['out_dir']
subprocess.run([sys.executable,'-B','harness/sell_score.py',D,'--disasm'],cwd='/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm',capture_output=True)
lines=open(D+'/sell-align.diff').read().splitlines()
def op(l):
    t=l[16:].split(';')[0].strip(); return re.sub(r'0x[0-9a-f]+|-?\d+','N',t)
i=0
while i<len(lines):
    if lines[i][:1] in '+-':
        j=i
        while j<len(lines) and lines[j][:1] in '+-': j+=1
        h=lines[i:j]
        if [op(l) for l in h if l[0]=="-"]!=[op(l) for l in h if l[0]=="+"] or any("r9" in l for l in h):
            print('----', i)
            for l in lines[max(0,i-2):j+1]: print(l[:120])
        i=j
    else: i+=1
