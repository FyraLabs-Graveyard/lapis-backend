# logging component for lapis
import logging
import os
from re import match
import sys
import lapis.config
import logging.handlers
# get log from stdout
log = logging.getLogger(__name__)

#if argument --verbose is passed, print to stdout too

if '--verbose' in sys.argv or '-V' or os.environ.get('VERBOSE') == 'TRUE' in sys.argv:
    log.setLevel(logging.DEBUG)
    # in color
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # in color
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    log.addHandler(console)




# setup log file

try:
    log_file = os.path.join(os.path.dirname(sys.argv[0]), lapis.config.get('logfile'))
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setLevel(lapis.config.get('logfile_level').upper())
    log_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_file_handler)
except Exception as e:
    logging.error(e)
    log_file_handler = None

#logger functions
def debug(msg):
    log.debug(msg)

def info(msg):
    log.info(msg)

def error(msg):
    log.error(msg)

def critical(msg):
    log.critical(msg)

def warning(msg):
    log.warning(msg)
