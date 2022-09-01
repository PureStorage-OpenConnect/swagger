#!/bin/bash
# there are no new pdf versions so don't update them.
#python3 convert_all_fa_pdf.py

#Pureset download update highest version mnumbers then run
python3 purest_download.py
python3 apply_templates.py
python3 create_spec_index.py

