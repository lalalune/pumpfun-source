#!/bin/bash
set -e
rm -rf ~/pumpwork/venv-handlers
python3 -m pip install --user --break-system-packages -q 'solders==0.27.1' 'pyelftools==0.32' 'jsonalias==0.1.1' 'typing_extensions==4.16.0'
python3 -c "import solders, elftools; print('solders', solders.__version__)"
