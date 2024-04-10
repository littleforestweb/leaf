import hashlib

import werkzeug.utils
from flask import render_template, Blueprint, jsonify, request, session

from leaf.decorators import login_required
from .models import get_users_data, add_user_to_database, update_user_in_database, delete_users_from_database

users = Blueprint('users', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@users.route("/users")
@login_required
def view_users():
    """
    Render the users page.

    Returns:
        flask.Response: Rendered HTML page with user information.
    """
    try:
        return render_template('users.html', username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'])
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@users.route('/api/get_users')
@login_required
def api_get_users():
    """
    API endpoint to retrieve user information.

    Returns:
        flask.Response: JSON response containing user information.
    """
    try:
        # Retrieve user data from the model
        users_list = get_users_data()

        # Create JSON response
        json_response = {"users": users_list}

        return jsonify(json_response)

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in api_get_users: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@users.route('/add/user', methods=['POST'])
@login_required
def add_user():
    """
    API endpoint to add a new user.

    Returns:
        flask.Response: JSON response containing the result of adding a new user.
    """

    try:
        # Get post params
        username = werkzeug.utils.escape(request.form.get("username", type=str))
        email = werkzeug.utils.escape(request.form.get("email", type=str))
        is_admin = werkzeug.utils.escape(request.form.get("is_admin", type=str))
        is_master = werkzeug.utils.escape(request.form.get("is_master", type=str))
        password = hashlib.sha1(werkzeug.utils.escape(request.form['password']).encode()).hexdigest()

        # Add user to the database
        success = add_user_to_database(username, email, is_admin, is_master, password)

        if success:
            # Return fields back to view
            json_response = {"username": username, "email": email, "is_admin": is_admin}
            return jsonify(json_response)
        else:
            return jsonify({"error": "An error occurred while adding the user"}), 500

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in add_user: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@users.route('/update/user', methods=['POST'])
@login_required
def update_user():
    """
    API endpoint to update user information.

    Returns:
        flask.Response: JSON response containing the result of updating user information.
    """
    try:
        # Get post params
        original_user_name = werkzeug.utils.escape(request.form.get("original_user_name"))
        new_user_name = werkzeug.utils.escape(request.form.get("new_user_name"))
        new_user_email = werkzeug.utils.escape(request.form.get("new_user_email"))
        new_user_display_name = werkzeug.utils.escape(request.form.get("new_user_display_name"))

        # Update user in the database
        success = update_user_in_database(original_user_name, new_user_name, new_user_email, new_user_display_name)

        if success:
            # Return fields back to view
            json_response = {"name": new_user_name, "email": new_user_email, "display_name": new_user_display_name}
            return jsonify(json_response)
        else:
            return jsonify({"error": "An error occurred while updating the user"}), 500

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in update_user: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@users.route('/delete/users', methods=['POST'])
@login_required
def delete_users():
    """
    API endpoint to delete users.

    Returns:
        flask.Response: JSON response containing the result of deleting users.
    """
    try:
        # Get post params
        users_to_delete = werkzeug.utils.escape(request.form.get("users_to_delete"))

        if users_to_delete == "":
            json_response = {"users_to_delete": "None provided", "action": "none"}
            return jsonify(json_response)

        # Process user input
        users_to_delete = users_to_delete.replace("\\", "\\\\")
        usernames = users_to_delete.split(",")

        # Delete users from the database
        success = delete_users_from_database(usernames)

        if success:
            json_response = {"users_to_delete": users_to_delete, "action": "deleted"}
            return jsonify(json_response)
        else:
            return jsonify({"error": "An error occurred while deleting users"}), 500

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in delete_users: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500
