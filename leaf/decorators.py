import base64
import datetime
from functools import wraps

import jwt
import mysql.connector
from flask import session, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from leaf.config import Config

SECRET_KEY = base64.b64encode(Config.SECRET_KEY.encode()).decode()

limiter = Limiter(
    get_remote_address,
    default_limits=["60000 per day", "20000 per hour"],
    storage_uri="memory://",
)


def generate_jwt():
    """
    Generate a JSON Web Token (JWT) based on session data.

    Returns:
    - str: JWT token string.

    Raises:
    - ValueError: If session data is incomplete.
    """
    userId = session.get('id')
    username = session.get('username')
    email = session.get('email')
    is_admin = session.get('is_admin')

    # Check for None values in the payload
    if None in (userId, username, email, is_admin):
        raise ValueError("Session data incomplete")

    payload = {
        'id': userId,
        'username': username,
        'email': email,
        'is_admin': is_admin,
        'iat': datetime.datetime.utcnow(),  # Include issued at time
    }

    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRATION_TIME)
    payload['exp'] = expiration_time

    jwt_token_bytes = jwt.encode(payload, SECRET_KEY, algorithm="HS256").encode("utf-8")
    jwt_token = jwt_token_bytes.decode("utf-8")
    return jwt_token


def is_authenticated(jwt_token):
    """
    Check if a given JWT token is authenticated.

    Args:
    - jwt_token (str): JWT token to be checked.

    Returns:
    - bool: True if authenticated, False otherwise.
    """
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=['HS256'])

        # Check for expiration
        current_time = datetime.datetime.utcnow()
        if 'exp' in payload and payload['exp'] < current_time.timestamp():
            return False

        # Check for None and empty string for username
        return payload.get('username') and len(payload['username'].strip()) > 0
    except jwt.ExpiredSignatureError:
        # Token has expired
        return False
    except Exception as ex:
        # Log the error or provide more details
        print(f"Error: {ex}")
        return False


def login_required(f):
    """
    Decorator to require login for a route.

    Args:
    - f (function): The route function to be decorated.

    Returns:
    - function: Decorated route function.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):

        if session:
            jwt_token = session.get('jwt_token')
            if jwt_token:
                if not is_authenticated(jwt_token):
                    # Redirect to the login page instead of rendering
                    return render_template('login.html', msg="", msgClass="", is_saml_active=Config.SAML_ACTIVE)
                else:
                    return f(*args, **kwargs)
            else:
                # Redirect to the login page instead of rendering
                return render_template('login.html', msg="", msgClass="", is_saml_active=Config.SAML_ACTIVE)
        else:
            session['loggedin'] = False
            session['id'] = False
            session['user_image'] = False
            session['username'] = False
            session['email'] = False
            session['accountId'] = False
            session['accountName'] = False
            session['is_admin'] = False
            session['is_manager'] = False
            session['jwt_token'] = False

            # Redirect to the login page instead of rendering
            return render_template('login.html', msg="", msgClass="", is_saml_active=Config.SAML_ACTIVE)

    return wrapper


def db_connection():
    """
    Establish a connection to the database and return a cursor.

    Returns:
    - tuple: Connection and cursor objects.

    If an error occurs during the connection, an error message is returned as a string.
    """
    db_config = {
        'user': Config.DB_USER,
        'password': Config.DB_PASS,
        'database': Config.DB_NAME,
    }

    if getattr(Config, 'DB_SOCKET', None):  # if socket is defined
        print("Connection using socket!")
        db_config['unix_socket'] = Config.DB_SOCKET
    else:
        print("Connection using TCP!")
        db_config['host'] = Config.DB_HOST
        db_config['port'] = Config.DB_PORT

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    return connection, cursor


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("is_admin") == 0:
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)

    return decorated_function
