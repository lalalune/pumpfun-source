#!/bin/sh
# The plain compiler hook also uses fastbuild's selected interpreter.
exec "${PUMP_RECON_PYTHON:?fastbuild must select Python}" "${0%/*}/pump_physical_source_wrapper.py" "$@"
