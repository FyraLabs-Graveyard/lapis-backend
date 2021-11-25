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

import configparser as cp
import datetime
import os
import threading
import time

import mockbuild.util as mock

import lapis.apiHandler as api
import lapis.auth as auth
import lapis.config as config
import lapis.db as db
import lapis.internal
import lapis.logger as logger
import lapis.util as util

# load the relevant variables from the config file
home = config.get('datadir')
logdir = config.get('logfile')

# variables for the various sub-directories next becuase we're lazy
# also convert them to absolute paths
builddir = os.path.join(home, 'builds')
repodir = os.path.join(home, 'results')
workdir = os.path.join(home, 'work')
mockdir = os.path.join(home, 'mock')
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
        if not os.path.exists(mockdir):
            os.makedirs(mockdir)
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
            logger.error("Failed to initialize buildroot %s: %s" %
                         buildroot, e)
            return False
    # actually, make everything run locally for now, lapisd can wait
    mock.run('mock -r %s --init --configdir %s' % buildroot, mockdir)
    # bit first, create the repo directory
    try:
        os.makedirs(repodir + '/' + buildroot)
    except Exception as e:
        logger.error("Failed to create repo directory: %s" % e)
        return False
    finally:
        mock.run('createrepo -o %s/%s %s/%s' % repodir, buildroot, repodir, buildroot)


def initrepo(buildroot):
    """
    Initialize the repo for the buildroot.
    """


def mockRebuild(srpm, buildroot):
    """
    Rebuild the srpm using mock.
    """
    # the srpm is the path to the srpm file
    # the buildroot is the name of the buildroot, which will be the mockdir + the buildroot name
    # the buildroot should be created by the caller before this is called
    # the buildroot should be created with initbuildroot()
    if not os.path.exists(srpm) and not os.path.exists(mockdir + '/' + buildroot + '.cfg'):
        logger.error("SRPM or buildroot does not exist")
        return False, "SRPM or buildroot does not exist"
    # then start the rebuilding process
    # but first, we get to get the RPM metadata

    # get the metadata from the srpm
    # this is a bit of a hack, but it works for now
    # it uses the RPM module to get the metadata and also starts a transaction
    rpm = util.analyze_rpm(srpm)
    build = util.newBuild(
        source=srpm,
        type='mock_rebuild',
        name=rpm['name'],
        description=rpm['description'],
        buildroot=buildroot,
    )
    # create a new task for the build
    task = util.newTask(build_id=build,type= 'mock_rebuild', source=srpm, buildroot=buildroot, status='running')
    mock.run('mock -r %s --configdir %s --rebuild %s --chain --localrepo %s' %
             (buildroot, mockdir, srpm, home)) # set to home because mock likes to output to results/
    # then update the task to be finished
    util.updateTask(task, status='finished')
    return True, "Successfully rebuilt %s" % srpm

# data processing sub-thread, now only manages dead workers


class datathread(threading.Thread):
    """
    The Lapis data processing thread.
    """

    def __init__(self):
        """
        Initialize the data processing thread.
        """
        threading.Thread.__init__(self)
        self.running = True
        self.thread = None
        self.name = "Data Processing Thread"

    def run(self):
        """
        Start the data processing thread.
        """
        logger.info("Lapis data processing thread started.")
        while self.running:
            # check for workers
            workers = db.workers.list()
            #logger.debug("Workers: %s" % workers)
            # worker last seen time is a datetime object.
            # if worker's last seen is more than 10 minutes ago, set it to offline
            for worker in workers:
                # logger.debug(worker['last_seen'])
                if worker['last_seen'] < datetime.datetime.now() - datetime.timedelta(minutes=10):
                    db.workers.update(worker['id'], {
                        'name': worker['name'],
                        'type': worker['type'],
                        'status': 'offline',
                        'token': worker['token'],
                    })
            time.sleep(1)


# start the data processing thread
datathread().start()

init()
