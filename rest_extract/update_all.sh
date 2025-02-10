#!/bin/bash
echo "Get the latest files from artfactory: https://artifactory.pstg-inf.net/ui/repos/tree/General/virtual-pure-shared-purest-maven/release/com/purestorage/purest"

echo "And extract to definitions/oas2.0 & definitions/oas3.0 (not used yet)"
read -p "Press enter to continue"

python3 apply_templates.py
python3 create_spec_index.py