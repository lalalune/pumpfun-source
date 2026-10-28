"""Explicit offline dependency/root rebuild of the retained overflow control."""
from pathlib import Path
import argparse,gzip,importlib.util,json,shutil
HERE=Path(__file__).resolve().parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def run(args):
    parent=HERE.parent.parent;v=module('overflow_rebuild_parent',parent/'verify.py');c=module('overflow_rebuild_composition',HERE.parent/'verify.py');a=module('overflow_rebuild_sources',HERE/'verify.py');v.manifest_check(parent)
    if args.variant in ('checked-price-first-late','option-projection-late'):
        g=module('guard_rebuild_sources',HERE/'guard/verify.py');source=g.variant(HERE/'guard',v,c,a,c.sources(HERE.parent,v),args.variant);builds=HERE/'guard/builds'
    else:source=a.variant(HERE,v,c,c.sources(HERE.parent,v),args.variant);builds=HERE/'builds'
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);controller=output/'controller';shutil.copytree(parent/'controller',controller);rows=[]
    for name,b in sorted(source.items()):
        p=controller/'sources'/(name+'.gz');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(gzip.compress(b,mtime=0));rows.append(dict(path=name,**v.identity(b)))
    (controller/'source-inputs.json').write_text(json.dumps(dict(source_files=rows),indent=2)+'\n',encoding='utf-8')
    builder=module('overflow_rebuild_builder',controller/'build.py');args.output=output/'build';result=builder.build(args)
    expected=v.read(builds/args.variant/'result.json.gz')['outputs'];comparison=dict(outputs_equal=result['outputs']==expected,actual=result['outputs'],expected=expected,variant=args.variant,scope='Fresh offline dependency and root compilation; no target execution.')
    (output/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n',encoding='utf-8');v.require(comparison['outputs_equal'],'overflow full rebuild differs');return comparison
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sdk','target-sysroot','vendor','msvc','windows-sdk','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--kit-version',default='10.0.26100.0');p.add_argument('--variant',default='overflow-late',choices=['overflow-early','overflow-late','checked-price-first-late','option-projection-late'])
    print(json.dumps(run(p.parse_args()),indent=2))
