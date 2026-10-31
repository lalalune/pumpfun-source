import sys,difflib
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a89-cto-jtnodup/tools/amap.py').read().split('o=toks(O)')[0])
a=toks(open(sys.argv[1],'rb').read()); b=toks(open(sys.argv[2],'rb').read())
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
mn=int(sys.argv[3]) if len(sys.argv)>3 else 8
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal' and max(i2-i1,j2-j1)>=mn: print(op,(i1,i2),(j1,j2),i2-i1,j2-j1)
print('ratio',round(sm.ratio(),4),len(a),len(b))
