import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import relab as R, json
b=R.g['elf_fn'](sys.argv[1],R.g['KEEP']); sp=R.spills(sys.argv[2]); mp,_=R.bestperm(b,sp,3)
print(json.dumps({'f':sys.argv[1],'bytes':len(b),'M':R.M(b),'ratio':R.ratio(b),'Mperm':mp}))
