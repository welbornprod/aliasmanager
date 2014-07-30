'''
    aliasmgr_util.py
    Various utilities for Alias Manager (cmdline & gui)
Created on Sep 24, 2013

@author: Christopher Welborn
'''
import re
import gtk
import os
import aliasmgr_integrator
import aliasmgr_settings
# For changing file mode when scripts are generated.
from stat import S_IREAD, S_IWRITE, S_IEXEC
# Shorthand for read, write, and exec.
S_RWX = S_IREAD | S_IWRITE | S_IEXEC

settings = aliasmgr_settings.am_settings()
integrator = aliasmgr_integrator.am_integrator()


# Command/Alias Object ------------------------------------
class Command():

    def __init__(self, name=None, cmd=None, comment=None, exported=None):
        # set defaults.
        self.name = name if name else ''
        self.cmd = cmd if cmd else []
        self.comment = comment if comment else ''
        self.exported = exported if exported else 'New'
        self.shebang = '#!/bin/bash'

    def __repr__(self):
        """ return string representation of this command. """

        commentstr = self.comment if self.comment else '(No Comment)'
        return '{} : {} \n'.format(self.name, commentstr)

    def __str__(self):
        return self.__repr__()

    def to_scriptfile(self, filepath=None, overwrite=False):
        """ Convert a function/alias to its own script file. """
        if not self.name:
            raise ValueError('Cannot convert a command with no name.')
        elif not self.cmd:
            raise ValueError('Cannot convert a command with no content.')

        # Ensure a full path is built.
        if filepath:
            basedir, filename = os.path.split(filepath)
            if not basedir:
                basedir = os.getcwd()
            if not filename:
                filename = '{}.sh'.format(self.name)
        else:
            basedir = os.getcwd()
            filename = '{}.sh'.format(self.name)

        # Don't clobber existing scripts.
        if not overwrite:
            uniqueid = 2
            while os.path.exists(filename):
                filename = '{}{}.sh'.format(self.name, uniqueid)
                uniqueid += 1

        # Build the full path.
        filepath = os.path.join(basedir, filename)
        desctype = 'a function' if self.isfunction() else 'an alias'
        descfile = settings.get('aliasfile', 'an alias file.')
        desclines = [
            '# Script generated with {}:'.format(settings.versionstr),
            '# Original code was {} in {}.'.format(desctype, descfile),
        ]
        desc = '{}\n'.format('\n'.join(desclines))
        content = '\n{}\n'.format(self.to_function())

        if not content.endswith('\n'):
            content = '{}\n'.format(content)
        with open(filepath, 'w') as f:
            f.write('{}\n\n'.format(self.shebang))
            f.write(desc)
            f.write(content)
            f.write('\n# Call the function when this script runs.\n')
            f.write('{} $@\n'.format(self.name))

            f.flush()

        # Chmod to allow execution by the user.
        os.chmod(filepath, S_RWX)

        return filepath

    def isfunction(self):
        """ Returns true/false depending on linecount """
        return (len(self.cmd) > 1)

    def isexported(self):
        lowerexported = self.exported.lower()
        return ((lowerexported == 'yes') or (lowerexported == 'new'))

    def setexport(self, bexported, bnew=False):
        """ Sets the appropriate string value for cmd.exported using booleans,
            Note: String values were used at first for automatic pretty printing
                  in command line output, but later used to determine if an alias
                  was new or not, therefore 'automagically' exporting new functions.
            **Aliases are never exported no matter what the export value is**
        """
        if bnew:
            self.exported = "New"
        else:
            if bexported:
                self.exported = "Yes"
            else:
                self.exported = "No"

    def to_function(self):
        """ Return a string containing a function definition for this cmd """
        if not (self.name and self.cmd):
            return ''

        if self.isfunction():
            cmdlines = ['    {}'.format(l) for l in self.cmd]
        else:
            cmdlines = ['    {} $@'.format(self.cmd[0])]

        content = ['function {} {{'.format(self.name)]
        if self.comment:
            content.append('    # {}\n'.format(self.comment))
        content.extend(cmdlines)
        content.append('}')
        return '\n'.join(content)

# Dialog/Msgbox --------------------------------------------------------


class Dialogs():

    """ Dialog boxes and Messageboxes made easier/portable
        ** for dialogs you might want to set the filter after initializing
            like:
            mydialog = dlg()
            mydialog.filter = [["All Files", "*"], ["Test Files", "*.txt"]]
            # dlg() will build the filter using dlg.filter before running
    """

    def __init__(self):
        # main dialog window
        self.dlgwindow = gtk.FileChooserDialog()
        self.msgwindow = None

        # shortcode for dialog actions
        self.open = gtk.FILE_CHOOSER_ACTION_OPEN
        self.save = gtk.FILE_CHOOSER_ACTION_SAVE
        self.saveas = gtk.FILE_CHOOSER_ACTION_SAVE
        self.folder = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
        self.foldercreate = gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER
        # shortcode for msg types
        self.info = gtk.MESSAGE_INFO
        self.error = gtk.MESSAGE_ERROR
        self.question = gtk.MESSAGE_QUESTION
        self.warning = gtk.MESSAGE_WARNING
        self.other = gtk.MESSAGE_OTHER

        # filter types
        self.filter_all = ["All files", "*"]
        self.filter_text = ["Text files", "*.txt"]
        self.filter_shell = ["Shell files", "*.sh"]

        # last dialog path
        self.lastpath = None

        # options
        self.show_hidden = True

        # filter to use by default
        self.filter = [self.filter_all, self.filter_shell]

    def clear_filter(self):
        """ removes all current filters in dlgwindow """
        for filter_item in self.dlgwindow.list_filters():
            self.dlgwindow.remove_filter(filter_item)

    def build_filter(self, lst_filters=None, bclear_filters=True):
        """ build dlgwindow filters from list of filters
            lst_filters = [["Description", "*.type"], ["Desc2", "*.typ2"]]
        """
        if bclear_filters:
            self.clear_filter()
        # use self.filter to build from instead of custom filters
        if lst_filters is None:
            lst_filters = self.filter

        for filter_itm in lst_filters:
            dfilter = gtk.FileFilter()
            dfilter.set_name(filter_itm[0])
            dfilter.add_pattern(filter_itm[1])
            self.dlgwindow.add_filter(dfilter)

    def dialog(self, stitle="Select file...", gtkaction=gtk.FILE_CHOOSER_ACTION_OPEN):
        # Create File Dialog (GTK)
        if (gtkaction is None) or (gtkaction == self.open):
            gtkbtn = gtk.STOCK_OPEN
        elif gtkaction == self.save:
            gtkbtn = gtk.STOCK_SAVE
        elif gtkaction == self.saveas:
            gtkbtn = gtk.STOCK_SAVE
        elif gtkaction == self.folder:
            gtkbtn = gtk.STOCK_OK
        elif gtkaction == self.foldercreate:
            gtkbtn = gtk.STOCK_OK
        else:
            gtkbtn = gtk.STOCK_OPEN

        # Add app name to title if its not already given.
        if not stitle.lower().startswith(settings.name.lower()):
            stitle = '{}: {}'.format(settings.name, stitle)
        # Create Dialog.
        self.dlgwindow = gtk.FileChooserDialog(stitle,
                                               None,
                                               gtkaction,
                                              (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                               gtkbtn, gtk.RESPONSE_OK))
        self.dlgwindow.set_default_response(gtk.RESPONSE_OK)

        # build filters
        self.build_filter()

        # Show hidden files because user files are in /.local and /.config
        self.dlgwindow.set_show_hidden(self.show_hidden)
        # Got lastpath?
        try:
            if self.lastpath is not None:
                self.dlgwindow.set_current_folder(self.lastpath)
        except:
            pass
        # Show Dialog, get response
        response = self.dlgwindow.run()
        # Get Filename Selected
        if response == gtk.RESPONSE_OK:
            respFile = self.dlgwindow.get_filename()
            # Save last path
            self.lastpath = self.dlgwindow.get_current_folder()
            # close dialog
            self.dlgwindow.destroy()
            return respFile
        else:
            # Return an empty string (CANCELED)
            self.dlgwindow.destroy()
            return ""

    # MessageBox ---------------------------------------
    def msgbox(self, smessage, gtktype=gtk.MESSAGE_INFO, gtkbuttons=gtk.BUTTONS_OK):
        # get type
        if ((gtktype is None) or
            (gtktype == self.info) or
            (gtktype == self.warning) or
            (gtktype == self.error)):
            if gtkbuttons != gtk.BUTTONS_OK:
                btns = gtkbuttons
            else:
                btns = gtk.BUTTONS_OK
        elif gtktype == self.question:
            btns = gtk.BUTTONS_YES_NO

        # Shows a messagebox with the INFO icon and OK button
        self.msgwindow = gtk.MessageDialog(None,
                                           gtk.DIALOG_MODAL,
                                           gtktype,
                                           buttons=btns)
        self.msgwindow.set_markup('<b>{}</b>'.format(settings.name))
        self.msgwindow.format_secondary_markup(smessage)
        self.msgwindow.run()
        self.msgwindow.destroy()

    def msgbox_warn(self, message):
        """ Show a warning messagebox. """
        self.msgbox(message, gtktype=self.warning)

    def msgbox_yesno(self, smessage):
        self.msgwindow = gtk.MessageDialog(None,
                                           gtk.DIALOG_MODAL,
                                           gtk.MESSAGE_QUESTION,
                                           buttons=gtk.BUTTONS_YES_NO)

        self.msgwindow.set_markup('<b>{}</b>'.format(settings.name))
        self.msgwindow.format_secondary_markup(smessage)
        response = self.msgwindow.run()
        self.msgwindow.destroy()
        return response

# Functions ----------------------------------------


def get_def_count(contents, defword):
    """ Counts lines beginning with 'defword',
        to retrieve actual 'alias' and 'function' defs in
        the file.
        returns: count (Integer)
    """

    if '\n' in contents:
        lines = contents.split('\n')
    else:
        lines = [contents]

    cnt = 0
    for line in lines:
        if line.startswith(defword):
            cnt += 1
    return cnt


def getfilecontents(aliasfile=None):
    """ Return alias files raw content (string)
        Shows a message if alias file cannot be found.
        Returns None on failure.
    """
    if aliasfile is None:
        aliasfile = settings.get("aliasfile")

    if not os.path.isfile(aliasfile):
        #print("Alias file not found!: " + aliasfile)
        dlg = Dialogs()
        dlg.msgbox('Alias file not found!:\n{}'.format(aliasfile), dlg.error)
        return None

    # Load file
    try:
        with open(aliasfile, 'r') as fread:
            filecontent = fread.read()
        return filecontent
    except (IOError, OSError) as exio:
        msg = 'Unable to read file:\n{}'.format(aliasfile)
        fullmsg = '{}\n{}'.format(msg, str(exio))
        dlg = Dialogs()
        dlg.msgbox(fullmsg, dlg.error)
        return None


def parsealiasline_old(sline):
    """ old deprecated method of parsing alias info from a line. """
    # Detect Alias --------------------------------
    if (sline.startswith("alias")):
        # Replace TABS/NEWLINE
        sline = sline.replace('\t', '').replace('\n', '')

        # Trim 'alias'
        sbuf = sline.replace("alias ", "")

        # Trim Comments
        if "#" in sbuf:
            sbuf = sbuf[:sbuf.index("#")]
            # Get comment
            scomment = sline[sline.index("#") + 1:]
            # Trim leading space
            scomment = scomment.strip(' ')
        else:
            # No Comment
            scomment = ""

        # Retrieve name and command, without quotes.
        aliasparts = sbuf.split('=')
        sname = aliasparts[0].strip(" ")
        scommand = aliasparts[1].strip(" ").strip('"').strip("'")
        # Add command to list (Name, Command, Comment, Exported [not needed for alias])
        return Command(name=sname,
                       cmd=[scommand],
                       comment=scomment)
    return None


def parse_aliases(filecontents):
    """ parse all aliases from file, return a list of Command() objects """

    # this one handles quotes inside of commands better...
    name_pat = re.compile(r'alias[ ]?(?P<name>[\d\w_\-]+)=(?P<cmdinfo>.+)')
    cmd_comment_pat = re.compile(r'(?P<command>.+)[#](?P<comment>.+)?')
    cmd_nocomment_pat = re.compile(r'(?P<command>.+)')

    lst_commands = []
    # Get all alias lines, with (name, raw command and comment)
    aliases = name_pat.findall(filecontents)
    for name, rawcmd in aliases:
        # use regex for separating comments from command.
        if '#' in rawcmd:
            cmdmatch = cmd_comment_pat.search(rawcmd)
        else:
            # use normal regex.
            cmdmatch = cmd_nocomment_pat.search(rawcmd)
        if cmdmatch:
            command = cmdmatch.groupdict()['command']
            if cmdmatch.groupdict().has_key('comment'):
                comment = cmdmatch.groupdict()['comment']
            else:
                comment = ''
        # Add alias to list as a Command() object...
        lst_commands.append(Command(name=stripchars(name, ' \t\n'),
                                    cmd=[stripquotes(stripchars(command, ' \t\n'))],
                                    comment=stripchars(comment, '# \t\n'),
                                    exported='[n/a]'))
    return lst_commands


def parse_exports(filecontents):
    """ parse all exports from file contents, return a list of exported names. """

    exportpat = re.compile(r'export[ ]+?(?P<export>.+)', flags=re.MULTILINE)
    exports = exportpat.findall(filecontents)
    if exports:
        exports = [stripchars(e, ' \t\n') for e in exports]
    return exports


def parse_functions(filecontents):
    """ parse all functions from the alias file. """

    # Get all exports from the file
    exports = parse_exports(filecontents)

    # Parse all functions from the file.
    # Flag for setting if we are inside a function
    bfunction = False
    # Flag for setting if we found function comments
    bcomment = False
    scomment = ''
    # List of parsed Command() objects...
    commands = []
    # Temporary list for raw function contents
    lst_contents = []

    # Initialize Tab Depths
    tabdepth = 0
    spacedepth = 0

    for sline in filecontents.split('\n'):

        # Detect Function -------------------------------
        if sline.replace('\t', '').replace(' ', '').startswith("function"):
            # Grab function name
            ssplit = sline.split(" ")
            sname = ssplit[1].replace('\n', '').replace("()", "")

            # Find initial tab/space depth
            if tabdepth == 0:
                if sline.startswith('\t'):
                    sbuf = sline
                    tabdepth, sbuf = trimcount(sbuf, '\t')

            if spacedepth == 0:
                if sline.startswith(" "):
                    sbuf = sline
                    spacedepth, sbuf = trimcount(sbuf, ' ')

            # We are now inside a function
            bfunction = True
        # Inside Function ----------------------------------
        if bfunction:
            # Detect comment
            if sline.replace('\t', '').replace(' ', '').startswith("#"):
                # First comment only
                if not bcomment:
                    # Found comment
                    scomment = sline.replace('\t', '').replace('\n', '')[1:]
                    scomment = scomment.strip(' ')
                    # Set flag
                    bcomment = True

            # Add raw contents
            # Skip over function definition if multi-line function
            if not sline.strip(" ").replace('\n', '').endswith("()"):
                lst_contents.append(sline.replace('\n', ''))

            # Found end of function (could be a single line though)
            # Parse contents, decide which to keep
            if ((sline.strip().replace('\n', '').endswith(" }")) or
                (sline.replace('\n', '').replace('\t', '').replace(' ', '') == "}")):
                # End of function
                bfunction = False
                # Reset comment finder
                bcomment = False

                # Keep function contents
                lst_keep = []
                for itm in lst_contents:
                    # Save trimmed version of line
                    strim = itm.replace('\t', '').replace(' ', '').replace('\n', '')
                    snotabs = itm.replace('\t', '').replace('\n', '')
                    # Figure out which contents to keep. No Braces.
                    if (strim != "{") and (strim != "}"):  # and (not strim.startswith("#")):
                        # Trim single line definition
                        if "()" in itm:
                            itm = itm[itm.index("()") + 2:]
                            snotabs = itm.replace('\t', '').replace('\n', '')
                            strim = snotabs.replace(' ', '')
                            if strim.startswith("{"):
                                snotabs = snotabs[snotabs.index("{") + 1:]
                                if snotabs.endswith("}"):
                                    snotabs = snotabs[:snotabs.index("}")]
                                itm = snotabs
                        # Trim leading { and following }...
                        if snotabs.startswith("{"):
                            snotabs = snotabs[1:]
                            if snotabs.endswith("}"):
                                snotabs = snotabs[:len(snotabs) - 1]
                            itm = snotabs
                        # Trim initial tabdepth from itm
                        if itm.startswith('\t'):
                            #self.printlog("TRIMMING TABDEPTH: " + str(tabdepth))
                            itm = itm[tabdepth:]
                            # Trim one more tab depth
                            if itm.startswith('\t'):
                                itm = itm[1:]

                        # Append Function Contents, don't add initial coment
                        if ((scomment != "") and
                            (not ((itm.startswith("#")) and (scomment in itm)))):
                            lst_keep.append(itm)
                        elif scomment == "":
                            lst_keep.append(itm)
                        #self.printlog("...." + itm)

                # Append function name/contents/comment /exported [set with fixexports()]
                sexported = 'Yes' if (sname in exports) else 'No'
                commands.append(Command(name=sname,
                                        cmd=lst_keep,
                                        comment=scomment,
                                        exported=sexported))

                # Reset comment string
                scomment = ''
                # Reset contents finder list
                lst_contents = []
    # Return finished list
    return commands


def readfile(aliasfile=None):
    """ Read alias/script file, return a list of command() objects.
        Returns empty list on failure.
    """

    # Get alias file contents
    filecontents = getfilecontents(aliasfile=aliasfile)
    aliaslinecnt = get_def_count(filecontents, 'alias')
    functionlinecnt = get_def_count(filecontents, 'function')

    commands = []
    if filecontents is None:
        return []
    # Get all aliases from the file.(also, initialize lst_commands)
    aliases = parse_aliases(filecontents)
    commands = commands + aliases
    # Get all functions form the file (also fills in exported items)
    functions = parse_functions(filecontents)
    commands = commands + functions
    # Validate parsing of aliases/functions
    warnmsg = []
    if aliaslinecnt != len(aliases):
        msg = 'Could not parse all aliases, may be missing some.\n{}\n{}'
        msg = msg.format('     alias lines: {}'.format(str(aliaslinecnt)),
                         '  parsed aliases: {}'.format(str(len(aliases))))
        warnmsg.append(msg)
    if functionlinecnt != len(functions):
        msg = 'Could not parse all functions, may be missing some.\n{}\n{}'
        msg = msg.format('  function lines: {}'.format(str(functionlinecnt)),
                         'parsed functions: {}'.format(str(len(functions))))
        warnmsg.append(msg)
    if warnmsg:
        print('\nreadfile: missing aliases/functions: \n{}'.format('\n'.join(warnmsg)))
        Dialogs().msgbox_warn('\n'.join(warnmsg))

    return commands


def fixexports_old(lst_data):
    """ Deprecated - readfile()->parse_functions() does this already (except better)
        Fixes export data in main list,
        "Yes", "No", or "Not Needed" is added to item info
    """
    lst_exports = readexports()

    # file failed to load completely
    if (not lst_exports) or (not lst_data):
        print('\nfixexports: Failed to load exports list.')
        return False

    if lst_exports and lst_data:
        # Check main list for this export
        for idata in range(0, len(lst_data)):
            sdata = lst_data[idata].name
            #self.printlog("CHECKING EXPORT:'" + sdata + "'")
            if sdata in lst_exports:
                lst_data[idata].exported = "Yes"
            else:
                # Function? check command length..
                if len(lst_data[idata].cmd) > 1:
                    lst_data[idata].exported = "No"
                else:
                    # Don't break markup for new items (load_aliases needs this 'new')
                    lst_data[idata].exported = "[N/A]"
    # Loaded empty exports list
    # if len(lst_data) == 0:
        #print("fixexports: empty exports list.")
    return lst_data


def readexports():
    """ Reads exports only, returns a list of exports """
    aliasfile = settings.get("aliasfile")
    with open(aliasfile, 'r') as fread:
        # Temp list for exports
        lst_temp = []
        # Get file contents
        slines = fread.readlines()

        for sline in slines:
            snotabs = sline.replace('\t', '').replace('\n', '')
            if snotabs.startswith("export"):
                # Found export, retrieve name
                lst_temp.append(snotabs.split(" ")[1])

        # Finished with file, return list of exports
        return lst_temp

    # Failed to open file
    #print("Failed to open alias file: " + aliasfile)
    return False


def input_text(message, default=''):
    """
    Display a dialog with a text entry.
    Returns the text, or None if canceled.
    """
    dlg = gtk.MessageDialog(None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_OTHER,
                            gtk.BUTTONS_OK_CANCEL,
                            message)
    entry = gtk.Entry()
    entry.set_text(default)
    entry.show()
    dlg.vbox.pack_end(entry)
    entry.connect('activate', lambda _: dlg.response(gtk.RESPONSE_OK))
    dlg.set_default_response(gtk.RESPONSE_OK)

    r = dlg.run()
    text = entry.get_text().decode('utf8')
    dlg.destroy()
    if r == gtk.RESPONSE_OK:
        return text
    else:
        return None


def filename_safe(sfilename, maxchars=30):
    """ trim filename to maxchars if needed for printing output"""
    if maxchars < 1:
        maxchars = 30

    # Make sure the filename isn't too long (30 chars)
    if len(sfilename) > maxchars:
        sfilename = "..." + sfilename[len(sfilename) - maxchars:]

    # Return filename
    return sfilename


def trim_markup(sstring):
    """ Trims all basic markup tags from string """
    sfinal = sstring
    # Don't need all these cycles if text doesn't have markup at all
    if ("<" in sfinal) and (">" in sfinal):
        lst_tags = ["i", "b", "u"]
        for stag in lst_tags:
            sfinal = sfinal.replace("<" + stag + ">", "").replace("</" + stag + ">", "")

        return sfinal
    else:
        # No markup
        return sfinal


def pick_aliasfile(saliasfile="", bexit_on_refusal=True):
    """ force user to select a good alias file, or create a blank one """
    sfile = saliasfile
    dlg = Dialogs()
    while (not os.path.isfile(sfile)):
        dlg.msgbox("No alias file found, click ok to select one to use.", dlg.info)
        sfile = dlg.dialog("Select an alias file to use:")

        # good aliasfile?
        if os.path.isfile(sfile):
            settings.setsave("aliasfile", sfile)
        else:
            #print("pick_aliasfile: Alias file not found!: " + sfile)
            response = dlg.msgbox_yesno("Alias file not found,\n Would you like to create a blank alias file?", )
            if response == gtk.RESPONSE_NO:
                #print("No alias file, quitting...")
                if bexit_on_refusal:
                    dlg.msgbox(settings.name + " cannot run with an alias file, goodbye,", dlg.info)
                    exit(1)
                else:
                    return ""
            else:
                integrator = aliasmgr_integrator.am_integrator()
                sblankfile = os.path.join(integrator.home, "bash.alias.sh")
                create_blank_file(sblankfile, True)
    # return good alias filename
    return sfile


def create_blank_file(sfilename, bshow_exists_warning=False):
    """ Creates a blank alias file """
    if (bshow_exists_warning and
        os.path.isfile(sfilename)):
        dlg = Dialogs()
        resp = dlg.msgbox_yesno("File exists:\n" + sfilename + '\n\n' +
                                "Would you like to overwrite it?")
        if resp == gtk.RESPONSE_NO:
            return False

    try:
        with open(sfilename, 'w') as fwrite:
            fwrite.write("# Blank alias file for " + settings.name)
            settings.setsave("aliasfile", sfilename)
            return True
    except Exception as ex:
        dlg.msgbox("Could not create blank file:\n" +
                   sfilename + '\n\n' +
                   "<b><u>Error:</u></b>\n" + str(ex))
        print("aliasmgr.py: Error creating blank file:\n" +
              str(ex))

    return False


def integration_choice():
    """ Ask the user if they want to automatically integrate Alias Manager with bashrc """
    dlg = Dialogs()
    resp = dlg.msgbox_yesno(settings.name + " will add a line to bashrc that will " +
                            "allow you to easily integrate alias scripts into bashrc.\n" +
                            "If your bashrc requires root permissions to edit, you will " +
                            "have to enter root's password.\n\n" +
                            "Would you like to add this line to bashrc?")
    if resp == gtk.RESPONSE_YES:
        integrator.integrate_self()
        settings.setsave("integration", "true")
        print("Integrated " + settings.name + " into bashrc...")
        return True
    else:
        settings.setsave("integration", "false")
        return False


def chmod_file(sfilename):
    """ makes file executable,
        if gksudo/kdesudo is needed, the user is asked before entering a pw
    """
    # chmod to destination file
    stat_exec = os.access(sfilename, os.X_OK)
    #print("chmod_file executable: " + str(stat_res))
    if stat_exec:
        return "chmod_file: already executable."
    else:
        st_owner = os.stat(sfilename).st_uid
        # needs root, user not root
        if st_owner == 0 and os.getuid() != 0:
            dlg = Dialogs()
            do_chmod = dlg.msgbox_yesno("For this script to work it needs " +
                                        "to be executable, and you will need " +
                                        "to enter root's password.\n" +
                                        "Would you like to make this script executable?")
            if do_chmod == gtk.RESPONSE_YES:
                # use elevation command to chmod
                selevcmd = ''
                if os.path.isfile('/usr/bin/kdesudo'):
                    selevcmd = 'kdesudo'
                elif os.path.isfile('/usr/bin/gksudo'):
                    selevcmd = 'gksudo'
                else:
                    return ("No elevcmd found to use!, can't chmod!")

                try:
                    os.system(selevcmd + ' chmod a+x ' + sfilename)
                    return (selevcmd + ' chmod +x ' + sfilename)
                except:
                    return ("Unable to use elevcmd to chmod!")
            else:
                return ("chmod declined.")
        else:
            # doesn't need root, user is or isnt root.
            os.system('chmod a+x ' + sfilename)
            return ('chmod +x ' + sfilename)


def stripchars(original, chars):
    """ remove chars from beginning and end of string """
    if hasattr(chars, 'lower'):
        chars = [c for c in chars]
    #print("STRIPPING: '{}'".format(original))
    if original:
        while original and (original[0] in chars):
            original = original[1:]
    if original:
        while original and (original[-1] in chars):
            original = original[:-1]

    return original


def stripquotes(original):
    """ Trims a single quote from the string """

    if ((original.startswith("'") and original.endswith("'")) or
        (original.startswith('"') and original.endswith('"'))):
        return original[1:-1]
    return original


def trimcount(originalstring, chartotrim):
    """ trims a char from the beginning of string,
        and returns a count and the trimmed string.
        example:
            spacecnt, trimmed = trimcount('   no spaces', ' ')
            # returns: (3, "no spaces")
    """
    cnt = 0
    while originalstring.startswith(chartotrim):
        cnt += 1
        originalstring = originalstring[1:]
    return cnt, originalstring
