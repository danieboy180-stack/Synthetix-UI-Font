#!/usr/bin/env bash
set -e; cd "$(dirname "$0")/scripts"
python3 varbuild.py 300 400 500
python3 export_family.py
python3 qa_font.py && python3 interp_test.py && python3 confusables.py A
