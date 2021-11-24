#Authentication for Lapis
import hashlib
import hmac
from re import match
import lapis.config as config
import json
import lapis.db as database
import lapis.logger as log
import lapis.util as util
import lapis.config as config
import secrets

def passHash(password: str) -> str:
    hash1 = hashlib.sha256(password.encode()).hexdigest()
    # salt the hash with string
    hash2 = hashlib.sha256((hash1 + config.get('secret')).encode()).hexdigest()
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