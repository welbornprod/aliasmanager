# Alias Manager Integration Script
# This script is called from bashrc to allow
# one or many alias/function scripts to be
# called on BASH startup.
# Alias Manager will over-write any changes
# you make to this file.
echo 'Alias Manager loading scripts...'
if [ -f /etc/bash.alias.sh ]; then
    source /etc/bash.alias.sh
    echo '    Loaded /etc/bash.alias.sh'
else
    echo 'Alias Manager file not found: /etc/bash.alias.sh'
fi
echo ' '
