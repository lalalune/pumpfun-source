import sys,subprocess
f,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
out=subprocess.run(['python3','/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a10-cto-newentrycopy/tools/dis.py',f,'0','99999'],capture_output=True,text=True).stdout
for l in out.splitlines():
    try: a=int(l.split()[0],16)
    except: continue
    if lo<=a<=hi: print(l)
