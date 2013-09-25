'''
    aliasmgr_cmdline.py
    Command-line interface for Alias Manager.
Created on Sep 24, 2013

@author: Christopher Welborn
'''
import sys, os, re

import aliasmgr_util as amutil
# settings helper
settings = amutil.settings

class CmdLine():
    """ alias manager command line tools """

    def __init__(self, largs = None):
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
            print("No arguments supplied to aliasmgr.cmdline!")
            return 1

           
    def arg_handler(self, largs):
        """ receives list of args, handles accordingly """
        
        # scan for alias file to use.
        for sarg in largs:
            if (os.path.isfile(sarg) or
                os.path.isfile(os.path.join(sys.path[0], sarg))):
                self.aliasfile = sarg
                self.commands = amutil.readfile(aliasfile = self.aliasfile)
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
            elif sarg.startswith('-h') or sarg.startswith('--h'):
                # HELP
                self.printusage()
                self.printhelp()
                return 0
            elif sarg.startswith('-v') or sarg.startswith('--v'):
                # VERSION
                self.printver()
                return 0
            elif sarg.startswith('-e') or sarg.startswith('--e'):
                # EXPORTS
                ret = self.printexports()
                return ret
            elif sarg.startswith('-p') or sarg.startswith('--p'):
                # PRINT aliases (sarg will tell us normal/short/comment/or full style)        
                ret = self.printaliases(sarg)
                return ret
            else:
                # Search automatically ran
                ret = self.printsearch(sarg)
                return ret
              
    def printver(self):
        print(settings.name + " version " + settings.version)
        print("")
    
    def printusage(self):
        print('aliasmgr\n' + \
              '         Usage:\n' + \
              '            aliasmgr\n' + \
              '                     ...run the alias manager gui.\n' + \
              '            aliasmgr <known_alias_name>\n' + \
              '                     ...list info about an existing alias/function.\n' + \
              '            aliasmgr [file] -p | -h | -v | -e\n' + \
              '                     ...list info about all aliases/functions. Use specific alias file if given.\n')
          
    
    def printhelp(self):
        aliasfile = settings.get("aliasfile")
        if aliasfile == "":
            aliasfile = "(Not selected yet)"
        print("  Current file:    " + aliasfile + '\n' + \
              "      Commands:\n" + \
              "                  -h : Show this help message\n" + \
              "                  -v : Print version\n" + \
              "                  -e : Print exported names only\n" + \
              "     -p[x|s|c|][f|a] : Print current aliases/functions\n\n" + \
              '    Formatting:\n' + \
              "                   x : will print entire functions.\n" + \
              "                   s : only shows names\n" + \
              "                   c : shows names : comments\n\n" + \
              "         Types: \n" + \
              "                   a : shows aliases only\n" + \
              "                   f : shows functions only\n\n" + \
              "       Example:\n" + \
              '           \'aliasmgr myshortcut\' will show any info found for alias/function called \'myshortcut\'\n' + \
              '           \'aliasmgr -pcf\' shows names and comments for functions only\n' + \
              '           \'aliasmgr -psa\' shows just the names for aliases (not functions).\n')
        

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


    def printcommand(self, cmdobj, showcommand = True):
        """ Print a Command() object, with some formatting. """
        
        sexported = 'Yes' if cmdobj.exported.lower() == 'new' else cmdobj.exported

        sformatted = '    Name: {}\n'.format(cmdobj.name) + \
                     ' Comment: {}\n'.format(cmdobj.comment) + \
                     'Exported: {}'.format(sexported)
        # include command?
        if showcommand:
            sformatted += '\n Command:\n  {}\n'.format('\n  '.join(cmdobj.cmd))

        print('{}'.format(sformatted))
    
    
    def printsearch(self, aliasname):
        """ Searches aliases for aliasname (regex), and prints results """
        
        matches = self.searchalias(aliasname)
        usedivider = (len(matches) > 1)
        if matches:
            lastmatch = matches[-1]
            for cmdinfo in matches:
                self.printcommand(cmdinfo, showcommand = False)
                if usedivider and (cmdinfo != lastmatch):
                    print('-' * 40)
            print('\nFound {} matches for: {}\n'.format(str(len(matches)), aliasname))
            return 0
        else:
            print('\nNo aliases found matching: {}\n'.format(aliasname))
            return 1
        
    
    def searchalias(self, aliasname):
        """ Searches and retrieves all aliases matching aliasname (regex) """
        
        try:
            repat = re.compile(aliasname, flags = re.IGNORECASE)
        except:
            print('\nInvalid alias name given!: {}\n'.format(aliasname))
            return 1
        
        matches = []
        for cmdinfo in self.commands:
            wholecmd = '{} {} {} {}'.format(cmdinfo.name, 
                                            cmdinfo.cmd, 
                                            cmdinfo.comment, 
                                            cmdinfo.exported)
            matchcmd = repat.search(wholecmd)
            if matchcmd:
                matches.append(cmdinfo)

        return matches
    
    
    def printaliases(self, sarg):
        """ Print aliases in current file """
        
        lst_items = amutil.fixexports(self.commands)
        if lst_items:
            for itm in lst_items:
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
                    maxcmdlength = 20
                    thiscmdlength = len(itm.name)
    
                    sfinalname = (itm.name + \
                                 (" " * (maxcmdlength - thiscmdlength)) + \
                                 ": " + scomment)
                else:
                    # printing normal (p), or full version (px)
                    sfinalname = (itm.name + ":")
                    # Show comment/export/command
                    sfinalname += ("\n    Comment: " + scomment + "\n     Export: " + sexport)
                    # Function, show full cmd list?
                    if itm.isfunction():
                        # Function, show all commands?
                        if "x" in sarg:
                            # Build full command items string
                            scmd = "    Command:\n"
                            for itmcmd in itm.cmd:
                                scmd += "             " + itmcmd + '\n'
                        else:
                            # Only show first line of function
                            scmd = "    Command:\n" + \
                                   "             " + itm.cmd[0] + " (more lines...)\n"
                    else:
                        # Simple 1 liner, alias
                        scmd = "    Command:\n             " + itm.cmd[0] + '\n'
                    
                    sfinalname += '\n' + scmd
                
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
        lst_exports = amutil.readexports()
        if lst_exports:
            #print("Found " + str(len(lst_exports)) + " exports:")
            for itm in lst_exports:
                print(itm)
            return 0
        else:
            print('\nUnable to load exports!')
            return 1
