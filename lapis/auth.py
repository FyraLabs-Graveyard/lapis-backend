#Authentication for Lapis
import hashlib
import hmac
import lapis.config as config
import json
import lapis.db as database
import lapis.logger as log

def passHash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def isValid(username: str, password: str) -> bool:
    """
    Checks if the username and password are valid
    """
    if not username or not password:
        return {'success': False, 'error': 'No username or password provided'}
    user = database.getUser(username)
    if not user:
        return {'success': False, 'error': 'User not found'}
    if user['password'] == passHash(password):
        return {'success': True, 'user': user}
    else:
        return {'success': False, 'error': 'Invalid password'}


def checkWorkerToken(token: str) -> dict:
    # Check token validity from database
    if not token:
        return {'success': False, 'error': 'No token provided'}
    user = database.workers.get_by_token(token)
    if not user:
        return {'success': False, 'error': 'Invalid token'}
    return {'success': True, 'user': user}

def checkUserToken(token: str) -> dict:
    # Check token validity from database
    if not token:
        return {'success': False, 'error': 'No token provided'}
    user = database.users.get_by_token(token)
    if not user:
        return {'success': False, 'error': 'Invalid token'}
    return {'success': True, 'user': user}