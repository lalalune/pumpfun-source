#!/bin/sh
# Keep the optional root-crate hook on the selected Python.
exec "${PUMP_VERIFIED_PYTHON:?text layout must select Python}" "${0%/*}/pump_text_layout_rustc.py" "$@"
