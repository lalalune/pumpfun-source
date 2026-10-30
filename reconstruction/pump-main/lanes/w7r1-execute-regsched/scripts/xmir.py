import sys
t=open(sys.argv[1]).read()
i=t.index('fn sweep::execute(')
j=t.index('\nfn ',i+10)
print(t[i:j])
