#!/usr/bin/env python
'''
    Alias Manager
    ...manage bash alias files through a GUI
        view, edit, add, delete, save, load alias scripts
        integrate one or more scripts into bashrc

    -Christopher Welborn 12-28-2012

    Copyright (C) 2012-2015  Christopher Welborn

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
# python3 style print function
from __future__ import print_function
import sys    # for argv
import gtk    # user interface main() loop


# local utilities
import aliasmgr_integrator
integrator = aliasmgr_integrator.am_integrator()

import aliasmgr_util as amutil
settings = amutil.settings

from aliasmgr_gui import winMain
from aliasmgr_cmdline import CmdLine


def main():
    """ Main entry point for Alias Manager """
    # get user info
    integrator.get_userinfo()
    # get bash file
    aliasfile = settings.get("aliasfile")
    # force file picker if setting does not exist or bad file
    amutil.pick_aliasfile(aliasfile)
    # self integration
    if (not integrator.is_integrated() and
            settings.get("integration") != "false"):
        amutil.integration_choice()

    largs = sys.argv[1:]
    try:
        if len(largs) == 0:
            # No Args, Load GUI
            appMain = winMain()  # noqa
            gtk.main()
        else:
            # Args, send to command line
            appcmdline = CmdLine()
            ret = appcmdline.main(largs)
            sys.exit(ret)
    except KeyboardInterrupt:
        print('\nUser Cancelled, goodbye.\n')
        sys.exit(1)


# Start.of.script -------------------------------------------------------------
if __name__ == '__main__':
    dlg = amutil.Dialogs()
    if settings.get("dlglastpath") != "":
        dlg.lastpath = settings.get("dlglastpath")
    main()
