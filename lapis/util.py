# miscallenous utility functions

import datetime
import lapis.logger as logger

timestamp = datetime.datetime.now().isoformat()

import pkgutil
import sys


def loadmod(dirname):
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        full_package_name = '%s.%s' % (dirname, package_name)
        if full_package_name not in sys.modules:
            module = importer.find_module(package_name
                        ).load_module(full_package_name)
            logger.info(module)
