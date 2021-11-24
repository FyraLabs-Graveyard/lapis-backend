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

from flask import Blueprint

tasks = Blueprint('tasks', __name__)


@tasks.route('/', methods=['GET'])
def get_tasks():
    """
    Get all tasks
    """
    return {"tasks": database.tasks.list()}

@tasks.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    Get task by id
    """
    return {"task": database.tasks.get(task_id)}

