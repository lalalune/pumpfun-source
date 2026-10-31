import fcntl,time,sys,subprocess,pathlib,os
LOCKDIR=pathlib.Path(sys.argv[1]); N=int(os.environ.get('PUMP_BUILD_SLOTS','10'))
while True:
    for i in range(N):
        f=open(LOCKDIR/f'sbf{i}.lock','w')
        try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB); break
        except BlockingIOError: f.close(); f=None
    if f: break
    time.sleep(1)
sys.exit(subprocess.call(sys.argv[2:]))
