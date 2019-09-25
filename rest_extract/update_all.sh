#!/bin/bash
python3 convert_all_fa_pdf.py
python3 purest_download.py
python3 apply_templates.py
python3 create_spec_index.py

