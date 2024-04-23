import werkzeug.utils
from flask import Blueprint, jsonify, request, session, render_template

from leaf.decorators import login_required, db_connection, admin_required
from .models import get_deployments

deployments = Blueprint('deployments', __name__)


# ---------------------------------------------------------------------------------------------------------- #

@deployments.route("/deployments")
@login_required
@admin_required
def view_deployments():
    """
    View deployments route.

    Returns:
        render_template: Rendered template for deployments.
    """
    try:
        # Render the template with user information
        return render_template('deployments.html', username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], site_notice=Config.SITE_NOTICE)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@deployments.route("/api/deployments")
@login_required
@admin_required
def api_deployments():
    """
    API endpoint to fetch deployments.

    Returns:
        jsonify: JSON response containing deployments.
    """
    try:
        # Fetch deployments data from the model
        deployments_data = get_deployments()
        # Create JSON response
        json_response = {"deployments": deployments_data}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #

@deployments.route('/delete/deployments', methods=['POST'])
@login_required
@admin_required
def delete_deployments():
    """
    Delete deployments route.

    Returns:
        jsonify: JSON response indicating the success of the delete operation.
    """
    try:
        # Get the deployment numbers to delete from the form
        deployments_to_delete = werkzeug.utils.escape(request.form.get("deployments_to_delete"))
        # Establish a database connection
        mydb, mycursor = db_connection()
        # Construct and execute the SQL command to delete deployments
        cmd = "DELETE FROM deployments WHERE deployment_number IN (%s)"
        mycursor.execute(cmd, (deployments_to_delete,))
        # Commit the changes to the database
        mydb.commit()
        # Close the database connection
        mydb.close()
        # Create a JSON response indicating the success of the operation
        json_response = {"deployments_deleted": deployments_to_delete, "action": "deleted"}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #

@deployments.route('/pause/deployments', methods=['POST'])
@login_required
@admin_required
def pause_deployments():
    """
    Pause deployments route.

    Returns:
        jsonify: JSON response indicating the success of the pause operation.
    """
    try:
        # Get the deployment numbers to pause from the form
        deployments_to_pause = werkzeug.utils.escape(request.form.get("deployments_to_pause"))
        # Establish a database connection
        mydb, mycursor = db_connection()
        # Construct and execute the SQL command to update deployment status to 'paused'
        cmd = "UPDATE deployments SET status='paused' WHERE deployment_number IN (%s) AND (status='pending' OR status='failed')"
        mycursor.execute(cmd, (deployments_to_pause,))
        # Commit the changes to the database
        mydb.commit()
        # Close the database connection
        mydb.close()
        # Create a JSON response indicating the success of the operation
        json_response = {"deployments_paused": deployments_to_pause, "action": "paused"}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #

@deployments.route('/update/deployment', methods=['POST'])
@login_required
@admin_required
def deployment_group():
    """
    Update deployment route.

    Returns:
        jsonify: JSON response indicating the success of the update operation.
    """
    try:
        # Get parameters from the form
        deployment_number = werkzeug.utils.escape(request.form.get("h_e_deployment_number"))
        new_deployment_source_server = werkzeug.utils.escape(request.form.get("e_deployment_source_server"))
        new_deployment_source_path = werkzeug.utils.escape(request.form.get("e_deployment_source_path"))
        new_deployment_target_server = werkzeug.utils.escape(request.form.get("e_deployment_target_server"))
        new_deployment_target_path = werkzeug.utils.escape(request.form.get("e_deployment_target_path"))

        # Establish a database connection
        mydb, mycursor = db_connection()

        # Update source_server_name, source_files, destination_server_name, destination_location
        cmd = f"UPDATE deployments SET source_server_name=%s, source_files=%s, destination_server_name=%s, destination_location=%s WHERE deployment_number=%s"
        mycursor.execute(cmd, (new_deployment_source_server, new_deployment_source_path, new_deployment_target_server, new_deployment_target_path, deployment_number))

        # Update source_server_ip, source_files, destination_server_ip, destination_location
        cmd = f"UPDATE deployments SET source_server_ip=%s, source_files=%s, destination_server_ip=%s, destination_location=%s WHERE deployment_number=%s"
        mycursor.execute(cmd, (new_deployment_source_server, new_deployment_source_path, new_deployment_target_server, new_deployment_target_path, deployment_number))

        # Commit the changes to the database
        mydb.commit()
        # Close the database connection
        mydb.close()

        # Create a JSON response indicating the success of the operation
        json_response = {"deployment_number": deployment_number, "action": "updated"}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
