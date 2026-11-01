#!/bin/sh
# Rustc launches this hook directly, even when PATH has no python3.
exec "${PUMP_VERIFIED_PYTHON:?text layout must select Python}" "${0%/*}/pump_text_layout_linker.py" "$@"
