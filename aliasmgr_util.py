'''
    aliasmgr_util.py
    Various utilities for Alias Manager (cmdline & gui)
Created on Sep 24, 2013

@author: Christopher Welborn
'''

import gtk
import os
import aliasmgr_integrator
import aliasmgr_settings
settings = aliasmgr_settings.am_settings()
integrator = aliasmgr_integrator.am_integrator()


# Command/Alias Object ------------------------------------
class Command():
    def __init__(self, name="", cmd=[], comment="", exported="New"):
        self.name = name
        self.cmd = cmd
        self.comment = comment
        self.exported = exported
    
    def __repr__(self):
        """ return string representation of this command. """
        
        commentstr = self.comment if self.comment else '(No Comment)'
        return '{} : {} \n'.format(self.name, commentstr)

    
    def __str__(self):
        return self.__repr__()
    
    
    def isfunction(self):
        """ Returns true/false depending on linecount """
        return (len(self.cmd) > 1)
      
    def isexported(self):
        return (self.exported.lower() == "yes" or self.exported.lower() == "new")
      
    def setexport(self, bexported, bnew = False):
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
               
    def build_filter(self, lst_filters = None, bclear_filters = True):
        """ build dlgwindow filters from list of filters 
            lst_filters = [["Description", "*.type"], ["Desc2", "*.typ2"]]
        """
        if bclear_filters:
            self.clear_filter()
        # use self.filter to build from instead of custom filters    
        if lst_filters == None:
            lst_filters = self.filter
            
        for filter_itm in lst_filters:
            dfilter = gtk.FileFilter()
            dfilter.set_name(filter_itm[0])
            dfilter.add_pattern(filter_itm[1])
            self.dlgwindow.add_filter(dfilter)
         
                        
    def dialog(self, stitle = "Select file...", gtkaction = gtk.FILE_CHOOSER_ACTION_OPEN):
        # Create File Dialog (GTK)
        if gtkaction == None or gtkaction == self.open:
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
            if self.lastpath != None:
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
    def msgbox(self, smessage, gtktype=gtk.MESSAGE_INFO, gtkbuttons = gtk.BUTTONS_OK):
        # get type
        if (gtktype == None or 
            gtktype == self.info or 
            gtktype == self.warning or
            gtktype == self.error):
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
        self.msgwindow.set_markup("<b>" + settings.name + "</b>")
        self.msgwindow.format_secondary_markup(smessage)
        self.msgwindow.run()
        self.msgwindow.destroy()
        
    def msgbox_yesno(self, smessage):
        self.msgwindow = gtk.MessageDialog(None,
                                    gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_QUESTION,
                                    buttons=gtk.BUTTONS_YES_NO)
        
        self.msgwindow.set_markup("<b>" + settings.name + "</b>")
        self.msgwindow.format_secondary_markup(smessage)
        response = self.msgwindow.run()
        self.msgwindow.destroy()
        return response
                
# Functions ----------------------------------------
def readfile(aliasfile = None):
    """ Read alias/script file, return a list of command() objects.
        Returns empty list on failure.
    """
    if aliasfile is None:
        aliasfile = settings.get("aliasfile")
        
    if not os.path.isfile(aliasfile):
        #print("Alias file not found!: " + aliasfile)
        dlg = Dialogs()
        dlg.msgbox("Alias file not found!:\n" + aliasfile, dlg.error)
        return False
    # Temporary list of aliases/functions
    #lst_temp = []
    lst_commands = []
    
    # Load file
    with open(aliasfile, 'r') as fread:
        # Flag for setting if we are inside a function
        bfunction = False
        # Flag for setting if we found function comments
        bcomment = False
        scomment = ""
        
        # Temporary list for function contents
        lst_contents = []
        # Initialize Tab Depths
        tabdepth = 0
        spacedepth = 0
        
        for sline in fread.readlines():
            # Initialize new command object
            cmd = Command()
            
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
                    while scomment.startswith(" "):
                        scomment = scomment[1:]
                else:
                    # No Comment
                    scomment = ""
               
                # Retrieve name
                sname = sbuf.split("=")[0].strip(" ")
                scommand = sbuf.split("=")[1].strip(" ")
                # Trim quotes
                scommand = scommand.strip('"').strip("'")
                # Add command to list (Name, Command, Comment, Exported [not needed for alias])
                cmd.name = sname
                cmd.cmd = [scommand]
                cmd.comment = scomment
                lst_commands.append(cmd)
                #lst_temp.append([sname, [scommand], scomment, ""])
 
            # Detect Function -------------------------------
            if sline.replace('\t', '').startswith("function"):
                # Grab function name
                ssplit = sline.split(" ")
                sname = ssplit[1].replace('\n', '').replace("()", "")
                
                # Find initial tab/space depth
                if tabdepth == 0:
                    if sline.startswith('\t'):
                        sbuf = sline
                        while sbuf.startswith('\t'):
                            sbuf = sbuf[1:]
                            tabdepth += 1
                        #self.printlog("TABDEPTH=" + str(tabdepth))
                if spacedepth == 0:
                    if sline.startswith(" "):
                        sbuf = sline
                        while sbuf.startswith(" "):
                            sbuf = sbuf[1:]
                            spacedepth += 1
                        #self.printlog("SPACEDEPTH=" + str(spacedepth))
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
                        while scomment.startswith(" "):
                            scomment = scomment[1:]
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
                    #print "Keeping Contents:"
                    lst_keep = []
                    for itm in lst_contents:
                        # Save trimmed version of line
                        strim = itm.replace('\t', '').replace(' ', '').replace('\n', '')
                        snotabs = itm.replace('\t', '').replace('\n', '')
                        # Figure out which contents to keep. No Braces.
                        if (strim != "{") and (strim != "}"): ## and (not strim.startswith("#")):
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
                                    snotabs = snotabs[:len(snotabs) -1]
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
                    cmd.name = sname
                    cmd.cmd = lst_keep
                    cmd.comment = scomment
                    lst_commands.append(cmd)
                    
                    #lst_temp.append([sname, lst_keep, scomment, ""])
                    # Reset comment string
                    scomment = ""
                    # Reset contents finder list
                    lst_contents = []
        # Return finished list
        return lst_commands #lst_temp
    
    # Failed to open file
    #print("Failed to open alias file: " + aliasfile)
    return False

def fixexports(lst_data):
    """ 
        Fixes export data in main list, 
        "Yes", "No", or "Not Needed" is added to item info 
    """
    lst_exports = readexports()
    
    # file failed to load completely
    if lst_exports == False or lst_data == False:
        #print("fixexports: Failed to load exports list.")
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
    #if len(lst_data) == 0: 
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

def filename_safe(sfilename, maxchars = 30):
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
      
def pick_aliasfile(saliasfile = "", bexit_on_refusal = True):
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

def create_blank_file(sfilename, bshow_exists_warning = False):
    """ Creates a blank alias file """
    if (bshow_exists_warning and
        os.path.isfile(sfilename)):
        dlg = Dialogs()
        resp = dlg.msgbox_yesno("File exists:\n" + sfilename  + '\n\n' + \
                                 "Would you like to overwrite it?")
        if resp == gtk.RESPONSE_NO:
            return False
        
    try:
        with open(sfilename, 'w') as fwrite:
            fwrite.write("# Blank alias file for " + settings.name)
            settings.setsave("aliasfile", sfilename)
            return True
    except Exception as ex:
        dlg.msgbox("Could not create blank file:\n" + \
                    sfilename + '\n\n' + \
                    "<b><u>Error:</u></b>\n" + str(ex))
        print("aliasmgr.py: Error creating blank file:\n" + \
              str(ex))
    
    return False
    
def integration_choice():
    """ Ask the user if they want to automatically integrate Alias Manager with bashrc """
    dlg = Dialogs()
    resp = dlg.msgbox_yesno(settings.name + " will add a line to bashrc that will " + \
               "allow you to easily integrate alias scripts into bashrc.\n" + \
               "If your bashrc requires root permissions to edit, you will " + \
               "have to enter root's password.\n\n" + \
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
            do_chmod = dlg.msgbox_yesno("For this script to work it needs " + \
                                        "to be executable, and you will need " + \
                                        "to enter root's password.\n" + \
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
 
