import sys,re
print('errorder',' '.join(str(int(m,16)) for m in re.findall(r'stw \[r10 - 0x2b8\], (0x[0-9a-f]+)',open(sys.argv[1]).read())))
