# Flask user blueprint

import lapis.logger as logger
import lapis.auth as auth
import flask
from flask.config import Config as FlaskConfig
import lapis.config as config
import lapis.db as database

users = flask.Blueprint('users', __name__)

# route for any method

@users.route('/signup', methods=['GET','POST'])
def signup():
    """
    Sign up a new user
    """
    # get the user's email and password from the request
    username = flask.request.args.get('username')
    password = flask.request.args.get('password')
    email = flask.request.args.get('email')
    # if anything is missing, return an error
    if not username or not password or not email:
        return flask.make_response(flask.jsonify({'error': 'Missing username, password, or email'}), 400)
    else:
        # check if the user already exists
        if database.user.get_by_name(username):
            return flask.make_response(flask.jsonify({'error': 'User already exists'}), 409)
        else:
            # sign up the user
            return {
                'response': auth.signup(username=username, password=password, email=email),
                'args': flask.request.args.to_dict()
            }
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

