'''
  Alias Manager - Settings
  ...saves/retrieves saved alias manager settings

Created on Jan 16, 2013

@author: Christopher Welborn
'''
from __future__ import print_function
# file related imports
import sys
import os.path
__VERSION__ = '1.7.9'


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
        self.version = __VERSION__
        self.versionstr = '{} v. {}'.format(self.name, self.version)
        # default config file
        self.configfile = os.path.join(sys.path[0], 'aliasmgr.conf')
        # empty setting dictionary
        self.settings = {}
        # load setting from config file
        self.read_file()

    def read_file(self, sfile=None):
        """ reads config file into settings object """
        if sfile is None:
            sfile = self.configfile
        else:
            self.configfile = sfile

        if os.path.isfile(sfile):
            with open(sfile, 'r') as fread:
                slines = fread.readlines()

                # cycle thru lines
                for sline in slines:
                    # actual setting?
                    if '=' in sline:
                        splitindex = sline.index('=')
                        sopt = sline[:splitindex]
                        sval = sline[splitindex + 1:].replace('\n', '')

                        self.set(sopt, sval)
                # success
                return True
        # failure
        return False

    def set(self, soption, svalue):
        """ sets a setting in config file """

        if ('=' in soption) or ('=' in svalue):
            print('alias_settings: illegal char \'=\' in option/value!')
            return False

        if len(soption.replace(' ', '')) == 0:
            print('alias_settings: empty options are not allowed!')
            return False

        try:
            self.settings[soption] = svalue
            return True
        except Exception:
            # Bad type?
            return False

    def setsave(self, soption, svalue):
        """ sets a setting in config file, and saves the file """
        if self.set(soption, svalue):
            self.save()
        else:
            print('aliasmgr_settings: unable to set option: {} = {}'.format(
                soption, svalue))
            return False

    def get(self, soption, sdefault=""):
        """ retrieves a setting from config file """
        if soption in self.settings:
            return self.settings[soption]
        else:
            return sdefault

    def save(self, sfile=None):
        if sfile is None:
            sfile = self.configfile

        with open(sfile, 'w') as f:
            for skey in self.settings.iterkeys():
                f.write('{}={}\n'.format(skey, self.settings[skey]))
            # flush right away, so other modules can read the changes.
            f.flush()
            f.close()
            # success
            return True
        # failed to open file
        print('aliasmgr_settings: failed to open file for write!: '.format(
            sfile))
        return False

    def configfile_exists(self, bcreateblank=True):
        if os.path.isfile(self.configfile):
            return True
        else:
            if bcreateblank:
                fconfig = open(self.configfile, 'w')
                fconfig.write('# configuration for Alias Manager\n')
                fconfig.close()
                del fconfig
                return True
            else:
                return False
