#!/bin/bash
# there are no new pdf versions so don't update them.

#Pureset download update highest version mnumbers then run
echo "Get the latest files from artfactory: https://artifactory.pstg-inf.net/ui/repos/tree/General/virtual-pure-shared-purest-maven/release/com/purestorage/purest"

echo "And extract to definitions/oas2 & definitions/oas3"
input "Press enter to continue"

python3 apply_templates.py
python3 create_spec_index.py

pyth