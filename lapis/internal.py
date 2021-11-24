# lapisd internal worker

import lapis.config as config
import lapis.auth as auth
import lapis.db as database
import lapis.logger as logger
import lapis.util as util
import threading
import mockbuild.util as mock

# internal lapisd thread
class lapisd_internal():
    """
    The internal lapis daemon is a replacement for the lapis daemon.
    """
    def __init__(self):
        """
        Initialize the internal thread.
        """
        self.running = True
        self.thread = None

    def start(self):
        """
        Start the internal thread.
        """
        worktoken = auth.addWorker({'name': 'internal', 'type': 'internal'})['token']
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        """
        Run the internal thread.
        """
        while self.running:
            # check database for builds to process
            # if there are builds, process them
            # if there are no builds, sleep for a bit
            logger.debug('lapis-internal', 'Processing task: %s' % task)
            if database.tasks.list() == []:
                logger.log('lapis-internal', 'No tasks to process, sleeping for a bit.')
                util.sleep(10)
                # process the build
            else:
                task = database.tasks.list()[0]
                logger.debug('lapis-internal', 'Processing task: %s' % task)

    def stop(self):
        """
        Stop the internal thread.
        """
        worker = database.workers.get_by_name('internal')
        database.workers.remove(worker['id'])
        self.running = False
        self.thread.join()