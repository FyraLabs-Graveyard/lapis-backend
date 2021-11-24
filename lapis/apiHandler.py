
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
#The funny blueprints, idk i never used flask before

from flask import Blueprint




baseurl = config.get('baseurl')
#print(config.list())

# get lapis path from config


print(FlaskConfig.values)

def main():
    from . import app
    app.run(config)

app = flask.Flask(__name__)
app.config["DEBUG"] = True
# set flask port to config

app.register_blueprint(lapis.api.builds.builds, url_prefix=baseurl+'/builds')
app.register_blueprint(lapis.api.tasks.tasks, url_prefix=baseurl+'/tasks')
#app.register_blueprint(lapis.api.users.users, url_prefix=baseurl+'/users')
#app.register_blueprint(lapis.api.session.session, url_prefix=baseurl+'/session')
#app.register_blueprint(lapis.api.workers.workers, url_prefix=baseurl+'/workers')

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