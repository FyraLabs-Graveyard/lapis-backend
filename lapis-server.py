#!/usr/bin/python3
import lapis.db
import lapis.config as config
import lapis.logger as logger
import lapis.apiHandler as api
import datetime
#import lapis.plugins.standalone as standalone
import importlib
import os

""" from lapis.util import loadmod
# run the standalone thread

if config.get('standalone') == True:
    lapis.plugins.standalone.StandaloneSubprocess().start()


#try and touch database so it generates the tables
try:
    lapis.db.initialize()
except Exception as e:
    logger.warning(e)

try:
    # load all modules in the plugins directory
    loadmod('lapis/plugins')
    #load the managers
    loadmod('lapis/managers')
except Exception as e:
    logger.warning(e)
#standalone.StandaloneSubprocess().start()
 """
print("Lapis Backend server 0.1")

# start the api server
api.run()