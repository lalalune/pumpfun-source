import struct
def fixfs(c):
    b=bytearray(c); i=0
    while i<len(b):
        op=b[i]
        if op in (0x7b,0x73,0x6b,0x63,0x7a,0x72,0x6a,0x62) and (b[i+1]&0xf)==10:
            off=struct.unpack_from('<h',b,i+2)[0]
            if off>=0: struct.pack_into('<h',b,i+2,off-0x1000)
        i+=16 if op==0x18 else 8
    return bytes(b)
