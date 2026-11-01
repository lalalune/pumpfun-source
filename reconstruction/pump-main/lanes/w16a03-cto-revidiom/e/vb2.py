import runpy,os
E=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb01v.py'))['EDITS']
EDITS=[("sharing_update=Some(args.0);","sharing_update=match args.0{Some(_)=>Some(Some(target)),None=>Some(None)};")]+E[1:]
