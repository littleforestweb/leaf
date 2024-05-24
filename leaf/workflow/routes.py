import ast
import datetime
import json
import os
import re

import paramiko
import werkzeug.utils
from flask import render_template, Blueprint, jsonify, request, session, url_for, send_from_directory

from leaf import decorators
from leaf.config import Config
from leaf.decorators import limiter
from leaf.decorators import login_required
from leaf.users.models import get_user_permission_level
from .models import uniquify, workflow_changed_email, upload_file_with_retry, add_workflow, is_workflow_owner, get_workflow_details, get_workflows, get_task_requests, change_status_workflow, send_mail, gen_sitemap, gen_feed, find_page_assets, proceed_action_workflow

workflow = Blueprint("workflow", __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@workflow.route("/workflow")
@login_required
def view_workflow():
    """
    Render the workflow view.

    Returns:
        flask.Response: The rendered workflow template.
    """
    return render_template("workflow.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE)


@workflow.route("/task_requests")
@login_required
def view_task_requests():
    """
    Render the task requests view.

    Returns:
        flask.Response: The rendered task requests template.
    """
    return render_template("task_requests.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE)


@workflow.route("/assignment_form")
@login_required
def view_assignment_form():
    """
    Render the assignment form view.

    Returns:
        flask.Response: The rendered assignment form template.
    """
    return render_template("assignment_form.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE)


@workflow.route("/workflow_details")
@login_required
def view_workflow_details():
    """
    Render the workflow details view.

    Returns:
        flask.Response: The rendered workflow details template.
    """
    try:
        wid = werkzeug.utils.escape(request.args.get("id", type=str))
        
        # Get workflow details from models
        data = get_workflow_details(wid)

        return render_template("workflow_details.html", email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], data=data, site_notice=Config.SITE_NOTICE)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


@workflow.route("/api/get_workflows")
@login_required
def api_get_workflows():
    """
    Endpoint to retrieve workflows.

    Returns:
        jsonify: JSON response containing workflows.
            If successful, returns a dictionary with the "workflows" key.
            If an error occurs, returns a JSON response with an "error" key and a 500 Internal Server Error status code.
    """
    try:
        jsonR = {"workflows": get_workflows()}
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code
    return jsonify(jsonR)


@workflow.route("/api/get_task_requests")
@login_required
def api_get_task_requests():
    """
    Endpoint to retrieve Requests.

    Returns:
        jsonify: JSON response containing Requests.
            If successful, returns a dictionary with the "task_requests" key.
            If an error occurs, returns a JSON response with an "error" key and a 500 Internal Server Error status code.
    """
    try:
        jsonR = {"task_requests": get_task_requests()}
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code
    return jsonify(jsonR)


@workflow.route("/workflow/add", methods=["POST"])
@login_required
def api_add_workflow():
    """
    Endpoint for adding a workflow.

    Accepts a POST request with JSON data containing workflow details.
    Returns a JSON response with the result of the workflow addition.

    Returns:
        jsonify: JSON response with the result of the workflow addition.
    """
    try:
        # Validate and process the incoming JSON data
        json_data = request.get_json()
        json_response = add_workflow(json_data)
        return jsonify(json_response)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


@workflow.route("/workflow/change_status", methods=["POST"])
@login_required
def api_change_status_workflow():
    """
    Endpoint for changing the status of a workflow.

    Accepts a POST request with form data containing workflow ID, new status, and user to notify.
    Returns a JSON response with the result of the status change.

    Returns:
        jsonify: JSON response with the result of the status change.
    """
    try:
        workflow_id = int(werkzeug.utils.escape(request.form.get("id")))
        new_status = werkzeug.utils.escape(request.form.get("new_status"))
        user_to_notify = werkzeug.utils.escape(request.form.get("user_to_notify"))
        jsonR = change_status_workflow(workflow_id, new_status, user_to_notify)
        return jsonify(jsonR)
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


@workflow.route("/workflow/change_due_date", methods=["POST"])
@login_required
def change_due_date_workflow():
    workflow_id = werkzeug.utils.escape(request.form.get("id"))
    new_due_date = werkzeug.utils.escape(request.form.get("new_due_date"))

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    mycursor.execute("UPDATE workflow SET dueDate = %s WHERE id = %s", (new_due_date, workflow_id))
    mydb.commit()

    last_workflow_id = mycursor.lastrowid

    title = 'Leaf workflow due date changed'
    theEmailMessage = 'This task due date has been changed on Leaf CMS'

    emailToSend = workflow_changed_email(workflow_id, title, session["username"], new_due_date, "due_date_changed", theEmailMessage)

    send_mail(title, emailToSend, Config.ASSIGNED_USER_EMAIL)

    jsonR = {"message": "success", "workflow_id": str(last_workflow_id)}
    return jsonify(jsonR)


@workflow.route("/workflow/change_priority", methods=["POST"])
@login_required
def change_priority_workflow():
    workflow_id = werkzeug.utils.escape(request.form.get("id"))
    new_priority = werkzeug.utils.escape(request.form.get("new_priority"))

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    mycursor.execute("UPDATE workflow SET priority = %s WHERE id = %s", (new_priority, workflow_id))
    mydb.commit()

    last_workflow_id = mycursor.lastrowid

    title = 'Leaf workflow priority changed'
    theEmailMessage = 'This task priority has been changed on Leaf CMS'

    newPriorityString = "Standard"
    if new_priority == '2':
        newPriorityString = "Urgent"

    emailToSend = workflow_changed_email(workflow_id, title, session["username"], newPriorityString, "priority_changed", theEmailMessage)
    send_mail(title, emailToSend, Config.ASSIGNED_USER_EMAIL)

    jsonR = {"message": "success", "workflow_id": str(last_workflow_id)}
    return jsonify(jsonR)


@workflow.route("/workflow/add_new_comment", methods=["POST"])
@limiter.limit("5/minute")
@login_required
def add_new_comment_workflow():
    workflow_id = werkzeug.utils.escape(request.form.get("id"))
    user_to_notify = werkzeug.utils.escape(request.form.get("user_to_notify"))
    comments = request.form.get("comments")

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    mycursor.execute("SELECT comments FROM workflow WHERE id = %s", (workflow_id,))
    result = mycursor.fetchone()
    latestComments = result[0]

    theDateNow = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if latestComments:
        comments = latestComments + ("|__SepparateComments__|" + (comments if comments else "") + "|__TheUserCommentStarts__|" + session["email"] + "|__TheUserCommentStarts__|" + theDateNow)
    else:
        comments = comments if comments else ""

    mycursor.execute("UPDATE workflow SET comments = %s WHERE id = %s", (comments, workflow_id,))
    mydb.commit()

    last_workflow_id = mycursor.lastrowid

    title = 'Leaf workflow new comment added'
    theEmailMessage = 'You have a new comment on Leaf CMS'

    emailToSend = workflow_changed_email(workflow_id, title, session["username"], comments, "new_comment", theEmailMessage)
    send_mail(title, emailToSend, Config.ASSIGNED_USER_EMAIL)
    send_mail(title, emailToSend, user_to_notify)

    jsonR = {"message": "success", "workflow_id": str(last_workflow_id)}

    mydb.close()
    return jsonify(jsonR)


@workflow.route("/workflow/delete", methods=["POST"])
@login_required
def delete_workflow():
    workflow_id = werkzeug.utils.escape(request.form.get("entries_to_delete"))

    # Check if the workflow belongs to the user's account
    if not is_workflow_owner(int(workflow_id)):
        return jsonify({"error": "Forbidden"}), 403

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    mycursor.execute("DELETE FROM workflow WHERE id = %s", (workflow_id,))
    mydb.commit()
    workflow_id = mycursor.lastrowid

    jsonR = {"message": "success", "workflow_id": str(workflow_id)}
    return jsonify(jsonR)


@workflow.route("/workflow/action", methods=["POST"])
@login_required
def action_workflow():
    return jsonify(proceed_action_workflow(request))


@workflow.route('/api/workflow_files/<path:filename>')
@login_required
def api_uploaded_workflow_files(filename):
    return send_from_directory(os.path.join(Config.WORKFLOW_FILES_UPLOAD_FOLDER, filename))


@workflow.route('/api/upload_workflow_attachments', methods=['POST'])
@login_required
def api_upload_workflow_attachments():
    uploaded_file = request.files.get('upload')

    if uploaded_file is None:
        uploaded_file = request.files.getlist('files[]')[0]

    extension = uploaded_file.filename.split('.')[-1].lower()
    if extension.lower() not in ['jpg', 'gif', 'png', 'jpeg', 'pdf', 'docx', 'doc']:
        return jsonify(message="['jpg', 'gif', 'png', 'jpeg', 'pdf', 'docx', 'doc'] or PDF only!")

    pathToSave = Config.WORKFLOW_FILES_UPLOAD_FOLDER
    pathToSave = pathToSave.replace('//', '/')
    webPathToSave = Config.WORKFLOW_IMAGES_WEBPATH
    file_path = uploaded_file.filename.lower()
    file_path = file_path.replace(extension, "")
    file_path = os.path.join(pathToSave, re.sub(r'[^a-zA-Z0-9_]', '', file_path) + "." + extension)
    fileToReturn = file_path.replace(pathToSave, webPathToSave)

    file_path = uniquify(file_path)
    # set the file path
    uploaded_file.save(file_path)
    url = url_for('workflow.api_uploaded_workflow_files', filename=file_path)
    return jsonify({
        "uploaded": 1,
        "fileName": os.path.basename(file_path),
        "url": fileToReturn.replace("/leaf/", "/")
    })
