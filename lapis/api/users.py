# Flask user blueprint

import lapis.logger as logger
import lapis.auth as auth
import flask
from flask.config import Config as FlaskConfig
import lapis.config as config
import lapis.db as database

users = flask.Blueprint('users', __name__)

# route for any method on the /users endpoint

@users.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a user by ID
    """
    # Get the user
    # but exclude the password and token
    user = database.user.get(user_id)
    if user is None:
        return flask.jsonify({
            'error': 'User not found'
        }), 404
    return flask.jsonify({
        'user': user
    }), 200


