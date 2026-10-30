#!/usr/bin/env python3
"""RUSTC_WRAPPER: route only the root Pump cdylib's link through pump_link_lld.py (see link_order.py)."""
import os
import sys
from link_order import rustc_main

rustc_main(sys.argv, os.environ)
