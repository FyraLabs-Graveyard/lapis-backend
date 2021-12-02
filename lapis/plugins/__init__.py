# import and run all the modules in the lapis/managers directory

import os
import sys
import importlib
import lapis.logger

for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    importlib.import_module('lapis.plugins.' + module[:-3])
    lapis.logger.info('Loaded plugin: ' + module[:-3])