Alias Manager
=============

Manages bash alias/function scripts using a GUI (gtk-based).

Edit, View, Load, Save aliases/functions in one or more files.

Easily integrate alias/function scripts into bashrc with a mouse click.


New Features:
=============
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
  
  
