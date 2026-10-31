def matched_ops(A,B):
    n,k=len(A),len(B); L=[[0]*(k+1) for _ in range(n+1)]
    for i in range(n-1,-1,-1):
        Li=L[i]; L1=L[i+1]; x=A[i]
        for j in range(k-1,-1,-1):
            Li[j]=L1[j+1]+1 if x==B[j] else (L1[j] if L1[j]>Li[j+1] else Li[j+1])
    i=j=0; ops=[]
    while i<n and j<k:
        if A[i]==B[j] and L[i][j]==L[i+1][j+1]+1: ops.append(('=',i,j)); i+=1; j+=1
        elif L[i+1][j]>=L[i][j+1]: ops.append(('-',i,None)); i+=1
        else: ops.append(('+',None,j)); j+=1
    ops+=[('-',x,None) for x in range(i,n)]+[('+',None,y) for y in range(j,k)]
    return ops
