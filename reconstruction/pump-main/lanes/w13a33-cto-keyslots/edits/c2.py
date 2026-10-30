import runpy
EDITS=[]
EDITS+=runpy.run_path('edits/v1.py')['EDITS']
EDITS+=runpy.run_path('edits/pf.py')['EDITS']
EDITS+=[('validate(&st,hopt,fee,new,','validate(&st,hopt,fee,args.0,')]
