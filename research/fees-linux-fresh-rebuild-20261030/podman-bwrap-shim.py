#!/usr/bin/env python3
"""Local substitute for `podman run` used ONLY by programs/pump-fees/build_exact.py.
Deviation: no container image; runs the same argv under bubblewrap with the host's
/usr,/lib,/etc userland, same bind paths, same env (cleared), no network."""
import os,sys
a=sys.argv[1:]; assert a[0]=="run", a
i=1; binds=[]; env=[]; wd=None; ent=None; net=False
IMAGE="solanafoundation/solana-verifiable-build@sha256:6c73adc767ee7ff212f2532d4695472b12f3d4ac20aea3db22b89d8c614dac50"
while a[i]!=IMAGE:
    x=a[i]
    if x in("--rm",): i+=1
    elif x.startswith("--pull=") or x.startswith("--entrypoint="):
        if x.startswith("--entrypoint="): ent=x.split("=",1)[1]
        i+=1
    elif x=="--platform": assert a[i+1]=="linux/amd64"; i+=2
    elif x=="--network": assert a[i+1]=="none"; net=True; i+=2
    elif x=="-v": h,c,m=a[i+1].rsplit(":",2) if a[i+1].count(":")>=2 else (*a[i+1].split(":"),"rw"); binds.append((h,c,m)); i+=2
    elif x=="-e": env.append(a[i+1].split("=",1)); i+=2
    elif x=="-w": wd=a[i+1]; i+=2
    else: sys.exit("shim: unknown option "+x)
cmd=a[i+1:]
b=["bwrap","--die-with-parent","--unshare-all","--clearenv","--dev","/dev","--proc","/proc","--tmpfs","/tmp"]
for d in("/usr","/etc","/bin","/lib","/lib64","/sbin"):
    if os.path.exists(d): b+=["--ro-bind",d,d]
for h,c,m in sorted(binds,key=lambda t:t[1].count("/")):
    b+=["--bind" if m=="rw" else "--ro-bind",h,c]
for k,v in env: b+=["--setenv",k,v]
b+=["--chdir",wd,ent]+cmd
os.execvp("bwrap",b)
