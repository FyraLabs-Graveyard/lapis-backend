# flask submodule
#
#!/usr/bin/env python3
# Path: server/lapis/api/tasks.py

from json import dumps
import flask
from flask.config import Config as FlaskConfig
import lapis.config as config
import lapis.db as database
import lapis.logger as logger
import lapis.auth as auth
import lapis.manager as manager
from flask import Blueprint

tasks = Blueprint('tasks', __name__)


@tasks.route('/', methods=['GET'])
def get_tasks():
    """
    Get all tasks
    """
    return flask.make_response(dumps(database.tasks.list()), 200)

@tasks.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    Get task by id
    """
    return flask.make_response(dumps(database.tasks.get(task_id)), 200)

# rule for tasks/<int:task_id>/output
@tasks.route('/<int:task_id>/output', methods=['GET'])
def task_output(task_id):
    """
    Get task output
    """
    # return directory
    # stream output so we can tail logs
    return flask.send_from_directory(manager.workdir + '/' + str(task_id) + '/')

@tasks.route('/<int:task_id>/update', methods=['POST'])
def update_task(task_id):
    """
    Update task status
    """
    # get the token and sanitize it
    worker_token = flask.request.headers.get('Authorization').replace('Bearer ', '')
    # check if user is authorized
    is_authorized = auth.checkWorkerToken(worker_token)

    if is_authorized:
        # get task data from request
        data = flask.request.get_json()
        #TODO actually make the function
        manager.updateTask(task_id, data)
    else: return flask.make_response(dumps({'error': 'unauthorized'}), 401) # clean one liner

