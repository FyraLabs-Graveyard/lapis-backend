
from logging import error
import flask
from flask.config import Config as FlaskConfig
import lapis.config as config
import lapis.db as database
import lapis.logger as logger
import lapis.auth as auth

import lapis.api.builds
import lapis.api.users
import lapis.api.session
import lapis.api.workers
import lapis.api.tasks
import lapis.api.auth
import lapis.api.buildroot
#The funny blueprints, idk i never used flask before
from flask import Blueprint

import lapis.manager

from lapis.util import loadmod

# for weird reasons, we're making this the main entry point becuase Flask wouldn't like it otherwise
# The lapis-server.py script will still be up as a simple launcher for this script.

from lapis.util import loadmod
# run the standalone thread

#TODO make this actually run if it is set to true
if config.get('standalone') == True:
    lapis.plugins.standalone.StandaloneSubprocess().start()
#lapis.plugins.standalone.StandaloneSubprocess().start()

#try and touch database so it generates the tables, weird but it works
try:
    lapis.db.initialize()
except Exception as e:
    logger.warning(e)

try:
    # load all modules in the plugins directory
    loadmod('lapis.plugins')
    #load the managers
    loadmod('lapis.managers')
    loadmod('lapis.api')
except Exception as e:
    logger.warning(e)

baseurl = config.get('baseurl')
#print(config.list())

# get lapis path from config


#print(FlaskConfig.values)

def main():
    from . import app
    app.run(config)

app = flask.Flask(__name__)
app.config["DEBUG"] = True
# set flask port to config

# I'd replace this with a 501 response, but it's a waste of time so 404 it is

app.register_blueprint(lapis.api.builds.builds, url_prefix=baseurl+'/builds')
app.register_blueprint(lapis.api.tasks.tasks, url_prefix=baseurl+'/tasks')
app.register_blueprint(lapis.api.users.users, url_prefix=baseurl+'/users')
#app.register_blueprint(lapis.api.session.session, url_prefix=baseurl+'/session')
app.register_blueprint(lapis.api.workers.workers, url_prefix=baseurl+'/workers')
app.register_blueprint(lapis.api.buildroot.buildroot, url_prefix=baseurl+'/buildroot')
# register the authendication blueprint
app.register_blueprint(lapis.api.auth.authen, url_prefix=baseurl)

@app.after_request
def after_request(response):
    logger.info(response)
    return response
def run():
    app.run(
        host=config.get('host'),
        port=config.get('port'),
        debug=config.get('debug'),
        threaded=config.get('threaded'),
    )

# stdout from flask to logger
@app.before_request
def before_request():
    logger.info(flask.request)