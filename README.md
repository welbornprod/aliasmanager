Alias Manager
=============

Manages bash alias/function scripts using a GUI (gtk-based).

Edit, View, Load, Save aliases/functions in one or more files.

Easily integrate alias/function scripts into bashrc with a mouse click.


New Features:
=============

version 1.7.6:
----------------

Added the ability to convert functions/aliases to standalone scripts.
    usage: `aliasmgr -C <known_name> [<target_file.sh>] [-o]`


version 1.7.2:
--------------

Command-line flags format changed. Flags must have `-` before the first letter.
    usage: `aliasmgr.py -pcf`

Search for an alias/function from the command line.
    usage: `aliasmgr.py <searchterm>`

List info about a known alias/function from the command line.
    usage: `aliasmgr.py <known_name>`

Code cleaned (a little), classes, utilities, command-line, and GUI were separated
into their own py files. Still more to clean, but its a start.


version 1.7:
------------

Search integrated into main window, now searches correctly.

Rename item added, preserves export status if auto-save is checked.

Auto selects new items, re-selects items on save/load.

New sliding pane between items and command info.

Note to user:
=============
Looks for /home/username/.bashrc or bash.bashrc first, then in /etc/.

Uses elevation commands kdesudo/gksudo (whichever comes first) for operations that
 require root.


Technical Info:
===============

Code written in python 2.7 (uses the __future__.print_function)

GUI designed using Glade and GTK2. (gtk module required)


