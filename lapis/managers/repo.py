import sys
import os
import lapis.manager as manager
import threading
import configparser
import lapis.util as util
import time
import lapis.logger as logger

class RepoManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = 'RepoManager'

    def folders(self):
        # check the mock folder
        # find config files in manager.mockdir
        logger.info('Checking folder structure')
        config = {}
        for mockcfg in os.listdir(manager.mockdir):
            # read the config file
            with open(os.path.join(manager.mockdir, mockcfg), 'r') as f:
                # read each line of the config file and split it by the =
                for line in f:
                    line = line.split('=')
                    #print(line)
                    # then turn the 2 elements into a dictionary
                    # the key name will be the first element
                    # strip the newline character from the value
                    key = line[0].strip().replace('config_opts', '').replace('[', '').replace(']', '').replace('\'', '')
                    #print(key)
                    try:
                        value = line[1].strip().replace('\'', '').replace('\n', '').replace('"', '').split('#')[0].replace(' ', '')
                        data = {key: value}
                        # add the key and value to the dictionary
                        config.update(data)
                    except:
                        pass
            #print(config)
            # get config_opts['dist'] of config which is a string value
            dist = config['dist'].replace(' ', '').replace('{{releasever}}', config['releasever'])
            # get the config_opts['target_arch'] of config which is also a string value
            arch = config['target_arch']
            logger.debug(f'Checking {dist} {arch}')
            # mkdir with structure of dist/arch if not exist
            if not os.path.exists(os.path.join(manager.repodir, dist, arch)):
                os.makedirs(os.path.join(manager.repodir, dist, arch))
                # check if there's a 'Packages' folder in that directory
                if not os.path.exists(os.path.join(manager.repodir, dist, arch, 'Packages')):
                    # create one if not exist
                    os.makedirs(os.path.join(manager.repodir, dist, arch, 'Packages'))

            # also make a sources folder if not exist
            if not os.path.exists(os.path.join(manager.repodir, dist, 'Sources')):
                os.makedirs(os.path.join(manager.repodir, dist, 'Sources'))

        # we're doing this to emulate Pungi and Koji's behavior, plus it tidies up the repo
        # not as close but at least you have to traverse less

    def files(self):
        # check the builds folder for packages recursively
        # find all files in manager.builddir
        logger.info('Moving files to repo')
        for root, dirs, files in os.walk(manager.builddir):
            # for each RPM recursively in the builddir
            for file in files:
                # get the absolute path of the file
                file = os.path.join(root, file)
                # if it's an RPM
                if file.endswith('.rpm'):
                    # check if it's a source RPM
                    if file.endswith('src.rpm'):
                        #analyze the RPM
                        rpm = util.analyze_rpm(os.path.join(file))
                        # get the dist from the RPM
                        dist = rpm['release'].split('.')[-1]
                        # now move the source RPM to the repo
                        logger.debug(f'Moving {file} to {os.path.join(manager.repodir, dist, arch, "Packages")}')
                        os.system(f'mv {os.path.join(root, file)} {os.path.join(manager.repodir, dist, "Sources")}')
                    # now that's done, everything else should be a binary RPM
                    # analyze the RPM
                    else:
                        rpm = util.analyze_rpm(file)
                        dist = rpm['release'].split('.')[-1]
                        arch = rpm['arch']
                        if arch == 'noarch':
                            arch = 'x86_64'
                        logger.debug(dist)
                        logger.debug(f'Found file {file} with dist {dist} and arch {arch}')
                        logger.debug(f'Moving {file} to {os.path.join(manager.repodir, dist, arch, "Packages")}')
                        os.system(f'mv {os.path.join(root, file)} {os.path.join(manager.repodir, dist, arch, "Packages")}')
                # End of indent hell
                # Now check for ISO files
                if file.endswith('.iso'):
                    # create the iso folder in repodir if not exist
                    if not os.path.exists(os.path.join(manager.repodir, 'iso')):
                        os.makedirs(os.path.join(manager.repodir, 'iso'))
                    # move the ISO to the iso folder
                    os.system(f'mv {os.path.join(root, file)} {os.path.join(manager.repodir, "iso")}')
                # for everything else, buildtrees and other stuff should be pushed via rsync and already configured, probably with Onceler or plain Lorax
                # truly a 2021 devops moment
                # we have to do this because we're not using Pungi or Koji, but Onceler instead of Pungi and Lapis instead of Koji
                # items like this will be already configured to push to the correct location with your respective CI tools
    def repogen(self):
        # Now, the actual repo metadata itself.
        # Since this is not Debian, repos will need to have its own metadata
        # so, let's use createrepo from the command line because python modules from Fedora release engineering are just... horrid

        # The repo structure is:
        # dist/
        #  arch/
        #   Packages/
        # so traverse to dist/arch and run createrepo on Packages
        logger.info('generating repo metadata')
        for dist in os.listdir(manager.repodir):
            for arch in os.listdir(os.path.join(manager.repodir, dist)):
                if dist.startswith('.') and dist.endswith('}'):
                    # skip the broken dist
                    continue
                logger.debug(f'Generating repo metadata for {dist} {arch}')
                if arch == 'Sources':
                    os.system(f'createrepo --update {os.path.join(manager.repodir, dist, arch)}/ -o {os.path.join(manager.repodir, dist, arch)}')
                else:
                    os.system(f'createrepo --update {os.path.join(manager.repodir, dist, arch, "Packages")}/ -o {os.path.join(manager.repodir, dist, arch)}')
                # we're running update so that it won't waste time re-creating the repo if nothing has changed
                # using -o too because it will create the repo in the working directory if not specified
        # so much for a single command but we're done
    def run(self):
        # run all the functions in order, then after that run repogen in a separate thread to avoid blocking
        # this function should be run every time a build is finished or every 30 minutes
        # check every 30 minutes or when triggered by the function below
        # this is a blocking function
        # this will run forever unless you kill it

        # make sure only one of these threads is running at a time

        while self.is_alive():
            self.folders()
            self.files()
            self.repogen()
            # wait 30 minutes
            time.sleep(1800)
        # only one instance of this thread should be running at a time to avoid conflicts
        # so we're done here

    def trigger(self):
        # restart the thread and run it again
        # this function is called by the web server when the trigger is called
        self.start()
RepoManager().start()