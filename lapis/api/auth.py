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

#We're not using Flask-login because database is not a Flask app

# Authentication blueprint so it doesn't clutter up the main blueprint

authen = Blueprint('auth', __name__)

@authen.route('/signup', methods=['GET','POST'])
def signup():
    """
    Sign up a new user
    """
    # get the user's email and password from the request
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    email = flask.request.form.get('email')
    # if anything is missing, return an error
    return auth.signup(username=username, password=password, email=email)


@authen.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log in a user
    """
    try:
        response = flask.make_response()
        # get password from HTTP login form
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')

    except Exception as e:
        return flask.make_response(json.dumps({'error': str(e)}), 500)
    utoken = auth.login(username=username, password=password)
    response.set_cookie('token',value=utoken)
    #response.set_cookie('sid',str(value=database.sessions.get(utoken)['id']))
    return response

# for some godforsaken reason, token login has stopped working properly, so it is now a separate endpoint
@authen.route('/tokenlogin', methods=['GET', 'POST'])
def token_login():
    """
    Log in using a token
    """
    response = flask.make_response()
    # get bearer token from request
    token = flask.request.headers.get('Authorization').split(' ')[1]
    if not token:
        return flask.make_response(json.dumps({'error': 'No token provided, do you mean /login?'}), 401)
    # check the token
    utoken = auth.login(token=token)
    response.set_cookie('token',value=utoken)
    #response.set_cookie('sid',value=database.sessions.get(utoken))
    return response

@authen.route('/logout', methods=['GET'])
def logout():
    """
    Log out a user
    """
    # get the login cookie
    response = flask.make_response()
    token = flask.request.cookies.get('token')
    if not token:
        return 'Already logged out, all is fine!', 200
    # if anything is missing, return an error
    return flask.make_response(jsonify(database.sessions.kick(token)), 200)