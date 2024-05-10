import ast
import datetime
import json
import os
import re

import paramiko
import werkzeug.utils
from bs4 import BeautifulSoup
from flask import render_template, Blueprint, jsonify, request, session, url_for, send_from_directory, current_app

from leaf import decorators
from leaf.config import Config
from leaf.decorators import limiter
from leaf.decorators import login_required
from leaf.users.models import get_user_permission_level
from .models import uniquify, workflow_changed_email, upload_file_with_retry, add_workflow, is_workflow_owner, get_workflow_details, get_workflows, get_task_requests, change_status_workflow, send_mail, gen_sitemap

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
    # Get url from post params
    workflow_id = werkzeug.utils.escape(request.form.get("id"))
    action = werkzeug.utils.escape(request.form.get("status"))

    # Check if the workflow belongs to the user's account
    if not is_workflow_owner(int(workflow_id)):
        return jsonify({"error": "Forbidden"}), 403

    thisType = 1
    if werkzeug.utils.escape(request.form.get("type")):
        thisType = werkzeug.utils.escape(request.form.get("type"))
    thisType = int(thisType)

    listName = False
    if werkzeug.utils.escape(request.form.get("listName")) and werkzeug.utils.escape(request.form.get("listName")) != '':
        listName = werkzeug.utils.escape(request.form.get("listName"))

    isMenu = False

    if thisType == 4:
        isMenu = True

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    # Run SQL Command
    if action == "Approve":
        action = "Approved"
    elif action == "Reject":
        action = "Rejected"
        mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", (action, workflow_id,))
        mydb.commit()
        jsonR = {"message": "success", "action": action}
        return jsonify(jsonR)

    # Check if the user has permission
    if thisType in [1, 5, 6, 7]:
        query = "SELECT site_meta.HTMLPath FROM site_meta JOIN workflow ON site_meta.id = workflow.siteIds WHERE workflow.id = %s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        workflow_folder_path = f"/{mycursor.fetchone()[0].lstrip('/')}"
        perm_level = get_user_permission_level(session["id"], workflow_folder_path)
        if perm_level != 4:
            return jsonify({"error": "Forbidden"}), 403

    if not listName and thisType == 1:
        # Get local file path
        query = "SELECT site_meta.HTMLPath FROM site_meta JOIN workflow ON site_meta.id = workflow.siteIds WHERE workflow.id = %s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        HTMLPath = mycursor.fetchone()[0]

        for srv in Config.DEPLOYMENTS_SERVERS:
            HTMLPath = HTMLPath.strip("/")
            local_path = os.path.join(Config.WEBSERVER_FOLDER, HTMLPath)

            # Replace Preview Reference with Live webserver references
            with open(local_path) as inFile:
                data = inFile.read()
                original_content = data
            data = data.replace(Config.LEAFCMS_SERVER, srv["webserver_url"] + Config.DYNAMIC_PATH)
            with open(local_path, "w") as outFile:
                outFile.write(data)

            # Get all assets on the page
            soup = BeautifulSoup(original_content, "html5lib")
            imgAssets = [asset["src"] for asset in soup.find_all("img", {"src": lambda src: src and Config.IMAGES_WEBPATH in src})]
            pdfAssets = [asset["href"] for asset in soup.find_all("a", {"href": lambda href: href and href.endswith(".pdf") and Config.IMAGES_WEBPATH in href})]
            assets = imgAssets + pdfAssets

            # SCP Files
            remote_path = os.path.join(srv["remote_path"], HTMLPath)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if srv["pkey"] != "":
                ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                if srv["pw"] == "":
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                else:
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
            else:
                ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
            with ssh.open_sftp() as scp:
                actionResult, lp, rp = upload_file_with_retry(local_path, remote_path, scp)
                for asset in assets:
                    assetFilename = asset.split("/")[-1].strip('/')
                    assetLocalPath = os.path.join(Config.FILES_UPLOAD_FOLDER, assetFilename)
                    assetRemotePath = os.path.join(srv["remote_path"], Config.DYNAMIC_PATH.strip('/'), Config.IMAGES_WEBPATH.strip('/'), assetFilename)
                    actionResultAsset, alp, arp = upload_file_with_retry(assetLocalPath, assetRemotePath, scp)
                    if not actionResultAsset:
                        try:
                            raise Exception("Failed to SCP - " + lp + " - " + rp)
                        except Exception as e:
                            pass
                if not actionResult:
                    try:
                        raise Exception("Failed to SCP - " + lp + " - " + rp)
                    except Exception as e:
                        pass

            with open(local_path, "w") as outFile:
                outFile.write(original_content)



        # Regenerate Sitemap
        query = "SELECT site_id FROM site_meta WHERE HTMLPath = %s"
        mycursor.execute(query, [HTMLPath])
        site_id = mycursor.fetchone()[0]
        gen_sitemap(mycursor, site_id, thisType)

    elif not listName and thisType == 2:
        # do something with TASK
        pass

    elif not listName and thisType == 6:

        # Unescape HTML entities
        files_details = request.form.get("files_details")

        # Safely convert the string back to a list
        try:
            files_details = ast.literal_eval(files_details)
        except ValueError as e:
            print("Error evaluating string:", e)
            files_details = []

        # Loop through each item in the list
        for file_detail in files_details:
            file_path, _ = file_detail
            file_path = werkzeug.utils.escape(file_path)
            local_path = os.path.join(Config.WEBSERVER_FOLDER, file_path)

            # SCP to deployment servers
            remote_paths = []
            live_urls = []

            for srv in Config.DEPLOYMENTS_SERVERS:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
                with ssh.open_sftp() as scp:
                    remote_path = os.path.join(srv["remote_path"], file_path)
                    remote_paths.append(remote_path)
                    webserver_url = srv["webserver_url"] + "/" if not srv["webserver_url"].endswith("/") else srv["webserver_url"]
                    live_urls.append(webserver_url + os.path.join(file_path))
                    folder_path = os.path.dirname(remote_path)
                    ssh.exec_command("if not exist \"" + folder_path + "\" mkdir \"" + folder_path + "\" else mkdir -p " + folder_path)
                    scp.put(local_path, remote_path)

    elif listName:
        accountId = session['accountId']
        listName = ''.join(e for e in listName if e.isalnum())
        if isMenu:
            completeListName = listName + "Menu.json"
            account_list = "account_" + str(accountId) + "_menu_" + listName
        else:
            completeListName = listName + "List.json"
            account_list = "account_" + str(accountId) + "_list_" + listName

        saveByFields = werkzeug.utils.escape(request.form.get("saveByFields"))
        fieldsToSaveBy = False
        if saveByFields == '1':
            fieldsToSaveBy = werkzeug.utils.escape(request.form.get("fieldsToSaveBy"))

        # do scp for LISTS
        for srv in Config.DEPLOYMENTS_SERVERS:
            DYNAMIC_PATH = Config.DYNAMIC_PATH.strip('/')
            local_path = os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, completeListName)
            remote_path = os.path.join(srv["remote_path"], DYNAMIC_PATH, completeListName)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if srv["pkey"] != "":
                ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                if srv["pw"] == "":
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                else:
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
            else:
                ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
            with ssh.open_sftp() as scp:
                actionResult, lp, rp = upload_file_with_retry(local_path, remote_path, scp)
                if not actionResult:
                    try:
                        raise Exception("Failed to SCP - " + lp + " - " + rp)
                    except Exception as e:
                        pass

            # Save list by pre-selected field independently to speed up the front end (on preview and live environment)
            if fieldsToSaveBy:
                fieldsToSaveBy = "".join(fieldsToSaveBy)
                fieldsToSaveBy = fieldsToSaveBy.split(';')
                for singleFieldToSaveBy in fieldsToSaveBy:
                    if isMenu:
                        mycursor.execute("SELECT DISTINCT %s FROM account_%s_menu_%s", (str(singleFieldToSaveBy), str(accountId), listName,))
                    else:
                        mycursor.execute("SELECT DISTINCT %s FROM account_%s_list_%s", (str(singleFieldToSaveBy), str(accountId), listName,))

                    listCleanArray = set()
                    for fullSingleEntry in mycursor.fetchall():
                        entries = fullSingleEntry[0].split(';')
                        for singleEntry in entries:
                            listCleanArray.add(singleEntry.strip().lower())

                    final_list = list(listCleanArray)

                    for singleListItem in final_list:
                        if isMenu:
                            mycursor.execute("SELECT * FROM account_%s_menu_%s WHERE LOWER(%s) LIKE '%%s%' ", (str(accountId), listName, singleFieldToSaveBy, singleListItem,))
                        else:
                            mycursor.execute("SELECT * FROM account_%s_list_%s WHERE LOWER(%s) LIKE '%%s%' ", (str(accountId), listName, singleFieldToSaveBy, singleListItem,))

                        row_headers = [x[0] for x in mycursor.description]
                        fullListByCountry = mycursor.fetchall()
                        json_data_by_country = [dict(zip(row_headers, result)) for result in fullListByCountry]
                        json_data_to_write_by_country = json.dumps(json_data_by_country).replace('__BACKSLASH__TO_REPLACE__', '\\')

                        if isMenu:
                            with open(os.path.join(Config.ENV_PATH, "json_by_country", listName + "_" + singleListItem + "_Menu.json"), "w") as outFileByCountry:
                                outFileByCountry.write(json_data_to_write_by_country)
                            completeListNameByCountry = listName + "_" + singleListItem + "_" + "Menu.json"
                        else:
                            with open(os.path.join(Config.ENV_PATH, "json_by_country", listName + "_" + singleListItem + "_List.json"), "w") as outFileByCountry:
                                outFileByCountry.write(json_data_to_write_by_country)
                            completeListNameByCountry = listName + "_" + singleListItem + "_" + "List.json"

                        DYNAMIC_PATH = Config.DYNAMIC_PATH.strip('/')
                        local_path = os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, "json_by_country", completeListNameByCountry)
                        remote_path = os.path.join(srv["remote_path"], DYNAMIC_PATH, "json_by_country", completeListNameByCountry)
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        if srv["pkey"] != "":
                            ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                            if srv["pw"] == "":
                                ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                            else:
                                ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                        else:
                            ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
                        with ssh.open_sftp() as scp:
                            actionResult, lp, rp = upload_file_with_retry(local_path, remote_path, scp)
                        if not actionResult:
                            try:
                                raise Exception("Failed to SCP - " + lp + " - " + rp)
                            except Exception as e:
                                pass

            # Send Static Folder
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if srv["pkey"] != "":
                ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                if srv["pw"] == "":
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                else:
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
            else:
                ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
            for root, dirs, files in os.walk(Config.FILES_UPLOAD_FOLDER):
                for file_name in files:
                    local_path = os.path.join(root, file_name)
                    remote_path = os.path.join(srv["remote_path"], Config.DYNAMIC_PATH.strip('/'), Config.IMAGES_WEBPATH.strip('/'), file_name)
                    with ssh.open_sftp() as scp:
                        actionResult, lp, rp = upload_file_with_retry(local_path, remote_path, scp)
                    if not actionResult:
                        try:
                            raise Exception("Failed to SCP - " + lp + " - " + rp)
                        except Exception as e:
                            pass


            for srv in Config.DEPLOYMENTS_SERVERS:

                HTMLPath = werkzeug.utils.escape(request.form.get("list_item_url_path"))
                local_path = os.path.join(Config.WEBSERVER_FOLDER, HTMLPath)

                # SCP Files
                remote_path = os.path.join(srv["remote_path"], HTMLPath)
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if srv["pkey"] != "":
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                    if srv["pw"] == "":
                        ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                    else:
                        ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                else:
                    ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
                with ssh.open_sftp() as scp:
                    current_app.logger.info(local_path)
                    current_app.logger.info(remote_path)
                    actionResult, lp, rp = upload_file_with_retry(local_path, remote_path, scp)
                    
                    if not actionResult:
                        try:
                            raise Exception("Failed to SCP - " + lp + " - " + rp)
                        except Exception as e:
                            pass

            # Regenerate Sitemap
            # list_page_ids = werkzeug.utils.escape(request.form.get("site_id"))
            # list_page_ids = list_page_ids.split(",")
            # for list_page_id in list_page_ids:
            #   gen_sitemap(mycursor, list_page_id, thisType)

    if not listName and thisType == 5:
        # Get local file path
        query = "SELECT site_meta.id, site_meta.HTMLPath FROM site_meta JOIN workflow ON site_meta.id = workflow.siteIds WHERE workflow.id = %s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        res = mycursor.fetchone()
        pageId, HTMLPath = str(res[0]).split(",")[0], res[1]

        # Update page to "deleted" on db
        query = "UPDATE site_meta SET status = %s WHERE id = %s"
        params = ("-1", pageId)
        mycursor.execute(query, params)
        mydb.commit()

        # Remove from Deployment servers
        for srv in Config.DEPLOYMENTS_SERVERS:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if srv["pkey"] != "":
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                    if srv["pw"] == "":
                        ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                    else:
                        ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                else:
                    ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
                with ssh.open_sftp() as scp:
                    remote_path = os.path.join(srv["remote_path"], HTMLPath)
                    scp.remove(remote_path)
            except Exception as e:
                pass

        # Regenerate Sitemap
        query = "SELECT site_id FROM site_meta WHERE HTMLPath = %s"
        mycursor.execute(query, [HTMLPath])
        site_id = mycursor.fetchone()[0]
        gen_sitemap(mycursor, site_id, thisType)

    if not listName and thisType == 7:
        # Get local file path
        query = "SELECT site_assets.id, site_assets.path FROM site_assets JOIN workflow ON site_assets.id = workflow.siteIds WHERE workflow.id = %s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        res = mycursor.fetchone()
        assetsId, path = str(res[0]).split(",")[0], res[1]

        # Update asset to "deleted" on db
        query = "UPDATE site_assets SET status = %s WHERE id = %s"
        params = ("-1", assetsId)
        mycursor.execute(query, params)
        mydb.commit()

        # Remove from Deployment servers
        for srv in Config.DEPLOYMENTS_SERVERS:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if srv["pkey"] != "":
                    ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                    if srv["pw"] == "":
                        ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                    else:
                        ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                else:
                    ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
                with ssh.open_sftp() as scp:
                    remote_path = os.path.join(srv["remote_path"], path)
                    scp.remove(remote_path)
            except Exception as e:
                pass

    else:
        pass

    # Update on DB
    mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", (action, workflow_id))
    mydb.commit()

    jsonR = {"message": "success", "action": action}
    return jsonify(jsonR)


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
