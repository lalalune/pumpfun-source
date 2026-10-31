# oracle: native zero edge carries constant 0 (orig hoists mov r9,0) instead of the usub.sat value
x='[ %568, %bb92.i ], [ 0, %bb37.i113 ], [ 0, %bb43.i116 ], [ %556, %bb90.i122 ], [ %556, %bb86.i ]'
EDITS=[(x,'[ %568, %bb92.i ], [ 0, %bb37.i113 ], [ 0, %bb43.i116 ], [ %556, %bb90.i122 ], [ 0, %bb86.i ]')]
