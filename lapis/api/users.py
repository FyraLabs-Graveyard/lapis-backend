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
    return auth.signup(username=username, password=password, email=email)


@users.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log in a user
    """
    try:
        response = flask.make_response()
        # get password from HTTP login form
        username = flask.request.args.get('username')
        password = flask.request.args.get('password')


        if flask.request.args.get('token'):
            utoken = flask.request.args.get('token') 
        elif flask.request.headers.get('Authorization'):
            utoken = flask.request.headers.get('Authorization')
        else :
            utoken = None
        # get bearer token from request
        logger.debug(flask.request.headers)
        logger.debug(flask.request.args.to_dict())
        if username or password:
            token = auth.login(username=username, password=password)
            response.status_code = 200
        elif utoken:
            # return a cookie if succeeds
            token = auth.login(token=utoken)
            response.status_code = 200

        else:
            response.status_code = 401
        #logger.debug(token)
        #logger.debug(utoken)
        # finally, check the status of the token
        if token:
            response.set_cookie('token', token)
        else:
            response.status_code = 401
        #logger.debug(token)
        #logger.debug(utoken)
    except Exception as e:
        return str(e), 500
    return response


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


