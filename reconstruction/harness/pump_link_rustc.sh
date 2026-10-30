#!/bin/sh
# Keep Cargo's link hook on the interpreter selected by link_order.configure.
exec "${PUMP_RECON_PYTHON:?configure must select Python}" "${0%/*}/pump_link_rustc.py" "$@"
