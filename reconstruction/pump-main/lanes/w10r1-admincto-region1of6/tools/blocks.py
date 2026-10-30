import re
def split(fn):
    """returns header(list of lines up to first block label incl 'start:' block), blocks list[(label,text)], trailer"""
    lines=fn.split('\n')
    # first line is define ... {
    hdr=lines[0]
    blocks=[];cur=None;buf=[]
    for l in lines[1:]:
        m=re.match(r'^("[^"]+"|[A-Za-z0-9_.$\-]+):(\s|$)',l)
        if m or l=='}':
            if cur is not None or buf: blocks.append((cur,'\n'.join(buf)))
            if l=='}': cur=None;buf=[];break
            cur=m.group(1);buf=[l]
        else: buf.append(l)
    rest='\n'.join(lines[lines.index('}',1):])
    return hdr,blocks,rest
def join(hdr,blocks,rest):
    body='\n'.join(t for _,t in blocks)
    body=re.sub(r'%(\d+)\b',r'%v\1',body); body=re.sub(r'(?m)^(\d+):',r'v\1:',body)
    hdr=re.sub(r'%(\d+)\b',r'%v\1',hdr)
    return hdr+'\n'+body+'\n'+rest
def labels(fn):
    return [b for b,_ in split(fn)[1]]
def move(fn,names,after):
    h,b,r=split(fn)
    mv=[x for x in b if x[0] in names]; assert len(mv)==len(names),(names,[x[0] for x in mv])
    b=[x for x in b if x[0] not in names]
    k=[i for i,x in enumerate(b) if x[0]==after][0]
    b=b[:k+1]+mv+b[k+1:]
    return join(h,b,r)
