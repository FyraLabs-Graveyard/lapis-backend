#default config

import configparser
import os
import sys

default = {
    'port': 8080,
    'debug': True,
    'host': 'localhost',
    'tempdir': '/tmp',
    'datadir': '/srv/lapis',
    'database': 'lapis',
    'database_user': 'lapis',
    'database_password': 'lapis',
    'database_host': 'localhost',
    'database_port': 5432,
    'database_type': 'postgresql',
    'database_schema': 'public',
    'database_ssl': False,
    'database_ssl_key': '',
    'database_ssl_cert': '',
    'database_ssl_ca': '',
    'baseurl': '/api',
    'secret': '',
    'logfile': '/var/log/lapis/lapis.log',
    'logfile_level': 'DEBUG',
    'logfile_max_size': 10485760,
    'logfile_max_backups': 5,
    'logfile_max_age': 7,
    'datadir': '/srv/lapis',
}

# if --config or -c is not specified, use default config
if len(sys.argv) > 1 and (sys.argv[1] == '-c' or sys.argv[1] == '--config'):
    config_file = sys.argv[2]
else:
    config_file = '/etc/lapis/backend.conf'

# load config from file with configparser
config = configparser.ConfigParser()
# if config file exists, load it
if os.path.isfile(config_file):
    config.read(config_file)
# if config file does not exist, create it and write default config to it
else:
    try:
        # make dir if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        config.add_section('general')
        for key, value in default.items():
            config.set('general', key, str(value))
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    except OSError:
        #throw error if config file cannot be created
        raise OSError('Cannot create config file')

#export config to global namespace
def get(key):
    return config.get('general', key)

def set(key, value):
    config.set('general', key, value)
    # then write config to file
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def list():
    #return list of all config options as dict
    return {key: get(key) for key in config['general']}
