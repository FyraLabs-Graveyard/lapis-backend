# miscallenous utility functions

import datetime
import lapis.logger as logger
import lapis.db as db
timestamp = datetime.datetime.now().isoformat()

import pkgutil
import sys
import os
import rpm

def loadmod(dirname):
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        full_package_name = '%s.%s' % (dirname, package_name)
        if full_package_name not in sys.modules:
            module = importer.find_module(package_name
                        ).load_module(full_package_name)
            logger.info(module)

def last_entry(list:list):
    if len(list) == 0:
        return None
    else:
        #logger.debug(list)
        return max(list) + 1

def newTask(build_id:int,source: str,type: str, buildroot, status='pending',payload:dict={},):
    """
    Creates a new task
    """
    tasks = db.tasks.list(None)
    #logger.debug(tasks)
    if not tasks:
        task_id = 1
    else:
        task_id  = max([task['id'] for task in tasks]) + 1 # I should probably write a function just for these things
    logger.debug("Got the last task id: %s" % task_id)
    db.tasks.insert({
        'id': task_id,
        'source': source,
        'status': status,
        'type': type,
        'payload': payload,
        'build_id': build_id,
        'buildroot': buildroot
    })
    return task_id
def newBuild(source: str,type: str, buildroot, description, name, output):
    builds = db.build.list()
    if not builds:
        build_id = 1
    else:
        build_id  = max([build['id'] for build in builds]) + 1
    logger.debug("Got the last build id: %s" % build_id)
    db.build.insert({
        'id': build_id,
        'status': 'pending',
        'description': description,
        'name': name,
        'source': source,
        'type': type,
        'buildroot': buildroot,
        'started_at': timestamp,
        'output': output,
        'finished_at': None,
        'duration': None,
    })
    return build_id

def updateBuild(build_id:int, output:str,status:str='finished'):
    build = db.build.get(build_id)
    if status == 'finished':
        ts = timestamp
    else:
        ts = None
    db.build.update(build_id, {
        'name': build['name'],
        'description': build['description'],
        'source': build['source'],
        #'type': build['type'],
        'status': status,
        'started_at': build['started_at'],
        'finished_at': ts,
        'duration': datetime.datetime.now() - build['started_at'],
        'output': output,
    })
    return build_id

def updateTask(task_id,status:str='finished'):
    task = db.tasks.get(task_id)
    if status == 'finished':
        ts = timestamp
    else:
        ts = None
    db.tasks.update(task_id, {
        'status': status,
        'payload': task['payload'],
    })
    return task


def analyze_rpm(rpm_path:str):
    """[summary]
    Analyze an RPM to get its metadata
    """
    ts = rpm.TransactionSet()
    fdno = os.open(rpm_path, os.O_RDONLY)
    hdr = ts.hdrFromFdno(fdno)
    os.close(fdno)
    return hdr