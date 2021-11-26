import os
import flask
import subprocess

from werkzeug.datastructures import FileStorage
import lapis.config as config
import lapis.manager as manager
import lapis.db as database
import lapis.auth as auth
import lapis.logger as logger
from flask import Blueprint
buildroot = Blueprint('buildroot', __name__)
import json
@buildroot.route('/', methods=['GET'])
def list_buildroots():
    """
    List all buildroots
    """
    return flask.make_response(json.dumps(database.buildroot.list()), 200)

# now before processing any other request, we need to check if the user is authenticated
@buildroot.before_request
def before_request():
    """
    Check if the user is authenticated
    """
    token = flask.request.cookies.get('token')
    # check for auth
    if not auth.sessionAuth(token):
        return {"error": "Not authorized"}, 401

@buildroot.route('/<name>', methods=['GET'])
def get_buildroot(name):
    """
    Get buildroot by id
    """
    return flask.make_response(json.dumps(database.buildroot.get(name)), 200)

@buildroot.route('/submit', methods=['POST'])
def add_buildroot():
    """
    Add a buildroot
    """
    if not flask.request.files:
        return flask.make_response(json.dumps({'error': 'No file uploaded'}), 400)
    # get the mock config
    mock_config = flask.request.files['mock']
    # save the mock config to the lapis folder
    # if buildroot already exists, replace it instead
    try:
        path = f"{manager.mockdir}/{mock_config.filename}"
        mock_config.save(path)
        name = mock_config.filename.split('.')[0]
    except Exception as e:
        return flask.make_response(json.dumps({'error': e}), 400)
    finally:
        # check buildroot ids
        #check if buildroot with the same name exists
        # if yes, dont create a new one
        if database.buildroot.get_by_name(name):
            return flask.make_response(json.dumps(manager.buildroot_threaded(buildroot=name)), 200)



        buildroots = database.buildroot.list()
        if not buildroots:
            br_id = 1
        else:
            br_id = max([int(br['id']) for br in buildroots]) + 1
        database.buildroot.insert({
            "id": br_id,
            "name": name,
            "status": 'ready'
        })
        return flask.make_response(json.dumps(manager.buildroot_threaded(buildroot=name)), 200)

@buildroot.route('/<name>', methods=['DELETE'])
def delete_buildroot(name):
    """
    Delete a buildroot
    """
    try:
        id = database.buildroot.get_by_name(name)['id']
        logger.debug(f"Deleting buildroot {id}")
        try:
            delete = database.buildroot.remove(id)
            os.removedirs(f"{manager.mockdir}/{name}")
        except Exception as e:
            pass
        return flask.make_response(json.dumps({'success': 'Buildroot deleted'}), 200)
        #database.buildroot.remove(id)
    except Exception as e:
        return flask.make_response(json.dumps({'error': e}), 400)