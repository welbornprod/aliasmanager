'''
    aliasmgr_cmdline.py
    Command-line interface for Alias Manager.
Created on Sep 24, 2013

@author: Christopher Welborn
'''
import sys
import os
import re

import aliasmgr_util as amutil
# settings helper
settings = amutil.settings


class CmdLine():

    """ alias manager command line tools """

    def __init__(self, largs=None):
        """ Loads command-line interface, must pass args (largs). """
        # aliasfile can be replaced by arg_handler().
        self.aliasfile = settings.get('aliasfile')
        # load all aliases/functions (list of amutil.Command() objects)
        self.commands = amutil.readfile()

    def main(self, largs):
        """ runs command line style, accepts args """
        # Arg
        if len(largs) > 0:
            ret = self.arg_handler(largs)
            return ret
        else:
            print('No arguments supplied to aliasmgr.CmdLine!')
            return 1

    def arg_handler(self, largs):
        """ receives list of args, handles accordingly """

        # scan for alias file to use.
        for sarg in largs:
            if (os.path.isfile(sarg) or
                    os.path.isfile(os.path.join(sys.path[0], sarg))):
                self.aliasfile = sarg
                self.commands = amutil.readfile(aliasfile=self.aliasfile)
                largs.remove(sarg)

        # notify user about which alias file is being used.
        print('\nUsing alias file: {}\n'.format(self.aliasfile))
        # get lower() list of alias names
        if self.commands:
            aliasnames = [cmd.name.lower() for cmd in self.commands]
        else:
            aliasnames = []

        # scan for normal args.
        for sarg in largs:
            if sarg.lower() in aliasnames:
                self.printalias(sarg)
            elif sarg.startswith(('-h', '--help')):
                # HELP
                self.printusage()
                self.printhelp()
                return 0
            elif sarg.startswith(('-v', '--version')):
                # VERSION
                self.printver()
                return 0
            elif sarg.startswith(('-e', '--export')):
                # EXPORTS
                return self.printexports()
            elif sarg.startswith(('-p', '--p')):
                # PRINT aliases (sarg will tell us normal/short/comment/full
                # style)
                return self.printaliases(sarg)
            elif sarg.startswith(('-C', '--convert')):
                # CONVERT command to its own script file.
                return self.convert_toscript(largs)
            else:
                # Search automatically ran
                return self.printsearch(sarg)

    def convert_toscript(self, cmdlineargs):
        """ Convert an alias/function to a script file. """
        args = cmdlineargs[:]
        overwrite = False
        for i, arg in enumerate(args[:]):
            if arg.startswith('-'):
                args.pop(i)
                if arg.lower() in ('-o', '--overwrite'):
                    overwrite = True

        arglen = len(args)
        if (arglen not in [1, 2]):
            print('\nExpecting: AliasName [TargetFile] [--overwrite]')
            return 1
        if len(args) == 2:
            aliasname, targetfile = args
        else:
            aliasname = args[0]
            targetfile = None

        matches = self.searchalias(aliasname, names_only=True)
        if not matches:
            print('\nNo matches were found for: {}'.format(aliasname))
            return 1

        if len(matches) > 1:
            print('\nAmbiguos name, returned many results:')
            print('    {}'.format('\n    '.join(c.name for c in matches)))
            return 1

        cmd = matches[0]
        newfile = cmd.to_scriptfile(filepath=targetfile, overwrite=overwrite)
        if newfile:
            print('Script was generated: {}'.format(newfile))
            return 0
        print('\nUnable to generate script: {}'.format(newfile))
        return 1

    def printver(self):
        print('{}\n'.format(settings.versionstr))

    def printusage(self):
        print("""{ver}
         Usage:
             aliasmgr
                 ...run the alias manager gui.
             aliasmgr <alias_name>
                 ...list info about an existing alias/function.
             aliasmgr -C <alias_name> [<target_file>] [-o]
                 ...convert an alias/function into a stand-along script.
             aliasmgr [file] -p | -h | -v | -e
                 ...list info about all aliases/functions.
                    Use a specific alias file if given.
        """.format(ver=settings.versionstr))

    def printhelp(self):
        aliasfile = settings.get("aliasfile")
        if aliasfile == "":
            aliasfile = "(Not selected yet)"
        print("""
  Current file:    {aliasfile}

      Commands:
                  -h : Show this help message
                  -v : Print version
                  -e : Print exported names only
                  -C : Convert a function/alias to its own script file.
                  -o : Overwrite existing files when converting to scripts.
     -p[s|c][f|a]    : Print current aliases/functions.
                -pxf : Print entire functions (with content).

    Formatting:
                   x : will print entire functions, does nothing for aliases.
                   s : only shows names
                   c : shows names : comments

         Types:
                   a : shows aliases only
                   f : shows functions only

       Example:
           'aliasmgr myshortcut' will show any info found for an
           alias/function called 'myshortcut'.
           'aliasmgr -pcf' shows names and comments for functions only
           'aliasmgr -psa' shows just the names for aliases (not functions)
        """.format(aliasfile=aliasfile))

    def printalias(self, aliasname):
        """ Print a single alias (retrieved by name or Command() object) """

        if isinstance(aliasname, amutil.Command):
            self.printcommand(aliasname)
        else:
            # retrieve by name.
            aliasnames = [cmd.name for cmd in self.commands]
            if aliasname in aliasnames:
                self.printcommand(self.commands[aliasnames.index(aliasname)])
            else:
                print('\nNo alias by that name!: {}'.format(aliasname))
                return 1
        return 0

    def printcommand(self, cmdobj, showcommand=True):
        """ Print a Command() object, with some formatting. """
        cmdexported = cmdobj.exported.lower()
        exported = 'Yes' if cmdexported in ('new',) else cmdobj.exported
        fmtlines = [
            '    Name: {cmdobj.name}',
            ' Comment: {cmdobj.comment}',
            'Exported: {exported}'
        ]
        # include command?
        if showcommand:
            fmtlines.append(
                ' Command:\n {}\n'.format('\n  '.join(cmdobj.cmd))
            )

        print('\n'.join(fmtlines).format(cmdobj=cmdobj, exported=exported))

    def printsearch(self, aliasname):
        """ Searches aliases for aliasname (regex), and prints results """

        matches = self.searchalias(aliasname)
        if matches:
            usedivider = (len(matches) > 1)
            lastmatch = matches[-1]
            for cmdinfo in matches:
                self.printcommand(cmdinfo, showcommand=False)
                if usedivider and (cmdinfo != lastmatch):
                    print('-' * 40)
            print('\nFound {} matches for: {}\n'.format(
                str(len(matches)), aliasname))
            return 0
        else:
            print('\nNo aliases found matching: {}\n'.format(aliasname))
            return 1

    def searchalias(self, aliasname, names_only=False):
        """ Searches and retrieves all aliases matching aliasname (regex) """

        try:
            repat = re.compile(aliasname, flags=re.IGNORECASE)
        except re.error:
            print('\nInvalid alias name given!: {}\n'.format(aliasname))
            return []

        if names_only:
            def get_match(cmd):
                """ Match on name only. """
                return repat.search(cmd.name)
        else:
            def get_match(cmd):
                """ Match on all content. """
                return repat.search(
                    '{} {} {} {}'.format(
                        cmd.name,
                        cmd.cmd,
                        cmd.comment,
                        cmd.exported
                    )
                )
        return filter(get_match, self.commands)

    def printaliases(self, sarg):
        """ Print aliases in current file """

        # Get the length of the longest command name for formatting.
        maxcmdlength = len(max(self.commands, key=lambda c: len(c.name)).name)
        if self.commands:
            # Print in alphabetical order.
            for itm in sorted(self.commands, key=lambda c: c.name):
                # Comments?
                if len(itm.comment) > 0:
                    # Add Comment
                    scomment = itm.comment
                else:
                    scomment = "(No Comment)"
                # Exported?
                sexport = itm.exported
                # Print Name
                if "s" in sarg:
                    # printing short version, names only
                    sfinalname = (itm.name)
                elif "c" in sarg:
                    # print comment version, names/comments only
                    sfinalname = '{} : {}'.format(
                        itm.name.ljust(maxcmdlength),
                        scomment)
                else:
                    # printing normal (p), or full version (px)
                    sfinalname = '\n'.join((
                        '{}:',
                        '    Comment: {}',
                        '     Export: {}')).format(itm.name, scomment, sexport)
                    # Function, show full cmd list?
                    if itm.isfunction():
                        # Function, show all commands?
                        if "x" in sarg:
                            # Build full command items string
                            scmd = '\n'.join((
                                '    Command:',
                                '            {}\n'.format(
                                    '\n            '.join(itm.cmd))))
                        else:
                            # Only show first line of function
                            scmd = '\n'.join((
                                '    Command:',
                                '            {} (more lines...)\n')).format(
                                itm.cmd[0])
                    else:
                        # Simple 1 liner, alias
                        scmd = '\n'.join((
                            '    Command:',
                            '            {}\n'.format(itm.cmd[0])
                        ))
                    sfinalname = '\n'.join((sfinalname, scmd))

                # Final output built, print all/aliases/functions
                if "a" in sarg:
                    # Aliases only (also empty commands)
                    if not itm.isfunction():
                        print(sfinalname)
                elif "f" in sarg:
                    # Functions only
                    if itm.isfunction():
                        print(sfinalname)
                else:
                    # All
                    print(sfinalname)
        else:
            # No items found
            print('\nNo items found in alias file: {}'.format(self.aliasfile))
            return 1
        return 0

    def printexports(self):
        """ Prints exports only """
        exports = [
            f.name for f in self.commands if f.exported.lower() == 'yes'
        ]
        if exports:
            print('\n'.join(exports))
            return 0
        else:
            print('\nNo exports found!\n')
            return 1
