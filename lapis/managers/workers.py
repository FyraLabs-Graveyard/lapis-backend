import threading
import lapis.db as db
import lapis.logger as logger
import time
import datetime

class datathread(threading.Thread):
    """
    Worker Manager Functions
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.thread = None
        self.name = "Worker Management Thread"

    def run(self):
        """
        The main thread loop.
        """
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
            time.sleep(30)

datathread().start()