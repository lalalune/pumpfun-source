import re
def ren(t):
    """rename numbered SSA values/blocks in define bodies to %vN so edits can move instructions."""
    out=[];inb=False
    for l in t.split('\n'):
        if l.startswith('define '): inb=True; out.append(re.sub(r'%(\d+)\b',r'%v\1',l)); continue
        if inb and l=='}': inb=False
        if inb:
            l=re.sub(r'(?<![\w.$"])%(\d+)\b',r'%v\1',l)
            l=re.sub(r'^(\d+):',r'v\1:',l)
        out.append(l)
    return '\n'.join(out)
