# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.display import epaper
from subprocess import PIPE, Popen, check_output
import subprocess
import shlex
import configparser
import pathlib
import os, sys
import time
import json
import urllib.request

def get_lichess_api():
    global config
    lichess_api = config["lichess"]["api_token"]
    return lichess_api

def get_lichess_range():
    global config
    lichess_range = config["lichess"]["range"]
    return lichess_range

def get_sound():
    global config
    centaur_sound = config["sound"]["sound"]
    return centaur_sound

def set_lichess_api(key):
    global config
    global config_file
    config.set('lichess', 'api_token', key)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        configfile.close()

def set_lichess_range(newrange):
    global config
    global config_file
    config.set('lichess', 'range', newrange)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        configfile.close()

def set_sound(onoff):
    global config
    global config_file
    config.set('sound', 'sound', onoff)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        configfile.close()

def dgtcm_path():
    return str(pathlib.Path(__file__).parent.resolve()) + "/.."

def shell_run(rcmd):
    cmd = shlex.split(rcmd)
    executable = cmd[0]
    executable_options=cmd[1:]
    proc  = Popen(([executable] + executable_options), stdout=PIPE, stderr=PIPE)
    response = proc.communicate()
    response_stdout, response_stderr = response[0], response[1]
    if response_stderr:
        print(response_stderr)
        return -1
    else:
        print(response_stdout)
        return response_stdout


config_file = dgtcm_path() + "/config/centaur.ini"
config = configparser.ConfigParser()
config.read(config_file)

# Import configs
try:
    lichess_api = config["lichess"]["api_token"]
except:
    lichess_api = ""
try:
    lichess_range = config["lichess"]["range"]
except:
    lichess_range = ""
try:
    centaur_sound = config["sound"]["sound"]
except:
    centaur_sound = "on"

class UpdateSystem:
    def __init__(self):
        self.conf = ConfigSystem()
        self.status = self.getStatus()
        

    def info(self):
        print('Update system status: ' + self.getStatus())
        print("Update source: ",self.conf.read_value('update', 'source'))
        print('Update channel: ' + self.getChannel())
        print('Policy: ' + self.getPolicy())

    def getInstalledVersion(self):
        version = os.popen("dpkg -l | grep dgtcentaurmods | tr -s ' ' | cut -d' ' -f3").read().strip()
        return version

    def checkForUpdate(self):
        channel = self.getChannel()
        policy = self.getPolicy()
        print('Settings channel: '+channel)
        print('Settings policy: '+policy)
        try:
            curr_channel = self.getInstalledVersion().rsplit('.',1)[1].rsplit('-',1)[1]
        except:
            curr_channel = 'stable'
        print('Current channel: '+curr_channel)
        
        local_version = self.getInstalledVersion()
        local_major = self.getInstalledVersion().split('.')[0]
        local_minor = self.getInstalledVersion().split('.')[1]
        try:
            local_minor = self.getInstalledVersion().split('.')[1]
        except:
            local_minor = '0'

        if curr_channel == 'stable':
            try:
                local_revision = self.getInstalledVersion().split('.')[2]
            except:
                local_revision = '0'
        else:
            local_revision = self.getInstalledVersion().rsplit('.',1)[1].rsplit('-',1)[0]
        #Dpkg is skipping 0 if last in version number. e.g: 1.1.0 will be 1.1
        #We need to rebuild the version
        local_version = '{}.{}.{}'.format(local_major,local_minor,local_revision)
        print('Local ver: '+local_version+'\nLocal major: '+local_major+'\nLocal minor: '+local_minor+'\nLocal revision: '+local_revision)
        
        self.update = self.ver[channel]['ota']
        #No OTA, no update
        if self.update == 'None':
            return False
        update_major = self.update.split('.')[0]
        update_minor = self.update.rsplit('.')[1]
        if channel == 'stable':
            update_revision = self.update.rsplit('.',1)[1] 
        else:
            update_revision = self.update.rsplit('.',1)[1].rsplit('-',1)[0]
        print('Update ver: '+self.update+'\nUpdate major: '+update_major+'\nUpdate minor: '+update_minor+'\nUpdate revision: '+update_revision)
        
        #If local version is the same as update candidate, break
        if local_version == self.update:
            print('Versions are the same. No updates')
            return False
        
        #If user decides to switch channel, he will trigger a full reinstall
        if curr_channel != channel:
            print('Channel changed. Installing varsion {} at shutdown'.format(self.update))
            return True
        
        #Evaluate policies
        #On 'revision' install only if revision is newer
        if policy == 'revision':
            if local_major == update_major and local_minor == update_minor:
                if local_revision < update_revision:
                    return True
            else:
                print('Policy don\'t allow major updates.')
                return False

        #On 'always' just make sure this is an update to current installed version
        if policy == 'always':
            if local_major < update_major:
                return True 
            elif local_minor < update_minor:
                return True
            elif local_revision < update_revision:
                return True
            else:
                return False


    def downloadUpdate(self,update):
        download_url = 'https://github.com/{}/releases/download/v{}/dgtcentaurmods_{}_armhf.deb'.format(self.update_source,update,update)
        print(download_url)
        try:
            urllib.request.urlretrieve(download_url,'/tmp/dgtcentaurmods_armhf.deb')
        except:
            return False
        return


    def enable(self):
        self.conf.update_value('update','status','enabled')
        print('Autoupdate has been enabled')
        return
        

    def disable(self):
        self.conf.update_value('update','status','disabled')
        print('Autoupdate has beed disabled.')
        return


    def setPolicy(self,policy):
        self.conf.update_value('update','policy',policy)
        print('Policy set to: ' + policy)
        return


    def setChannel(self,channel):
        self.conf.update_value('update','channel',channel)
        print('Update channel  has beed set to ',channel)
        return


    def getChannel(self):
        return self.conf.read_value('update', 'channel')


    def getStatus(self):
        return self.conf.read_value('update', 'status')


    def getPolicy(self):
        return self.conf.read_value('update', 'policy')


    def updateInstall(self):
        # Check for available update
        package = '/tmp/dgtcentaurmods_armhf.deb'
        print('Put the board in update mode')
        import shutil

        epaper.writeText(3, '    System will')
        epaper.writeText(4, '       update')
        shutil.copy('update/update.py','/tmp')
        shutil.copytree('update/lib','/tmp/lib')
        print('Keep the info on the screen')
        time.sleep(5)
        subprocess.Popen('cd /tmp; python /tmp/update.py', shell=True)
        sys.exit()


    def main(self):
        #Download update ingormation file
        self.update_source = self.conf.read_value('update', 'source')
        print('Downloading update information...')
        url = 'https://raw.githubusercontent.com/{}/master/DGTCentaurMods/DEBIAN/versions'.format(self.update_source)
        try:
            with urllib.request.urlopen(url) as versions:
                self.ver = json.loads(versions.read().decode())
        except Exception as e:
            print('!! Cannot download update info: ', e)
            pass

        # This function will run as a thread once, sometime after boot if updting is enabled.
        if not self.getStatus() == "disabled" and self.checkForUpdate():
            self.downloadUpdate(self.update)
            return
        print('Update not needed or disabled')
        return


class ConfigSystem:
    def __init__(self):
        self.configfile = dgtcm_path() +'/config/centaur.ini'
        self.defconfigfile = dgtcm_path() + '/defaults/config/centaur.ini'
        
        #Get current config
        self.config = configparser.ConfigParser()
        self.config.read(self.configfile)
        
        #Get the defaults
        self.defconfig = configparser.ConfigParser()
        self.defconfig.read(self.defconfigfile)


    def add_defaults(self, section, key):
        '''
        Check if key is in configfile orherwise it will get it from default config
        '''
        if not self.config.has_section(section):
            self.config.add_section(section)
            self.write_config()
        # Add the new key from default
        def_value = self.defconfig[section][key]
        self.config.set(section, key, def_value)
        self.write_config()
        self.config.read(self.configfile)


    def write_config(self):
        with open(self.configfile, 'w') as f:
            self.config.write(f)


    def read_value(self, section, key):
        self.config.read(self.configfile)
        try:
            value = self.config[section][key]
        except:
            self.add_defaults(section, key)
            self.write_config()
            self.config.read(self.configfile)
            value = self.config[section][key]
        return value


    def update_value(self, section, key, value):
        self.config.read(self.configfile)
        try:
            self.config.set(section, key, value)
            self.write_config()
        except:
            self.add_defaults(section,key)
            self.congif.set(section, key, value)
            self.write_config()
            self.config.read(self.config_file)
 

    def delete_key(self, section, key):
        self.config.read(self.configfile)
        try:
            self.config.remove_option(section, key)
            self.write_config()
            self.config.read(configfile)
        except:
            pass
