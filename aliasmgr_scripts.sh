# Alias Manager Integration Script
# This script is called from bashrc to allow
# one or many alias/function scripts to be
# called on BASH startup.
# Alias Manager will over-write any changes
# you make to this file.
echo 'Alias Manager - Loading scripts...'
if [ -f /home/cj/bash.integration.test.sh ]; then
    . /home/cj/bash.integration.test.sh
    echo 'Loaded /home/cj/bash.integration.test.sh'
else
    echo 'Alias Manager file not found: /home/cj/bash.integration.test.sh'
fi
echo ' '
echo 'Alias Manager script files loaded.'
echo ' '
