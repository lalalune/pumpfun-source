#!/usr/bin/env python3
"""modparse.py: split a textual LLVM module into top-level entities (experiment only)."""
import re
DEF=re.compile(r'^define [^@]*(@"[^"]+"|@[\w.$-]+)\(')
DECL=re.compile(r'^declare [^@]*(@"[^"]+"|@[\w.$-]+)\(')
GLOB=re.compile(r'^(@"[^"]+"|@[\w.$-]+) = ')
REF=re.compile(r'@"[^"]+"|@[\w.$-]+')
def parse(text):
    """returns list of entities: (kind,name,lines) kind in define/declare/global/meta/other"""
    L=text.split('\n'); ents=[]; i=0; n=len(L)
    while i<n:
        l=L[i]
        m=DEF.match(l)
        if m:
            j=i
            while L[j]!='}': j+=1
            ents.append(('define',m.group(1),L[i:j+1])); i=j+1; continue
        m=DECL.match(l)
        if m: ents.append(('declare',m.group(1),[l])); i+=1; continue
        m=GLOB.match(l)
        if m: ents.append(('global',m.group(1),[l])); i+=1; continue
        if l.startswith('!'): ents.append(('meta',None,[l])); i+=1; continue
        ents.append(('other',None,[l])); i+=1
    return ents
def refs(lines):
    s=set()
    for l in lines:
        if '@' in l: s.update(REF.findall(l))
    return s
