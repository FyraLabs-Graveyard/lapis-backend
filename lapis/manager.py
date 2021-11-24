# This is the code that actually does all the data processing for builds.

"""
[Lapis Manager]
The Lapis manager is responsible for managing the build process, directories, file paths, etc for all builds. It works similarly to the Koji Hub.


This is basically where all the magic happens.

The manager should:
- Create a directory for each build
- Process the build request into a JSON object containing the build information, and instructions for the build into an array of commands to be executed within the payload section of the task.
- Manage the repository for the builds
- Manage the build directory and the payload directory.
"""

import os
import lapis.logger as logger
import lapis.util as util
import lapis.config as config
import lapis.db as db
import lapis.auth as auth
import lapis.apiHandler as api

# load the relevant variables from the config file
home = config.get('datadir')
logdir = config.get('logfile')

# variables for the various sub-directories next becuase we're lazy
# also convert them to absolute paths
builddir = os.path.join(home, 'builds')
repodir = os.path.join(home, 'repos')
workdir = os.path.join(home, 'work')

# Let's use the main server for repo management, for now.
# RPM repos are hardcoded at the moment, just so we can replace Koji with this for once.

# initialize the directories for first time use
def init():
    """
    Initialize the directories for the first time
    """
    try:
        if not os.path.exists(home):
            os.makedirs(home)
        if not os.path.exists(builddir):
            os.makedirs(builddir)
        if not os.path.exists(repodir):
            os.makedirs(repodir)
        if not os.path.exists(workdir):
            os.makedirs(workdir)
    except Exception as e:
        logger.error("Failed to initialize directories: %s" % e)
        return False
    return True

def initbuildroot(buildroot):
    """
    Initialize the buildroot.
    """
    if not os.path.exists(workdir + '/' + buildroot):
        try:
            os.makedirs(workdir + '/' + buildroot)
        except Exception as e:
            logger.error("Failed to initialize buildroot %s: %s" % buildroot, e)
            return False