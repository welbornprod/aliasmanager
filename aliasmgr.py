#!/usr/bin/env python
'''
    Alias Manager 
    ...manage bash alias files through a GUI
    	view, edit, add, delete, save, load alias scripts
    	integrate one or more scripts into bashrc
    	
    
    Created on Dec 28, 2012

    @author: Christopher Welborn
'''
# python3 style print function
from __future__ import print_function
import os, sys    # basic file/system stuff
import gtk        # user interface
import pango      # font stuff
import subprocess # opening external editor

# local utilities
import aliasmgr_integrator
import aliasmgr_settings

# Settings helper
settings = aliasmgr_settings.am_settings()
# Bash Integration helper
integrator = aliasmgr_integrator.am_integrator()
 
# save temp file to home dir
aliasfiletmp = os.path.join(integrator.home, ".aliasmanager.tmp")

def main():
    """ Main entry point for Alias Manager """
    # get user info
    integrator.get_userinfo()
    # get bash file
    aliasfile = settings.get("aliasfile")
    # force file picker if setting does not exist or bad file
    pick_aliasfile(aliasfile)
    # self integration
    if (not integrator.is_integrated() and
        settings.get("integration") != "false"):
        integration_choice()

    largs = sys.argv[1:]
    try:
        if len(largs) == 0:
            # No Args, Load GUI
            appMain = winMain() #@UnusedVariable
            gtk.main()
        else:
            # Args, send to command line
            aliasmgrcmd = cmdline(largs) #@UnusedVariable
            exit(0)
    except KeyboardInterrupt:
        print('\nUser Cancelled, goodbye.\n')
        exit(1)
          
class cmdline():
    """ alias manager command line tools """
    def __init__(self, largs):
        self.main(largs)
      
    def main(self, largs):
        """ runs command line style, accepts args """
        # Arg 
        if len(largs) > 0:
            # if filename was passed, this will be replaced with filename
            self.aliasfile = settings.get("aliasfile")
            self.arg_handler(largs)
        else:
            print("No arguments supplied to aliasmgr.cmdline!")
            exit(1)
            
    def arg_handler(self, largs):
        """ receives list of args, handles accordingly """
        # Asking for help?
        for sarg in largs:
            if (os.path.isfile(sarg) or
                os.path.isfile(os.path.join(sys.path[0], sarg))):
                self.aliasfile = sarg
            elif "h" in sarg:
                self.printusage()
                self.printhelp()
                exit(0)
            elif "v" in sarg:
                # Asking for version
                self.printver()
                exit(0)
            elif "e" in sarg:
                self.printexports()
                exit(0)
            elif (("p" in sarg)):
                # print aliases (sarg will tell us normal/short/comment/or full style)        
                self.printaliases(sarg)
                exit(0)
            else:
                # Weird arg given
                self.printusage()
                exit(1)
              
    def printver(self):
        print(settings.name + " version " + settings.version)
        print("")
    
    def printusage(self):
        print("Usage: aliasmgr [ p | h | v | e ] [file]\n")
    
    def printhelp(self):
        aliasfile = settings.get("aliasfile")
        if aliasfile == "":
            aliasfile = "(Not selected yet)"
            
        print("  Current file:    " + aliasfile + '\n')
        print("      Commands:")
        print("                   h : Show this help message")
        print("                   v : Print version")
        print("                   e : Print exported names only")
        print("      p[x|s|c|][f|a] : Print current aliases/functions\n")
        print('    Formatting:')
        print("                   x : will print entire functions.")
        print("                   s : only shows names")
        print("                   c : shows names : comments\n")
        print("         Types: ")
        print("                   a : shows aliases only")
        print("                   f : shows functions only\n")
        print("       Example:\n" + \
              "        'aliasmgr pcf' shows names and comments for functions only")
        

     
    def printaliases(self, sarg):
        """ Print aliases in current file """
        
        lst_items = fixexports(readfile())
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
            print("No items found in alias file: " + self.aliasfile)
            
    def printexports(self):
        """ Prints exports only """
        lst_exports = readexports()
        if lst_exports:
            #print("Found " + str(len(lst_exports)) + " exports:")
            for itm in lst_exports:
                print(itm)
        else:
            print("Unable to load exports!")

  
# winMain ------------------------------------------
class winMain():
    
    
    def __init__(self):
        # Open Logfile
        self.flogfile = open(os.path.join(sys.path[0], "aliasmgr.log"), 'w')
            
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(sys.path[0], "aliasmgr_main.glade"))
        # File data
        self.lst_data = None
        
        # Currently selected itm
        self.selname = None
        self.selindex = -1
        
        # Add main form
        self.winMain = self.builder.get_object("winMain")
        
        # Add controls
        self.mnuProgram = self.builder.get_object("mnuProgram")
        self.mnuNewFile = self.builder.get_object("mnuNewFile")
        self.mnuSelFile = self.builder.get_object("mnuSelFile")
        self.mnuSaveFile = self.builder.get_object("mnuSaveFile")
        self.mnuSaveFileAs = self.builder.get_object("mnuSaveFileAs")
        self.mnuAbout = self.builder.get_object("mnuAbout")
        self.mnuClose = self.builder.get_object("mnuClose")
        
        self.mnuBash = self.builder.get_object("mnuBash")
        self.mnuIntegrate = self.builder.get_object("mnuIntegrate")
        self.mnuDeintegrate = self.builder.get_object("mnuDeintegrate")
        self.mnuCheck = self.builder.get_object("mnuCheck")
        self.mnuIntegration = self.builder.get_object("mnuIntegration")
        self.mnuListIntegrated = self.builder.get_object("mnuListIntegrated")
        
        self.btnAdd = self.builder.get_object("btnAdd")
        self.btnRename = self.builder.get_object("btnRename")
        self.btnRemove = self.builder.get_object("btnRemove")
        self.btnReload = self.builder.get_object("btnReload")
        self.btnSave = self.builder.get_object("btnSave")
        self.btnClose = self.builder.get_object("btnClose")
        self.btnSaveCmd = self.builder.get_object("btnSaveCmd")
        self.btnEdit = self.builder.get_object("btnEdit")
        self.lblStat = self.builder.get_object("lblStat")
        self.lblFilename = self.builder.get_object("lblFilename")
        self.chkExport = self.builder.get_object("chkExport")
        self.chkAutosave = self.builder.get_object("chkAutosave")
        self.listAliases = self.builder.get_object("listAliases")
        self.treeAliases = self.builder.get_object("treeAliases")
        self.bufCommand = self.builder.get_object("bufCommand")
        self.txtCommand = self.builder.get_object("txtCommand")
        self.bufComment = self.builder.get_object("bufComment")
        self.txtComment = self.builder.get_object("txtComment")
        self.scrollAliases = self.builder.get_object("scrollAliases")
        self.scrollCommand = self.builder.get_object("scrollCommand")
        self.entrySearch = self.builder.get_object("entrySearch")

        # Setup treeAliases
        # Create 'Text' Column (MenuEntries) for tree
        cellNames = gtk.CellRendererText()
        # Create Column for tree
        self.colNames = gtk.TreeViewColumn("Aliases: 0")
        # Set spacing for icon/text
        self.colNames.set_spacing(4)
    
        # Add Markup to treeview
        self.colNames.pack_start(cellNames, False)
        self.colNames.add_attribute(cellNames, "markup", 0)
        # Add 'MenuEntries' column to tree
        self.treeAliases.append_column(self.colNames)
        
        
        # Create treeView Selection for tree
        self.treeSel = self.treeAliases.get_selection()
        self.treeSel.set_mode(gtk.SELECTION_SINGLE)
        # manually connect treeNamesSel to 'changed' event self.treeSel_changed()
        self.treeSel.connect("changed", self.treeSel_changed_cb)
        
        # Add monospace font for Command
        # Build available fonts list
        pango_context = self.winMain.create_pango_context()
        pango_fonts = pango_context.list_families()
        lst_fonts = []
        for itm in pango_fonts:
            lst_fonts.append(itm.get_name())
        
        # DejaVu Sans Mono available?
        if "DejaVu Sans Mono" in lst_fonts:
            font_use = pango.FontDescription("DejaVu Sans Mono 9")
        else:
            font_use = pango.FontDescription("Monospace 9")
            self.printlog("Using default monospace font...")
        # Set font used for Command
        self.txtCommand.modify_font(font_use)
        
        # Set Tab-Depth for Command
        pango_tabs = pango.TabArray(1, True)
        pango_tabs.set_tab(0, pango.TAB_LEFT, 30)
        self.txtCommand.set_tabs(pango_tabs)
        
        # Remove font list, not needed anymore. Will free up memory on garbage collection
        del pango_fonts
        del lst_fonts
        
        
        # Connect all signals
        self.builder.connect_signals(self)
        
        # Load data
        self.load_aliases()
        self.stat_settext("Alias file loaded.")
        self.treeAliases.set_search_column(0)
        # Load settings
        self.chkAutosave.set_active("true" in settings.get("autosave"))
        self.mnuIntegration.set_active("true" in settings.get("integration"))
        # Show window
        self.winMain.show()
        
        
    def winMain_destroy_cb(self, widget, data=None):
        if dlg.lastpath != None:
            settings.setsave("dlglastpath", dlg.lastpath)
        if self.flogfile != None:
            self.flogfile.close()
        gtk.mainquit()
        exit(0)
           
    def treeSel_changed_cb(self, widget, user_data=None):
        # Find info for this item

        # Get Selected Item
        (modelNames, iterNames) = self.treeSel.get_selected()
        
        # Item Selected?
        if iterNames == None:
            self.selname = ""
            self.selindex = -1
            self.selitem = None
        else:
            
            # Get Value of Selected Item
            itmValue = modelNames.get_value(iterNames, 0)
            # Set selected name/item (makes some code shorter later)
            self.selname = trim_markup(itmValue)
            self.selitem = self.get_item(self.selname)
            
            # get index for this item
            for itmindex in range(0, len(self.lst_data)):
                # Found value in main data list?
                if trim_markup(itmValue) == self.lst_data[itmindex].name:
                    # Set selected index
                    self.selindex = itmindex
                    
            # Retrieve command
            #scmdlst = self.lst_data[itmindex].cmd
            scmdlst = self.selitem.cmd
            self.txtCommand_clear()
            # Build command string
            scmd = ""
            for sitm in scmdlst:
                scmd += sitm + "\n"
            # Remove last \n char
            if scmd.endswith('\n'):
                scmd = scmd[:len(scmd) - 1]
                
            # Set to textbox
            self.txtCommand_settext(scmd)
            
            # Is item exported?
            #sexport = self.lst_data[itmindex].exported.lower()
            sexport = self.selitem.exported.lower()
            self.chkExport.set_active((sexport == "yes") or (sexport == "new"))
            
            # Set Export sensitive if its a function (if command is more than 1 line)
            self.chkExport.set_sensitive(len(scmdlst) > 1)
            
            # Get comment
            #scomment = self.lst_data[itmindex].comment
            scomment = self.selitem.comment
            self.txtComment_clear()
            if len(scomment.replace(' ', '')) > 0:
                self.txtComment_settext(scomment)
            # Fix status
            if self.lblStat.get_text() != settings.name:
                self.stat_settext(settings.name)
                       
    def chkExport_toggled_cb(self, widget, data=None):
        # No item selected?
        if self.selindex == -1:
            return False
        
        # Save exported value to lst_data
        if widget.get_active():
            # Toggled!
            self.lst_data[self.selindex].exported = "Yes"
            if self.selitem.isfunction():
                #if self.is_function(self.selname):
                # Set markup
                self.treeAliases_setvalue("<i>" + self.selname + "</i>")
            # Fix status
            self.stat_settext("Item " + self.selname + " is exported.")
        else:
            self.lst_data[self.selindex].exported = "No"
            if self.selitem.isfunction():
            #if self.is_function(self.selname):
                # Set markup
                self.treeAliases_setvalue("<b><i>" + self.selname + "</i></b>")
            # Fix status
            self.stat_settext("Item " + self.selname + " is not exported.")
        # Success    
        return True 
      
    def chkAutosave_toggled_cb(self, widget, data=None):
        # Save setting to file
        if widget.get_active():
            # with open(os.path.join(sys.path[0], "autosave.conf"), 'w') as fset:
            #     fset.write("1")
            if settings.setsave("autosave", "true"):
                self.stat_settext("Alias file will be saved on command save.")

        else:
            #with open(os.path.join(sys.path[0], "autosave.conf"), 'w') as fset:
            #    fset.write("0")
            if settings.setsave("autosave", "false"):
                self.stat_settext("Alias file will not be saved on command save.")
    
    def mnuProgram_deselect_cb(self, widget, data=None):
        """ Clears status label so menu-descriptions don't stick """
        self.lblStat.set_markup("")
    
    def mnuNewFile_select_cb(self, widget, data=None):
        self.stat_settext("Create a new blank alias file...")
    def mnuNewFile_button_release_event_cb(self, widget, signal_id, data=None):
        """ Creates a new, blank alias file to use/edit """
        sfile = dlg.dialog("Select a name for the new file...", dlg.saveas)
        
        if sfile == "":
            return False
            
        # Create a new blank file...
        if create_blank_file(sfile, True):
            settings.setsave("aliasfile", sfile)
            self.set_filename(sfile)
            self.load_aliases(True)
            self.stat_settext("Created new alias file: " + filename_safe(sfile))
        else:
            self.stat_settext("Unable to create new file!")
            dlg.msgbox("Unable to create new file at:\n" + sfile,
                        dlg.error) 
            
    def mnuSelFile_select_cb(self, widget, data=None):
        self.stat_settext("Select which alias file to use...")
    def mnuSelFile_button_release_event_cb(self, widget, signal_id, data=None):
        """ Open alias file """
        # Select new alias file
        sfile = dlg.dialog("Select an alias file to use:")
        
        if os.path.isfile(sfile):
            settings.setsave("aliasfile", sfile)
            self.stat_settext("Alias file: " + filename_safe(sfile))
            self.printlog("Selected alias file: " + settings.get("aliasfile"))
            # reload aliases from this file
            self.load_aliases(True)
    
    def mnuSaveFile_select_cb(self, widget, data=None):
        self.stat_settext("Save current alias file...")
    def mnuSaveFile_button_release_event_cb(self, widget, signal_id, data=None):
        """ Save current alias file """
        if self.save_file():
            self.stat_settext("Alias file saved: " + \
                              filename_safe(settings.get("aliasfile")))
        else:
            self.printlog("Unable to save alias file: " + \
                          filename_safe(settings.get("aliasfile")))
            self.stat_settext("Unable to save alias file!")
        
    def mnuSaveFileAs_select_cb(self, widget, data=None):
        self.stat_settext("Save alias file with another filename...")
    def mnuSaveFileAs_button_release_event_cb(self, widget, signal_id, data=None):
        """ Save alias file using aother filename """
        sfile = dlg.dialog("Save file as...", dlg.saveas)
        
        if sfile == "": 
            return False
        if os.path.isfile(sfile):
            resp = dlg.msgbox_yesno("File exists:\n" + sfile + '\n' + \
                                     "Would you like to overwrite the file?")
            if resp == gtk.RESPONSE_NO: 
                return False
        
        # actually save the file
        if self.save_file(sfile):
            self.stat_settext("Alias file saved as: " + \
                              filename_safe(sfile))
        else:
            self.stat_settext("Unable to save alias file: " + \
                              filename_safe(sfile))
          
    
    def mnuClose_select_cb(self, widget, data=None):
        self.stat_settext("Close " + settings.name + "...")
    def mnuClose_button_release_event_cb(self, widget, signal_id, data=None):
        if dlg.lastpath != None:
            settings.setsave("dlglastpath", dlg.lastpath)
        if self.flogfile != None:
            self.printlog("Closing log...")
            self.flogfile.close()
            
        self.stat_settext("Closing...")
        gtk.main_quit()
        exit(0)
        
    def mnuAbout_select_cb(self, widget, data=None):
        self.stat_settext("Alias Manager version and info...")
    def mnuAbout_button_release_event_cb(self, widget, signal_id, data=None):
        smsg = '<i>version ' + settings.version + '</i>\n\n' + \
                '<u>author:</u> Christopher Welborn\n' + \
                '<u>email:</u> <a href="mailto:cj@welbornproductions.net">' + \
                'cj@welbornproductions.net</a>'
        dlg.msgbox(smsg, gtk.MESSAGE_INFO)
        
    def mnuBash_deselect_cb(self, widget, data = None):
        self.stat_settext("")
        
    def mnuIntegrate_select_cb(self, widget, data=None):
        self.stat_settext("Integrate this alias file into bashrc...")
    def mnuIntegrate_button_release_event_cb(self, widget, signal_id, data=None):
        saliasfile = settings.get("aliasfile")
        if integrator.bashrc == None:
            if not integrator.find_bashrc():
                dlg.msgbox("Unable to find bashrc file!\n" + \
                           "You may need to create a file called\n" + \
                           ".bashrc or bash.bashrc in /home" + \
                           integrator.home + ' \n' + \
                           "or /etc/.", dlg.error)
                
        if integrator.helper_checkfile(saliasfile):
            dlg.msgbox("File is already integrated.")
        else:
            sfile = '<b><u>File:</u></b>\n<i>' + \
                    saliasfile + '</i>\n\n'
            sbashrc = '<b><u>Bashrc:</u></b>\n<i>' + \
                    integrator.bashrc + '</i>'
            sheader = sfile + sbashrc
            if integrator.helper_addfile(saliasfile):
                # go ahead and check file mode, chmod +x if needed.
                # (not everyone remembers they have to do this,
                #  they will want 'Integrate' to 'just work')
                chmod_file(saliasfile)
                dlg.msgbox(sheader + '\n\nFile was integrated.')
            else:
                dlg.msgbox(sheader + '\n\nFailed to integrate file into bashrc!')
    
    def mnuDeintegrate_select_cb(self, widget, data=None):
        self.stat_settext("Remove this alias file from bashrc integration...")
    def mnuDeintegrate_button_release_event_cb(self, widget, signal_id, data=None):
        saliasfile = settings.get("aliasfile")
        if integrator.bashrc == None:
            if not integrator.find_bashrc():
                dlg.msgbox("Unable to find bashrc file!\n" + \
                           "You may need to create a file called\n" + \
                           ".bashrc or bash.bashrc in /home" + \
                           integrator.home + ' \n' + \
                           "or /etc/.", dlg.error)
                
        if integrator.helper_checkfile(saliasfile):
            sfile = '<b><u>File:</u></b>\n<i>' + \
                    saliasfile + '</i>\n\n'
            sbashrc = '<b><u>Bashrc:</u></b>\n<i>' + \
                    integrator.bashrc + '</i>'
            sheader = sfile + sbashrc
            if integrator.helper_removefile(saliasfile):
                dlg.msgbox(sheader + '\n\nFile was de-integrated.')
            else:
                dlg.msgbox(sheader + '\n\nFailed to de-integrate file into bashrc!')
        else:
            dlg.msgbox("File is not integrated.")
    
    def mnuCheck_select_cb(self, widget, data=None):
        self.stat_settext("Check if this file is integrated with bashrc...")
    def mnuCheck_button_release_event_cb(self, widget, signal_id, data=None):
        if integrator.bashrc == None:
            if not integrator.find_bashrc():
                dlg.msgbox("Unable to find bashrc file!\n" + \
                           "You may need to create a file called\n" + \
                           ".bashrc or bash.bashrc in /home" + \
                           integrator.home + ' \n' + \
                           "or /etc/.", dlg.error)
            
        
        if integrator.helper_checkfile(settings.get("aliasfile")):
            sstatus = "File is integrated."
        else:
            sstatus = "File is NOT integrated."
            
        saliasfile = '<i>' + settings.get("aliasfile") + '</i>\n\n'
        sbashrc = '<i>' + integrator.bashrc + '</i>\n\n'
            
        smsg = "<b><u>File:</u></b>\n" + \
                saliasfile + \
                "<b><u>Bashrc:</u></b>\n" + \
                sbashrc + \
                sstatus
        dlg.msgbox(smsg, dlg.info)
    
    def mnuListIntegrated_select_cb(self, widget, data=None):
        self.stat_settext("List all shell scripts integrated with bashrc...")
    def mnuListIntegrated_button_release_event_cb(self, widget, signal_id, data=None):
        lst_integrated = integrator.get_integrated_files()
        lst_helperintegrated = integrator.helper_getfiles()
        if len(lst_integrated) == 0:
            dlg.msgbox("Cannot find any files integrated with bashrc.", 
                       dlg.info)
        else:
            sfiles = ""
            for sfile in lst_integrated:
                sfiles += '<small><i>' + sfile + '</i></small>\n'
            shelperfiles = ""
            for sfile in lst_helperintegrated:
                shelperfiles += '<small><i>' + sfile + '</i></small>\n'
            if sfiles == "":
                sfiles = "<small><i>(None)</i></small>"
            if shelperfiles == "":
                shelperfiles = "<small><i>(None)</i></small>"
            smsg = "<b><u>Bashrc file:</u></b>\n" + \
                    '<small><i>' + integrator.bashrc + '</i></small>\n\n' + \
                    "<b><u>Directly integrated:</u></b>\n" + \
                    sfiles + '\n' + \
                    "<b><u>" +  settings.name + " integrated:</u></b>\n" + \
                    shelperfiles
            dlg.msgbox(smsg, dlg.info)
    
    def mnuIntegration_select_cb(self, widget, data=None):
        self.stat_settext("Enable/Disable easy integration...")
    def mnuIntegration_toggled_cb(self, widget, data=None):
        if self.mnuIntegration.get_active():
            if settings.get("integration") != "true":
                if integrator.is_integrated():
                    settings.set('integration', 'true')
                    self.stat_settext("Already enabled in bashrc...")
                else:
                    if integration_choice():
                        settings.set('integration', 'true')
                        self.stat_settext("Integration enabled...")
        else:
            if settings.get("integration") == "true":
                resp = dlg.msgbox_yesno("Disabling integration means you will " + \
                                        "have to manually edit your bashrc for " + \
                                        "alias scripts to work.\n\n" + \
                                        "Are you sure you want to disable it?")
                if resp == gtk.RESPONSE_YES:
                    settings.set('integration', 'false')
                    integrator.deintegrate_self()
                    self.stat_settext("Integration disabled...")
        
        self.mnuIntegration.set_active(settings.get("integration") == "true")    
                              
    def txtComment_button_release_event_cb(self, widget, signal_id, data=None):
        pass
        
    def txtComment_key_release_event_cb(self, widget, event, data=None):
        if event.keyval == gtk.gdk.keyval_from_name('Return'):
        
            # Trim new line from comment, prevent multi line comments
            startiter, enditer = self.bufComment.get_bounds()
            scomment = self.bufComment.get_text(startiter, enditer)

            if scomment.endswith('\n'):
                self.txtComment_clear()
                self.txtComment_settext(scomment[:len(scomment) - 1])
                
            # Focus command window
            self.txtCommand.grab_focus()
            
            
    def txtCommand_key_release_event_cb(self, widget, event, data=None):
        if event.keyval == gtk.gdk.keyval_from_name('Return'):
            # Save command on [ENTER]
            scmd = self.buf_gettext(self.bufCommand)
            
            # Two newlines at end? must have wanted to save
            if scmd.endswith('\n\n'):
                scmd = scmd[: len(scmd) - 2]
                self.txtCommand_settext(scmd)
                
                # Call save button
                self.btnSaveCmd_clicked_cb(widget)
                       
    def btnAdd_activate_cb(self, widget):
        self.btnAdd_clicked_cb(widget)
    def btnRename_activate_cb(self, widget):
        self.btnRename_clicked_cb(widget)
    def btnRemove_activate_cb(self, widget):
        self.btnRemove_clicked_cb(widget)
    def btnSave_activate_cb(self, widget):
        self.btnSave_clicked_cb(widget)
    def btnReload_activate_cb(self, widget):
        self.btnReload_clicked_cb(widget)
    def btnClose_activate_cb(self, widget):
        self.btnClose_clicked_cb(widget)
    def btnSaveCmd_activate_cb(self, widget):
        self.btnSaveCmd_clicked_cb(widget)
    def btnEdit_activate_cb(self, widget):
        self.btnEdit_clicked_cb(widget)
        
    # Buttons.Click ----------------------------------------------      
    def btnAdd_clicked_cb(self, widget):
        sname = input_text(message="Enter a name for this command:")
        
        # No text, Item already exists, bad name?
        if self.item_badname(sname):
            return False
            
        # Add name to list with empty data
        cmd = command()
        cmd.name = sname
        cmd.cmd = []
        cmd.comment = ""
        cmd.exported = "New"
        self.lst_data.append(cmd)

        # Reload aliases from lst_data
        self.load_aliases(False)
        self.stat_settext("Item added: " + sname)
        self.printlog("Item added: " + sname)
        # Select new item
        self.alias_select_byname(cmd.name)
    
    def btnRename_clicked_cb(self, widget):
        if self.selindex < 0:
            dlg.msgbox("You must select an alias to rename.", gtk.MESSAGE_ERROR)
            return False

        sname = input_text(message="Enter a new name for this command:",
                           default=self.selname)

        # No text, Item already exists, bad name?
        if self.item_badname(sname):
            return False
            
        # Retrieve old command, alter its name.
        self.lst_data[self.selindex].name = sname
        sexported = self.selitem.exported
          
        
        # Reload aliases from lst_data
        self.load_aliases(False)
       
        self.stat_settext("Item renamed: " + sname)
        self.printlog("Item renamed: " + sname)
        # Select new item
        self.alias_select_byname(sname)
        
        # Autosave preserves exported status
        if self.chkAutosave.get_active():
            if self.selitem.exported != sexported:
                self.lst_data[self.selindex].exported = sexported
                self.btnSaveCmd_clicked_cb(widget)
                
    def btnReload_clicked_cb(self, widget):
        self.load_aliases(True)
        aliasfile = settings.get("aliasfile")
        self.stat_settext("File reloaded: " + filename_safe(aliasfile))
        self.printlog("Aliases reloaded from file: " + aliasfile)
            
    def btnSave_clicked_cb(self, widget):           
        self.save_file()
        
        # Finished, set status text and reload aliases
        if widget == self.btnSave:
            self.stat_settext("Saved alias file.")
            dlg.msgbox("Saved alias file to:\n" + settings.get("aliasfile"))
        else:
            # Saved from other command, give some more info
            # Function or alias?
            if self.selitem.isfunction():
            #if len(self.lst_data[self.selindex].cmd) > 1:
                # Function
                stype = "Function"
            else:
                # Alias
                stype = "Alias"
            # Name
            sname = self.selname
            # Set text using this commands data
            self.stat_settext(stype + " '" + sname + "' saved in alias file.")
        # Reload from file
        self.load_aliases(True)
        
    def btnRemove_clicked_cb(self, widget):
        """ Remove currently selected item from main data list """
        # Item Selected?
        if self.selindex < 0:
            return False
        
        litem = self.lst_data[self.selindex]
        sname = self.selname
        self.lst_data.remove(litem)
        self.selindex = None
        self.selitem = None
        self.selname = None
        self.txtComment_clear()
        self.txtCommand_clear()
        
        # Reload data
        self.load_aliases(False)
        self.stat_settext("Item removed: " + sname)
        self.printlog("Item removed: " + sname)
        # Auto save?
        if self.chkAutosave.get_active():
            self.btnSave_clicked_cb(widget)
                 
    def btnClose_clicked_cb(self, widget):
        self.printlog("Closing...")
        self.winMain_destroy_cb(widget)
    
    def btnSaveCmd_clicked_cb(self, widget):
        """ Save command into main data list """
        
        # Send to Add
        #    if not editing a selected item...
        if (self.selname == None or
            self.selitem == None or
            self.selindex == None):
            if len(self.listAliases) == 0:
                dlg.msgbox("You must add an alias before editing/saving commands.")
            else:
                dlg.msgbox("You must select an alias to edit.")
            return False
        
        #Get command text
        startiter, enditer = self.bufCommand.get_bounds()
        scmd = self.bufCommand.get_text(startiter, enditer)
        # multiline command
        if '\n' in scmd:
            slines = scmd.split('\n')
        else:
            # single line command
            slines = [scmd]

               
        # Alias or function?
        if len(slines) > 1:
            # Function
            # Make it auto exported if its a new item
            if (self.selitem.exported.lower() == "new" or
                self.selitem.exported.lower() == "n/a"):
                self.lst_data[self.selindex].setexport(True)
            stype = "Function"
            smarkup = "<i>" + self.selname + "</i>"
            if not self.lst_data[self.selindex].isexported():
                smarkup = "<b><i>" + self.selname + "</i></b>"
            self.chkExport.set_active(self.lst_data[self.selindex].isexported())
            self.chkExport.set_sensitive(True)

        else:
            # Alias doesn't need export
            self.lst_data[self.selindex].exported = "N/A"
            stype = "Alias"
            smarkup = self.selname
            self.chkExport.set_active(False)
            self.chkExport.set_sensitive(False)

        # Save Comment
        # Get comment text
        startiter, enditer = self.bufComment.get_bounds()
        scomment = self.bufComment.get_text(startiter, enditer)
        self.lst_data[self.selindex].comment = scomment
            
        # Save command data    
        self.lst_data[self.selindex].cmd = slines
        # Correct markup for this command (may have changed
        self.treeAliases_setvalue(smarkup)
          
        self.stat_settext(stype + " saved: " + self.selname)
        self.printlog(stype + " saved for: " + self.selname)
        # Auto save?
        if self.chkAutosave.get_active():
            self.btnSave_clicked_cb(widget)
            
    def btnEdit_clicked_cb(self, widget):
        sexe = settings.get("editor")
        if sexe == "":
            dlg.msgbox("No editor has been set, please select a valid text/" + \
                       "shell script editor.")
            sexe = self.select_editor()
            
        if not os.path.isfile(sexe):
            self.printlog("btnEdit: Invalid Editor!: " + sexe)
            dlg.msgbox("Invalid editor, file not found: " + sexe + '\n' + \
                       "Please select a valid editor.")
            sexe = self.select_editor()   
        
        if os.path.isfile(sexe):    
            scmd = sexe + " " + settings.get("aliasfile")
            try:
                subprocess.Popen(scmd.split(" "))
                self.stat_settext("Opened " + scmd + "...")
                self.printlog("Opened " + scmd + "...")
            except Exception as ex:
                self.stat_settext("Unable to open: " + scmd)
                self.printlog("Unable to open: " + scmd)
                self.printlog("Error: " + str(ex))
                dlg.msgbox("Unable to open: " + scmd + "\n\n" + \
                            "<b>Error:</b>\n" + str(ex))

    def entrySearch_changed_cb(self, user_data=None):
        """ auto-selects items based on search text """
        if self.entrySearch.get_text_length() > 0:
            stext = self.entrySearch.get_text()
            self.alias_select_bypart(stext)
        
# Local.Functions --------------------------------------------------
    def stat_settext(self, s_text, shtmlcolor = '#909090'):
        # Set Status text using color (saves typing, custom color available)
        self.lblStat.set_markup("<span foreground='" + shtmlcolor + "'>" + s_text + "</span>")
        
    def buf_gettext(self, bufferObj, startIter = None, endIter = None):
        """ get text from textbuffer, retrieves all text by default """
        #Get all bounds, we'll replace with custom ones if needed
        iterstart, iterstop = bufferObj.get_bounds()
        
        if startIter == None and endIter == None:
            # All Text
            return bufferObj.get_text(iterstart, iterstop)
        elif startIter == None and endIter != None:
            # Custom Stop
            return bufferObj.get_text(iterstart, endIter)
        elif startIter != None and endIter == None:
            # Custom Start
            return bufferObj.get_text(startIter, iterstop)
        else:
            # Both custom
            return bufferObj.get_text(startIter, endIter) 
    
           
    def txtComment_settext(self, strToAdd, sFormatTagName = None):
        """ Set text to txtComment """
        if (sFormatTagName == None) or (sFormatTagName == ""):
            # Set Text to Buffer without formatting
            self.bufComment.set_text(strToAdd)
        else:
            # Set text to BUffer with formatting..
            sob, eob = self.bufComment.get_bounds() #@UnusedVariable
            self.bufComment.insert_with_tags_by_name(eob, strToAdd, sFormatTagName)

        # Show Text Buffer
        self.txtComment.set_buffer(self.bufComment)
              
    def txtCommand_settext(self, strToAdd, sFormatTagName = None):
        """
            Set text to txtCommand using no formatting, or tag formatting..
        """
        if (sFormatTagName == None) or (sFormatTagName == ""):
            # Set Text to Buffer without formatting
            self.bufCommand.set_text(strToAdd)
        else:
            # Set text to BUffer with formatting..
            sob, eob = self.bufCommand.get_bounds() #@UnusedVariable
            self.bufCommand.insert_with_tags_by_name(eob, strToAdd, sFormatTagName)

        # Show Text Buffer
        self.txtCommand.set_buffer(self.bufCommand)
        
    def txtCommand_clear(self, iterStart = None, iterStop = None):
        """
            Clears all txtCommand text by default, with options for
            custom start/stop positions....
        """
        
        startiter, enditer = self.bufCommand.get_bounds() #@UnusedVariable
        if iterStart == None and iterStop == None:
            # Delete from actual start (ALL TEXT)
            self.bufCommand.delete(startiter, enditer)
        elif iterStop == None and iterStart != None:
            # Delete from custom start position to end
            self.bufCommand.delete(iterStart, enditer)
        elif iterStart == None and iterStop != None:
            # Delete from start to custom stop position
            self.bufCommand.delete(startiter, iterStop)
        else:
            # Delete from custom start & stop position
            self.bufCommand.delete(iterStart, iterStop)
    def txtComment_clear(self, iterStart = None, iterStop = None):
        """
            Clears all txtComment text by default, with options for
            custom start/stop positions....
        """
        
        startiter, enditer = self.bufComment.get_bounds() #@UnusedVariable
        if iterStart == None and iterStop == None:
            # Delete from actual start (ALL TEXT)
            self.bufComment.delete(startiter, enditer)
        elif iterStop == None and iterStart != None:
            # Delete from custom start position to end
            self.bufComment.delete(iterStart, enditer)
        elif iterStart == None and iterStop != None:
            # Delete from start to custom stop position
            self.bufComment.delete(startiter, iterStop)
        else:
            # Delete from custom start & stop position
            self.bufComment.delete(iterStart, iterStop)

    def treeAliases_setvalue(self, snewvalue, iiter = None):
        """ Set value in treeAliases, default is selected item, otherwise
            needs an iter... """
            
        if iiter == None:
            # Use selected item to set new value
            # Get selected data
            modelNames, iterNames = self.treeSel.get_selected()
            
            # Item Selected?
            if iterNames != None:
                modelNames.set_value(iterNames, 0, snewvalue)
                return True
                
        else:
            # Custom iter
            modelNames.set_value(iiter, 0, snewvalue)
            return True
        #  Failure
        return False
    
    def tree_select(self, iindex, selObject = None):
        """ Selects a row in treeView """
        if selObject is None:
            selObject = self.treeSel
        # Select an item (based on index) in the treeNames.treeSelection:
        selObject.select_path(iindex)


    def tree_select_byname(self, sname, listStore = None, selObject = None):
        """ selects a treeview object by name """
        if listStore is None:
            listStore = self.listAliases
        if selObject is None:
            selObject = self.treeSel
            
        iindex = self.tree_get_index(sname, listStore)
        if iindex > -1:
            self.tree_select(iindex, selObject)
    
    def tree_select_bypart(self, parttext, listStore = None, selObject = None):
        """ selects a treeview item if it starts with parttext """
        if listStore is None:
            listStore = self.listAliases
        if selObject is None:
            selObject = self.treeSel
            
        iindex = self.tree_get_index_search(parttext, listStore)
        if iindex > -1:
            self.tree_select(iindex, selObject)
                
    def tree_get_index(self, sname, listStore = None):
        """ retrieve an items index by name """
        if listStore is None:
            listStore = self.listAliases
            
        for i in range(0, len(listStore)):
            # get row i, column 0's text
            name = listStore[i][0]
            # probably has pango markup, we need to trim it,
            if sname == trim_markup(name):
                return i
        # not found
        return -1
    
    def tree_get_index_search(self, parttext, listStore = None):
        """ retrieves the index of the first item starting with parttext  """
        if listStore is None:
            listStore = self.listAliases
            
        for i in range(0, len(listStore)):
            name = trim_markup(listStore[i][0])
            if name.startswith(parttext):
                return i
        return -1
    
                       
    def tree_selindex(self, selObject = None):
        """ Gets selected item's index from tree. (tree object must be passed) """
        if selObject is None:
            selObject = self.treeSel
            
        # Get Selected Item
        (modelNames, iterNames) = selObject.get_selected()
        
        # Item Selected?
        if iterNames == None:
            return -1
        else:
            # Get Index of Selected Item
            itmPath = modelNames.get_path(iterNames)
            # return Numeric index of selected item
            return itmPath[0]
        
    def tree_selvalue(self, selObject = None):
        """ Gets selected item's value from treeview """
        if selObject is None:
            selObject = self.treeSel
            
        # Get Selected Item
        (modelNames, iterNames) = selObject.get_selected()
        
        # Item Selected?
        if iterNames == None:
            return ""
        else:
            # Get Value of Selected Item
            itmValue = modelNames.get_value(iterNames, 0)
            # return String containing selected item's value
            return itmValue

    def tree_adjustbars(self, listStore = None, selObject = None, scrollObject = None):
        """ Adjust the scrollbars for when item is selected thru code """
        if listStore is None:
            listStore = self.listAliases
        if selObject is None:
            selObject = self.treeSel
        if scrollObject is None:
            scrollObject = self.scrollAliases
            
        # Adjust scrollbars
        adj = scrollObject.get_vadjustment()
        
            
        itotal_len = len(listStore)    
        # No entries? something is horribly wrong.
        if itotal_len == 0:
            # division by zero error, because no items are loaded
            return False
        # Divide maximum value by total number of entries to get each entry height
        # Empty items, or not filling the list completely causes this to mess up, so
        # We need to account for lists that aren't filling at least one page
        if adj.upper >  adj.get_page_size():    
            iDiv = adj.upper / itotal_len
        else:
            iDiv = 24 # Icon height

        iSel = self.tree_selindex()
        # Calculate new position
        iNewPos = ((iDiv * iSel) - (iDiv / 2))

        adj.set_value(iNewPos)

        
    def alias_select_byname(self, sname):
        """ select alias by name, and adjust scrollbars accordingly """
        self.tree_select_byname(sname)
        self.tree_adjustbars()
    
    def alias_select_bypart(self, sparttext):
        """ select item by part of a name, adjust scrollbars accordingly """
        self.tree_select_bypart(sparttext)
        self.tree_adjustbars()
                           
    def save_file(self, sfilename = None):
        if sfilename == None:
            sfilename = settings.get("aliasfile")
        self.printlog("save_file: saving to: " + sfilename)
        # list for header
        lst_header = []
        # Setup shell script
        lst_header.append("#!/bin/bash\n\n")
        lst_header.append("# Generated by " + settings.name + " " + settings.version + '\n')
        lst_header.append("# Christopher Welborn (cj@welbornproductions.net)\n\n")
        lst_header.append("# Note to user:\n" + \
                         "#     If you must edit this file manually please stick to this style:\n" + \
                         "#         Use tabs, not spaces.\n" + \
                         "#         No tabs before definitons.\n" + \
                         "#         Seperate lines for curly braces.\n" + \
                         "#         Use 1 tab depth for start of code block in functions.\n" + \
                         "#         Function description is first comment in code block. \n" + \
                         "#         Alias description is comment right side of alias definition.\n" + \
                         "#         \n" + \
                         "#     ...if you use a different style it may or may not\n" + \
                         "#        break the program and I can't help you.\n\n")

        # Write Definitions, Cycle thru main data list
        #lst_lines.append("\n# Definitions:\n")
        
        # List for aliases (put'em at the top of the file)
        lst_aliases = []
        # List for functions (put'em after aliases)
        lst_functions = []
        # List for exports (put at bottom of file)
        lst_exports = []
        
        # Cycle thru items in treeAliases (alphabetical already)
        # This extra step makes the functions print in alphbetical order
        # ...aliases and exports don't need this method, a simple sorted(set()) works
        #    because they are single lines. multiline functions can't be sorted like that.
        treeitm = self.listAliases.get_iter_first()
        while (treeitm != None):
            # Get value for this item
            treeval = trim_markup(self.listAliases.get_value(treeitm, 0))
            # try to get next item
            treeitm = self.listAliases.iter_next(treeitm)

            # Search data list for this item, and save data to appropriate list.
            for itm in self.lst_data:
                # Name for alias/function
                sname = itm.name
                # Match tree name with data name, and retrieve it's info...
                if treeval == sname:
                    # Set type based on command length   
                    if len(itm.cmd) > 1:
                        bfunction = True
                    else:
                        bfunction = False
                    
                    # Comments?
                    scomment = itm.comment
                    # Append comment char if needed
                    if (len(scomment) > 0):
                        if not scomment.startswith("#"):
                            scomment = "# " + scomment               
                    # WRITE FUNCTION ITEM
                    if bfunction:
                        lst_functions.append("\nfunction " + sname + "()\n")
                        lst_functions.append("{\n")
                        # comment given?
                        if len(scomment) > 0:
                            lst_functions.append('\t' + scomment + '\n')
                        # Write command section
                        for scmdline in itm.cmd:
                            lst_functions.append('\t' + scmdline + '\n')
                        lst_functions.append("}\n")
                    else:
                        # WRITE ALIAS ITEM
                        # Fix quotes around command
                        if '"' in itm.cmd[0]:
                            scmd = "'" + itm.cmd[0] + "'"
                        else:
                            scmd = '"' + itm.cmd[0] + '"'
                        # Comment given?
                        if len(scomment) > 0:
                            scmd = scmd + " " + scomment
                        lst_aliases.append("alias " + sname + "=" + scmd + '\n')
       
        
        # Save Exports, cycle thru main data list
        #lst_lines.append("\n# Exports\n")
        for itm in self.lst_data:
            if (itm.exported.lower() == "yes"):
                lst_exports.append("export " + itm.name + '\n')
         
        # Finished creating, show what we've got
        #self.printlog("----Generated File:----")
        #for itm in lst_lines:
        #    self.printlog(itm)
        #self.printlog("----END OF FILE----\n")
        
        # Sort lines
        lst_aliases = sorted(set(lst_aliases))
        lst_exports = sorted(set(lst_exports))
        
        # Write file
        btmp = False #@UnusedVariable
        with open(aliasfiletmp, 'w') as fwrite:
            fwrite.writelines(lst_header)
            fwrite.write("\n\n# Aliases:\n")
            fwrite.writelines(lst_aliases)
            fwrite.write("\n# Functions:")
            fwrite.writelines(lst_functions)
            fwrite.write("\n# Exports:\n")
            fwrite.writelines(lst_exports)
            # add new line because its a shell script, needs to end with \n
            fwrite.write('\n')
            #self.printlog("Temporary file written: " + aliasfiletmp)
            btmp = True
        
        if not btmp:
            self.stat_text("Unable to write temp file: " + \
                           filename_safe(aliasfiletmp))
            self.printlog("Unable to write temp file: " + \
                          aliasfiletmp)
            # Temp file didn't write, there is no reason to continue.
            return False
             
        # chmod for tmp file (probably not needed, it doesn't do anything)
        #os.system("chmod a+rwx " + aliasfiletmp)
        
        try:
            # Backup destination file if it doesn't exist
            if (os.path.isfile(sfilename) and 
                (not os.path.isfile(sfilename + "~"))):
                os.system("cp " + sfilename + " " + sfilename + "~")
                self.printlog("Backup created.")
            # Copy temp file to destination,,,    
            os.system("cp " + aliasfiletmp + " " + sfilename)
        except Exception as ex:
            self.stat_settext("Unable to copy to destination: " + \
                              filename_safe(sfilename))
            self.printlog("Unable to copy to destination!")
            self.printlog("Error: " + str(ex))
            return False
            dlg.msgbox("Unable to copy to destination: " + \
                        filename_safe(sfilename), dlg.error)
        self.printlog("Temp file copied to destination: " + sfilename)
        
        # chmod +x if needed
        schmod_result = chmod_file(sfilename)
        self.printlog(schmod_result)
        
        # Success
        return True
                                          
    def load_aliases(self, from_file=True):
        """ Load aliases into treeview using correct markup """
        
        # item already selected? if so, save it to re-select it in a sec.
        prev_name = self.selname
        
        
        # Get file contents aliases/functions, fix Export info
        if from_file:
            self.lst_data = fixexports(readfile())
        else:
            self.lst_data = fixexports(self.lst_data)
            
        # failed to load list
        if self.lst_data == False:
            # Items couldn't be loaded!
            dlg.msgbox("Items could not be loaded!", dlg.error)
            self.printlog("Items could no be loaded!") 
            return False

        # Clear list if needed
        if len(self.listAliases) > 0:
            self.listAliases.clear()
        # Clear current command text
        self.txtComment_clear()
        self.txtCommand_clear()
        
        # Set current file
        self.set_filename(settings.get("aliasfile"))
            
        # Have aliases to load...         
        if self.lst_data:
            # Get sorted names list
            lst_names = []
            for itm in self.lst_data:
                lst_names.append(itm.name)
            lst_names = sorted(set(lst_names))
                
            # Cycle thru aliases
            for itmname in lst_names:
                # Actual item
                itm = self.get_item(itmname)
                # Base for adding markup
                smarkup = "$_ITEM_$"
                # markup for functions
                if itm.isfunction():
                    smarkup = "<i>" + smarkup + "</i>"
                    # Function is exported?
                    if not itm.isexported():
                        smarkup = "<b>" + smarkup + "</b>"            
                    
                # append item with or without markup
                self.listAliases.append([smarkup.replace("$_ITEM_$", itm.name)])
                
            
            self.printlog("Finished loading aliases...")
        else:
            # empty lst_data
            self.printlog("Empty list...")
            
        # Finished, show count
        self.colNames.set_title("Aliases: " + str(len(self.listAliases)))
          
        # Re-select item if needed
        if prev_name == "":
            self.txtComment_clear()
            self.txtCommand_clear()
        else:
            self.alias_select_byname(prev_name)
        
    def item_exists(self, sname):
        """ Item already exists/bad name? """
        for itm in self.lst_data:
            if sname == itm.name:
                self.stat_settext("Item already exists!: " + sname)
                self.printlog("Item already exists!: " + sname)
                dlg.msgbox("Item already exists!: " + sname, dlg.error)
                return True
        return False
    
    def item_badname(self, sname):
        """ Make sure item has a valid name. Does not exist, no $_ITEM_$. """
                # No text entered?
        if sname == None:
            return True
        if sname.replace(' ', '') == "":
            return True
        
        if sname == "$_ITEM_$":
            self.stat_settext("Bad name for item: $_ITEM_$")
            self.printlog("Bad name for item: $_ITEM_$")
            dlg.msgbox("Sorry, you can't use this name. I'm using it.")
            return True
        # exists?
        return self.item_exists(sname)
             
                                
    def get_item(self, sname):
        """ Retrieves item data in lst_data by name """
        if self.lst_data == None:
            return False
        
        for itm in self.lst_data:
            sdataname = itm.name
            if sdataname == sname:
                # Found item by name, return the data
                return itm
        
        # Failed to find it for some reason
        # Return empty command
        cmd = command()
        return cmd
    def set_filename(self, sfilename):
        """ Sets current filename in lblFilename """
        #settings.set("aliasfile", sfilename)
        self.lblFilename.set_markup('<span foreground="#909090">' + \
                                  '<u>Current File:</u>' + \
                                  '</span>' + \
                                  '<span foreground="#808080"> ' + \
                                  sfilename + \
                                  '</span>')
          
    def printlog(self, sstring):
        """ print string to terminal and log file """
        
        print("aliasmgr.py: " + sstring)
        
        if self.flogfile == None:
            self.flogfile = open(os.path.join(sys.path[0], "aliasmgr.log"), 'w')
            
        self.flogfile.write(sstring + '\n')

    def select_editor(self):
        """ Select a text editor, return its filepath. 
            Returns "" on failure.
        """
        dlg_editor = dialogs()
        dlg_editor.filter = [["All Files", "*"]]
        if os.path.isdir('/usr/bin'):
            dlg_editor.lastpath = '/usr/bin'
        sexe = dlg_editor.dialog("Select an editor...")           
        del dlg_editor
        
        if os.path.isfile(sexe):
            settings.setsave("editor", sexe)
        else:
            if sexe != "":
                dlg.msgbox("Editor doesn't exist!", gtk.MESSAGE_ERROR)
            sexe = ""
        return sexe                   
        
# Dialog/Msgbox --------------------------------------------------------       
class dialogs():
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
            
# Command/Alias Object ------------------------------------
class command():
    def __init__(self, name="", cmd=[], comment="", exported="New"):
        self.name = name
        self.cmd = cmd
        self.comment = comment
        self.exported = exported
    
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
                
# Functions ----------------------------------------
def readfile():
    """ Read file into a data list() """
    aliasfile = settings.get("aliasfile")
    if not os.path.isfile(aliasfile):
        #print("Alias file not found!: " + aliasfile)
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
            cmd = command()
            
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
                # Trim start quotes
                if scommand.startswith("'"):
                    scommand = scommand[1:]
                elif scommand.startswith('"'):
                    scommand = scommand[1:]
                # Trim end quotes
                if scommand.endswith("'"):
                    scommand = scommand[:len(scommand) - 1] 
                elif scommand.endswith('"'):
                    scommand = scommand[:len(scommand) - 1]
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
    """ trim filename to maxchars if needed """
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
                sblankfile = os.path.join(integrator.home, "bash.alias.sh")
                create_blank_file(sblankfile, True)
    # return good alias filename
    return sfile

def create_blank_file(sfilename, bshow_exists_warning = False):
    """ Creates a blank alias file """
    if (bshow_exists_warning and
        os.path.isfile(sfilename)):
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
          
# Start.of.script -------------------------------------------------------------
if __name__ == '__main__':
    dlg = dialogs()
    if settings.get("dlglastpath") != "":
        dlg.lastpath = settings.get("dlglastpath")
    main()
