#!/bin/bash
# batch.sh v1 v2 ... : src.sh two at a time
T=$(dirname "$0"); set -- "$@"
while [ $# -gt 0 ]; do
  if [ $# -ge 2 ]; then $T/src.sh $1 work0 & $T/src.sh $2 work1; wait; shift 2; else $T/src.sh $1 work0; shift; fi
done
