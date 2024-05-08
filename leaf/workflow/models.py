import datetime
import os
import smtplib
import subprocess
import time
import xml.etree.ElementTree as ET
from email.message import EmailMessage
from urllib.parse import unquote, urljoin

import paramiko
from flask import session

from leaf import Config
from leaf import decorators
from leaf.users.models import get_user_permission_level


def is_workflow_owner(workflow_id):
    """
    Check if the workflow ID belongs to the user's account ID.

    Args:
        workflow_id (int): The ID of the workflow.

    Returns:
        bool: True if the workflow belongs to the user's account, False otherwise.
    """
    try:
        mydb, mycursor = decorators.db_connection()
        workflow_id = int(workflow_id)

        # Check if the workflow ID belongs to the user's account
        query = "SELECT COUNT(*) FROM workflow WHERE id=%s AND accountId=%s"
        params = (workflow_id, session["accountId"])
        mycursor.execute(query, params)
        count = mycursor.fetchone()[0]

        mydb.close()

        return count > 0

    except Exception as e:
        # Handle exceptions (e.g., log the error)
        print(f"An error occurred: {e}")
        return False


def get_workflow_details(workflow_id):
    """
    Get details for a specific workflow.

    Args:
        workflow_id (str): The ID of the workflow.

    Returns:
        dict: Workflow details.
    """
    mydb, mycursor = decorators.db_connection()

    try:
        query = "SELECT workflow.id, workflow.startUser, workflow.title, workflow.assignEditor, workflow.dueDate, workflow.tags, workflow.comments, workflow.submittedDate, workflow.type, workflow.status, workflow.siteIds, workflow.attachments, workflow.priority, workflow.listName, workflow.lastEdited FROM workflow WHERE workflow.id=%s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        results = mycursor.fetchone()

        # Set workflow_data
        workflow_data = extract_workflow_data(results)
        user = get_user_details(workflow_data["startUser"], mycursor)
        workflow_data["startUser"], workflow_data["startUserEmail"] = user["username"], user["email"]
        workflow_data["assignEditor"] = get_user_details(workflow_data["assignEditor"], mycursor)["email"]
        process_specific_workflow_type(workflow_data, mycursor)

        # Get workflow folder
        if workflow_data["type"] in [1, 5, 6, 7]:
            query = "SELECT sm.HTMLPath FROM site_meta sm WHERE sm.id=%s"
            params = (workflow_data["siteIds"],)
            mycursor.execute(query, params)
            workflow_folder_path = f"/{mycursor.fetchone()[0].lstrip('/')}"

            # Get user Permission Level for the workflow folder
            user_permission_level = get_user_permission_level(session["id"], workflow_folder_path)
            workflow_data["user_permission_level"] = user_permission_level
        else:
            workflow_data["user_permission_level"] = 4

        mydb.close()
        return workflow_data
    except Exception as e:
        # Handle the exception (e.g., log the error)
        raise e


def extract_workflow_data(results):
    """
    Extract and format workflow data from the query results.

    Args:
        results (tuple): Workflow query results.

    Returns:
        dict: Formatted workflow data.
    """
    workflow_data = {
        "id": results[0],
        "startUser": results[1],
        "title": results[2],
        "assignEditor": results[3],
        "dueDate": results[4],
        "tags": results[5],
        "comments": results[6].split("|__SepparateComments__|")[::-1] if results[6] else "",
        "submittedDate": results[7],
        "type": results[8],
        "status": results[9],
        "siteIds": results[10],
        "attachments": results[11],
        "priority": results[12],
        "listName": results[13],
        "lastEdited": results[14],
        "statusMessage": "On track",
        "siteTitles": "",
        "siteUrl": "",
        "siteInfo": {}
    }

    return workflow_data


def get_user_details(user_id, mycursor):
    """
    Get details for a user by user ID.

    Args:
        user_id (str): User ID.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.

    Returns:
        dict: User details (username, email).
    """
    # First query to get username and email
    query = "SELECT username, email FROM user WHERE id = %s OR email = %s"
    params = [user_id, user_id]
    mycursor.execute(query, params)
    user_result = mycursor.fetchone()
    username, email = user_result[0], user_result[1]

    # Check if user has an display_name
    display_name = username
    image_query = "SELECT display_name FROM user_image WHERE user_id = %s"
    mycursor.execute(image_query, (user_id,))
    display_name_result = mycursor.fetchone()
    if display_name_result:
        display_name = display_name_result[0]

    return {"username": username, "email": email, "display_name": display_name}


def process_specific_workflow_type(workflow_data, mycursor):
    """
    Process workflow details based on specific workflow type.

    Args:
        workflow_data (dict): Workflow details.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.
    """
    if workflow_data["type"] == 1 or workflow_data["type"] == 5:
        process_type_1_or_5(workflow_data, mycursor)
    elif workflow_data["type"] == 6 or workflow_data["type"] == 7:
        process_type_6_or_7(workflow_data, mycursor)
    elif str(workflow_data["type"]) == "3":
        process_type_3(workflow_data, mycursor)


def process_type_1_or_5(workflow_data, mycursor):
    """
    Process workflow details for type 1 or 5.

    Args:
        workflow_data (dict): Workflow details.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.
    """
    if workflow_data["siteIds"]:
        site_titles = ""
        site_id = workflow_data["siteIds"].strip()

        query = "SELECT site_meta.title, site_meta.url, site_meta.HTMLPath FROM site_meta WHERE id=%s"
        params = (site_id,)

        mycursor.execute(query, params)
        result = mycursor.fetchone()

        site_title = result[0]

        site_titles += site_title + ";"
        site_titles = site_titles[0:-1]
        workflow_data["siteTitles"] = unquote(site_titles)
        workflow_data["siteIds"] = workflow_data["siteIds"]
        workflow_data["siteUrl"] = urljoin(Config.PREVIEW_SERVER, result[2])
        workflow_data["liveUrl"] = urljoin(Config.DEPLOYMENTS_SERVERS[0]["webserver_url"], result[2])

        workflow_data["siteInfo"] = dict(zip(workflow_data["siteIds"], workflow_data["siteTitles"]))


def process_type_6_or_7(workflow_data, mycursor):
    """
    Process workflow details for type 6.

    Args:
        workflow_data (dict): Workflow details.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.
    """
    if workflow_data["siteIds"]:
        filesIds = workflow_data["siteIds"].split(",")

        # Create a string with placeholders for each ID in the list
        placeholders = ', '.join(['%s'] * len(filesIds))

        # Construct the SQL query
        query = f"SELECT site_assets.path, site_assets.filename FROM site_assets WHERE id IN ({placeholders})"

        # Execute the query
        mycursor.execute(query, tuple(filesIds))  # Convert list to tuple for the query parameters
        result = mycursor.fetchall()  # fetchall if you expect more than one row, fetchone if you expect only one

        workflow_data["files_details"] = result
        workflow_data["preview_server"] = Config.PREVIEW_SERVER


def process_type_3(workflow_data, mycursor):
    """
    Process workflow details for type 3.

    Args:
        workflow_data (dict): Workflow details.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.
    """
    if workflow_data["siteIds"]:
        site_id = workflow_data["siteIds"]
        workflow_data["siteTitles"] = ""

        table_name = f"account_{session['accountId']}_list_configuration"
        mycursor.execute(f"SELECT * FROM %s WHERE main_table = %s", (table_name, workflow_data["listName"],))
        result_list = mycursor.fetchone()

        if result_list and len(result_list) > 0:
            lists_config = result_list
            this_template = lists_config[2]
            this_parameters = lists_config[3]
            this_parameters_to_grab = lists_config[4]

            query = f"SELECT %s FROM account_%s_list_%s WHERE id=%s"
            params = (this_parameters_to_grab, session['accountId'], workflow_data['listName'], site_id,)
            mycursor.execute(query, params)
            fields_to_link = mycursor.fetchone()[0]

            workflow_data["siteTitles"] = fields_to_link
            workflow_data["siteUrl"] = Config.PREVIEW_SERVER + Config.DYNAMIC_PATH + f"{this_template}.html?{this_parameters}={fields_to_link}"


def get_workflows():
    """
    Retrieve workflows from the database and enrich the data with additional information.

    Returns:
        list: List of dictionaries representing workflows with additional details.
    """
    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    try:
        mycursor.execute("SELECT id, title, startUser, assignEditor, dueDate, comments, submittedDate, type, status, tags, attachments, priority, listName FROM workflow WHERE type != 2 AND assignEditor = %s AND accountId = %s", (session["id"], session["accountId"],))
        workflowsLst = [
            {
                "id": wf[0],
                "title": wf[1],
                "startUser": wf[2],
                "assignEditor": wf[3],
                "dueDate": wf[4],
                "comments": wf[5],
                "submittedDate": wf[6],
                "type": wf[7],
                "status": wf[8],
                "tags": wf[9],
                "attachments": wf[10],
                "priority": wf[11],
                "listName": wf[12]
            } for wf in mycursor.fetchall()
        ]

        for entry in workflowsLst:
            # Get Start User
            user = get_user_details(entry["startUser"], mycursor)
            startUser = f'({user["display_name"]}) {user["email"]}'
            entry["startUser"] = startUser

            # Get Assign User
            user = get_user_details(entry["assignEditor"], mycursor)
            assignEditor = f'({user["display_name"]}) {user["email"]}'
            entry["assignEditor"] = assignEditor

            # Check Status Message
            current_datetime = datetime.datetime.now()
            due_datetime = datetime.datetime.strptime(str(entry["dueDate"]), '%Y-%m-%d %H:%M:%S')
            check_24_hours_before = current_datetime - datetime.timedelta(hours=24)
            status_message = "On track"
            if due_datetime < current_datetime:
                status_message = "Overdue"
            if check_24_hours_before < due_datetime < current_datetime:
                status_message = "At risk"
            entry["statusMessage"] = status_message

        return workflowsLst
    except Exception as e:
        # Log the error or handle it as needed

        raise e
    finally:
        mydb.close()


def get_task_requests():
    """
    Retrieve workflows from the database and enrich the data with additional information.

    Returns:
        list: List of dictionaries representing workflows with additional details.
    """
    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    try:
        mycursor.execute("SELECT id, title, startUser, assignEditor, dueDate, comments, submittedDate, type, status, tags, attachments, priority, listName FROM workflow WHERE type = 2 AND accountId = %s", (session["accountId"],))
        requestsLst = [
            {
                "id": tr[0],
                "title": tr[1],
                "startUser": tr[2],
                "assignEditor": tr[3],
                "dueDate": tr[4],
                "comments": tr[5],
                "submittedDate": tr[6],
                "type": tr[7],
                "status": tr[8],
                "tags": tr[9],
                "attachments": tr[10],
                "priority": tr[11],
                "listName": tr[12]
            } for tr in mycursor.fetchall()
        ]

        for entry in requestsLst:
            # Get Start User
            user = get_user_details(entry["startUser"], mycursor)
            startUser = f'({user["username"]}) {user["email"]}'
            entry["startUser"] = startUser

            # Get Assign User
            user = get_user_details(entry["assignEditor"], mycursor)
            assignEditor = f'({user["username"]}) {user["email"]}'
            entry["assignEditor"] = assignEditor

            # Check Status Message
            current_datetime = datetime.datetime.now()
            due_datetime = datetime.datetime.strptime(str(entry["dueDate"]), '%Y-%m-%d %H:%M:%S')
            check_24_hours_before = current_datetime - datetime.timedelta(hours=24)
            status_message = "On track"
            if due_datetime < current_datetime:
                status_message = "Overdue"
            if check_24_hours_before < due_datetime < current_datetime:
                status_message = "At risk"
            entry["statusMessage"] = status_message

        return requestsLst
    except Exception as e:
        # Log the error or handle it as needed
        raise e
    finally:
        mydb.close()


def uniquify(path):
    """
    Generate a unique filename by appending a counter to the original filename if it already exists.

    Args:
        path (str): The original file path.

    Returns:
        str: A unique file path.
    """
    if not os.path.isabs(path):
        raise ValueError("The provided path must be an absolute path.")

    if not os.path.isfile(path):
        return path  # Nothing to uniquify if the path does not exist

    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        counter_str = f"{counter:03d}"  # Zero-padded counter
        path = f"{filename}-({counter_str}){extension}"
        counter += 1

    return path


def new_task_email(workflow_id, title, assignedBy, priority, submittedDate, dueDate):
    email_content = '''<table class="nl-container" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;background-color:#fff">
       <tbody>
          <tr>
             <td>
                <table class="row row-2" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0">
                   <tbody>
                      <tr>
                         <td>
                            <table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;color:#000;width:600px" width="600">
                               <tbody>
                                  <tr>
                                     <td class="column column-1" width="100%" style="mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:30px;padding-top:40px;vertical-align:top;border-top:0;border-right:0;border-bottom:0;border-left:0">
                                        <table class="text_block block-1" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;word-break:break-word">
                                           <tr>
                                              <td class="pad">
                                                 <div style="font-family:sans-serif">
                                                    <div class style="font-size:12px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;mso-line-height-alt:14.399999999999999px;color:#1f1f1f;line-height:1.2">
                                                       <p style="margin:0;font-size:14px;mso-line-height-alt:16.8px"><strong><span style="font-size:22px;">''' + title + '''</span></strong></p>
                                                    </div>
                                                 </div>
                                              </td>
                                           </tr>
                                        </table>
                                        <table class="button_block block-2" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0">
                                           <tr>
                                              <td class="pad">
                                                 <div class="alignment" align="left">
                                                    <!--[if mso]>
                                                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" style="height:42px;width:108px;v-text-anchor:middle;" arcsize="8%" stroke="false" fillcolor="#198754">
                                                       <w:anchorlock/>
                                                       <v:textbox inset="0px,0px,0px,0px">
                                                          <center style="color:#ffffff; font-family:Arial, sans-serif; font-size:16px">
                                                             <![endif]-->
                                                             <a href="''' + Config.LEAFCMS_SERVER + '''/workflow_details?id=''' + str(workflow_id) + '''" style="text-decoration:none;display:inline-block;color:#fff;background-color:#198754;border-radius:3px;width:auto;border-top:0 solid transparent;font-weight:undefined;border-right:0 solid transparent;border-bottom:0 solid transparent;border-left:0 solid transparent;padding-top:5px;padding-bottom:5px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all">
                                                                <span style="padding-left:20px;padding-right:20px;font-size:16px;display:inline-block;letter-spacing:normal;"><span dir="ltr" style="word-break: break-word; line-height: 32px;">View task</span></span>
                                                             </a>
                                                             <!--[if mso]>
                                                          </center>
                                                       </v:textbox>
                                                    </v:roundrect>
                                                    <![endif]-->
                                                 </div>
                                              </td>
                                           </tr>
                                        </table>
                                        <table class="text_block block-3" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;word-break:break-word">
                                           <tr>
                                              <td class="pad">
                                                 <div style="font-family:sans-serif">
                                                    <div class style="font-size:12px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;mso-line-height-alt:18px;color:#1f1f1f;line-height:1.5">
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">You were assigned to a new task on Leaf CMS</span></p>
                                                       <p style="margin:0;mso-line-height-alt:18px">&nbsp;</p>
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Requested by: ''' + assignedBy + '''</span></p>
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Priority: ''' + ('Standard' if str(priority) == "2" else 'High') + '''</span></p>
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Created on: ''' + submittedDate + '''</span></p>
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Due date: ''' + dueDate + '''</span></p>
                                                       <p style="margin:0;mso-line-height-alt:18px">&nbsp;</p>
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">To view more details and to take action, click the "View task" button above.</span></p>
                                                    </div>
                                                 </div>
                                              </td>
                                           </tr>
                                        </table>
                                     </td>
                                  </tr>
                               </tbody>
                            </table>
                         </td>
                      </tr>
                   </tbody>
                </table>
             </td>
          </tr>
       </tbody>
    </table>'''

    return email_content


def workflow_changed_email(workflow_id, title, assignedBy, newDetails, thisType, message):
    messageDetails = '''<p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Changed by: ''' + assignedBy + '''</span></p>
        <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">New status: ''' + newDetails + '''</span></p>'''

    if thisType == 'due_date_changed':
        messageDetails = '''<p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Changed by: ''' + assignedBy + '''</span></p>
            <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">New due date: ''' + newDetails + '''</span></p>'''

    if thisType == 'priority_changed':
        messageDetails = '''<p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Changed by: ''' + assignedBy + '''</span></p>
            <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">New priority: ''' + newDetails + '''</span></p>'''

    if thisType == 'new_comment':
        messageDetails = '''<p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">Added by: ''' + assignedBy + '''</span></p>'''

    email_content = '''<table class="nl-container" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;background-color:#fff">
       <tbody>
          <tr>
             <td>
                <table class="row row-2" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0">
                   <tbody>
                      <tr>
                         <td>
                            <table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;color:#000;width:600px" width="600">
                               <tbody>
                                  <tr>
                                     <td class="column column-1" width="100%" style="mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:30px;padding-top:40px;vertical-align:top;border-top:0;border-right:0;border-bottom:0;border-left:0">
                                        <table class="text_block block-1" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;word-break:break-word">
                                           <tr>
                                              <td class="pad">
                                                 <div style="font-family:sans-serif">
                                                    <div class style="font-size:12px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;mso-line-height-alt:14.399999999999999px;color:#1f1f1f;line-height:1.2">
                                                       <p style="margin:0;font-size:14px;mso-line-height-alt:16.8px"><strong><span style="font-size:22px;">''' + title + '''</span></strong></p>
                                                    </div>
                                                 </div>
                                              </td>
                                           </tr>
                                        </table>
                                        <table class="button_block block-2" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0">
                                           <tr>
                                              <td class="pad">
                                                 <div class="alignment" align="left">
                                                    <!--[if mso]>
                                                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" style="height:42px;width:108px;v-text-anchor:middle;" arcsize="8%" stroke="false" fillcolor="#198754">
                                                       <w:anchorlock/>
                                                       <v:textbox inset="0px,0px,0px,0px">
                                                          <center style="color:#ffffff; font-family:Arial, sans-serif; font-size:16px">
                                                             <![endif]-->
                                                             <a href="''' + Config.LEAFCMS_SERVER + '''/workflow_details?id=''' + str(workflow_id) + '''" style="text-decoration:none;display:inline-block;color:#fff;background-color:#198754;border-radius:3px;width:auto;border-top:0 solid transparent;font-weight:undefined;border-right:0 solid transparent;border-bottom:0 solid transparent;border-left:0 solid transparent;padding-top:5px;padding-bottom:5px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all">
                                                                <span style="padding-left:20px;padding-right:20px;font-size:16px;display:inline-block;letter-spacing:normal;"><span dir="ltr" style="word-break: break-word; line-height: 32px;">View task</span></span>
                                                             </a>
                                                             <!--[if mso]>
                                                          </center>
                                                       </v:textbox>
                                                    </v:roundrect>
                                                    <![endif]-->
                                                 </div>
                                              </td>
                                           </tr>
                                        </table>
                                        <table class="text_block block-3" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace:0;mso-table-rspace:0;word-break:break-word">
                                           <tr>
                                              <td class="pad">
                                                 <div style="font-family:sans-serif">
                                                    <div class style="font-size:12px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;mso-line-height-alt:18px;color:#1f1f1f;line-height:1.5">
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">''' + message + '''</span></p>
                                                       <p style="margin:0;mso-line-height-alt:18px">&nbsp;</p>
                                                       ''' + messageDetails + '''
                                                       <p style="margin:0;mso-line-height-alt:18px">&nbsp;</p>
                                                       <p style="margin:0;mso-line-height-alt:21px"><span style="font-size:14px;">To view more details and to take action, click the "View task" button above.</span></p>
                                                    </div>
                                                 </div>
                                              </td>
                                           </tr>
                                        </table>
                                     </td>
                                  </tr>
                               </tbody>
                            </table>
                         </td>
                      </tr>
                   </tbody>
                </table>
             </td>
          </tr>
       </tbody>
    </table>'''

    return email_content


def create_remote_folder(scp, remote_path):
    """
    Create a remote folder and its parent folders if they do not exist.

    Args:
        scp (paramiko.SSHClient): An established SSHClient connected to the remote server.
        remote_path (str): The remote path of the folder to be created.

    Raises:
        OSError: If an error occurs while creating the remote folder.
    """
    try:
        scp.stat(remote_path)
    except (IOError, OSError) as e:
        if isinstance(e, FileNotFoundError):
            # Remote folder does not exist, create it
            parent_folder = os.path.dirname(remote_path)
            create_remote_folder(scp, parent_folder)  # Recursively create parent folders if needed
            try:
                scp.mkdir(remote_path)
            except OSError as mkdir_error:
                raise OSError(f"Error creating remote folder '{remote_path}': {mkdir_error}")
        else:
            raise OSError(f"Error checking remote folder '{remote_path}': {e}")


def upload_file_with_retry(local_path, remote_path, scp, max_retries=2, retry_delay=1):
    """
    Upload a file to a remote location with retry functionality.

    Args:
        local_path (str): The local path of the file to be uploaded.
        remote_path (str): The remote path where the file will be uploaded.
        scp (paramiko.SFTPClient): An established SFTPClient connected to the remote server.
        max_retries (int, optional): The maximum number of retry attempts. Default is 2.
        retry_delay (int, optional): The delay (in seconds) between retry attempts. Default is 1.

    Returns:
        tuple: A tuple (success, local_path, remote_path), where success is a boolean indicating the upload success.
    """
    retries = 0

    while retries < max_retries:
        try:
            create_remote_folder(scp, os.path.dirname(remote_path))
            scp.put(local_path, remote_path)
            return True, local_path, remote_path
        except (OSError, IOError) as e:
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)
                remote_path = remote_path.replace("/", "\\") if ":" in remote_path else remote_path
                print(f"Retry {retries}: {e}")

    return False, local_path, remote_path


def add_workflow(thisRequest):
    """
    Add a new workflow to the database and send an email notification.

    Args:
        thisRequest (dict): The request containing workflow details.

    Returns:
        dict: A dictionary with a success message and the workflow ID.

    Raises:
        Exception: If an error occurs during the workflow creation process.
    """
    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    try:
        startUser = str(session["id"])

        # Extract workflow details from the request
        assignEditor = thisRequest.get("assignEditor")
        if not assignEditor:
            assignEditor = session["id"]
        dueDate = str(thisRequest.get("dueDate")) if thisRequest.get("dueDate") else str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        comments = str(thisRequest.get("comments")) if thisRequest.get("comments") else ""
        tags = str(thisRequest.get("tags")) if thisRequest.get("tags") else ""
        siteIds = str(thisRequest.get("siteIds")).split(";")[0] if thisRequest.get("siteIds") else ""
        thisType = int(thisRequest.get("type")) if thisRequest.get("type") else 1
        listName = thisRequest.get("listName") if thisRequest.get("listName") else ""

        # Set default title based on workflow type
        if thisRequest.get("title"):
            title = str(thisRequest.get("title"))
        else:
            title_dict = {
                1: 'New Leaf workflow review',
                2: 'New Leaf content request',
                5: 'New Leaf delete page',
            }
            title = title_dict.get(thisType, 'New Leaf dynamic workflow review')

        # Handle specific types
        if thisType == 3 or thisType == 5:
            siteIds = thisRequest.get("entryId")

        if thisType == 6 or thisType == 7:
            # For file types, save file IDs within siteId field
            filesIds = thisRequest.get("entryId")
            if filesIds and isinstance(filesIds, list):
                siteIds = ', '.join(filesIds)
            else:
                siteIds = ""

        # Set default status, attachments, priority, and submitted date
        status = str("1")
        attachments = ';'.join(thisRequest.get("attachments")) if thisRequest.get("attachments") else ""
        priority = str(thisRequest.get("priority"))
        submittedDate = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        accountId = session["accountId"]

        # Add Workflow to DB
        query = "INSERT INTO workflow (startUser, assignEditor, comments, siteIds, submittedDate, title, type, status, tags, dueDate, attachments, priority, accountId, listName) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (startUser, assignEditor, comments, siteIds, submittedDate, title, thisType, status, tags, dueDate, attachments, priority, accountId, listName)
        mycursor.execute(query, params)
        mydb.commit()
        workflow_id = mycursor.lastrowid

        mycursor.execute(f"SELECT email FROM user WHERE id={assignEditor}")
        assignEditorEmail = mycursor.fetchone()[0]
        emailToSend = new_task_email(workflow_id, title, session["username"], priority, submittedDate, dueDate)

        send_mail(title, emailToSend, assignEditorEmail)

        return {"message": "success", "workflow_id": str(workflow_id)}

    except Exception as e:
        # Log the error or handle it as needed
        raise e
    finally:
        mydb.close()


def change_status_workflow(workflow_id, new_status, user_to_notify):
    """
    Change the status of a workflow, update the database, and send email notifications.

    Args:
        workflow_id (int): The ID of the workflow to update.
        new_status (str): The new status of the workflow.
        user_to_notify (str): The email address of the user to notify.

    Returns:
        dict: A dictionary with a success message and the workflow ID.

    Raises:
        Exception: If an error occurs during the status change process.
    """
    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    try:
        # Update status
        mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", (new_status, workflow_id))
        mydb.commit()
        last_workflow_id = mycursor.lastrowid

        # Set email info
        title = 'Leaf workflow status changed'
        theEmailMessage = 'This task status has been changed on Leaf CMS'
        newStatusString = "New Request"
        if new_status == '2':
            newStatusString = "In Progress"
        if new_status == '3':
            newStatusString = "Sent back for clarification"
        if new_status == '4':
            newStatusString = "Send back for review"
        if new_status == '5':
            newStatusString = "Approved and awaiting deployment"
        if new_status == '6':
            newStatusString = "Complete"

        # Get email body
        emailToSend = workflow_changed_email(workflow_id, title, session["username"], newStatusString, "status_changed", theEmailMessage)

        send_mail(title, emailToSend, Config.ASSIGNED_USER_EMAIL)
        send_mail(title, emailToSend, user_to_notify)

        jsonR = {"message": "success", "workflow_id": str(last_workflow_id)}
        return jsonR
    except Exception as e:
        # Log the error or handle it as needed
        raise e
    finally:
        mydb.close()


def send_mail(title, emailToSend, user_to_notify):
    """
    Send an email using the configured method.

    Args:
        title (str): Title of the email.
        email_to_send (str): Content of the email.
        user_to_notify (str): Email address of the recipient.

    Returns:
        None
    """

    if Config.EMAIL_METHOD == "SMTP":
        send_smtp(title, emailToSend, Config.SMTP_USER, user_to_notify)

    if Config.EMAIL_METHOD == "sendmail":
        send_sendmail(title, emailToSend, Config.SMTP_USER, user_to_notify)


def send_smtp(subject, email_to_send, from_addr, to_addr):
    """
    Send an email using SMTP.

    Args:
        subject (str): Subject of the email.
        email_to_send (str): Content of the email.
        from_addr (str): Sender's email address.
        to_addr (str): Recipient's email address.

    Returns:
        None
    """

    message = EmailMessage()
    message['From'] = from_addr
    message['To'] = to_addr
    message['Subject'] = subject
    message.set_content(email_to_send, subtype='html')
    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        if Config.SMTP_PORT != 25:
            server.starttls()
        if Config.SMTP_PASSWORD != "":
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(message)


def send_sendmail(subject, message, from_addr, to_addr):
    """
    Send an email using the sendmail method.

    Args:
        subject (str): Subject of the email.
        message (str): Content of the email.
        from_addr (str): Sender's email address.
        to_addr (str): Recipient's email address.

    Returns:
        None
    """

    sendmail_path = subprocess.run(['whereis', 'sendmail'], stdout=subprocess.PIPE).stdout.decode().split(':')[1].strip()
    if sendmail_path:
        email_text = f"""
From: {from_addr}
To: {to_addr}
Subject: {subject}

{message}
"""
        # Start the sendmail process
        process = subprocess.Popen([sendmail_path, "-t", "-oi"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        # Send the email
        process.communicate(email_text.encode())


def gen_sitemap(mycursor, site_id):
    query = "SELECT HTMLPath FROM site_meta WHERE status <> -1 AND site_id = %s"
    mycursor.execute(query, [site_id])
    site_pages = [page[0] for page in mycursor.fetchall()]

    for srv in Config.DEPLOYMENTS_SERVERS:
        # Gen Remove Sitemap File
        urlset = ET.Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        urlset.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")
        sitemap_path = os.path.join(Config.WEBSERVER_FOLDER, "sitemap.xml")
        for page in site_pages:
            url_elem = ET.SubElement(urlset, "url")
            loc_elem = ET.SubElement(url_elem, "loc")
            loc_elem.text = urljoin(srv["webserver_url"], page)
        tree = ET.ElementTree(urlset)
        tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)

        # SCP Files
        remote_path = os.path.join(srv["remote_path"], "sitemap.xml")
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
            actionResult, lp, rp = upload_file_with_retry(sitemap_path, remote_path, scp)
            if not actionResult:
                try:
                    raise Exception("Failed to SCP - " + lp + " - " + rp)
                except Exception as e:
                    pass

    # Gen Local Sitemap File
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    urlset.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")
    sitemap_path = os.path.join(Config.WEBSERVER_FOLDER, "sitemap.xml")
    for page in site_pages:
        url_elem = ET.SubElement(urlset, "url")
        loc_elem = ET.SubElement(url_elem, "loc")
        loc_elem.text = urljoin(Config.PREVIEW_SERVER, page)
    tree = ET.ElementTree(urlset)
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
