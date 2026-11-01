#!/bin/sh
# Cargo executes this hook directly; use the verified builder's interpreter.
exec "${PUMP_VERIFIED_PYTHON:?verified builder must select Python}" "${0%/*}/pump_physical_source_wrapper.py" "$@"
