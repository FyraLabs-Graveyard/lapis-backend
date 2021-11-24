# Worker Flask blueprint to manage workers
import os
import json
import flask
from flask import Blueprint
from flask.json import jsonify
import lapis.config
import lapis.manager as manager
import lapis.auth as auth
import lapis.util as util
import lapis.db as database
import lapis.logger as logger

workers = Blueprint('workers', __name__)

@workers.route('/', methods=['GET'])
def list_workers():
    """
    List all workers
    """
    return flask.make_response(json.dumps(database.workers.list()), 200)

@workers.route('/', methods=['POST'])
def add_worker():
    """
    Add a new worker
    """
    token = flask.request.cookies.get('token')
    # check for authentication from cookie
    if not auth.sessionAuth(token):
        return flask.make_response(json.dumps({'error': 'Not authenticated'}), 401)
    # check for required fields
    if not 'name' in flask.request.form:
        return flask.make_response(json.dumps({'error': 'Missing required fields'}), 400)
    name = flask.request.form['name']
    # optional type field
    if flask.request.form.get('type'):
        type = flask.request.form['type']
    else: type = 'mock' # default to mock
    #logger.debug('Adding worker: ' + name)
    #logger.debug('Type: ' + type)
    # try to add a new worker
    try:
        worker = auth.addWorker(name,type)
        if worker['success']:
            return flask.make_response(json.dumps(worker), 200)
        else:
            return flask.make_response(json.dumps(worker), 400)
    except Exception as e:
        return flask.make_response(json.dumps({'error': str(e)}), 500)

# for workers to ping the server
@workers.route('/ping', methods=['HEAD'])
def ping():
    """
    Ping the server to show that it's still alive
    """
    # get worker token from bearer token
    token = flask.request.headers.get('Authorization').split(' ')[1]
    #logger.debug('Worker token: ' + token)
    if token:
        return flask.make_response(jsonify(database.workers.ping(token), 200))
    else:
        return flask.make_response(json.dumps({'error': 'Not authenticated'}), 401)

@workers.route('/<worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    """
    Delete a worker
    """
    token = flask.request.cookies.get('token')
    # check for authentication from cookie
    if not auth.sessionAuth(token):
        return flask.make_response(json.dumps({'error': 'Not authenticated'}), 401)
    # check for required fields
    # check if worker exists
    if not database.workers.get(worker_id):
        return flask.make_response(json.dumps({'error': 'Worker not found'}), 404)
    # try to delete the worker

    return flask.make_response(json.dumps(worker = database.workers.remove(worker_id)), 200)
        # if worker is deleted, return success
        

@workers.route('/<worker_id>', methods=['GET'])
def get_worker(worker_id):
    """
    Get a worker by ID
    """
    # check if worker exists
    if not database.workers.get(worker_id):
        return flask.make_response(json.dumps({'error': 'Worker not found'}), 404)
    # try to get the worker
    try:
        worker = database.workers.get(worker_id)
    except Exception as e:
        return flask.make_response(json.dumps({'Backend error': str(e)}), 500)
    return flask.make_response(json.dumps(worker), 200)

@workers.route('/<worker_id>/status', methods=['GET'])
def worker_status(worker_id):
    """
    Get the status of a worker
    """
    # check if worker exists
    if not database.workers.get(worker_id):
        return flask.make_response(json.dumps({'error': 'Worker not found'}), 404)
    # try to get the worker
    try:
        status = database.workers.status(worker_id)
    except Exception as e:
        return flask.make_response(json.dumps({'Backend error': str(e)}), 500)
    return flask.make_response(json.dumps(status), 200)
