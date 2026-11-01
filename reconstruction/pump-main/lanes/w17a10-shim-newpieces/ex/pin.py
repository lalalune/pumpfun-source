exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/c1.py').read())
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/x3.py').read().split('V={')[0])
P660='  %230 = icmp eq i64 %val14, 0\n  br i1 %230, label %bb22, label %bb23\n'
def pin(v=True): return (P660, P660.replace('  br i1 %230,',f'  %e660 = call i1 @llvm.expect.i1(i1 %230, i1 {"true" if v else "false"})\n  br i1 %e660,'))
V={
 'pin660':[pin()],
 'pin660_x3h':[pin(),(B15,entry())],
 'pin660_c1a':[pin(),(VAL,piece('%sharing_update16','%val8'))],
 'pin660_x3a':[pin(),(B15,entry()),(VAL,c1('split'))],
}
