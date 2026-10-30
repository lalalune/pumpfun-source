#!/usr/bin/env python3
"""Linker for the root Pump cdylib: the default SBF script swapped for the crate's pinned link/ordered.ld."""
import os
import sys
from link_order import lld_main

lld_main(sys.argv, os.environ)
