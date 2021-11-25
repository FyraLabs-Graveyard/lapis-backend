# flask submodule
#
#!/usr/bin/env python3
# Path: server/lapis/api/builds.py

import json
import flask
from flask.config import Config as FlaskConfig
from flask.helpers import make_response
from flask.json import jsonify
import lapis.config as config
import lapis.db as database
import lapis.logger as logger
import lapis.auth as auth
import lapis.manager as manager
from flask import Blueprint

builds = Blueprint('builds', __name__)


@builds.route('/', methods=['GET'])
def get_builds():
    """
    Get all builds
    """
    return make_response(json.dumps(database.build.list(), default=str), 200)

@builds.route('/<int:build_id>', methods=['GET'])
def get_build(build_id):
    """
    Get build by id
    """
    return {"build": database.build.get(build_id)}

# let user upload file to build, or send a link to source code
@builds.route('submit', methods=['POST'])
def submit_build():
    """
    Submit a build
    """
    link = flask.request.form.get('link')
    token = flask.request.cookies.get('token')
    # check for auth
    if not auth.sessionAuth(token):
        return {"error": "Not authorized"}, 401
    buildroot = flask.request.form.get('buildroot')
    if not buildroot:
        return {"error": "Missing buildroot"}, 400

    else:
        try:
            logger.debug("Got buildroot: %s" % buildroot)
            #logger.debug("Got link: %s" % link)
            if link:
                logger.debug("Got link: %s" % link)
                build = manager.gitBuilder_threaded(link, buildroot)
                return flask.make_response(jsonify(build)), 202
            elif 'file' in flask.request.files:
                # get the file
                file = flask.request.files['file']
                # save the file to the server
                try:
                    path = manager.workdir + '/' + file.filename
                    file.save(manager.workdir + '/' + file.filename)
                except Exception as e:
                    logger.error(e)
                    return {"error": "Could not save file: %s" % e}, 500
                # get the absolute path to the saved file
                logger.debug("File path: " + path)
                # submit the file to the build system, then wait for their response
                build = manager.builder_threaded(path, buildroot)
                # now wait for the build manager to respond
                # don't close the connection, we want to keep the connection open and wait for a response
                # get the return value from the build manager
                # if the build manager returns a value, it means the build was successful
                return flask.make_response(jsonify(build)), 202
            # if there is no file, check if there is a link
            else:
                return flask.make_response(flask.jsonify({"error": "No file or link provided"}), 400)
        except Exception as e:
            logger.error(e)
            return flask.make_response(flask.jsonify({"error": "Something went wrong: %s" % e}), 500)