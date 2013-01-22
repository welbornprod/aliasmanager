'''
  Alias Manager - Integrator
  ...helps to integrate bash alias file into bashrc
  
Created on Jan 16, 2013

@author: Christopher Welborn
'''
import sys
import os.path
import aliasmgr_settings

def printx(sstring):
    print("aliasmgr_integrator: " + sstring)
    
class am_integrator():
    """ validates and integrates alias file into bash.bashrc
          saliasfile = alias file to integrate into bashrc
    """
    def __init__(self):
        self.settings = aliasmgr_settings.am_settings()
        self.user = None
        self.home = None
        self.bashrc = None
        self.helperfiles = os.path.join(sys.path[0], "integrated.lst")
        self.helperscript = os.path.join(sys.path[0], "aliasmgr_scripts.sh")
        
        self.headerlist = "# Alias Manager Integration Files\n" + \
                          "# A script is generated using these filenames,\n" + \
                          "# and that script is called from bashrc.\n" + \
                          "# Editing this file will do nothing, you must\n" + \
                          "# edit it using Alias Manager.\n"
        self.headerscript = "# Alias Manager Integration Script\n"+ \
                            "# This script is called from bashrc to allow\n" + \
                            "# one or many alias/function scripts to be\n" + \
                            "# called on BASH startup.\n" + \
                            "# Alias Manager will over-write any changes\n" + \
                            "# you make to this file.\n"
                            
        # load user info  
        self.get_userinfo()
    
    def get_userinfo(self):
        """ retrieve user name and home dir """
    
        if os.environ.has_key("HOME"):
            self.home = os.environ["HOME"]
            self.user = os.path.split(self.home)[-1]
        else:
            if os.environ.has_key("USER"):
                self.user = os.environ["USER"]
                self.home = "/home/" + self.user
            else:
                # failure
                self.user = None
                self.home = None
                return False
        # success
        return True
  
    def find_bashrc(self):
        """ find bashrc file automagically """
    
        # try user home first?
        btryuser = True
    
        # no user home dir?
        if self.home == None:
            # try setting home automagically
            self.get_userinfo()
      
        # still nothing?
        if self.home == None:
            btryuser = False
        
        # acceptable bashrc filenames
        lst_bashrc = ["bash.bashrc", ".bashrc"]
        for sbashrc in lst_bashrc:
            if btryuser:
                if os.path.isfile(os.path.join(self.home, sbashrc)):
                    self.bashrc = os.path.join(self.home, sbashrc)
                    return self.bashrc
            # try /etc
            if os.path.isfile(os.path.join("/etc/", "bash.bashrc")):
                self.bashrc = os.path.join("/etc/", "bash.bashrc")
                return self.bashrc
        
        # Failure
        return False
        
    def refresh_bashrc(self):
        if not self.find_bashrc():
            printx("refresh_bashrc: Cannot find bashrc file!")
            return False
        return True
    
    def is_integrated(self, sfilename = None):
        """ Checks to see if a file is integrated with bashrc
            Used to make sure integrated.lst is integrated
            Can be used to check other filenames also..
        """
        # good alias filename?
        if sfilename == None:
            sfilename = self.helperscript
        if self.bashrc == None:
            if not self.refresh_bashrc():
                printx("is_integrated: unable to find bashrc file!")
                return False
            
        #printx("testing " + self.bashrc + " for " + sfilename + "...")
        if sfilename in self.get_integrated_files():
            return True
        else:
            # do a bit deeper search
            
            return False
    
    def integrate_self(self):
        """ Integrate the helper script into bashrc """
        if self.is_integrated(self.helperscript):
            return True
        else:
            if not self.find_bashrc():
                printx("integrate_self: Unable to find bashrc file!")
                return False
            
        # do self integration
        if (os.stat(self.bashrc).st_uid == 0 and
            self.user != "root"):
            sfile = os.path.join(sys.path[0], "aliasmgr_bashrc.tmp")
            broot = True
            # copy root file to current dir to work with
            os.system("cp " + self.bashrc + " " + sfile)
        else:
            sfile = self.bashrc
            broot = False
            
        with open(sfile, 'a') as fwrite:
            fwrite.write("\nif [ -f " + self.helperscript + " ]; then source " + \
                         self.helperscript + "; fi\n")
            fwrite.close()
            
            if broot:
                if os.path.isfile("/usr/bin/kdesudo"):
                    selevcmd = "kdesudo"
                elif os.path.isfile("/usr/bin/gksudo"):
                    selevcmd = "gksudo"
                else:
                    printx("Unable to find suitable elevation command!")
                    printx("Integration will have to be done manually.")
                    return False
                os.system(selevcmd + " cp " + sfile + " " + self.bashrc)
                printx("Temp file copied to bashrc: " + self.bashrc)
            return True
        
        return False
    
    def deintegrate_self(self):
        """ De-integrates the helper script with bashrc """
        if not self.is_integrated():
            return True
        else:
            if not self.find_bashrc():
                printx("deintegrate_self: Unable to find bashrc file!")
                return False
        
        # do self deintegration
        if (os.stat(self.bashrc).st_uid == 0 and
            self.user != "root"):
            sfile = os.path.join(sys.path[0], "aliasmgr_bashrc.tmp")
            broot = True
            # copy root file to current dir to work with
            os.system("cp " + self.bashrc + " " + sfile)
        else:
            sfile = self.bashrc
            broot = False
        
        # Alias Manager Integration Line...
        stagline = "if [ -f " + self.helperscript + " ]; then source " + \
                    self.helperscript + "; fi"
        # read lines from bashrc
        with open(sfile, 'r') as fread:
            slines = fread.readlines()
            fread.close()
            for sline in slines:
                if stagline in sline:
                    slines.remove(sline)
                    break
        # write correct line into file
        with open(sfile, 'w') as fwrite:
            fwrite.writelines(slines)
            fwrite.close()
            if broot:
                if os.path.isfile("/usr/bin/kdesudo"):
                    selevcmd = "kdesudo"
                elif os.path.isfile("/usr/bin/gksudo"):
                    selevcmd = "gksudo"
                else:
                    printx("Unable to find suitable elevation command!")
                    printx("DeIntegration will have to be done manually.")
                    return False
                os.system(selevcmd + " cp " + sfile + " " + self.bashrc)
                printx("Temp file copied to bashrc: " + self.bashrc)
            return True
        return False
                            
    def get_integrated_files(self):
        """ lists all files integrated into bashrc """
        if self.bashrc == None:
            if not self.refresh_bashrc():
                return []
         
        lst_integrated = []
        with open(self.bashrc, 'r') as fread:
            slines = fread.readlines()
            for sline in slines:
                sline = sline.replace('\t', '').replace('\n', '')
                strim = sline.replace(' ', '')
                if (strim.startswith("./")):
                    # found script integration, get filename
                    lst_integrated.append(strim[strim.index(".") + 1:])
                elif ((strim.startswith("if[")) and 
                       (";then./" in strim or ";thensource/" in strim) and 
                       (strim.endswith(";fi"))):
                    # possible single-line if statement integration
                    if "./" in strim:
                        smarker = "./"
                    elif "source/" in strim:
                        smarker = "source/"
                    srough = strim[strim.index(smarker) + (len(smarker) -1):]
                    lst_integrated.append(srough[:srough.index(';')])    
            # success
            return lst_integrated
            
        # failed to open file
        printx("get_integrated_files: failed to open bashrc: " + self.bashrc)
        return []
           
    def helper_createfile(self):
        """ Creates the blank helper file 
            (the list of shell scripts bashrc will launch)
            ...also returns True if the file exists already. 
        """
        if os.path.isfile(self.helperfiles):
            # No need to create
            return True
        else:
            with open(self.helperfiles, 'w') as fwrite:
                fwrite.write(self.headerlist)
                fwrite.close()
                return True
            
        # failure
        return False
    
    def helper_getfiles(self):
        """ Reads the integration file, 
            and returns a list of integrated files in it.
            ** skips commented lines (#filename.sh) 
        """
        try:
            lst_files = []
            if self.helper_createfile():
                with open(self.helperfiles, 'r') as fread:
                    slines = fread.readlines()
                    for sline in slines:
                        sline = sline.replace('\n', '').replace('\t', '')
                        # skip comments
                        if (not sline.startswith("#")) and (sline != ""):
                            lst_files.append(sline)
                    # file was not closing in time
                    fread.close()
            return lst_files
        except Exception as ex:
            printx("helper_getfiles: Error:")
            printx(str(ex))
            return []
        
            
    def helper_addfile(self, sfilename):
        """ Adds a shell script to the 'integrated list'
            this file will be shelled by bashrc if its in the list
        """
        if sfilename == "":
            return False
      
        if self.helper_createfile():
            with open(self.helperfiles, 'a') as fwrite:
                fwrite.write('\n' + sfilename + '\n')
                fwrite.flush()
                fwrite.close()
                return self.helper_generate_script()
        
        
        # Failure
        return False
    
    def helper_removefile(self, sfilename):
        """ Removes a file from the integrated list """
        if sfilename == "":
            return False
        
        lst_files = self.helper_getfiles()
        if sfilename in lst_files:
            lst_files.remove(sfilename)
            return self.helper_writelist(lst_files)
        # failure/file was not in the list
        return False
                    
    def helper_checkfile(self, sfilename):
        """ Checks to see if a file is integrated (in integrated.lst) """
        if sfilename == "":
            return False
        return (sfilename in self.helper_getfiles())
    
    def helper_writelist(self, lst_files):
        """ Writes a list of filenames to the integrated list """
        if self.helper_createfile():
            
            with open(self.helperfiles, 'w') as fwrite:
                fwrite.write(self.headerlist)
                fwrite.writelines(lst_files)
                fwrite.flush()
                fwrite.close()
                # update the scriptfile
                return self.helper_generate_script()
                
        # failure    
        return False
    
    def helper_generate_script(self):
        """ generates the script file that bashrc shells """
        printx("generate_script: " + str(self.helper_getfiles())) 
        try:
            with open(self.helperscript, 'w') as fwrite:
                fwrite.write(self.headerscript)
                lst_files = self.helper_getfiles()
                if len(lst_files) > 0:
                    fwrite.write("echo 'Alias Manager loading scripts...'\n")
                    for sfile in self.helper_getfiles():
                        fwrite.write("if [ -f " + sfile + " ]; then\n")
                        fwrite.write("    source " + sfile + '\n')
                        fwrite.write("    echo '    Loaded " + sfile + "'\n")
                        fwrite.write("else\n")
                        fwrite.write("    echo 'Alias Manager file not found: " + \
                                     sfile + "'\n")
                        fwrite.write("fi\n")
                        fwrite.write("echo ' '\n")    
                #fwrite.write("echo 'Alias Manager script files loaded.'\n")
                #fwrite.write("echo ' '\n")
                fwrite.close()
            # chmod to script
            os.system("chmod a+x " + self.helperscript)
            return True
        except Exception as ex:
            printx("helper_generate_script: Error:")
            printx(str(ex))
            pass
        # Failure
        return False
        
