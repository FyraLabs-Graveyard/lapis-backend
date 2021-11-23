# flask submodule
#
#!/usr/bin/env python3
# Path: server/lapis/api/builds.py

import flask
from flask.config import Config as FlaskConfig
import lapis.config as config
import lapis.db as database
import lapis.logger as logger
import lapis.auth as auth

from flask import Blueprint

builds = Blueprint('builds', __name__)


@builds.route('/', methods=['GET'])
def get_builds():
    """
    Get all builds
    """
    return database.build.list()

@builds.route('/<int:build_id>', methods=['GET'])
def get_build(build_id):
    """
    Get build by id
    """
    return {"build": database.build.get(build_id)}