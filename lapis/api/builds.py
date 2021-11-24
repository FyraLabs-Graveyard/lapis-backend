# flask submodule
#
#!/usr/bin/env python3
# Path: server/lapis/api/builds.py

from json import dumps
import flask
from flask.config import Config as FlaskConfig
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
    return {"builds": database.build.list()}

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
    token = flask.request.cookies.get('token')
    # check for auth
    if not auth.sessionAuth(token):
        return {"error": "Not authorized"}, 401

    else:
        try:
            logger.debug(flask.request.files['file'])
            # check if theres a file or a link attached
            if 'file' in flask.request.files:
                # get the file
                file = flask.request.files['file']
                # save the file to the server
                try:
                    file.save(manager.workdir + '/' + file.filename)
                except Exception as e:
                    logger.error(e)
                    return {"error": "Could not save file: %s" % e}, 500
                # get the absolute path to the saved file
                logger.debug("File path: " + file.filename)
                # submit the file to the build system, then wait for their response
                manager.build(file.filename)
                # now wait for the build manager to respond
                # don't close the connection, we want to keep the connection open and wait for a response
                return flask.Response(status=202)
            # if there is no file, check if there is a link
            elif 'link' in flask.request.form:
                # check if it's a direct file link or a git link
                # by checking if it has a .git at the end
                if flask.request.form['link'].endswith('.git'):
                    # it's a git link
                    manager.git_build(flask.request.form['link'])
                    return flask.Response(status=202)
                else:
                    # it's a direct link
                    # this might not work, but mock does support direct links so it should build
                    manager.build(flask.request.form['link'])
                    return flask.Response(status=202)
            else:
                return flask.make_response(flask.jsonify({"error": "No file or link provided"}), 400)
        except Exception as e:
            logger.error(e)
            return flask.make_response(flask.jsonify({"error": "Something went wrong: %s" % e}), 500)