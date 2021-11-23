# Standalone plugin for the builder to run on the server

# Imports
import os
import sys
import time
import json
import subprocess
import threading
import logging
import signal
import socket
import select
import traceback
import platform
import shutil
import zipfile
import tarfile
import tempfile
import hashlib
import lapis.config as config
import lapis.api
import lapis.db as db
import lapis.logger as logger
import secrets
import lapis.util as util

#import all modules in the plugins directory
import importlib
for module in os.listdir(os.path.dirname(__file__)):
    if module == "__init__.py" or module[-3:] != '.py':
        continue
    importlib.import_module("lapis.plugins." + module[:-3])

# standalone subprocess
class StandaloneSubprocess(threading.Thread):
    # init
    def __init__(self):
        # init thread
        threading.Thread.__init__(self)
        # set daemon
        self.daemon = True
        # set name
        self.name = "Lapis-Standalone"
        # set running
        self.running = True
        # set process
        self.process = None
        # set logger
        # set db
        self.db = lapis.db.connection()
        # set port
        self.port = config.get('port')
        # set host
        self.host = config.get("host") + ":" + str(self.port) + config.get("baseurl")
        # set token
        self.token = secrets.token_urlsafe(32)
    # run
    def run(self):
        while self.running:
            # check for sigint and sigterm
            if self.process.poll() is not None:
                # stop the process
                self.stop
            # watch database for tasks
            #lapis.db.list_tasks()
            # check if there are tasks
            #check database for tasks
            #logger.debug(db.tasks.list())
            # check if there are tasks
            #print(db.tasks.list())
            if db.tasks.list():
                # check the task type
                task = db.tasks.list()[0]
                #logger.debug("Selected task:" + str(task))
                logger.debug("worker data:" + db.workers.get(0))
                # check if one of the entries in worker type is in the task type


    def start(self):
        # set running to true
        self.running = True
        # start the process
        self.process = subprocess.Popen(["python3", "-m", "lapis.api.main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #check if WID 0 exists
        if db.workers.get(0):
            # delete WID 0
            db.workers.remove(0)
        else:
            # add the worker
            db.workers.insert({
                "id": 0,
                "name": "Standalone Server",
                "type":["mock"],
                "status": "idle",
                "token": self.token
            })
        # start the thread``
        threading.Thread.start(self)

    def stop(self):
        logger.info("Stopping Standalone Server...")
        db.workers.remove(0)
        # set running to false
        self.running = False
        # stop the process
        self.process.terminate()
        # join the process
        self.process.join()