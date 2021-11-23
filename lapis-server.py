#!/usr/bin/python3
import lapis.db
import lapis.config as config
import lapis.logger as logger
import lapis.api.main as api
import datetime
#import lapis.plugins.standalone as standalone
import importlib
import os

# run the standalone thread

if config.get('standalone') == True:
    lapis.plugins.standalone.StandaloneSubprocess().start()


#touch database so it generates the tables
lapis.db.initialize()


#standalone.StandaloneSubprocess().start()

print("Lapis Backend server Pre-alpha")

api.run()