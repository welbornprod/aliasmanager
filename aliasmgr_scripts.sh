# Alias Manager Integration Script
# This script is called from bashrc to allow
# one or many alias/function scripts to be
# called on BASH startup.
# Alias Manager will over-write any changes
# you make to this file.
Alias Manager loading scripts...if [ -f /home/cj/bash.chmod.test.sh ]; then
    source /home/cj/bash.chmod.test.sh
    echo '    Loaded /home/cj/bash.chmod.test.sh'
else
    echo 'Alias Manager file not found: /home/cj/bash.chmod.test.sh'
fi
echo ' '
