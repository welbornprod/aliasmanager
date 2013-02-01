'''
  Alias Manager - Settings
  ...saves/retrieves saved alias manager settings
  
Created on Jan 16, 2013

@author: Christopher Welborn
'''
from __future__ import print_function
# file related imports
import sys, os.path

class am_settings():
    ''' helper for saving/retrieving alias manager settings
      file     = configuration file (usually ../aliasmanager.conf)
      settings = dict object where settings are stored.
                 settings are retrieved like this:
                   myfile = settings.settings["aliasfile"]
                   or:
                   myfile = settings.get("aliasfile")
                 settings are set like this:
                   settings.settings["aliasfile"] = "myfile.sh"
                   or:
                   settings.set("aliasfile", "myfile")
      '''
    def __init__(self):
        ''' creates new settings object to work with '''
        # application info
        self.name = 'Alias Manager'
        self.version = '1.7'
        # default config file
        self.configfile = os.path.join(sys.path[0], "aliasmgr.conf")
        # empty setting dictionary
        self.settings = {}
        # load setting from config file
        self.read_file()
    
    def read_file(self, sfile = None):
        """ reads config file into settings object """
        if sfile == None: 
            sfile = self.configfile
        else:
            self.configfile = sfile
    
        if os.path.isfile(sfile):
            with open(sfile, 'r') as fread:
                slines = fread.readlines()
        
                # cycle thru lines
                for sline in slines:
                    # actual setting?
                    if "=" in sline:
                        sopt = sline[:sline.index("=")]
                        sval = sline[sline.index("=") + 1:].replace('\n', '')
            
                        self.set(sopt, sval)
                # success
                return True
        # failure
        return False
  
    def set(self, soption, svalue):
        """ sets a setting in config file """
    
        if ("=" in soption) or ("=" in svalue):
            print("alias_settings: illegal char '=' in option/value!")
            return False
    
        if len(soption.replace(' ', '')) == 0:
            print("alias_settings: empty options are not allowed!")
            return False
        #if len(svalue.replace(' ', '')) == 0:
        #  print("alias_Settings: empty values are not allowed!")
        #  return False
    
        try:
            self.settings[soption] = svalue
            #print("settings.set(): " + soption + "=" + self.settings[soption])
            return True
        except:
            return False
  
    def setsave(self, soption, svalue):
        """ sets a setting in config file, and saves the file """
        if self.set(soption, svalue):
            self.save()
        else:
            print("aliasmgr_settings: unable to set option: " + \
                  soption + "=" + svalue)
            return False
      
    def get(self, soption, sdefault = ""):
        """ retrieves a setting from config file """
        if self.settings.has_key(soption):
            return self.settings[soption]
        else:
            #print("alias_settings: key not found: " + soption)
            return sdefault
    
  
    def save(self, sfile = None):
        if sfile == None: 
            sfile = self.configfile
    
        with open(sfile, 'w') as fwrite:
            for skey in self.settings.iterkeys():
                fwrite.write(skey + '=' + self.settings[skey] + '\n')
            # success  
            return True
        # failed to open file
        print("alias_settings: failed to open file for write!: " + sfile)
        return False

    def configfile_exists(self, bcreateblank = True):
        if os.path.isfile(self.configfile):
            return True
        else:
            if bcreateblank:
                fconfig = open(self.configfile, 'w')
                fconfig.write("# configuration for Alias Manager\n")
                fconfig.close()
                del fconfig
                return True
            else:
                return False