#!/bin/sh
# Rustc executes this hook directly; PATH may have an older Python or none.
exec "${PUMP_RECON_PYTHON:?configure must select Python}" "${0%/*}/pump_link_lld.py" "$@"
