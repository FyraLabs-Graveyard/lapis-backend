#Authentication for Lapis
import hashlib
import hmac
from os import name
from re import match
import lapis.config as config
import json
import lapis.db as database
import lapis.logger as log
import lapis.util as util
import lapis.config as config
import secrets

"""
Authentication functions for Lapis
There's no real verification here, these functions are *for* verifying the session itself to be sure that the user exists.
The real gatekeeper is the API itself, which runs these functions to verify the user.
There are also functions here for generating tokens for workers and users, and managing sessions.
"""

def passHash(password: str) -> str:
    """
    Hashes a string with SHA-512.
    """
    # I was going to use SHA-256 or scrypt, but then if they had an ASIC miner for either, they'd be able to brute force it.
    # Hooray for Bitcoin and Lite/Dogecoin!
    # Edit: never fucking mind, SHA-512 is still insecure, but it's still better than nothing, also it's salted.
    hash1 = hashlib.sha512(password.encode()).hexdigest()
    # salt the hash with string
    hash2 = hashlib.sha512((hash1 + config.get('secret')).encode()).hexdigest()
    return hash2

def isValid(username: str, password: str) -> bool:
    """
    Checks if the username and password are valid
    """
    try:
        if not username or not password:
            return {'success': False, 'error': 'invalidAuth'}
        user = database.user.get_by_name(username)
        if not user:
            return {'success': False, 'error': 'invalidUser'}
        if user['password'] == passHash(password):
            return {'success': True, 'user': user}
        else:
            return {'success': False, 'error': 'invalidPass'}
    except Exception as e:
        log.error(e)
        return {'success': False, 'error': e}


def checkWorkerToken(token: str) -> dict:
    # Check token validity from database
    token = token.replace('Bearer ', '')
    if not token:
        return {'success': False, 'error': 'No token provided'}
    user = database.workers.get_by_token(token)
    if not user:
        return {'success': False, 'error': 'Invalid token'}
    return {'success': True, 'user': user}

def checkUserToken(token: str) -> dict:
    # Check token validity from database
    token = token.replace('Bearer ', '')
    if not token:
        return {'success': False, 'error': 'No token provided'}
    user = database.user.get_by_token(token)
    if not user:
        return {'success': False, 'error': 'Invalid token'}
    return {'success': True, 'user': user}

def login(username: str=None, password: str=None, token:str=None) -> dict:
    """
    Logs the user in
    """
    check = isValid(username, password)
    if token:
        token = token.replace('Bearer ', '')
        # check if the token is valid
        # Check the token against the database
        check = checkUserToken(token)
        if not check['success']:
            # check the error
            match check['error']:
                case 'Invalid token':
                    return {'success': False, 'error': 'Invalid token', 'code': check['error']}
                case _:
                    return {'success': False, 'error': 'Unknown error', 'code': check['error']}
        else:
            # give the user a session
            token = secrets.token_urlsafe(32)
            # look at existing session ids
            sessions = database.sessions.list_all()
            user = check['user']
            # if there are no sessions, start at 1
            if not sessions:
                session_id = 1
            else:
                session_id = max([session['id'] for session in sessions]) + 1
            # add the session to the database
            database.sessions.add({
                "id": session_id,
                "user_id": user['id'],
                "token": token,
                "created": util.timestamp
            })
            # Update the login time
            conn = database.connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (util.timestamp, user['id']))
            cur.close()
            conn.close()
            return token
    elif not check['success']:
        # check the error
        match check['error']:
            case 'invalidAuth':
                return {'success': False, 'error': 'Invalid username or password', 'code': check['error']}
            case 'invalidUser':
                return {'success': False, 'error': 'Invalid username', 'code': check['error']}
            case 'invalidPass':
                return {'success': False, 'error': 'Invalid password', 'code': check['error']}
            case _:
                return {'success': False, 'error': 'Unknown error', 'code': check['error']}

    else:
        # get the user by their username
        user = database.user.get_by_name(username)
        # generate token
        token = secrets.token_urlsafe(32)
        # look at existing session ids
        sessions = database.sessions.list_all()
        # if there are no sessions, start at 1
        if not sessions:
            session_id = 1
        else:
            session_id = max([session['id'] for session in sessions]) + 1
        # add the session to the database
        database.sessions.add({
            "id": session_id,
            "user_id": user['id'],
            "token": token,
            "created": util.timestamp
        })
        conn = database.connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (util.timestamp, user['id']))
        cur.close()
        conn.close()
        return token

def signup(username: str, password: str, email: str) -> dict:
    """
    Signs up the user
    """
    # check if the username is taken
    if database.user.get_by_name(username):
        return {'success': False, 'error': 'Username taken'}
    # check if the email is taken
    if database.user.get_by_email(email):
        return {'success': False, 'error': 'Email taken'}
    # check if the username is valid
    if not username or not password or not email:
        return {'success': False, 'error': 'Please check your input'}
    if not match(r'^[a-zA-Z0-9_]{3,16}$', username):
        return {'success': False, 'error': 'Invalid username'}
    if not match(r'^[a-zA-Z0-9_]{3,16}$', password):
        return {'success': False, 'error': 'Invalid password'}
    if not match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return {'success': False, 'error': 'Invalid email'}
    # generate random token with secrets, then salt with secret key
    token = secrets.token_urlsafe(32)
    # look at existing session ids
    users = database.user.list()
    # if there are no sessions, start at 1
    if not users:
        user_id = 1
    else:
        user_id = max([user['id'] for user in users]) + 1
    # add the user to the database
    try:
        user_id = database.user.insert({
        "username": username,
        "password": passHash(password),
        "email": email,
        "created": util.timestamp,
        "id": user_id,
        "token": token
        })
    except Exception as e:
        return {'success': False, 'error': e}

    # return the token
    return {'success': True, 'token': token}

def sessionAuth(token: str) -> dict:
    """
    Checks the session token
    """
    # check the token against the sessions table and see if it's valid
    session = database.sessions.get(token)
    if not session:
        return False
    else: return True
def addWorker(name, type):
    """
    Adds a worker for Lapis to build with
    """
    # We dont really need authentication for this, becuase why would you intentionally hack it so you can waste CPU cycles?
    # I mean, you can inject malware into the repo, but then you can also sign the files with GPG, and do checksums, and shit
    # and so, you can't do anything anyway because you'll need to have the Lapis directory directly mounted to run the daemon.
    # Unless someone were to do a massive hack and make the server somehow proxy the mock config upload from the server to use their infected repos, but at that point, be my guest. The repo's yours.
    # So, we can just add the worker and it will be fine
    # oh yea, about the authentication, it'll be handled in the REST APIs instead.
    # It's just a matter of how you handle it in the frontend. Or even if it's written at all at the moment

    # First, check if the worker name is already taken
    if database.workers.get_by_name(name):
        return {'success': False, 'error': 'Worker name already taken'}
    # Next, check if the worker name is valid
    if not name:
        return {'success': False, 'error': 'Please check your input'}
    if not match(r'^[a-zA-Z0-9_]{3,16}$', name):
        return {'success': False, 'error': 'Invalid worker name'}
    # then add the worker to the database
    # generate a token for authentication
    token = secrets.token_urlsafe(128)
    # look at existing worker ids
    workers = database.workers.list()
    # if there are no workers, start at 1
    if not workers:
        worker_id = 1
    else:
        worker_id = max([worker['id'] for worker in workers]) + 1 # I should probably write a function just for these things
    # add the worker to the database
    try:
        worker_id = database.workers.insert({
        "name": name,
        "token": token,
        "type": type,
        "status": "offline", # Will default to offline until it pings the server
        "created": util.timestamp,
        "id": worker_id
        })
    except Exception as e:
        return {'success': False, 'error': e}
    # return the token
    return {'success': True, 'token': token}

def logout(token: str) -> dict:
    """
    Logs the user out
    """
    # check the token against the sessions table and see if it's valid
    session = database.sessions.get(token)['id']
    if not session:
        return {'success': False, 'error': 'Invalid token'}
    # delete the session from the database
    database.sessions.kick(session)
    return {'success': True}