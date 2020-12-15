from configparser import ConfigParser
import os

class ConfigReader:
    def __init__(self):
        self.param = ConfigParser()

        if os.path.exists('config.ini'):
            self.config_path = 'config.ini'    
        elif os.path.exists('./raspi/config.ini'):
            self.config_path = './raspi/config.ini'
        else:
            sys.exit('ERROR: No config file found!')
        self.read_param()

    def read_param(self):
        self.param.read(self.config_path)

    def write_param(self):
        with open(self.config_path, 'w') as f:
            self.param.write(f)
        print('Parameters saved')