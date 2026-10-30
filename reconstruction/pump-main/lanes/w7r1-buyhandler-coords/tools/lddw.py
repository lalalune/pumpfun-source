import sys,struct
sys.path.insert(0,'.')
from score import BASE
from original_input import resolve_original
exec(open(sys.argv[0].replace('lddw.py','loc.py')).read().split('blob = load')[0])
p=sys.argv[1]; start=int(sys.argv[2],16); n=int(sys.argv[3])
blob=open(resolve_original(BASE/'original.so') if p=='orig' else p,'rb').read()
code=vread(blob,start,n)
i=0
while i<len(code):
    op=code[i]
    if op==0x18:
        lo=struct.unpack_from('<I',code,i+4)[0]; hi=struct.unpack_from('<I',code,i+12)[0]; v=lo|hi<<32
        try:
            d=vread(blob,v,24); pp,l,line,col=struct.unpack('<QQII',d); s=vread(blob,pp,min(l,80)) if 0<l<200 else None
        except Exception: pp=l=line=col=None; s=None
        print(hex(start+i),hex(v),'loc?',line,col,s)
        i+=16
    else: i+=8
