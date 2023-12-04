import datetime
import os
import time
import smtplib
from urllib.parse import unquote
from leaf import Config
from leaf import decorators
from flask import session
from email.message import EmailMessage


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

        workflow_data = extract_workflow_data(results)
        user = get_user_details(workflow_data["startUser"], mycursor)
        workflow_data["startUser"], workflow_data["startUserEmail"] = user["username"], user["email"]
        workflow_data["assignEditor"] = get_user_details(workflow_data["assignEditor"], mycursor)["email"]
        process_specific_workflow_type(workflow_data, mycursor)

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
    query = "SELECT user.username, user.email FROM user WHERE user.id=%s OR user.email=%s"
    params = [user_id, user_id]
    mycursor.execute(query, params)
    result = mycursor.fetchone()
    username, email = result[0], result[1]
    return {"username": username, "email": email}


def process_specific_workflow_type(workflow_data, mycursor):
    """
    Process workflow details based on specific workflow type.

    Args:
        workflow_data (dict): Workflow details.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.
    """
    if workflow_data["type"] == 1 or workflow_data["type"] == 5:
        process_type_1_or_5(workflow_data, mycursor)
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
        workflow_data["siteUrl"] = Config.PREVIEW_SERVER + "/" + result[2]

        workflow_data["siteInfo"] = dict(zip(workflow_data["siteIds"], workflow_data["siteTitles"]))


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
        mycursor.execute(f"SELECT * FROM {table_name} WHERE main_table = %s", (workflow_data["listName"],))
        result_list = mycursor.fetchone()

        if result_list and len(result_list) > 0:
            lists_config = result_list
            this_template = lists_config[2]
            this_parameters = lists_config[3]
            this_parameters_to_grab = lists_config[4]

            query = f"SELECT {this_parameters_to_grab} FROM account_{session['accountId']}_list_{workflow_data['listName']} WHERE id=%s"
            params = (site_id,)
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
        mycursor.execute("SELECT id, title, startUser, assignEditor, dueDate, comments, submittedDate, type, status, tags, attachments, priority, listName FROM workflow WHERE type != 2 AND accountId = %s", (session["accountId"],))
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
                                                             <a href="''' + Config.MAIN_SERVER + '''/workflow_details?id=''' + str(workflow_id) + '''" style="text-decoration:none;display:inline-block;color:#fff;background-color:#198754;border-radius:3px;width:auto;border-top:0 solid transparent;font-weight:undefined;border-right:0 solid transparent;border-bottom:0 solid transparent;border-left:0 solid transparent;padding-top:5px;padding-bottom:5px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all">
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
                                                             <a href="''' + Config.MAIN_SERVER + '''/workflow_details?id=''' + str(workflow_id) + '''" style="text-decoration:none;display:inline-block;color:#fff;background-color:#198754;border-radius:3px;width:auto;border-top:0 solid transparent;font-weight:undefined;border-right:0 solid transparent;border-bottom:0 solid transparent;border-left:0 solid transparent;padding-top:5px;padding-bottom:5px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;text-align:center;mso-border-alt:none;word-break:keep-all">
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
        scp (paramiko.SSHClient): An established SSHClient connected to the remote server.
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
        assignEditor = thisRequest.get("assignEditor")

        # Check for SQL injection in assignEditor
        if assignEditor and "@" in assignEditor:
            assignEditor = ';'.join(assignEditor)
        else:
            assignEditor = str(Config.ASSIGNED_USER_EMAIL)

        dueDate = str(thisRequest.get("dueDate")) if thisRequest.get("dueDate") else str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        comments = str(thisRequest.get("comments")) if thisRequest.get("comments") else ""
        tags = str(thisRequest.get("tags")) if thisRequest.get("tags") else ""
        siteIds = str(thisRequest.get("siteIds")).split(";")[0] if thisRequest.get("siteIds") else ""
        thisType = int(thisRequest.get("type")) if thisRequest.get("type") else 1
        listName = thisRequest.get("listName") if thisRequest.get("listName") else ""

        if thisRequest.get("title"):
            title = str(thisRequest.get("title"))
        else:
            title_dict = {
                1: 'New Leaf workflow review',
                2: 'New Leaf content request',
                5: 'New Leaf delete page',
            }
            title = title_dict.get(thisType, 'New Leaf dynamic workflow review')

        if thisType == 3 or thisType == 5:
            siteIds = thisRequest.get("entryId")

        status = str("1")

        attachments = ';'.join(thisRequest.get("attachments")) if thisRequest.get("attachments") else ""
        priority = str(thisRequest.get("priority"))
        submittedDate = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        accountId = session["accountId"]

        # Run SQL Command
        query = "INSERT INTO workflow (startUser, assignEditor, comments, siteIds, submittedDate, title, type, status, tags, dueDate, attachments, priority, accountId, listName) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (startUser, assignEditor, comments, siteIds, submittedDate, title, thisType, status, tags, dueDate, attachments, priority, accountId, listName)
        mycursor.execute(query, params)
        mydb.commit()
        workflow_id = mycursor.lastrowid

        if Config.SMTP_USER != "":
            emailToSend = new_task_email(workflow_id, title, session["username"], priority, submittedDate, dueDate)
            message = EmailMessage()
            message['From'] = Config.SMTP_USER
            message['To'] = Config.ASSIGNED_USER_EMAIL
            message['Subject'] = title
            message.set_content(emailToSend, subtype='html')
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(message)

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

        # Send Email to ASSIGNED_USER_EMAIL
        message = EmailMessage()
        message['From'] = Config.SMTP_USER
        message['To'] = Config.ASSIGNED_USER_EMAIL
        message['Subject'] = title
        message.set_content(emailToSend, subtype='html')
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(message)

        # Send email to user
        message2 = EmailMessage()
        message2['From'] = Config.SMTP_USER
        message2['To'] = user_to_notify
        message2['Subject'] = title
        message2.set_content(emailToSend, subtype='html')
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(message2)

        jsonR = {"message": "success", "workflow_id": str(last_workflow_id)}
        return jsonR
    except Exception as e:
        # Log the error or handle it as needed
        raise e
    finally:
        mydb.close()
