'''
    aliasmgr_gui.py
    GUI for Alias Manager

Created on Sep 24, 2013

@author: cj
'''

import sys
import os
import gtk
import pango
import subprocess

import aliasmgr_integrator
import aliasmgr_util as amutil

# Globals.
settings = amutil.settings
integrator = aliasmgr_integrator.am_integrator()
dlg = amutil.Dialogs()

# winMain ------------------------------------------


class winMain():

    def __init__(self):
        # Open Logfile (if we can)
        self.openlog()

        self.builder = gtk.Builder()
        self.builder.add_from_file(
            os.path.join(sys.path[0], 'aliasmgr_main.glade'))
        # File data
        self.lst_data = None

        # Currently selected itm
        self.selname = None
        self.selindex = -1

        # Add main form
        self.winMain = self.builder.get_object('winMain')

        # Add controls
        self.mnuProgram = self.builder.get_object('mnuProgram')
        self.mnuNewFile = self.builder.get_object('mnuNewFile')
        self.mnuSelFile = self.builder.get_object('mnuSelFile')
        self.mnuSaveFile = self.builder.get_object('mnuSaveFile')
        self.mnuSaveFileAs = self.builder.get_object('mnuSaveFileAs')
        self.mnuAbout = self.builder.get_object('mnuAbout')
        self.mnuClose = self.builder.get_object('mnuClose')

        self.mnuBash = self.builder.get_object('mnuBash')
        self.mnuIntegrate = self.builder.get_object('mnuIntegrate')
        self.mnuDeintegrate = self.builder.get_object('mnuDeintegrate')
        self.mnuCheck = self.builder.get_object('mnuCheck')
        self.mnuIntegration = self.builder.get_object('mnuIntegration')
        self.mnuListIntegrated = self.builder.get_object('mnuListIntegrated')

        self.btnAdd = self.builder.get_object('btnAdd')
        self.btnRename = self.builder.get_object('btnRename')
        self.btnRemove = self.builder.get_object('btnRemove')
        self.btnReload = self.builder.get_object('btnReload')
        self.btnSave = self.builder.get_object('btnSave')
        self.btnClose = self.builder.get_object('btnClose')
        self.btnSaveCmd = self.builder.get_object('btnSaveCmd')
        self.btnEdit = self.builder.get_object('btnEdit')
        self.lblStat = self.builder.get_object('lblStat')
        self.lblFilename = self.builder.get_object('lblFilename')
        self.chkExport = self.builder.get_object('chkExport')
        self.chkAutosave = self.builder.get_object('chkAutosave')
        self.listAliases = self.builder.get_object('listAliases')
        self.treeAliases = self.builder.get_object('treeAliases')
        self.bufCommand = self.builder.get_object('bufCommand')
        self.txtCommand = self.builder.get_object('txtCommand')
        self.bufComment = self.builder.get_object('bufComment')
        self.txtComment = self.builder.get_object('txtComment')
        self.scrollAliases = self.builder.get_object('scrollAliases')
        self.scrollCommand = self.builder.get_object('scrollCommand')
        self.entrySearch = self.builder.get_object('entrySearch')

        # Setup treeAliases
        # Create 'Text' Column (MenuEntries) for tree
        cellNames = gtk.CellRendererText()
        # Create Column for tree
        self.colNames = gtk.TreeViewColumn('Aliases: 0')
        # Set spacing for icon/text
        self.colNames.set_spacing(4)

        # Add Markup to treeview
        self.colNames.pack_start(cellNames, False)
        self.colNames.add_attribute(cellNames, 'markup', 0)
        # Add 'MenuEntries' column to tree
        self.treeAliases.append_column(self.colNames)

        # Create treeView Selection for tree
        self.treeSel = self.treeAliases.get_selection()
        self.treeSel.set_mode(gtk.SELECTION_SINGLE)
        # manually connect treeNamesSel to 'changed' event
        # self.treeSel_changed()
        self.treeSel.connect('changed', self.treeSel_changed_cb)

        # Add monospace font for Command
        # Build available fonts list
        pango_context = self.winMain.create_pango_context()
        pango_fonts = pango_context.list_families()
        lst_fonts = []
        for itm in pango_fonts:
            lst_fonts.append(itm.get_name())

        # DejaVu Sans Mono available?
        if 'DejaVu Sans Mono' in lst_fonts:
            font_use = pango.FontDescription('DejaVu Sans Mono 9')
        else:
            font_use = pango.FontDescription('Monospace 9')
            self.printlog('Using default monospace font...')
        # Set font used for Command
        self.txtCommand.modify_font(font_use)

        # Set Tab-Depth for Command
        pango_tabs = pango.TabArray(1, True)
        pango_tabs.set_tab(0, pango.TAB_LEFT, 30)
        self.txtCommand.set_tabs(pango_tabs)

        # Remove font list, not needed anymore. Will free up memory on garbage
        # collection
        del pango_fonts
        del lst_fonts

        # Connect all signals
        self.builder.connect_signals(self)

        # Load data
        self.load_aliases()
        self.stat_settext('Alias file loaded.')
        self.treeAliases.set_search_column(0)
        # Load settings
        self.chkAutosave.set_active('true' in settings.get('autosave'))
        self.mnuIntegration.set_active('true' in settings.get('integration'))

        # Show window
        self.winMain.show()

    def winMain_destroy_cb(self, widget, data=None):
        if dlg.lastpath is not None:
            settings.setsave('dlglastpath', dlg.lastpath)
        if self.flogfile is not None:
            self.flogfile.close()
        gtk.mainquit()
        sys.exit(0)

    def treeSel_changed_cb(self, widget, user_data=None):
        # Find info for this item

        # Get Selected Item
        (modelNames, iterNames) = self.treeSel.get_selected()

        # Item Selected?
        if iterNames is None:
            self.selname = ''
            self.selindex = -1
            self.selitem = None
            return None

        # Get Value of Selected Item
        itmValue = modelNames.get_value(iterNames, 0)
        # Set selected name/item (makes some code shorter later)
        self.selname = amutil.trim_markup(itmValue)
        self.selitem = self.get_item(self.selname)

        # get index for this item
        for itmindex in range(0, len(self.lst_data)):
            # Found value in main data list?
            if amutil.trim_markup(itmValue) == self.lst_data[itmindex].name:
                # Set selected index
                self.selindex = itmindex

        # Retrieve command
        cmdlst = self.selitem.cmd
        self.txtCommand_clear()
        # Build command string
        scmd = '\n'.join(cmdlst)
        # Set to textbox
        self.txtCommand_settext(scmd)

        # Is item exported?
        sexport = self.selitem.exported.lower()
        self.chkExport.set_active(sexport in ('yes', 'new'))

        # Set Export sensitive if its a function (if command is more than 1
        # line)
        self.chkExport.set_sensitive(len(cmdlst) > 1)

        # Get comment
        # scomment = self.lst_data[itmindex].comment
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
            self.lst_data[self.selindex].exported = 'Yes'
            if self.selitem.isfunction():
                # if self.is_function(self.selname):
                # Set markup
                self.treeAlises_setValue('<i>{}</i>'.format(self.selname))
            # Fix status
            self.stat_settext('Item {} is exported.'.format(self.selname))
        else:
            self.lst_data[self.selindex].exported = 'No'
            if self.selitem.isfunction():
                # if self.is_function(self.selname):
                # Set markup
                self.treeAliases_setvalue(
                    '<b><i>{}</b></i>'.format(self.selname)
                )
            # Fix status
            self.stat_settext('Item {} is not exported.'.format(self.selname))
        # Success
        return True

    def chkAutosave_toggled_cb(self, widget, data=None):
        # Save setting to file
        if widget.get_active():
            if settings.setsave('autosave', 'true'):
                self.stat_settext('Alias file will be saved on command save.')

        else:
            if settings.setsave('autosave', 'false'):
                self.stat_settext(
                    'Alias file will not be saved on command save.'
                )

    def mnuProgram_deselect_cb(self, widget, data=None):
        """ Clears status label so menu-descriptions don't stick """
        self.lblStat.set_markup('')

    def mnuNewFile_select_cb(self, widget, data=None):
        self.stat_settext('Create a new blank alias file...')

    def mnuNewFile_button_release_event_cb(
            self, widget, signal_id, data=None):
        """ Creates a new, blank alias file to use/edit """
        filename = dlg.dialog('Select a name for the new file...', dlg.saveas)

        if not filename:
            return False

        # Create a new blank file...
        if amutil.create_blank_file(filename, True):
            settings.setsave('aliasfile', filename)
            self.set_filename(filename)
            self.load_aliases(True)
            self.stat_settext(
                'Created new alias file: {}'.format(
                    amutil.filename_safe(filename)
                )
            )
        else:
            self.stat_settext('Unable to create new file!')
            dlg.msgbox(
                'Unable to create new file at:\n{}'.format(filename),
                dlg.error
            )

    def mnuSelFile_select_cb(self, widget, data=None):
        self.stat_settext('Select which alias file to use...')

    def mnuSelFile_button_release_event_cb(
            self, widget, signal_id, data=None):
        """ Open alias file """
        # Select new alias file
        sfile = dlg.dialog('Select an alias file to use:')

        if os.path.isfile(sfile):
            settings.setsave('aliasfile', sfile)
            self.stat_settext(
                'Alias file: {}'.format(amutil.filename_safe(sfile))
            )
            self.printlog(
                'Selected alias file: {}'.format(settings.get('aliasfile'))
            )
            # reload aliases from this file
            self.load_aliases(True)

    def mnuSaveFile_select_cb(self, widget, data=None):
        self.stat_settext('Save current alias file...')

    def mnuSaveFile_button_release_event_cb(
            self, widget, signal_id, data=None):
        """ Save current alias file """
        if self.save_file():
            self.stat_settext(
                'Alias file saved: {}'.format(
                    amutil.filename_safe(settings.get('aliasfile'))
                )
            )
        else:
            self.printlog(
                'Unable to save alias file: {}'.format(
                    amutil.filename_safe(settings.get('aliasfile'))
                )
            )
            self.stat_settext('Unable to save alias file!')

    def mnuSaveFileAs_select_cb(self, widget, data=None):
        self.stat_settext('Save alias file with another filename...')

    def mnuSaveFileAs_button_release_event_cb(
            self, widget, signal_id, data=None):
        """ Save alias file using aother filename """
        filename = dlg.dialog('Save file as...', dlg.saveas)

        if not filename:
            return False
        if os.path.isfile(filename):
            resp = dlg.msgbox_yesno(
                '\n'.join((
                    'File exists:\n',
                    filename,
                    'Would you like to overwrite the file?',
                ))
            )
            if resp == gtk.RESPONSE_NO:
                return False

        # actually save the file
        if self.save_file(filename):
            self.stat_settext('Alias file saved as: {}'.format(
                amutil.filename_safe(filename)
            ))
        else:
            self.stat_settext('Unable to save alias file: {}'.format(
                amutil.filename_safe(filename)
            ))

    def mnuClose_select_cb(self, widget, data=None):
        self.stat_settext('Close {}...'.format(settings.name))

    def mnuClose_button_release_event_cb(self, widget, signal_id, data=None):
        if dlg.lastpath is not None:
            settings.setsave('dlglastpath', dlg.lastpath)
        if self.flogfile is not None:
            self.printlog('Closing log...')
            self.flogfile.close()

        self.stat_settext('Closing...')
        gtk.main_quit()
        sys.exit(0)

    def mnuAbout_select_cb(self, widget, data=None):
        self.stat_settext('Alias Manager version and info...')

    def mnuAbout_button_release_event_cb(self, widget, signal_id, data=None):
        dlg.msgbox(
            '\n'.join((
                '<i>version {ver}</i>\n',
                '<u>author:</u> Christopher Welborn',
                '<u>email:</u> <a href=\'mailto:cj@welbornprod.com\'>',
                'cj@welbornprod.com',
                '</a>'
            )),
            gtk.MESSAGE_INFO
        )

    def mnuBash_deselect_cb(self, widget, data=None):
        self.stat_settext('')

    def mnuIntegrate_select_cb(self, widget, data=None):
        self.stat_settext('Integrate this alias file into bashrc...')

    def mnuIntegrate_button_release_event_cb(
            self, widget, signal_id, data=None):
        if not self.ensure_bashrc():
            return None

        aliasfile = settings.get('aliasfile')
        if integrator.helper_checkfile(aliasfile):
            dlg.msgbox('File is already integrated.')
            return None

        if self.file_integrate_msg(
                integrator.helper_addfile(aliasfile),
                successmsg='File was integrated.',
                failuremsg='Failed to integrate file into bashrc!'):
            # go ahead and check file mode, chmod +x if needed.
            # (not everyone remembers they have to do this,
            #  they will want 'Integrate' to 'just work')
            amutil.chmod_file(aliasfile)

    def mnuDeintegrate_select_cb(self, widget, data=None):
        self.stat_settext('Remove this alias file from bashrc integration...')

    def mnuDeintegrate_button_release_event_cb(
            self, widget, signal_id, data=None):
        """ Deintegrate the alias file in bashrc. """
        if not self.ensure_bashrc():
            return None
        aliasfile = settings.get('aliasfile')
        if integrator.helper_checkfile(aliasfile):
            self.file_integrate_msg(
                integrator.helper_removefile(aliasfile),
                successmsg='File was de-integrated.',
                failuremsg='Failed to de-integrate file in bashrc!'
            )
        else:
            dlg.msgbox('File is not integrated.')

    def mnuCheck_select_cb(self, widget, data=None):
        self.stat_settext('Check if this file is integrated with bashrc...')

    def mnuCheck_button_release_event_cb(self, widget, signal_id, data=None):
        if not self.ensure_bashrc():
            return None
        self.file_integrate_msg(
            integrator.helper_checkfile(settings.get('aliasfile')),
            successmsg='File is integrated.',
            failuremsg='File is NOT integrated.'
        )

    def mnuListIntegrated_select_cb(self, widget, data=None):
        self.stat_settext('List all shell scripts integrated with bashrc...')
        
##############################################################################
# TODO: Finished cleanup from here down, much testing needed!
##############################################################################

    def mnuListIntegrated_button_release_event_cb(
            self, widget, signal_id, data=None):
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
                "<b><u>" + settings.name + " integrated:</u></b>\n" + \
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
                    if amutil.integration_choice():
                        settings.set('integration', 'true')
                        self.stat_settext("Integration enabled...")
        else:
            if settings.get("integration") == "true":
                msg = ' '.join((
                    'Disabling integration means you will',
                    'have to manually edit your bashrc for',
                    'alias scripts to work.\n\n',
                    'Are you sure you want to disable it?'
                ))
                if dlg.msgbox_yesno(msg) == gtk.RESPONSE_YES:
                    settings.set('integration', 'false')
                    integrator.deintegrate_self()
                    self.stat_settext("Integration disabled...")

        self.mnuIntegration.set_active(settings.get("integration") == "true")

    def txtComment_button_release_event_cb(
            self, widget, signal_id, data=None):
        """ Nothing yet. """
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

            # Three newlines at end? Do a save.
            if scmd.endswith('\n\n\n'):
                scmd = scmd[:-3]
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
        sname = amutil.input_text(message="Enter a name for this command:")

        # No text, Item already exists, bad name?
        if self.item_badname(sname):
            return False

        # Add name to list with empty data
        cmd = amutil.Command()
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
            dlg.msgbox(
                "You must select an alias to rename.", gtk.MESSAGE_ERROR)
            return False

        sname = amutil.input_text(message="Enter a new name for this command:",
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
        self.stat_settext("File reloaded: " + amutil.filename_safe(aliasfile))
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
                # if len(self.lst_data[self.selindex].cmd) > 1:
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
        if (self.selname is None or
                self.selitem is None or
                self.selindex is None):
            if len(self.listAliases) == 0:
                dlg.msgbox(
                    "You must add an alias before editing/saving commands.")
            else:
                dlg.msgbox("You must select an alias to edit.")
            return False

        # Get command text
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
            self.chkExport.set_active(
                self.lst_data[self.selindex].isexported())
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
            dlg.msgbox("No editor has been set, please select a valid text/" +
                       "shell script editor.")
            sexe = self.select_editor()

        if not os.path.isfile(sexe):
            self.printlog("btnEdit: Invalid Editor!: " + sexe)
            dlg.msgbox("Invalid editor, file not found: " + sexe + '\n' +
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
                dlg.msgbox("Unable to open: " + scmd + "\n\n" +
                           "<b>Error:</b>\n" + str(ex))

    def entrySearch_changed_cb(self, user_data=None):
        """ auto-selects items based on search text """
        if self.entrySearch.get_text_length() > 0:
            stext = self.entrySearch.get_text()
            self.alias_select_bypart(stext)

# Local.Functions --------------------------------------------------
    def stat_settext(self, s_text, shtmlcolor='#909090'):
        # Set Status text using color (saves typing, custom color available)
        self.lblStat.set_markup(
            "<span foreground='" + shtmlcolor + "'>" + s_text + "</span>")

    def buf_gettext(self, bufferObj, startIter=None, endIter=None):
        """ get text from textbuffer, retrieves all text by default """
        # Get all bounds, we'll replace with custom ones if needed
        iterstart, iterstop = bufferObj.get_bounds()

        if startIter is None and endIter is None:
            # All Text
            return bufferObj.get_text(iterstart, iterstop)
        elif startIter is None and endIter is not None:
            # Custom Stop
            return bufferObj.get_text(iterstart, endIter)
        elif startIter is not None and endIter is None:
            # Custom Start
            return bufferObj.get_text(startIter, iterstop)
        else:
            # Both custom
            return bufferObj.get_text(startIter, endIter)

    def txtComment_settext(self, strToAdd, sFormatTagName=None):
        """ Set text to txtComment """
        if not sFormatTagName:
            # Set Text to Buffer without formatting
            self.bufComment.set_text(strToAdd)
        else:
            # Set text to BUffer with formatting..
            sob, eob = self.bufComment.get_bounds()  # @UnusedVariable
            self.bufComment.insert_with_tags_by_name(
                eob, strToAdd, sFormatTagName)

        # Show Text Buffer
        self.txtComment.set_buffer(self.bufComment)

    def txtCommand_settext(self, strToAdd, sFormatTagName=None):
        """
            Set text to txtCommand using no formatting, or tag formatting..
        """
        if not sFormatTagName:
            # Set Text to Buffer without formatting
            self.bufCommand.set_text(strToAdd)
        else:
            # Set text to BUffer with formatting..
            sob, eob = self.bufCommand.get_bounds()  # @UnusedVariable
            self.bufCommand.insert_with_tags_by_name(
                eob, strToAdd, sFormatTagName)

        # Show Text Buffer
        self.txtCommand.set_buffer(self.bufCommand)

    def txtCommand_clear(self, iterStart=None, iterStop=None):
        """
            Clears all txtCommand text by default, with options for
            custom start/stop positions....
        """

        startiter, enditer = self.bufCommand.get_bounds()  # @UnusedVariable
        if iterStart is None and iterStop is None:
            # Delete from actual start (ALL TEXT)
            self.bufCommand.delete(startiter, enditer)
        elif iterStop is None and iterStart is not None:
            # Delete from custom start position to end
            self.bufCommand.delete(iterStart, enditer)
        elif iterStart is None and iterStop is not None:
            # Delete from start to custom stop position
            self.bufCommand.delete(startiter, iterStop)
        else:
            # Delete from custom start & stop position
            self.bufCommand.delete(iterStart, iterStop)

    def txtComment_clear(self, iterStart=None, iterStop=None):
        """
            Clears all txtComment text by default, with options for
            custom start/stop positions....
        """

        startiter, enditer = self.bufComment.get_bounds()  # @UnusedVariable
        if iterStart is None and iterStop is None:
            # Delete from actual start (ALL TEXT)
            self.bufComment.delete(startiter, enditer)
        elif iterStop is None and iterStart is not None:
            # Delete from custom start position to end
            self.bufComment.delete(iterStart, enditer)
        elif iterStart is None and iterStop is not None:
            # Delete from start to custom stop position
            self.bufComment.delete(startiter, iterStop)
        else:
            # Delete from custom start & stop position
            self.bufComment.delete(iterStart, iterStop)

    def treeAliases_setvalue(self, snewvalue, iiter=None):
        """ Set value in treeAliases, default is selected item, otherwise
            needs an iter... """

        if iiter is None:
            # Use selected item to set new value
            # Get selected data
            modelNames, iterNames = self.treeSel.get_selected()

            # Item Selected?
            if iterNames is not None:
                modelNames.set_value(iterNames, 0, snewvalue)
                return True

        else:
            # Custom iter
            modelNames.set_value(iiter, 0, snewvalue)
            return True
        #  Failure
        return False

    def tree_select(self, iindex, selObject=None):
        """ Selects a row in treeView """
        if selObject is None:
            selObject = self.treeSel
        # Select an item (based on index) in the treeNames.treeSelection:
        selObject.select_path(iindex)

    def tree_select_byname(self, sname, listStore=None, selObject=None):
        """ selects a treeview object by name """
        if listStore is None:
            listStore = self.listAliases
        if selObject is None:
            selObject = self.treeSel

        iindex = self.tree_get_index(sname, listStore)
        if iindex > -1:
            self.tree_select(iindex, selObject)

    def tree_select_bypart(self, parttext, listStore=None, selObject=None):
        """ selects a treeview item if it starts with parttext """
        if listStore is None:
            listStore = self.listAliases
        if selObject is None:
            selObject = self.treeSel

        iindex = self.tree_get_index_search(parttext, listStore)
        if iindex > -1:
            self.tree_select(iindex, selObject)

    def tree_get_index(self, sname, listStore=None):
        """ retrieve an items index by name """
        if listStore is None:
            listStore = self.listAliases

        for i in range(0, len(listStore)):
            # get row i, column 0's text
            name = listStore[i][0]
            # probably has pango markup, we need to trim it,
            if sname == amutil.trim_markup(name):
                return i
        # not found
        return -1

    def tree_get_index_search(self, parttext, listStore=None):
        """ retrieves the index of the first item starting with parttext  """
        if listStore is None:
            listStore = self.listAliases

        for i in range(0, len(listStore)):
            name = amutil.trim_markup(listStore[i][0])
            if name.startswith(parttext):
                return i
        return -1

    def tree_selindex(self, selObject=None):
        """ Gets selected item's index from tree. (tree object must be passed)
        """
        if selObject is None:
            selObject = self.treeSel

        # Get Selected Item
        (modelNames, iterNames) = selObject.get_selected()

        # Item Selected?
        if iterNames is None:
            return -1
        else:
            # Get Index of Selected Item
            itmPath = modelNames.get_path(iterNames)
            # return Numeric index of selected item
            return itmPath[0]

    def tree_selvalue(self, selObject=None):
        """ Gets selected item's value from treeview """
        if selObject is None:
            selObject = self.treeSel

        # Get Selected Item
        (modelNames, iterNames) = selObject.get_selected()

        # Item Selected?
        if iterNames is None:
            return ""
        else:
            # Get Value of Selected Item
            itmValue = modelNames.get_value(iterNames, 0)
            # return String containing selected item's value
            return itmValue

    def tree_adjustbars(
            self, listStore=None, selObject=None, scrollObject=None):
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
        # Divide maximum value by total number of entries to get each entry
        # height.
        # Empty items, or not filling the list completely causes this to mess
        # up, so we need to account for lists that aren't filling at least one
        # page
        if adj.upper > adj.get_page_size():
            iDiv = adj.upper / itotal_len
        else:
            iDiv = 24  # Icon height

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

    def ensure_bashrc(self):
        """ Ensure the bashrc file can be found.
            Returns True if it can, False otherwise.
        """
        if (integrator.bashrc is None) and (not integrator.find_bashrc()):
            dlg.msgbox(
                ' '.join((
                    'Unable to find bashrc file!\n',
                    'You may need to create a file called',
                    '.bashrc or bash.bashrc in /home{instpath}\n',
                    'or /etc/.',
                )).format(instpath=integrator.home),
                dlg.error
            )
            return False
        return True

    def file_integrate_msg(self, success, successmsg, failuremsg):
        """ Display info about the alias file's integration status,
            and any info/error message provided.
        """
        aliasfile = settings.get('aliasfile')
        msg = '\n'.join((
            '<b><u>File:</u></b>',
            '<i>{aliasfile}</i>\n',
            '<b><u>Bashrc</u></b>',
            '<i>{bashrc}</i>'
        )).format(aliasfile=aliasfile, bashrc=integrator.bashrc)

        dlg.msgbox(
            '\n\n'.join((msg, successmsg if success else failuremsg)),
            None if success else dlg.error
        )
        return bool(success)

    def save_file(self, sfilename=None):  # noqa
        if sfilename is None:
            sfilename = settings.get("aliasfile")
        self.printlog("save_file: saving to: " + sfilename)

        # Setup shell script
        header = """#!/bin/bash
# Generated by {settings.name} {settings.version}
# -Christopher Welborn

# Note to user:
#     If you must edit this file manually please stick to this style:
#         Use tabs, not spaces.
#         No tabs before definitons.
#         Seperate lines for curly braces.
#         Use 1 tab depth for start of code block in functions.
#         Function description is first comment in code block.
#         Alias description is comment right side of alias definition.
#
#     ...if you use a different style it may or may not
#        break the program and I can't help you.
""".format(settings=settings)

        # Write Definitions, Cycle thru main data list
        # lst_lines.append("\n# Definitions:\n")

        # List for aliases (put'em at the top of the file)
        lst_aliases = []
        # List for functions (put'em after aliases)
        lst_functions = []
        # List for exports (put at bottom of file)
        lst_exports = []

        # Cycle thru items in treeAliases (alphabetical already)
        # This extra step makes the functions print in alphbetical order
        # ...aliases and exports don't need this method, a simple sorted(set())
        # works because they are single lines. multiline functions can't be
        # sorted like that.
        treeitm = self.listAliases.get_iter_first()
        while (treeitm is not None):
            # Get value for this item
            treeval = amutil.trim_markup(
                self.listAliases.get_value(treeitm, 0))
            # try to get next item
            treeitm = self.listAliases.iter_next(treeitm)

            # Search data list for this item, and save data to appropriate
            # list.
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
                    if scomment and (not scomment.startswith('#')):
                        scomment = ' '.join(('#', scomment))

                    # WRITE FUNCTION ITEM
                    if bfunction:
                        lst_functions.append('\nfunction {}()\n'.format(sname))
                        lst_functions.append('{\n')
                        # comment given?
                        if scomment:
                            lst_functions.append('\t{}\n'.format(scomment))
                        # Write command section
                        for scmdline in itm.cmd:
                            lst_functions.append('\t{}\n'.format(scmdline))
                        lst_functions.append('}\n')
                    else:
                        # WRITE ALIAS ITEM
                        # Fix quotes around command
                        if '"' in itm.cmd[0]:
                            scmd = "'" + itm.cmd[0] + "'"
                        else:
                            scmd = '"' + itm.cmd[0] + '"'
                        # Comment given?
                        if len(scomment) > 0:
                            scmd = ' '.join((scmd, scomment))
                        lst_aliases.append('alias {}={}\n'.format(sname, scmd))

        # Save Exports, cycle thru main data list
        # lst_lines.append("\n# Exports\n")
        for itm in self.lst_data:
            if (itm.exported.lower() == 'yes'):
                lst_exports.append('export {}\n'.format(itm.name))

        # Sort lines
        lst_aliases = sorted(set(lst_aliases))
        lst_exports = sorted(set(lst_exports))

        # Write file
        # save temp file to home dir
        aliasfiletmp = os.path.join(integrator.home, '.aliasmanager.tmp')

        btmp = False  # @UnusedVariable
        with open(aliasfiletmp, 'w') as fwrite:
            fwrite.write(header)
            fwrite.write("\n\n# Aliases:\n")
            fwrite.writelines(lst_aliases)
            fwrite.write("\n# Functions:")
            fwrite.writelines(lst_functions)
            fwrite.write("\n# Exports:\n")
            fwrite.writelines(lst_exports)
            # add new line because its a shell script, needs to end with \n
            fwrite.write('\n')
            # self.printlog("Temporary file written: " + aliasfiletmp)
            btmp = True

        if not btmp:
            self.stat_text('Unable to write temp file: {}'.format(
                           amutil.filename_safe(aliasfiletmp)))
            self.printlog('Unable to write temp file: {}'.format(
                          aliasfiletmp))
            # Temp file didn't write, there is no reason to continue.
            return False

        try:
            # Backup destination file if it doesn't exist
            backupfile = '{}~'.format(sfilename)
            if (os.path.isfile(sfilename) and
                    (not os.path.isfile(backupfile))):
                backupcmd = 'cp {} {}'.format(sfilename, backupfile)
                os.system(backupcmd)
                self.printlog('Backup created.')
            # Copy temp file to destination,,,
            copycmd = 'cp {} {}'.format(aliasfiletmp, sfilename)
            os.system(copycmd)
        except Exception as ex:
            self.stat_settext('Unable to copy to destination: {}'.format(
                              amutil.filename_safe(sfilename)))
            self.printlog('Unable to copy to destination!')
            self.printlog('Error: {}'.format(ex))
            return False
            dlg.msgbox(
                'Unable to copy to destination: {}'.format(
                    amutil.filename_safe(sfilename)),
                dlg.error)
        self.printlog('Temp file copied to destination: {}'.format(sfilename))

        # chmod +x if needed
        schmod_result = amutil.chmod_file(sfilename)
        self.printlog(schmod_result)

        # Success
        return True

    def load_aliases(self, from_file=True):
        """ Load aliases into treeview using correct markup """

        # item already selected? if so, save it to re-select it in a sec.
        prev_name = self.selname

        # Get file contents aliases/functions, fix Export info
        if from_file:
            self.lst_data = amutil.readfile()

        # failed to load list
        if not self.lst_data:
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
                itemname = '{}'
                # markup for functions
                if itm.isfunction():
                    itemname = '<i>{}</i>'
                    # Function is exported?
                    if not itm.isexported():
                        itemname = '<b>{}</b>'

                # append item with or without markup
                self.listAliases.append([itemname.format(itm.name)])

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
        """ Make sure item has a valid name. Not: None, Empty String, or Exists
        """
        # No text entered?
        badname = (sname is None or
                   self.item_exists(sname) or
                   (not sname.replace(' ', '')))
        # none, empty, or exists?
        return badname

    def get_item(self, sname):
        """ Retrieves item data in lst_data by name """
        if self.lst_data is None:
            return False

        for itm in self.lst_data:
            sdataname = itm.name
            if sdataname == sname:
                # Found item by name, return the data
                return itm

        # Failed to find it for some reason
        # Return empty command
        cmd = amutil.Command()
        return cmd

    def set_filename(self, sfilename):
        """ Sets current filename in lblFilename """
        # settings.set("aliasfile", sfilename)
        self.lblFilename.set_markup('<span foreground="#909090">' +
                                    '<u>Current File:</u>' +
                                    '</span>' +
                                    '<span foreground="#808080"> ' +
                                    sfilename +
                                    '</span>')

    def createlog(self):
        """ create the logfile atribute, an open file object, or None """

        try:
            logfilename = os.path.join(sys.path[0], 'aliasmgr.log')
            self.flogfile = open(logfilename, 'w')
            self.logfilename = logfilename
            return True
        except (IOError, OSError) as exio:
            self.logfilename = '__error__'
            self.flogfile = None
            exiomsg = "Unable to open log file!: {}".format(logfilename)
            print('aliasmgr.py: {}\n{}\n'.format(exiomsg, str(exio)))
            return False

    def openlog(self):
        """ open the log file if it hasn't been opened yet. """

        # Try to create the log file the first time.
        if not (hasattr(self, 'flogfile') and hasattr(self, 'logfilename')):
            self.createlog()

        # Already tried (and failed) to open a log?
        if self.logfilename == '__error__':
            return False
        # only return true if log is write()able.
        return (hasattr(self.flogfile, 'write'))

    def printlog(self, sstring):
        """ print string to terminal and log file """

        print("aliasmgr.py: " + sstring)

        if self.openlog():
            # write to existing (and opened) logfile object.
            self.flogfile.write(sstring + '\n')

    def select_editor(self):
        """ Select a text editor, return its filepath.
            Returns "" on failure.
        """
        dlg_editor = amutil.Dialogs()
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
