import re
import paramiko
from flask import render_template, Blueprint, jsonify, request, session, send_from_directory, redirect
from leaf.config import Config
import hashlib
import os
from leaf.decorators import login_required, limiter, db_connection, generate_jwt
import werkzeug.utils
from urllib.parse import urlparse

main = Blueprint('main', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@main.errorhandler(429)
def ratelimit_handler():
    """
    Error handler for handling 429 Too Many Requests status code.

    Parameters:
    - e (Exception): The exception object that triggered the error handler.

    Returns:
    - str: HTML content to be rendered, displaying a message about the rate limit exceeded.
    """
    msg = 'Too many attempts. Please try again in 1 minute.'
    msgClass = 'alert alert-danger'
    return render_template('login.html', msg=msg, msgClass=msgClass)


@main.route("/")
@main.route("/home")
@main.route("/index.html")
@login_required
def index():
    """
    Render the main index page.

    Requires the user to be logged in.

    Returns:
    - str: HTML content to be rendered, displaying the main index page.
    """
    return render_template('sites.html', username=session['username'], user_image=session['user_image'],
                           accountId=session['accountId'], accountName=session['accountName'],
                           is_admin=session['is_admin'], is_manager=session['is_manager'])


@main.route("/login", methods=['GET', 'POST'])
@limiter.limit("5/minute")
def login():
    """
    Handle user login.

    This route accepts both GET and POST requests. For POST requests, it validates
    the submitted email and password against the database. If successful, it creates
    a session for the user and redirects to the appropriate page. If unsuccessful,
    it redirects to the login page with an error message.

    Returns:
    - str: HTML content to be rendered, redirecting to the appropriate page based on login success or failure.
    """

    email = werkzeug.utils.escape(request.form['email'])
    password = werkzeug.utils.escape(request.form['password'])

    # Check if "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and len(email.strip()) > 0 and len(password.strip()) > 0:

        mydb, mycursor = db_connection()
        sql = "SELECT user.id, \
               CASE \
                   WHEN image IS NOT NULL AND image <> '' \
                   THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) \
                   WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' \
                   THEN color \
                   ELSE '#176713' \
               END AS user_image, \
               CASE \
                   WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') \
                   THEN username \
                   ELSE CONCAT(first_name, ' ', last_name) \
               END AS username, \
               user.email, user.account_id, name, user.is_admin, user.is_manager \
               FROM user \
               LEFT JOIN user_image ON user_id = user.id \
               LEFT JOIN account ON user.account_id = account.id \
               WHERE email = %s AND password = %s"

        # Decode hash
        password = hashlib.sha1(password.encode()).hexdigest()
        params = (email, password)

        try:
            mycursor.execute(sql, params)
            lfi_user = mycursor.fetchone()

            if lfi_user:
                # Create session data
                session['loggedin'] = True
                session['id'] = lfi_user[0]
                session['user_image'] = lfi_user[1]
                session['username'] = lfi_user[2]
                session['email'] = lfi_user[3]
                session['accountId'] = lfi_user[4]
                session['accountName'] = '' if lfi_user[5] is None else lfi_user[5]
                session['is_admin'] = lfi_user[6]
                session['is_manager'] = lfi_user[7]
                session['logout_redirect'] = False

                # Generate and store JWT token in the session
                jwt_token = generate_jwt()
                session['jwt_token'] = jwt_token

                msg = 'Logged in successfully!'
                msgClass = 'alert alert-success'
                return render_template('sites.html', userId=session['id'], username=session['username'],
                                       user_image=session['user_image'], accountId=session['accountId'],
                                       accountName=session['accountName'], is_admin=session['is_admin'],
                                       is_manager=session['is_manager'], msg=msg, msgClass=msgClass,
                                       jwt_token=jwt_token)
            else:
                # Account doesn't exist or username/password incorrect
                msg = 'Incorrect username/password!'
                msgClass = 'alert alert-danger'
                return render_template('login.html', msg=msg, msgClass=msgClass)
        except Exception as e:
            # Log the error or provide more details
            print(f"Error during login: {e}")
            msg = 'An error occurred during login.'
            msgClass = 'alert alert-danger'
            return render_template('login.html', msg=msg, msgClass=msgClass)
        finally:
            mydb.close()
    else:
        # Redirect to the login page for GET requests
        return render_template('login.html', msg="", msgClass="")


# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route('/logout')
def logout():
    """
    Handle the user logout process by clearing session data and performing redirection.

    This route first checks if a 'logout_redirect' URL is set in the session. If so,
    it redirects to the specified URL. Otherwise, it clears the session data to log the user out 
    and then redirects them to the login page.

    The function clears various session keys related to user authentication and preferences.

    Returns:
    - Response: A redirect response to either the 'logout_redirect' URL or the login page.
    """
    logout_redirect = session.get('logout_redirect', False)

    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('user_image', None)
    session.pop('email', None)
    session.pop('accountId', None)
    session.pop('accountName', None)
    session.pop('is_admin', None)
    session.pop('is_manager', None)
    session.pop('jwt_token', None)
    session.pop('logout_redirect', None)

    if logout_redirect is not False and is_valid_url(logout_redirect):
        return redirect(logout_redirect)

    # Redirect to login page
    return render_template('login.html', msg="", msgClass="")

# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

def is_valid_url(url):
    """
    Validate the given URL.

    This function uses urllib.parse.urlparse to parse the URL and checks if it has both a scheme
    (like 'http', 'https') and a netloc (like 'www.example.com'). It's a basic validation to ensure
    the URL's structure is correct and can be particularly useful for validating redirect URLs.

    Parameters:
    - url (str): The URL string to be validated.

    Returns:
    - bool: True if the URL has both a scheme and a netloc, False otherwise.
    """
    parsed = urlparse(url)
    return bool(parsed.scheme) and bool(parsed.netloc)

# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route("/list_lfi_users")
@login_required
def api_list_lfi_users():
    """
    Render the page listing LFI users.

    This route requires the user to be logged in. It renders the 'list_lfi_users.html' template,
    displaying information about the logged-in user, including username, user image, account ID,
    account name, admin status, and manager status.

    Returns:
    - str: HTML content to be rendered, displaying the list of LFI users page.
    """
    return render_template('list_lfi_users.html', username=session['username'],
                           user_image=session['user_image'], accountId=session['accountId'],
                           accountName=session['accountName'], is_admin=session['is_admin'],
                           is_manager=session['is_manager'])


# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route("/api/get_lfi_users/<accountId>")
@login_required
def api_get_lfi_users(accountId):
    """
    Retrieve a list of LFI users in JSON format for a specific account.

    This route requires the user to be logged in. It queries the database for LFI users,
    formats the data into a JSON response, and returns it. If the account ID is specified,
    it retrieves users for that specific account; otherwise, it retrieves users for all accounts
    except the admin account.

    Parameters:
    - accountId (str): The ID of the account for which to retrieve users.

    Returns:
    - Response: JSON response containing a list of LFI users for the specified account.
    """
    mydb, mycursor = db_connection()

    if accountId == 1:
        mycursor.execute("SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE user.is_admin <> 1 AND account.active = 1")
    else:
        sql = "SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE user.is_admin <> 1 AND account.active = 1 AND account.id = %s"
        val = (accountId,)
        mycursor.execute(sql, val)
    users = mycursor.fetchall()

    usersLst = [{"id": singleUser[0], "user_image": singleUser[1], "username": singleUser[2], "email": singleUser[3],
                 "account_id": singleUser[4], "account_name": singleUser[5], "is_admin": singleUser[6],
                 "is_manager": singleUser[7]} for singleUser in users]

    # Create JSON
    jsonR = {"users": usersLst}

    mydb.close()
    return jsonify(jsonR)


# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route("/api/get_lfi_admin_users/<accountId>")
@login_required
def api_get_lfi_admin_users(accountId):
    """
    Retrieve a list of LFI admin users in JSON format for a specific account.

    This route requires the user to be logged in. It queries the database for LFI admin users,
    formats the data into a JSON response, and returns it. If the account ID is specified,
    it retrieves admin users for that specific account; otherwise, it retrieves admin users
    for all accounts.

    Parameters:
    - accountId (str): The ID of the account for which to retrieve admin users.

    Returns:
    - Response: JSON response containing a list of LFI admin users for the specified account.
    """
    mydb, mycursor = db_connection()

    if accountId == 1:
        mycursor.execute("SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE user.is_admin = 1 AND account.active = 1")
    else:
        sql = "SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE user.is_admin = 1 AND account.active = 1 AND account.id = %s"
        val = (accountId,)
        mycursor.execute(sql, val)
    users = mycursor.fetchall()

    usersLst = [{"id": singleUser[0], "user_image": singleUser[1], "username": singleUser[2], "email": singleUser[3],
                 "account_id": singleUser[4], "account_name": singleUser[5], "is_admin": singleUser[6],
                 "is_manager": singleUser[7]} for singleUser in users]

    # Create JSON
    jsonR = {"users": usersLst}
    mydb.close()
    return jsonify(jsonR)


# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route("/api/get_all_users/<accountId>")
@login_required
def api_get_all_users(accountId):
    """
    Retrieve a list of all LFI users in JSON format for a specific account.

    This route requires the user to be logged in. It queries the database for all LFI users,
    formats the data into a JSON response, and returns it. If the account ID is specified,
    it retrieves all users for that specific account; otherwise, it retrieves all users
    for all accounts.

    Parameters:
    - accountId (str): The ID of the account for which to retrieve all users.

    Returns:
    - Response: JSON response containing a list of all LFI users for the specified account.
    """
    mydb, mycursor = db_connection()

    if accountId == 1:
        mycursor.execute("SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE account.active = 1")
    else:
        sql = "SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE account.active = 1 AND account.id = %s"
        val = (accountId,)
        mycursor.execute(sql, val)
    users = mycursor.fetchall()

    usersLst = [{"id": singleUser[0], "user_image": singleUser[1], "username": singleUser[2], "email": singleUser[3],
                 "account_id": singleUser[4], "account_name": singleUser[5], "is_admin": singleUser[6],
                 "is_manager": singleUser[7]} for singleUser in users]

    # Create JSON
    jsonR = {"users": usersLst}
    mydb.close()
    return jsonify(jsonR)


# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route("/api/get_single_user/<accountId>/<is_admin>/<thisUserId>")
@login_required
def api_get_single_user(accountId, is_admin, thisUserId):
    """
    Retrieve details of a single LFI user in JSON format.

    This route requires the user to be logged in. It queries the database for details
    of a single LFI user based on the specified account ID, admin status, and user ID.
    The data is then formatted into a JSON response and returned.

    Parameters:
    - accountId (str): The ID of the account for which to retrieve the user.
    - is_admin (str): The admin status indicating whether to retrieve an admin user.
    - thisUserId (str): The ID of the user to retrieve details for.

    Returns:
    - Response: JSON response containing details of the specified LFI user.
    """
    mydb, mycursor = db_connection()

    if accountId == 1:
        if is_admin == 1:
            mycursor.execute("SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE AND account.active = 1")
        else:
            mycursor.execute("SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id AND user.id = %s WHERE AND account.active = 1", (thisUserId,))
    else:
        if is_admin == 1:
            sql = "SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id WHERE account.active = 1 AND account.id = %s"
            val = (accountId,)
        else:
            sql = "SELECT user.id, CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username ELSE CONCAT(first_name, ' ', last_name) END AS username, user.email, user.account_id, name, user.is_admin, user.is_manager FROM user LEFT JOIN user_image ON user_id = user.id LEFT JOIN account ON user.account_id = account.id AND user.id = %s WHERE account.active = 1 AND account.id = %s"
            val = (thisUserId, accountId)
        mycursor.execute(sql, val)
    users = mycursor.fetchall()

    usersLst = [{"id": singleUser[0], "user_image": singleUser[1], "username": singleUser[2], "email": singleUser[3],
                 "account_id": singleUser[4], "account_name": singleUser[5], "is_admin": singleUser[6],
                 "is_manager": singleUser[7]} for singleUser in users]

    # Create JSON
    jsonR = {"users": usersLst}
    mydb.close()
    return jsonify(jsonR)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@main.route('/api/add_lfi_user', methods=['POST'])
@login_required
def api_add_lfi_user():
    """
    Add a new LFI user to the database via a POST request.

    This route requires the user to be logged in. It retrieves user information
    from the POST parameters, including first name, last name, email, account ID,
    account name, admin status, manager status, and password. It then inserts the
    user data into the database and returns the newly created user's details in JSON format.

    Returns:
    - Response: JSON response containing the details of the newly created LFI user.
    """
    if request.method == 'POST':
        # Get post params
        first_name = werkzeug.utils.escape(request.form["first_name"])
        last_name = werkzeug.utils.escape(request.form["last_name"])
        email = werkzeug.utils.escape(request.form["email"])
        account_id = werkzeug.utils.escape(request.form["account_id"])
        account_name = werkzeug.utils.escape(request.form["account_name"])
        is_admin = werkzeug.utils.escape(request.form["is_admin"])
        is_manager = werkzeug.utils.escape(request.form["is_manager"])
        password = werkzeug.utils.escape(request.form["password"])
        password = hashlib.sha1(password.encode())

        mydb, mycursor = db_connection()

        # Run SQL Command
        insert_user_query = "INSERT INTO user (username, password, email, account_id, is_admin, is_manager) VALUES (%s, %s, %s, %s, %s, %s)"
        insert_user_values = (email, password.hexdigest(), email, account_id, is_admin, is_manager)
        mycursor.execute(insert_user_query, insert_user_values)
        mydb.commit()

        select_user_query = "SELECT id FROM user WHERE email = %s"
        select_user_value = (email,)
        mycursor.execute(select_user_query, select_user_value)
        this_user_id = str(mycursor.fetchone()[0])

        insert_user_image_query = "INSERT INTO user_image (user_id, first_name, last_name) VALUES (%s, %s, %s)"
        insert_user_image_values = (this_user_id, first_name, last_name)
        mycursor.execute(insert_user_image_query, insert_user_image_values)
        mydb.commit()

        # Return fields back to view
        jsonR = {"id": this_user_id, "image": "#176713", "first_name": first_name, "last_name": last_name, "email": email, "account_id": account_id, "account_name": account_name, "is_admin": is_admin, "is_manager": is_manager}
        mydb.close()
        return jsonify(jsonR)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@main.route('/api/update_lfi_user', methods=['POST'])
@login_required
def api_update_lfi_user():
    """
    Update an existing LFI user in the database via a POST request.

    This route requires the user to be logged in. It retrieves user information
    from the POST parameters, including the original user name, email, admin status,
    and manager status, as well as the updated user name, email, admin status, and
    manager status. It then updates the user data in the database and returns the
    updated user details in JSON format.

    Returns:
    - Response: JSON response containing the details of the updated LFI user.
    """
    if request.method == 'POST':
        # Get post params
        original_user_name = werkzeug.utils.escape(request.form.get("original_name"))
        original_email = werkzeug.utils.escape(request.form.get("original_email"))
        new_user_name = werkzeug.utils.escape(request.form.get("new_user_name"))
        new_email = werkzeug.utils.escape(request.form.get("new_email"))
        new_is_admin = werkzeug.utils.escape(request.form.get("new_is_admin"))
        new_is_manager = werkzeug.utils.escape(request.form.get("new_is_manager"))

        mydb, mycursor = db_connection()

        # Run SQL Command
        cmd = "UPDATE user SET username=%s, email=%s, is_admin=%s, is_manager=%s WHERE email=%s"
        values = (new_user_name, new_email, new_is_admin, new_is_manager, original_email)
        mycursor.execute(cmd, values)
        mydb.commit()

        # Return fields back to view
        jsonR = {"username": new_user_name, "email": new_email, "is_admin": new_is_admin, "is_manager": new_is_manager}
        mydb.close()
        return jsonify(jsonR)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@main.route('/api/delete_lfi_users', methods=['POST'])
@login_required
def api_delete_lfi_users():
    """
    Delete LFI users from the database via a POST request.

    This route requires the user to be logged in. It retrieves user information
    from the POST parameters, including the users to be deleted and the account ID.
    It then deletes the specified users from the database and returns details of
    the deleted users in JSON format.

    Returns:
    - Response: JSON response containing details of the deleted LFI users.
    """
    if request.method == 'POST':
        # Get post params
        users_to_delete = werkzeug.utils.escape(request.form.get("users_to_delete"))
        account_id = werkzeug.utils.escape(request.form.get("account_id"))

        if users_to_delete == "":
            jsonR = {"users_to_delete": "None provided", "action": "none"}
            return jsonify(jsonR)

        users_to_delete = users_to_delete.replace("\\", "\\\\")
        users_to_delete = "'" + users_to_delete.replace(",", "','") + "'"

        mydb, mycursor = db_connection()

        # Run SQL Command
        cmd = "DELETE FROM user WHERE account_id = %s AND id IN (%s)"
        values = (account_id, users_to_delete)
        mycursor.execute(cmd, values)
        mydb.commit()

        # Return fields back to view
        jsonR = {"users_to_delete": users_to_delete, "action": "deleted"}
        mydb.close()
        return jsonify(jsonR)


# ------------------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------ #

@main.route('/api/files/<path:filename>')
@login_required
def api_uploaded_files(filename):
    """
    Serve uploaded files from the specified directory.

    This route requires the user to be logged in. It takes a filename as a path parameter
    and serves the corresponding file from the configured files upload folder.

    Parameters:
    - filename (str): The name of the file to be served.

    Returns:
    - Response: The file to be served from the specified directory.
    """
    return send_from_directory(os.path.join(Config.FILES_UPLOAD_FOLDER, filename))


@main.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """
    Handle file uploads via a POST request.

    This route requires the user to be logged in. It retrieves the uploaded file
    from the request and saves it to the appropriate folder based on the file type
    (image or PDF). The file path and URL are then returned in JSON format.

    Returns:
    - Response: JSON response containing the details of the uploaded file.
    """
    uploaded_file = werkzeug.utils.secure_filename(request.files.get('upload'))
    lastIndexOfFileNamePath = werkzeug.utils.escape(request.form.get('lastIndexOfFileNamePath'))

    if uploaded_file is None:
        uploaded_file = request.files.getlist('files[]')[0]

    extension = uploaded_file.filename.split('.')[-1].lower()
    if extension.lower() not in ['jpg', 'gif', 'png', 'jpeg', 'pdf']:
        return jsonify(message='Image or PDF only!')

    imagePathToCheck = Config.IMAGES_WEBPATH.replace(Config.PREVIEW_SERVER, '')
    if lastIndexOfFileNamePath and imagePathToCheck not in lastIndexOfFileNamePath:
        pathToSave = Config.WEBSERVER_FOLDER
        webPathToSave = lastIndexOfFileNamePath.replace(Config.MAIN_SERVER, '').replace(Config.PREVIEW_SERVER, '')
        file_path = (pathToSave + webPathToSave + uploaded_file.filename).replace('//', '/')
        fileToReturn = file_path.replace(pathToSave, Config.PREVIEW_SERVER + "/")
    else:
        pathToSave = Config.FILES_UPLOAD_FOLDER
        pathToSave = pathToSave.replace('//', '/')
        webPathToSave = Config.MAIN_SERVER + Config.IMAGES_WEBPATH
        file_path = os.path.join(pathToSave, uploaded_file.filename.lower().replace(' ', '-'))
        fileToReturn = webPathToSave + '/' + uploaded_file.filename.lower().replace(' ', '-')

    # set the file path
    uploaded_file.save(file_path)
    return jsonify({
        "uploaded": 1,
        "fileName": os.path.basename(file_path),
        "url": fileToReturn
    })


def uniquify(path):
    """
    Ensure the uniqueness of a file path by appending a numerical counter.

    Parameters:
    - path (str): The original file path.

    Returns:
    - str: A unique file path by appending a numerical counter if necessary.
    """
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + "-(" + str(counter) + ")" + extension
        counter += 1

    return path


@main.route("/temp/fileupload", methods=['GET'])
@login_required
def temp_view_upload():
    """
    Render the template for temporary file upload view.

    This route renders the HTML template "temp_fileupload.html" when accessed via
    a GET request. The route requires the user to be logged in.

    Returns:
    - Response: The rendered template for the temporary file upload view.
    """
    return render_template("temp_fileupload.html")


@main.route("/temp/fileupload_api", methods=["POST"])
@login_required
def temp_api_upload():
    """
    Handle the API endpoint for uploading files to temporary storage.

    This route processes a POST request containing a file upload. It retrieves
    the folder and file information from the request, sanitizes the names, creates
    a local folder if it doesn't exist, and saves the file to disk. It then
    transfers the file to deployment servers using SCP (Secure Copy Protocol).

    Parameters:
    - folder (str): The destination folder for the uploaded file.
    - file (FileStorage): The uploaded file.

    Returns:
    - str: A message indicating the success of the file upload, along with local,
      remote, and live URLs for reference.
    """
    folder = werkzeug.utils.escape(request.form.get("folder"))
    file = werkzeug.utils.escape(request.files["file"])
    filename = file.filename

    folder = re.sub(r'[^a-zA-Z0-9\-._\/]', '_', folder)
    filename = re.sub(r'[^a-zA-Z0-9\-._\/]', '_', filename)

    # Remove "/"
    folder = folder.lstrip("/") if folder.startswith("/") else folder
    filename = filename.lstrip("/") if filename.startswith("/") else filename

    # Create local folder if it does not exist
    folder_path = os.path.join(Config.WEBSERVER_FOLDER, folder)
    os.makedirs(folder_path, exist_ok=True)

    # Save file to disk
    local_path = os.path.join(folder_path, filename)
    file.save(local_path)

    # SCP to deployment servers
    remote_paths = []
    live_urls = []
    preview_url = Config.PREVIEW_SERVER + "/" if not Config.PREVIEW_SERVER.endswith("/") else Config.PREVIEW_SERVER
    preview_url = preview_url + os.path.join(folder, filename)

    for srv in Config.DEPLOYMENTS_SERVERS:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
        with ssh.open_sftp() as scp:
            remote_path = os.path.join(srv["remote_path"], folder, filename)
            remote_paths.append(remote_path)
            webserver_url = srv["webserver_url"] + "/" if not srv["webserver_url"].endswith("/") else srv["webserver_url"]
            live_urls.append(webserver_url + os.path.join(folder, filename))
            folder_path = os.path.dirname(remote_path)
            ssh.exec_command("if not exist \"" + folder_path + "\" mkdir \"" + folder_path + "\" else mkdir -p " + folder_path)
            scp.put(local_path, remote_path)

    return "File uploaded successfully.<br>" + local_path + "<br>" + "<br>".join(remote_paths) + "<br>" + "<br>".join(live_urls) + "<br>" + preview_url
