exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3/e/common.py').read())
import runpy
G=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3/tools/genes30.py')['G']
EDITS=[(ARGS,''),(SKL,ARGS+SKL)]
for g in ['e_reset','u_sand']: EDITS+=G[g]
