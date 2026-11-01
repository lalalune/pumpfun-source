#!/bin/bash
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a28-cto-skelunion17; cd $OUT
python3 tools/step.py K8_NAT_VE_FOp_S3_OL --mv58 --R 12 > /dev/null 2>&1
tools/c2q.sh K8_NAT_VE_FOp_S3_OL NAT VE
tools/joint.sh K8_NAT_VE_FOp_S3_OL > c2/j_K8_NAT_VE_FOp_S3_OL.json 2>&1
tools/joint.sh NAT > c2/j_NAT.json 2>&1
tools/joint.sh VE > c2/j_VE.json 2>&1
echo done > c2/olq.done
