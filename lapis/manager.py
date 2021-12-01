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
import glob
import configparser as cp
import datetime
from logging import exception
import os
import threading
import time
import git
import mockbuild.util as mock
import mockbuild.external
import lapis.apiHandler as api
import lapis.auth as auth
import lapis.config as config
import lapis.db as db
import lapis.internal
import lapis.logger as logger
import lapis.util as util
import shutil
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


def initbuildroot(buildroot,comps=None):
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
    mock.run(f'mock -q -r {buildroot} --configdir {mockdir} --init')
    # bit first, create the repo directory
    try:
        os.makedirs(repodir + '/' + buildroot)
    except Exception as e:
        logger.error("Failed to create repo directory: %s" % e)
        pass
    finally:
        # create the buildroot repo so createrepo doesn't complain
        # if comps file is specified, add it to the repo
        if comps:
            mock.run(f'createrepo -p -o {repodir}/{buildroot}/ {repodir}/{buildroot}/ -g {comps}')
        else:
            mock.run(f'createrepo -o {repodir}/{buildroot}/ {repodir}/{buildroot}/ -p')

def buildroot_threaded(buildroot, comps=None):
    """
    Initializes a buildroot in a separate thread
    """
    thread = threading.Thread(target=initbuildroot, args=(buildroot,comps))
    thread.start()
    return True, 'Successfully started buildroot initialization'

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
    nvr = str(rpm['name'] + '-' + rpm['version'] + '-' + rpm['release'])
    logger.info("Building %s" % nvr)
    try:
        build = util.newBuild(
            source=srpm,
            type='mock_rebuild',
            name=rpm['name'],
            description=rpm['description'],
            buildroot=buildroot,
            # lets use the NVR for the output
            output={
                'repo': repodir + '/' + buildroot + nvr
            }
        )
    except Exception as e:
        logger.error("Failed to create build: %s" % e)
        return False, "Failed to create build", e
    # create a new task for the build
    task = util.newTask(build_id=build,type= 'mock_rebuild', source=srpm, buildroot=buildroot, status='running')
    pkgpath = f'{repodir}/{buildroot}/{nvr}/'
    logger.debug("pkgpath: %s" % pkgpath)
    # if the package is already built, delete the success file so we can rebuild it
    if os.path.exists(pkgpath + 'success'):
        os.remove(f'{pkgpath}/success')
    
    # make a new working directory for the build
    try:
        os.makedirs(f"{workdir}/{buildroot}/{task}")
        # move the srpm into the working directory
        os.rename(srpm, f"{workdir}/{buildroot}/{task}/{nvr}.src.rpm")
        # redefine the srpm to be the new path
        srpm = f"{workdir}/{buildroot}/{task}/{nvr}.src.rpm"
    except Exception as e:
        logger.error("Failed to create working directory: %s" % e)
        return False, "Failed to create working directory", e
    mock.run(f'mock -r {buildroot} --configdir {mockdir} --rebuild {srpm} --chain --localrepo {home} -q --uniqueext={build} --cleanup-after') # set to home because mock likes to output to results/
    
    
    # copy the SRPM to the repo
    try:
        shutil.copy(srpm, f"{repodir}/{buildroot}/{nvr}/{nvr}.src.rpm")
    except Exception as e:
        logger.error("Failed to copy SRPM to repo: %s" % e)
        return False, "Failed to copy SRPM to repo", e
    # update the repos for the buildroot
    mock.run(f'createrepo -o {repodir}/{buildroot}/ {repodir}/{buildroot}/ --update')
    if os.path.exists(workdir):
        mock.run(f'rm -rf {workdir}/{task}*')

    util.updateTask(task, status='finished')
    util.updateBuild(build, status='finished', output={
            'repo': repodir + '/' + buildroot + nvr
        })
    return True, "Successfully rebuilt %s" % srpm

# data processing sub-thread, now only manages dead workers

def git_clone(url,path):
    # do a recursive clone
    # use gitpython
    git.Repo.clone_from(url, path, depth=1, recursive=True)
    # print output
    print('Cloned %s to %s' % (url, path))

def build_git(url ,clonepath, buildroot, path='/var/lib/mock/lapis', outdir='result', subdir=None):
    """
    builds an SRPM from a git repository
    """
    # copied over from lapisd code, because i'd rather not rewrite it
    try:
        git_clone(url,clonepath) #
        # except if the repo is already cloned
    except git.exc.GitCommandError as e:
        print(e)
    try:
        command = 'mock'

        if subdir is not None:
            # add cd clonepath + <subdir> && before the command
            command = 'cd %s/%s &&' % (clonepath, command)

        args = [
            '-r', buildroot,
            '--rootdir', path,
            '--resultdir', outdir,
            '--buildsrpm '
            # find the spec file in the clonepath, then pass it to mock as an absolute path
            '--spec $(readlink -f $(find %s -name *.spec))' % clonepath,
            # --source is basename of the spec file
            '--source $(dirname $(readlink -f $(find %s -name *.spec)))' % clonepath,
            # Enable network building by default
            '--enable-network',
            '--configdir %s' % mockdir,
            '--undefine=\"%_disable_source_fetch\"',
        ]
        cmd = ' '.join([command] + args)
        print('running ' + cmd)
        mock.run(cmd)
    except mockbuild.external.CommandError as e:
        print(e)
        os.system('rm -rf %s' % clonepath)
        return False, "Failed to build git: %s" % e

def gitBuild(url, buildroot):
    # will call the function above, then call mockRebuild
    # i'm only doing this because the git builder function is PAINFULLY convoluted
    # create a build in the db first
    build = util.newBuild(
            source=url,
            type='mock_rebuild',
            # get the git name from the url
            name=url.split('/')[-1].split('.')[0],
            description='Built from Git',
            buildroot=buildroot,
            # lets use the NVR for the output
            output={
                'git': url
            }
    )
    builddir = workdir + '/' + str(build)
    task = util.newTask(build_id=build,type= 'mock_git', source=url, buildroot=buildroot, status='running')
    try:
        build_git(
            url,
            clonepath=builddir,
            buildroot=buildroot,
            path='/var/lib/mock/lapis',
            outdir=builddir + '/result',
        ) # I swear to god if this doesn't work
        # now find the srpm that we just built right in the workdir
        srpm = glob.glob(builddir + '/result/*.src.rpm')
        if len(srpm) == 0:
            logger.error("Failed to find srpm")
            return False, "Failed to find srpm"
        srpm = srpm[0]
    except Exception as e:
        logger.error("Failed to build git: %s" % e)
        util.updateTask(task, status='failed')
        util.updateBuild(build, status='failed', output={
                'git': url
            })
        return False, "Failed to build git: %s" % e
    finally:
        # now call mockRebuild
        util.updateTask(task, status='finished')
        util.updateBuild(build, status='finished', output={
                'git': url
            })
        return builder_threaded(srpm, buildroot)

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


def gitBuilder_threaded(url, buildroot):
    # do not output logs to the console
    thread = threading.Thread(target=gitBuild, args=(url, buildroot))
    thread.start()
    return True, 'Successfully started git build'

def builder_threaded(srpm, buildroot):
    thread = threading.Thread(target=mockRebuild, args=(srpm, buildroot))
    thread.start()
    return True, 'Successfully started mock rebuild'

# start the data processing thread
datathread().start()

init()
