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
import threading
import lapis.logger as logger
import lapis.util as util
import lapis.config as config
import lapis.db as db
import lapis.auth as auth
import lapis.apiHandler as api
import mockbuild.util as mock
import time
import datetime

import lapis.internal

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
    # actually, make everything run locally for now, lapisd can wait
    mock.run('mock -r %s --init' % buildroot)

#manager thread
class buildthread(threading.Thread):
    """
    The Lapis Manager thread.
    """
    def __init__(self):
        """
        Initialize the manager thread.
        """
        threading.Thread.__init__(self)
        self.running = True
        self.thread = None
        self.name = "Lapis Manager"

    def run(self):
        """
        Start the manager thread.
        """
        logger.info("Lapis manager thread started.")
        while self.running:
            # check if there are any builds to be processed
            #logger.debug(db.build.list())
            for build in db.build.list():
                # split the build into task and payload
                logger.debug("Found build " + str(build['id']))
                # check if the build is already running
                if build['status'] == 'running':
                    pass
                # check if the build is already finished
                elif build['status'] == 'finished':
                    pass
                # check if the build was canceled or failed
                elif build['status'] == 'canceled' or build['status'] == 'failed':
                    pass
                # check if theres already a task for the build
                # list all tasks and find if there already is one with the same build id as the current one
                elif db.tasks.find_by_build(build['id']):
                    pass
                # create a new task for the build
                # elif the build source doesn't end with src.rpm (default for mock)
                elif not build['source'].endswith('src.rpm'):
                    # get a list of task id's
                    if not db.tasks.list(None):
                        task_id = 1
                    else:
                        task_id = util.last_entry(db.tasks.list())
                    
                    db.tasks.insert({
                        "id": task_id,
                        "type": "mock_srpm", # default to mock
                        "status": "pending", # wait for lapisd to yoink it
                        "build_id": build['id'],
                        "payload": {
                            "command": "mock build --spec %s" % build['source']
                        }
                    })
                    # then track the build until it's finished and set to "waiting"
                    # if a mock_srpm task is found done, rebuild it as an RPM
                continue
            time.sleep(1)
            pass
        logger.info("Lapis manager thread stopped.")
#data processing sub-thread
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
                #logger.debug(worker['last_seen'])
                if worker['last_seen'] < datetime.datetime.now() - datetime.timedelta(minutes=10):
                    db.workers.update(worker['id'], {
                        'name': worker['name'],
                        'type': worker['type'],
                        'status': 'offline',
                        'token': worker['token'],
                        })
            time.sleep(1)

class taskmanager(threading.Thread):
    """
    The Lapis task manager thread.
    """
    def __init__(self):
        """
        Initialize the task manager thread.
        """
        threading.Thread.__init__(self)
        self.running = True
        self.thread = None
        self.name = "Task Manager"

    def run(self):
        """
        Start the task manager thread.
        """
        logger.info("Lapis task manager thread started.")
        while self.running:
            # check for tasks
            for task in db.tasks.list('waiting'): # please send me a better way to do this, please
                # check if the task is finished
                logger.debug("Found task: %s" % task)
                # check if the task is a mock_build task with the same build id
                if task['type'] == 'mock_build' and task['build_id'] == task['id']:
                    # then check if there's also a waiting mock_srpm task with the same build id
                    if db.tasks.find_by_build(task['build_id'], 'waiting', 'mock_srpm'):
                        # then update the task to finished
                        db.tasks.update(task['id'], {
                            'status': 'finished',
                            'worker_id': task['worker_id'],
                            })
                        # and start the task
                        mock.run(task['payload']['command'])
                    else:
                        # if there's no waiting mock_srpm task, then update the task to done
                        db.tasks.update(task['id'], {
                            'status': 'done',
                            'worker_id': task['worker_id'],
                            })
                else:
                    # get the build id
                    build_id = task['build_id']
                    tasks = db.tasks.list(None)
                    if not tasks:
                        task_id = 1
                    else:
                        task_id = max([task['id'] for task in tasks]) + 1
                    db.tasks.insert({
                    "id": task_id,
                    "type": "mock_build", # default to mock
                    "status": "pending", # wait for lapisd to yoink it
                    "build_id": build_id,
                    "payload": {
                        "command": [
                            'aaaaaaaaaaaaaaaaaaaa'
                        ]
                    }

                    })
            time.sleep(1)


# start the data processing thread
datathread().start()
buildthread().start()
taskmanager().start()