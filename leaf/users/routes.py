import hashlib

import werkzeug.utils
from flask import render_template, Blueprint, jsonify, request, session

from leaf import Config
from leaf.decorators import login_required, admin_required
from .models import get_users_data, add_user_to_database, edit_user_to_database, delete_user_to_database

users = Blueprint('users', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@users.route("/users")
@login_required
@admin_required
def view_users():
    """
    Render the users page.

    Returns:
        flask.Response: Rendered HTML page with user information.
    """
    try:
        return render_template('users.html', email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], site_notice=Config.SITE_NOTICE)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@users.route('/api/get_users')
@login_required
@admin_required
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


@users.route('/user/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """
    API endpoint to add a new user.

    Returns:
        flask.Response: JSON response containing the result of adding a new user.
    """

    try:
        # Get post params
        username = str(werkzeug.utils.escape(request.form.get("username", type=str)))
        email = str(werkzeug.utils.escape(request.form.get("email", type=str)))
        is_admin = int(werkzeug.utils.escape(request.form.get("is_admin", type=int)))
        is_manager = int(werkzeug.utils.escape(request.form.get("is_manager", type=int)))
        password = hashlib.sha1(werkzeug.utils.escape(request.form['password']).encode()).hexdigest()

        # Check if User email already exists
        users_list = get_users_data()
        user_emails = [user["email"] for user in users_list]
        if email in user_emails:
            json_response = {"error": "Email already registered"}
            return jsonify(json_response)

        # Add user to the database
        result = add_user_to_database(username, email, is_admin, is_manager, password)

        if result:
            # Return fields back to view
            json_response = {"username": username, "email": email, "is_admin": is_admin}
            return jsonify(json_response)
        else:
            return jsonify({"error": "An error occurred while adding the user"}), 500

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in add_user: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500


@users.route('/user/edit', methods=['POST'])
@login_required
@admin_required
def edit_user():
    try:
        user_id = int(werkzeug.utils.escape(request.form.get("user_id", type=int)))
        is_admin = int(werkzeug.utils.escape(request.form.get("is_admin", type=int)))
        is_manager = int(werkzeug.utils.escape(request.form.get("is_manager", type=int)))

        # Edit User from DB
        edit_user_to_database(user_id, is_admin, is_manager)

        return jsonify({"Message": "success"})
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in edit_user: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500


@users.route('/user/delete', methods=['POST'])
@login_required
@admin_required
def delete_user():
    try:
        user_id = int(werkzeug.utils.escape(request.form.get("user_id", type=int)))

        # Delete User from DB
        delete_user_to_database(user_id)

        return jsonify({"Message": "success"})
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in delete_user: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500
