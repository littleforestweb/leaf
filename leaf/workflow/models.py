import ast
import datetime
import json
import os
import re
import smtplib
import subprocess
import time
import xml.etree.ElementTree as ET
from email.message import EmailMessage
from urllib.parse import unquote, urljoin

import paramiko
import werkzeug.utils
from bs4 import BeautifulSoup
from flask import session, current_app
from git import Actor
from werkzeug.datastructures import MultiDict

from leaf import Config
from leaf import decorators
from leaf.files_manager.models import get_rss_feed_by_id
from leaf.lists.models import get_list_configuration, custom_serializer, get_list_columns_with_properties
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
        query = "SELECT workflow.id, workflow.startUser, workflow.title, workflow.assignEditor, workflow.dueDate, workflow.tags, workflow.comments, workflow.submittedDate, workflow.type, workflow.status, workflow.siteIds, workflow.attachments, workflow.priority, workflow.listName, workflow.lastEdited, workflow.pubDate FROM workflow WHERE workflow.id=%s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        results = mycursor.fetchone()

        # Set workflow_data
        workflow_data = extract_workflow_data(results)
        user = get_user_details(workflow_data["startUser"], mycursor)
        workflow_data["startUser"], workflow_data["startUserEmail"] = user["username"], user["email"]
        workflow_data["assignEditor"] = get_user_details(workflow_data["assignEditor"], mycursor)["email"]
        process_specific_workflow_type(workflow_data, mycursor)
        if workflow_data["type"] == 3:
            workflow_data["publication_date"] = workflow_data["publication_date"] + " 00:00:00" if ":" not in workflow_data["publication_date"] else workflow_data["publication_date"]

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
        "siteInfo": {},
        "publication_date": results[15]
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
    elif str(workflow_data["type"]) == "3" or str(workflow_data["type"]) == "8":
        process_type_3_or_8(workflow_data, mycursor)


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
        mycursor.execute(query, tuple(filesIds))  # Convert list to tuple for the query parameters
        result = mycursor.fetchall()  # fetchall if you expect more than one row, fetchone if you expect only one

        workflow_data["files_details"] = result
        workflow_data["preview_server"] = Config.PREVIEW_SERVER

        # Add site URL
        query = f"SELECT site_assets.path FROM site_assets WHERE id = %s"
        mycursor.execute(query, filesIds)
        result = mycursor.fetchone()[0]
        workflow_data["siteUrl"] = urljoin(Config.PREVIEW_SERVER, result)


def process_type_3_or_8(workflow_data, mycursor):
    """
    Process workflow details for type 3 or 8.

    Args:
        workflow_data (dict): Workflow details.
        mycursor (mysql.connector.cursor): MySQL cursor for executing queries.
    """
    if workflow_data["siteIds"]:
        site_id = workflow_data["siteIds"]
        workflow_data["siteTitles"] = ""

        query = f"SELECT template_location, feed_location FROM account_%s_list_template WHERE in_lists=%s"
        params = (session['accountId'], workflow_data['listName'],)
        mycursor.execute(query, params)
        result_list = mycursor.fetchone()

        if result_list and len(result_list) > 0:
            list_template = result_list[0]
            list_feed = result_list[1]

            # Regular expression to find words within curly braces
            pattern = r'{(.*?)}'

            # Using re.findall() to extract the contents within the braces
            items = re.findall(pattern, list_template)

            publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']

            workflow_list_name = werkzeug.utils.escape(workflow_data['listName'])
            query_list = f"SELECT * FROM account_{session['accountId']}_list_{workflow_list_name} WHERE id=%s"
            params_list = (site_id,)
            mycursor.execute(query_list, params_list)
            fields_to_link = mycursor.fetchall()

            # Get column headers from the cursor description
            headers = [description[0] for description in mycursor.description]

            # Combine headers and data
            results = [dict(zip(headers, row)) for row in fields_to_link]

            publication_date = False
            list_page_url = []

            if results and len(results) > 0:

                workflow_data["leaf_selected_rss"] = ""
                workflow_data["leaf_selected_rss_ids"] = ""

                list_columns_with_properties_raw = get_list_columns_with_properties(session['accountId'], workflow_data['listName'])
                list_columns_with_properties = json.loads(list_columns_with_properties_raw.get_data(as_text=True))

                field_to_split_by = False
                for this_properties in list_columns_with_properties:
                    for this_property in list_columns_with_properties[this_properties]:
                        if (this_property[3] == '-_leaf_access_folders_-'):
                            field_to_split_by = this_property[2]

                for result in results:
                    if field_to_split_by:
                        field_to_split_by_in_result = result[field_to_split_by].split(",")
                        for field_in_result in field_to_split_by_in_result:
                            list_page_url_template = list_template
                            for key, value in result.items():
                                if key.lower() in publication_names:
                                    publication_date = value
                                    if publication_date == "Invalid date":
                                        publication_date = ""
                                elif key.lower() == field_to_split_by:
                                    list_page_url_template = list_page_url_template.replace("{" + key + "}", str(field_in_result))
                                else:
                                    list_page_url_template = list_page_url_template.replace("{" + key + "}", str(value))

                                for field in items:
                                    if publication_date and (field == "year" or field == "month" or field == "day"):
                                        single_field = extract_month_and_day(publication_date, field)
                                        single_field = str(single_field)

                                        list_page_url_template = list_page_url_template.replace("{" + field + "}", single_field)

                                if key.lower() == "leaf_selected_rss" and value is not None:
                                    rss_values = value
                                    rss_values = rss_values.split(",")
                                    rss_data = []
                                    for rss_item in rss_values:
                                        rss_data.append(get_rss_feed_by_id(rss_item))

                                    workflow_data["leaf_selected_rss"] = rss_data
                                    workflow_data["leaf_selected_rss_ids"] = value

                            list_page_url.append(f"{list_page_url_template}" + (Config.PAGES_EXTENSION if not list_page_url_template.endswith(Config.PAGES_EXTENSION) else ""))
                    else:
                        list_page_url_template = list_template
                        for key, value in result.items():
                            if key.lower() in publication_names:
                                publication_date = value
                            else:
                                list_page_url_template = list_page_url_template.replace("{" + key + "}", str(value))

                            for field in items:
                                if publication_date and (field == "year" or field == "month" or field == "day"):
                                    single_field = extract_month_and_day(publication_date, field)
                                    single_field = str(single_field)

                                    list_page_url_template = list_page_url_template.replace("{" + field + "}", single_field)

                            if key.lower() == "leaf_selected_rss":
                                rss_values = value
                                rss_values = rss_values.split(",")
                                rss_data = []
                                for rss_item in rss_values:
                                    rss_data.append(get_rss_feed_by_id(rss_item))

                                workflow_data["leaf_selected_rss"] = rss_data
                                workflow_data["leaf_selected_rss_ids"] = value

                        list_page_url.append(f"{list_page_url_template}" + (Config.PAGES_EXTENSION if not list_page_url_template.endswith(Config.PAGES_EXTENSION) else ""))

                clean_url = []
                for list_page_url_single in list_page_url:
                    workflow_data_temporary_url = urljoin(Config.PREVIEW_SERVER, list_page_url_single)
                    protocol = "https://" if "https://" in workflow_data_temporary_url else "http://"
                    clean_url.append(protocol + workflow_data_temporary_url.replace(protocol, "").replace("//", "/"))

                workflow_data["siteUrl"] = clean_url

            else:
                workflow_data["siteUrl"] = False

            workflow_data["siteTitles"] = list_page_url
            workflow_data["list_feed_path"] = list_feed

            workflow_data["siteId"] = list_page_url

            workflow_data["publication_date"] = False if not publication_date else publication_date

            workflow_data["preview_server"] = Config.PREVIEW_SERVER


def get_workflows():
    """
    Retrieve workflows from the database and enrich the data with additional information.

    Returns:
        list: List of dictionaries representing workflows with additional details.
    """
    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    try:
        mycursor.execute("SELECT id, title, startUser, assignEditor, dueDate, comments, submittedDate, type, status, tags, attachments, priority, listName FROM workflow WHERE type != 2 AND (startUser = %s OR assignEditor = %s) AND accountId = %s", (session["id"], session["id"], session["accountId"],))
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
        pubDate = str(thisRequest.get("pubDate")) if thisRequest.get("pubDate") else str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

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
        if thisType == 3 or thisType == 5 or thisType == 8:
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
        query = "INSERT INTO workflow (startUser, assignEditor, comments, siteIds, submittedDate, title, type, status, tags, dueDate, attachments, priority, accountId, listName, pubDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (startUser, assignEditor, comments, siteIds, submittedDate, title, thisType, status, tags, dueDate, attachments, priority, accountId, listName, pubDate)
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
        if new_status == '7':
            newStatusString = "Waiting"

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


def gen_sitemap(mycursor, site_id, thisType):
    query = "SELECT HTMLPath FROM site_meta WHERE status <> -1 AND site_id = %s"
    mycursor.execute(query, [site_id])
    site_pages = [page[0] for page in mycursor.fetchall()]

    for srv in Config.DEPLOYMENTS_SERVERS:
        # Gen Remove Sitemap File
        urlset = ET.Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        urlset.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")
        sitemap_path = os.path.join(Config.WEBSERVER_FOLDER, "sitemap.xml")
        # Ensure the directory exists
        sitemap_directory = os.path.dirname(sitemap_path)
        if not os.path.exists(sitemap_directory):
            os.makedirs(sitemap_directory)
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
    # Ensure the directory exists
    sitemap_directory = os.path.dirname(sitemap_path)
    if not os.path.exists(sitemap_directory):
        os.makedirs(sitemap_directory)
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)


def proceed_action_workflow(request, not_real_request=None):
    # Get url from post params
    workflow_id = werkzeug.utils.escape(request.form.get("id"))
    action = werkzeug.utils.escape(request.form.get("status"))
    publication_date = werkzeug.utils.escape(request.form.get("publication_date"))

    if not_real_request is None:
        # Check if the workflow belongs to the user's account
        if not is_workflow_owner(int(workflow_id)):
            return {"error": "Forbidden"}

    target_date = False
    if publication_date and publication_date != False and publication_date != "False":
        target_date = datetime.datetime.strptime(publication_date, "%Y-%m-%d %H:%M:%S").date()
    current_date = datetime.datetime.now().date()

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
        return jsonR

    # Check if the user has permission
    if thisType in [1, 5, 6, 7]:
        query = "SELECT site_meta.HTMLPath FROM site_meta JOIN workflow ON site_meta.id = workflow.siteIds WHERE workflow.id = %s"
        params = (workflow_id,)
        mycursor.execute(query, params)
        workflow_folder_path = f"/{mycursor.fetchone()[0].lstrip('/')}"
        if not_real_request is None:
            perm_level = get_user_permission_level(session["id"], workflow_folder_path)
        else:
            perm_level = get_user_permission_level(werkzeug.utils.escape(request.form.get("user_id")), workflow_folder_path)
        if perm_level != 4:
            return {"error": "Forbidden"}

    if not listName and thisType == 1:

        # Check for pubDate
        if target_date and target_date > current_date:
            mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", ("7", workflow_id))
            mydb.commit()
            return {"message": "waiting", "action": action}

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
            data = data.replace(str(os.path.join(Config.LEAFCMS_SERVER.rstrip("/"), Config.IMAGES_WEBPATH.lstrip('/leaf/').rstrip("/"))), str(os.path.join("/", Config.REMOTE_UPLOADS_FOLDER.lstrip("/"))))
            with open(local_path, "w") as outFile:
                outFile.write(data)

            assets = find_page_assets(original_content)

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
                    assetRemotePath = os.path.join(srv["remote_path"], Config.REMOTE_UPLOADS_FOLDER, assetFilename)
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
        query = "SELECT id, site_id FROM site_meta WHERE HTMLPath = %s"
        mycursor.execute(query, [HTMLPath])
        page_id, site_id = mycursor.fetchone()
        gen_sitemap(mycursor, site_id, thisType)

        # Git operations
        query = "SELECT workflow.comments FROM workflow WHERE id = %s"
        mycursor.execute(query, [workflow_id])
        workflow_comment = mycursor.fetchone()[0]
        Config.GIT_REPO.index.add([os.path.join(Config.WEBSERVER_FOLDER, HTMLPath), os.path.join(Config.WEBSERVER_FOLDER, "sitemap.xml")])
        Config.GIT_REPO.index.commit(workflow_comment, author=Actor(session["username"], session["email"]))

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
        if target_date and target_date <= current_date or thisType == 8:

            if not_real_request is None:
                accountId = session['accountId']
            else:
                accountId = werkzeug.utils.escape(request.form.get("accountId"))

            action = "Approved"

            jsonR = {"message": "success", "action": action}

            listName = ''.join(e for e in listName if e.isalnum())
            if isMenu:
                completeListName = listName + "Menu.json"
                account_list = f"account_{str(accountId)}_menu_{listName}"
            else:
                completeListName = listName + "List.json"
                account_list = f"account_{str(accountId)}_list_{listName}"

            publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']
            # Check which publication date fields actually exist in the table
            existing_publication_names = [name for name in publication_names if column_exists(mycursor, account_list, name)]
            date_conditions = " AND ".join([f"({field} IS NULL OR {field} <= %s)" for field in existing_publication_names])
            current_date_to_compare_in_db = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            current_app.logger.debug(current_date_to_compare_in_db)

            site_ids = werkzeug.utils.escape(request.form.get("site_ids"))

            for srv in Config.DEPLOYMENTS_SERVERS:
                DYNAMIC_PATH = Config.DYNAMIC_PATH.strip('/')
                saveByFields = werkzeug.utils.escape(request.form.get("saveByFields"))
                fieldsToSaveBy = False
                fieldsToSaveByIncludes = False
                if saveByFields == '1':
                    fieldsToSaveBy = werkzeug.utils.escape(request.form.get("fieldsToSaveBy"))
                    fieldsToSaveByIncludes = werkzeug.utils.escape(request.form.get("fieldsToSaveByIncludes"))

                final_list = list()
                # Save list by pre-selected field independently to speed up the front end (on preview and live environment)
                if fieldsToSaveBy:
                    fieldsToSaveBy = "".join(fieldsToSaveBy)
                    fieldsToSaveBy = fieldsToSaveBy.split(';')
                    for singleFieldToSaveBy in fieldsToSaveBy:
                        mycursor.execute(f"SELECT {singleFieldToSaveBy} FROM {account_list} WHERE id = %s", (site_ids,))
                        fullEntry = mycursor.fetchall()

                        if fullEntry and len(fullEntry) > 0:

                            listCleanArray = set()
                            for fullSingleEntry in fullEntry:
                                entries = fullSingleEntry[0].split(';')
                                for singleEntry in entries:
                                    listCleanArray.add(singleEntry.strip().lower())

                            final_list.append(listCleanArray)

                    pages_to_delete_from_feed = False
                    if thisType == 8:
                        current_app.logger.debug("thisType:")
                        current_app.logger.debug(thisType)
                        query_list = f"SELECT * FROM {account_list} WHERE id=%s"
                        params_list = (site_ids,)
                        mycursor.execute(query_list, params_list)
                        pages_to_delete_from_feed = mycursor.fetchall()
                        mycursor.execute(f"DELETE FROM {account_list} WHERE id=%s", (site_ids,))
                        mydb.commit()

                    for singleListItemList in final_list:
                        for singleListItem in singleListItemList:
                            singleListItemToSearch = singleListItem.split(",")
                            for singleItem in singleListItemToSearch:
                                singleItem = singleItem.split(",")
                                by_field_conditions = " OR ".join([f"FIND_IN_SET(%s, `{singleFieldToSaveBy}`)" for _ in singleItem])
                                by_field_query = f"SELECT {fieldsToSaveByIncludes} FROM {account_list} WHERE {by_field_conditions} AND ({date_conditions})"
                                by_field_params = tuple(singleItem) + (current_date_to_compare_in_db,) * len(existing_publication_names)
                                mycursor.execute(by_field_query, by_field_params)

                                current_app.logger.debug(by_field_query, by_field_params)

                                row_headers = [x[0] for x in mycursor.description]
                                fullListByField = mycursor.fetchall()

                                json_data_by_field = [dict(zip(row_headers, result)) for result in fullListByField]
                                json_data_to_write_by_field = json.dumps(json_data_by_field, default=custom_serializer).replace('__BACKSLASH__TO_REPLACE__', '\\')

                                if isMenu:
                                    completeListNameByField = listName + "_" + singleItem[0].replace("/", "__fslash__") + "_Menu.json"
                                    os.makedirs(os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, "json_by_field"), exist_ok=True)
                                    with open(os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, "json_by_field", completeListNameByField), "w") as outFileByField:
                                        outFileByField.write(json_data_to_write_by_field)
                                else:
                                    completeListNameByField = listName + "_" + singleItem[0].replace("/", "__fslash__") + "_List.json"
                                    os.makedirs(os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, "json_by_field"), exist_ok=True)
                                    with open(os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, "json_by_field", completeListNameByField), "w") as outFileByField:
                                        outFileByField.write(json_data_to_write_by_field)

                                # do scp for LISTS by field
                                local_path = os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, "json_by_field", completeListNameByField)
                                remote_path = os.path.join(srv["remote_path"], DYNAMIC_PATH, "json_by_field", completeListNameByField)
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

                # if date_conditions == "":
                #     full_query = f"SELECT * FROM {account_list}"
                # else:
                #     full_query = f"SELECT * FROM {account_list} WHERE ({date_conditions})"
                # full_params = (current_date_to_compare_in_db,) * len(existing_publication_names)
                # mycursor.execute(full_query, full_params)

                # row_headers = [x[0] for x in mycursor.description]
                # fullList = mycursor.fetchall()

                # json_data = [dict(zip(row_headers, result)) for result in fullList]
                # json_data_to_write = json.dumps(json_data, default=custom_serializer).replace('__BACKSLASH__TO_REPLACE__', '\\')

                # os.makedirs(os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH), exist_ok=True)
                # with open(os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, completeListName), "w") as outFile:
                #     outFile.write(json_data_to_write)

                # # do scp for LISTS
                # local_path = os.path.join(Config.WEBSERVER_FOLDER, DYNAMIC_PATH, completeListName)
                # remote_path = os.path.join(srv["remote_path"], DYNAMIC_PATH, completeListName)
                # ssh = paramiko.SSHClient()
                # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # if srv["pkey"] != "":
                #     ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"], password=srv["pw"]))
                #     if srv["pw"] == "":
                #         ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                #     else:
                #         ssh.connect(srv["ip"], srv["port"], srv["user"], pkey=paramiko.RSAKey(filename=srv["pkey"]))
                # else:
                #     ssh.connect(srv["ip"], srv["port"], srv["user"], srv["pw"])
                # with ssh.open_sftp() as scp:
                #     actionResult, lp, rp = upload_file_with_retry(local_path, remote_path, scp)
                #     if not actionResult:
                #         try:
                #             raise Exception("Failed to SCP - " + lp + " - " + rp)
                #         except Exception as e:
                #             pass

            # LOOP THROUGH list_item_url_path TO PUBLISH FILE IN MULTIPLE LOCATIONS
            if int(thisType) != 4:
                list_items_url_path = request.form.get("list_item_url_path")
                list_items_url_path = ast.literal_eval(list_items_url_path)
                for list_item_url_path in list_items_url_path:
                    HTMLPath = werkzeug.utils.escape(list_item_url_path.strip("/"))
                    local_path = os.path.join(Config.WEBSERVER_FOLDER, HTMLPath)
                    list_feed_path = werkzeug.utils.escape(request.form.get("list_feed_path").strip("/"))
                    rss_ids = werkzeug.utils.escape(request.form.get("rss_ids"))
                    if thisType != 8:
                        for srv in Config.DEPLOYMENTS_SERVERS:

                            # Replace Preview Reference with Live webserver references
                            with open(local_path) as inFile:
                                data = inFile.read()

                            assets = find_page_assets(data)

                            if not srv["webserver_url"].endswith('/'):
                                srv["webserver_url"] += '/'

                            original_content = data
                            original_content_changed = data.replace(Config.LEAFCMS_SERVER, Config.PREVIEW_SERVER + Config.DYNAMIC_PATH.strip('/') + '/leaf/')
                            current_app.logger.debug(srv["webserver_url"] + Config.DYNAMIC_PATH.strip('/') + '/leaf/')
                            current_app.logger.debug(Config.LEAFCMS_SERVER)
                            data = data.replace(Config.LEAFCMS_SERVER, srv["webserver_url"] + Config.DYNAMIC_PATH.strip('/') + '/leaf/')
                            with open(local_path, "w") as outFile:
                                outFile.write(data)

                            # Replace Preview Reference with Live webserver references
                            # with open(local_path) as inFile:
                            #     data = inFile.read()
                            #     original_content = data
                            # data = data.replace(str(os.path.join(Config.LEAFCMS_SERVER.rstrip("/"), Config.IMAGES_WEBPATH.lstrip('/leaf/').rstrip("/"))), str(os.path.join("/", Config.REMOTE_UPLOADS_FOLDER.lstrip("/"))))
                            # with open(local_path, "w") as outFile:
                            #     outFile.write(data)

                            # assets = find_page_assets(original_content)

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
                                    assetRemotePath = os.path.join(srv["remote_path"], Config.DYNAMIC_PATH.strip('/'), Config.IMAGES_WEBPATH, assetFilename)
                                    actionResultAsset, alp, arp = upload_file_with_retry(assetLocalPath, assetRemotePath, scp)
                                    if not actionResultAsset:
                                        try:
                                            current_app.logger.debug("Failed to SCP - " + lp + " - " + rp)
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

                    # Regenerate Feed
                    if not isMenu:
                        # This will generate a global feed for all items using the same template
                        if list_feed_path and list_feed_path != "":
                            gen_feed(mycursor, account_list, list_feed_path, listName, accountId)

                        if rss_ids and rss_ids != "":
                            update_feed_lists_and_or_delete_from_directory(mycursor, account_list, rss_ids, listName, accountId, site_ids, thisType, pages_to_delete_from_feed)
                        else:
                            update_feed_lists_and_or_delete_from_directory(mycursor, account_list, False, listName, accountId, site_ids, thisType, pages_to_delete_from_feed)

        else:
            print("Publication date in the future: " + str(target_date) + "; current date: " + str(current_date))

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

    if not listName or ((listName and target_date and target_date <= current_date) or (listName and not target_date)):
        # Update on DB
        mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", (action, workflow_id))
        mydb.commit()

        jsonR = {"message": "success", "action": action}
        return jsonR
    else:

        if not_real_request is None:
            # Update on DB
            mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", ("7", workflow_id))
            mydb.commit()
        else:
            print("No need to Set Status as it's already set to 'Waiting'")

        return {"message": "waiting", "action": action}


# Function to check if a column exists in the table
def column_exists(cursor, table_name, column_name):
    cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'")
    return cursor.fetchone() is not None


def update_feed_lists_and_or_delete_from_directory(mycursor, account_list, rss_ids, list_name, accountId, site_ids, thisType, pages):
    if rss_ids:
        rss_ids = rss_ids.split(",")

    site_ids = site_ids.split(",")
    for site_item in site_ids:
        if thisType != 8:
            query_list = f"SELECT * FROM account_{accountId}_list_{list_name} WHERE id=%s"
            params_list = (site_item,)
            mycursor.execute(query_list, params_list)
            pages = mycursor.fetchall()

        # Get column headers from the cursor description
        headers = [description[0] for description in mycursor.description]

        # Combine headers and data
        results = [dict(zip(headers, row)) for row in pages]
        result = results[0]

        if rss_ids:
            for rss_item in rss_ids:
                rss_data = get_rss_feed_by_id(rss_item)
                update_rss_feed(mycursor, accountId, list_name, rss_data[0][2], result, thisType)
        else:
            update_rss_feed(mycursor, accountId, list_name, False, result, thisType)


def gen_feed(mycursor, account_list, list_feed_path, list_name, accountId):
    query = f"SELECT * FROM {account_list}"
    mycursor.execute(query)
    list_column_names = [desc[0] for desc in mycursor.description]
    list_results = mycursor.fetchall()
    list_items = [{list_column_names[i]: item[i] for i in range(len(list_column_names))} for item in list_results]

    template_query = f"SELECT template_location FROM account_%s_list_template WHERE in_lists=%s"
    params = (int(accountId), list_name,)
    mycursor.execute(template_query, params)
    result_list = mycursor.fetchone()

    if result_list and len(result_list) > 0:
        list_template = result_list[0]

        # Regular expression to find words within curly braces
        pattern = r'{(.*?)}'

        # Using re.findall() to extract the contents within the braces
        items = re.findall(pattern, list_template)

        publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']

        for srv in Config.DEPLOYMENTS_SERVERS:
            # Define the RSS feed's root and channel elements
            rss = ET.Element("rss", version="2.0")
            rss.set("encoding", "UTF-8")
            channel = ET.SubElement(rss, "channel")

            # Populate the channel with some metadata
            ET.SubElement(channel, "title").text = "News"
            ET.SubElement(channel, "generator").text = "Leaf"
            ET.SubElement(channel, "link").text = os.path.join(srv["webserver_url"], list_feed_path)
            ET.SubElement(channel, "description").text = "Latest news"

            # Add each news item to the channel
            for item in list_items:

                if is_empty_item(item):
                    continue  # Skip this item entirely if it's empty or all fields are empty

                item_elem = ET.SubElement(channel, "item")
                guid_found = False
                image_element = None  # Track the image element to attach captions
                for key, value in item.items():

                    if key.lower() == 'id':
                        query_list_item = f"SELECT * FROM account_{accountId}_list_{list_name} WHERE id=%s"
                        params_list_item = (value,)
                        mycursor.execute(query_list_item, params_list_item)
                        fields_to_link = mycursor.fetchall()

                        # Get column headers from the cursor description
                        headers = [description[0] for description in mycursor.description]

                        # Combine headers and data
                        item_results = [dict(zip(headers, row)) for row in fields_to_link]

                        publication_date = False

                        list_page_url = list_template

                        for result in item_results:
                            for item_key, item_value in result.items():
                                if item_key.lower() in publication_names:
                                    publication_date = item_value
                                else:
                                    list_page_url = list_page_url.replace("{" + item_key + "}", str(item_value))

                        if publication_date:
                            for field in items:
                                if field == "year" or field == "month" or field == "day":
                                    single_field = extract_month_and_day(publication_date, field)
                                    single_field = str(single_field)

                                    list_page_url = list_page_url.replace("{" + field + "}", single_field)

                    if publication_date:
                        if key.lower() == 'id' or key.lower() == 'modified_by' or key.lower() == 'created_by':
                            continue  # Skip if it's the id key, modified_by key or created_by key

                        if is_empty_or_whitespace(value):
                            continue  # Skip creating element for empty or whitespace-only values

                        if isinstance(value, datetime.datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')

                        # Check if this field can serve as a GUID
                        if is_guid_candidate(key):
                            if isinstance(value, str) and not (value.startswith('http://') or value.startswith('https://')):
                                value = os.path.join(srv["webserver_url"], list_page_url)
                                value = value + (Config.PAGES_EXTENSION if not value.endswith(Config.PAGES_EXTENSION) else "")

                            guid_elem = ET.SubElement(item_elem, "guid")
                            guid_elem.text = value
                            guid_found = True

                        # Normalize key names to camelCase
                        normalized_key = camel_case_convert(key)
                        sub_elem = ET.SubElement(item_elem, normalized_key)
                        sub_elem.text = value

                        # Check for image URLs and create a separate image element
                        if is_image_url(str(value)):
                            image_element = ET.SubElement(sub_elem, "image")
                            ET.SubElement(image_element, "url").text = value

                        # Attach captions directly to the image element
                        if image_element and is_caption_key(key):
                            ET.SubElement(image_element, "title").text = value

                # Ensure every item has a GUID, falling back to a default message if none is found
                if not guid_found:
                    channel.remove(item_elem)
                # if not guid_found:
                # ET.SubElement(item_elem, "guid").text = "Unique identifier not found"

            # Write the complete RSS feed to a file
            tree = ET.ElementTree(rss)
            sitemap_path = os.path.join(Config.WEBSERVER_FOLDER, list_feed_path)
            # Ensure the directory exists
            sitemap_directory = os.path.dirname(sitemap_path)
            if not os.path.exists(sitemap_directory):
                os.makedirs(sitemap_directory)
            tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)

            # SCP Files
            remote_path = os.path.join(srv["remote_path"], list_feed_path)
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

        # Gen Local RSS Feed File
        rss = ET.Element("rss", version="2.0")
        rss.set("encoding", "UTF-8")
        channel = ET.SubElement(rss, "channel")

        # Populate the channel with some metadata
        ET.SubElement(channel, "title").text = "News"
        ET.SubElement(channel, "generator").text = "Leaf"
        ET.SubElement(channel, "link").text = os.path.join(Config.PREVIEW_SERVER, list_feed_path)
        ET.SubElement(channel, "description").text = "Latest news"

        # Add each news item to the channel
        for item in list_items:

            if is_empty_item(item):
                continue  # Skip this item entirely if it's empty or all fields are empty

            item_elem = ET.SubElement(channel, "item")
            guid_found = False
            image_element = None  # Track the image element to attach captions
            for key, value in item.items():

                if key.lower() == 'id':
                    query_list_item = f"SELECT * FROM account_{accountId}_list_{list_name} WHERE id=%s"
                    params_list_item = (value,)
                    mycursor.execute(query_list_item, params_list_item)
                    fields_to_link = mycursor.fetchall()

                    # Get column headers from the cursor description
                    headers = [description[0] for description in mycursor.description]

                    # Combine headers and data
                    item_results = [dict(zip(headers, row)) for row in fields_to_link]

                    publication_date = False

                    list_page_url = list_template

                    for result in item_results:
                        for item_key, item_value in result.items():
                            if item_key.lower() in publication_names:
                                publication_date = item_value
                            else:
                                list_page_url = list_page_url.replace("{" + item_key + "}", str(item_value))

                    if publication_date:
                        for field in items:
                            if field == "year" or field == "month" or field == "day":
                                single_field = extract_month_and_day(publication_date, field)
                                single_field = str(single_field)

                                list_page_url = list_page_url.replace("{" + field + "}", single_field)

                if publication_date:
                    if key.lower() == 'id' or key.lower() == 'modified_by' or key.lower() == 'created_by':
                        continue  # Skip if it's the id key

                    if is_empty_or_whitespace(value):
                        continue  # Skip creating element for empty or whitespace-only values

                    if isinstance(value, datetime.datetime):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')

                    # Check if this field can serve as a GUID
                    if is_guid_candidate(key):
                        if isinstance(value, str) and not (value.startswith('http://') or value.startswith('https://')):
                            value = os.path.join(Config.PREVIEW_SERVER, list_page_url)
                            value = value + (Config.PAGES_EXTENSION if not value.endswith(Config.PAGES_EXTENSION) else "")

                        guid_elem = ET.SubElement(item_elem, "guid")
                        guid_elem.text = value
                        guid_found = True

                    # Normalize key names to camelCase
                    normalized_key = camel_case_convert(key)
                    sub_elem = ET.SubElement(item_elem, normalized_key)
                    sub_elem.text = value

                    # Check for image URLs and create a separate image element
                    if is_image_url(str(value)):
                        image_element = ET.SubElement(sub_elem, "image")
                        ET.SubElement(image_element, "url").text = value

                    # Attach captions directly to the image element
                    if image_element and is_caption_key(key):
                        ET.SubElement(image_element, "title").text = value

            # Ensure every item has a GUID, falling back to a default message if none is found
            if not guid_found:
                channel.remove(item_elem)
            # if not guid_found:
            # ET.SubElement(item_elem, "guid").text = "Unique identifier not found"

        # Write the complete RSS feed to a file
        tree = ET.ElementTree(rss)
        sitemap_path = os.path.join(Config.WEBSERVER_FOLDER, list_feed_path)
        # Ensure the directory exists
        sitemap_directory = os.path.dirname(sitemap_path)
        if not os.path.exists(sitemap_directory):
            os.makedirs(sitemap_directory)
        tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)


def find_page_assets(original_content):
    # Get all assets on the page
    soup = BeautifulSoup(original_content, "html5lib")
    imgAssets = [asset["src"] for asset in soup.find_all("img", {"src": lambda src: src and Config.LEAFCMS_SERVER in src})]
    pdfAssets = [asset["href"] for asset in soup.find_all("a", {"href": lambda href: href and href.endswith(".pdf") and Config.LEAFCMS_SERVER in href})]
    assets = imgAssets + pdfAssets

    return assets


def update_rss_feed(mycursor, account_id, list_name, file_path, new_item_data, thisType):
    tree = False
    root = False
    if file_path:
        tree, root = parse_xml(os.path.join(Config.WEBSERVER_FOLDER, file_path))
    create_or_update_item_element(tree, root, mycursor, account_id, list_name, new_item_data, file_path, thisType)


def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return tree, root


def find_item_by_guid(root, new_guid):
    for item in root.findall('./channel/item'):
        guid = item.find('guid').text
        # print(guid + " : "+ new_guid)
        if guid == new_guid:
            return item
    return None


def find_and_delete_item_by_guid(root, new_guid):
    channel = root.find('./channel')
    for item in channel.findall('item'):
        guid = item.find('guid').text
        if guid == new_guid:
            channel.remove(item)
            return True
    return False


def create_or_update_item_element(tree, root, mycursor, account_id, list_name, new_item_data, file_path, thisType):
    template_query = f"SELECT template_location FROM account_%s_list_template WHERE in_lists=%s"
    params = (int(account_id), list_name,)
    mycursor.execute(template_query, params)
    list_template_result = mycursor.fetchone()

    if list_template_result and len(list_template_result) > 0:
        list_template = list_template_result[0]

        # Regular expression to find words within curly braces
        pattern = r'{(.*?)}'

        # Using re.findall() to extract the contents within the braces
        items = re.findall(pattern, list_template)

        publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']

        item = ET.Element('item')

        for srv in Config.DEPLOYMENTS_SERVERS:
            guid_found = False
            existing_item = False
            publication_date = False
            publication_date_formated = False
            guid_key = False
            guid_key_value = False
            list_page_url = list_template
            image_element = None  # Track the image element to attach captions

            if tree:
                for key, value in new_item_data.items():
                    # Check if this field can serve as a GUID
                    if is_guid_candidate(key):
                        guid_key = key
                        guid_key_value = value
                        guid_found = True

                    if key.lower() in publication_names:
                        publication_date = value
                        value = format_pub_date(value)
                    else:
                        list_page_url = list_page_url.replace("{" + key + "}", str(value))

                    if publication_date:
                        for field in items:
                            if field == "year" or field == "month" or field == "day":
                                single_field = extract_month_and_day(publication_date, field)
                                single_field = str(single_field)

                                list_page_url = list_page_url.replace("{" + field + "}", single_field)

                        if isinstance(value, datetime.datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')

                    if key.lower() == 'id' or key.lower() == 'modified_by' or key.lower() == 'created_by' or key.lower() == 'created' or key.lower() == 'modified' or key.lower() == 'leaf_selected_rss':
                        continue  # Skip if it's the id key, modified_by key or created_by key

                    if is_empty_or_whitespace(value):
                        continue  # Skip creating element for empty or whitespace-only values

                    # Normalize key names to camelCase
                    normalized_key = camel_case_convert(key)
                    if guid_key != key:
                        sub_elem = ET.SubElement(item, normalized_key)
                        sub_elem.text = value

                    # Check for image URLs and create a separate image element
                    if is_image_url(str(value)):
                        image_element = ET.SubElement(sub_elem, "image")
                        ET.SubElement(image_element, "url").text = value

                    # Attach captions directly to the image element
                    if image_element and is_caption_key(key):
                        ET.SubElement(image_element, "title").text = value

            if guid_found:
                if isinstance(guid_key_value, str) and not (guid_key_value.startswith('http://') or guid_key_value.startswith('https://')):
                    guid_key_value = os.path.join(srv["webserver_url"], list_page_url)
                    guid_key_value = guid_key_value + (Config.PAGES_EXTENSION if not guid_key_value.endswith(Config.PAGES_EXTENSION) else "")

                guid_elem = ET.SubElement(item, "guid")
                guid_elem.text = guid_key_value
                existing_item = find_item_by_guid(root, guid_key_value)

                guid_candidate_elem = ET.SubElement(item, guid_key)
                guid_candidate_elem.text = guid_key_value

                existing_item = find_item_by_guid(root, guid_key_value)

                if thisType == 8:
                    delete_item_from_disk(list_page_url)

                if existing_item:
                    if thisType == 8:
                        existing_item = find_and_delete_item_by_guid(root, guid_key_value)
                    else:
                        for elem in item:
                            existing_elem = existing_item.find(elem.tag)
                            if existing_elem is not None:
                                existing_elem.text = elem.text
                            else:
                                existing_item.append(elem)
                        create_or_update_item_element(tree, root, mycursor, account_id, list_name, item, file_path, thisType)
                        # Write the RSS Feed in Preview Server

                    tree.write(os.path.join(Config.WEBSERVER_FOLDER, file_path), encoding='UTF-8', xml_declaration=True)

                    # Write the RSS Feed in Remote Server
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
                        create_remote_folder(scp, os.path.dirname(os.path.join(srv["remote_path"], file_path)))
                        scp.put(os.path.join(Config.WEBSERVER_FOLDER, file_path), os.path.join(srv["remote_path"], file_path))

                    if thisType == 8:
                        print("Existing item deleted in RSS feed.")
                    else:
                        print("Existing item updated in RSS feed.")
                else:
                    if thisType != 8:
                        add_item_to_channel(tree, root, item, file_path, account_id, list_name, mycursor, srv)
                        print("New item added to RSS feed.")
                    else:
                        print("No item to remove in RSS feed.")
            else:
                if thisType == 8:
                    delete_item_from_disk(list_page_url)


def add_item_to_channel(tree, root, new_item, file_path, account_id, list_name, mycursor, srv):
    channel = root.find('channel')
    channel.append(new_item)
    # Write the RSS Feed in Preview Server
    tree.write(os.path.join(Config.WEBSERVER_FOLDER, file_path), encoding='UTF-8', xml_declaration=True)

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
        create_remote_folder(scp, os.path.dirname(os.path.join(srv["remote_path"], file_path)))
        scp.put(os.path.join(Config.WEBSERVER_FOLDER, file_path), os.path.join(srv["remote_path"], file_path))


def delete_item_from_disk(item_path):
    to_delete = os.path.join(Config.WEBSERVER_FOLDER, item_path)
    to_delete = to_delete + (Config.PAGES_EXTENSION if not to_delete.endswith(Config.PAGES_EXTENSION) else "")
    if os.path.isfile(to_delete):
        os.remove(to_delete)
        print(f"File {to_delete} has been removed.")
    else:
        print(f"File {to_delete} does not exist.")
    for srv in Config.DEPLOYMENTS_SERVERS:
        to_delete_remote = os.path.join(srv['remote_path'], item_path)
        to_delete_remote = to_delete_remote + (Config.PAGES_EXTENSION if not to_delete_remote.endswith(Config.PAGES_EXTENSION) else "")
        if os.path.isfile(to_delete_remote):
            os.remove(to_delete_remote)
            print(f"File {to_delete_remote} has been removed.")
        else:
            print(f"File {to_delete_remote} does not exist.")


def format_pub_date(date_str):
    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')


def camel_case_convert(key):
    """Convert keys from 'pub-date' or 'pub date' to 'pubDate'."""
    parts = re.split('-| ', key)
    return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])


def is_guid_candidate(key):
    """Determine if the key is a suitable candidate for use as a GUID."""
    candidates = ['link', 'url', 'file_link', 'file_url', 'item_link', 'item_url', 'doc_link', 'document_url']
    key_lower = key.lower().replace('_', '').replace('-', '')
    return any(candidate in key_lower for candidate in candidates)


def is_image_url(url):
    """Check if a URL points to an image based on its extension."""
    return re.search(r'\.(jpg|jpeg|png|gif)$', url, re.IGNORECASE)


def is_caption_key(key):
    """Check if the key likely represents a caption."""
    return 'caption' in key.lower() or 'imgcaption' in key.lower() or 'imagecaption' in key.lower()


def is_empty_item(item):
    """Check if the news item is empty or contains only empty fields."""
    return all(not value.strip() if isinstance(value, str) else False for value in item.values())


def is_empty_or_whitespace(value):
    """Check if the given value is empty or consists only of whitespace."""
    return isinstance(value, str) and not value.strip()


def add_leading_zero(value):
    """Ensures that all single-digit numbers are returned with a leading zero."""
    return f"{value:02d}"


def extract_month_and_day(date_string, field):
    """Extracts the year, month, or day from a date string based on the provided field."""
    year, month, day = None, None, None

    # Detect and parse the date format
    if "-" in date_string:
        date_string = date_string.split(" ")[0]
        year_str, month_str, day_str = date_string.split("-")
    elif "/" in date_string:
        date_string = date_string.split(" ")[0]
        year_str, month_str, day_str = date_string.split("/")
    elif date_string.isdigit():  # Check if the string is a valid epoch time
        date = datetime.fromtimestamp(int(date_string))
        year, month, day = date.year, date.month, date.day
    else:  # Assume the format is "Day, DD Month YYYY"
        parts = date_string.split(" ")
        day_str = parts[1]
        month_str = parts[2]
        year_str = parts[3]
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month = month_names.index(month_str[:3]) + 1

    # Convert to integers and format if not already done
    if not year:  # Will only execute these lines if year is None (handles non-epoch cases)
        year = add_leading_zero(int(year_str))
        month = add_leading_zero(int(month_str))
        day = add_leading_zero(int(day_str))
    # Return the requested part
    field = field.lower()
    if field == "year":
        return year
    elif field == "month":
        return month
    elif field == "day":
        return day


def check_if_should_publish_items():
    mydb, mycursor = decorators.db_connection()
    mycursor.execute(f"SELECT * FROM workflow WHERE status=7")
    data = mycursor.fetchall()

    # Fetch column headers from the cursor
    column_headers = [i[0] for i in mycursor.description]

    # Convert query result to list of dictionaries
    waiting_workflows = [dict(zip(column_headers, row)) for row in data]

    # Process each workflow
    for workflow in waiting_workflows:
        if workflow["type"] == 1:
            check_if_should_publish_pages(workflow)
        elif workflow["type"] == 3:
            check_if_should_publish_list(workflow)


def check_if_should_publish_pages(workflow):
    mydb, mycursor = decorators.db_connection()

    workflow_id = workflow["id"]

    # Skip if pubDate
    if workflow["pubDate"] > datetime.datetime.now():
        return

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

        assets = find_page_assets(original_content)

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
    query = "SELECT id, site_id FROM site_meta WHERE HTMLPath = %s"
    mycursor.execute(query, [HTMLPath])
    page_id, site_id = mycursor.fetchone()
    gen_sitemap(mycursor, site_id, 1)

    # Get Assign User Info
    editorInfo = get_user_details(workflow["assignEditor"], mycursor)

    # Git operations
    query = "SELECT workflow.comments FROM workflow WHERE id = %s"
    mycursor.execute(query, [workflow_id])
    workflow_comment = mycursor.fetchone()[0]
    Config.GIT_REPO.index.add([os.path.join(Config.WEBSERVER_FOLDER, HTMLPath), os.path.join(Config.WEBSERVER_FOLDER, "sitemap.xml")])
    Config.GIT_REPO.index.commit(workflow_comment, author=Actor(editorInfo["username"], editorInfo["email"]))

    # Update DB Status
    mycursor.execute("UPDATE workflow SET status = %s WHERE id = %s", ("Approved", workflow_id))
    mydb.commit()


def check_if_should_publish_list(workflow):
    publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']

    mydb, mycursor = decorators.db_connection()

    try:

        template_query = f"SELECT template_location, feed_location FROM account_%s_list_template WHERE in_lists=%s"
        template_params = (workflow['accountId'], workflow['listName'],)
        mycursor.execute(template_query, template_params)
        template_list = mycursor.fetchone()

        if template_list and len(template_list) > 0:
            list_template = template_list[0]
            list_feed = template_list[1]

            # Regular expression to find words within curly braces
            pattern = r'{(.*?)}'

            # Using re.findall() to extract the contents within the braces
            items = re.findall(pattern, list_template)

            site_ids = workflow['siteIds']
            query_list = f"SELECT * FROM account_{workflow['accountId']}_list_{workflow['listName']} WHERE id=%s"
            params_list = (site_ids,)
            mycursor.execute(query_list, params_list)
            fields_to_link = mycursor.fetchall()

            # Get column headers from the cursor description
            headers = [description[0] for description in mycursor.description]

            # Combine headers and data
            results = [dict(zip(headers, row)) for row in fields_to_link]

            publication_date = False

            list_page_url = list_template

            if results and len(results) > 0:
                for result in results:
                    for key, value in result.items():
                        if key.lower() in publication_names:
                            publication_date = value
                        else:
                            list_page_url = list_page_url.replace("{" + key + "}", str(value))

                if publication_date:
                    for field in items:
                        if publication_date and (field == "year" or field == "month" or field == "day"):
                            single_field = extract_month_and_day(publication_date, field)
                            single_field = str(single_field)

                            list_page_url = list_page_url.replace("{" + field + "}", single_field)
                            list_page_url = f"{list_page_url}" + (Config.PAGES_EXTENSION if not list_page_url.endswith(Config.PAGES_EXTENSION) else "")

                    passed_session = {"accountId": workflow['accountId']}

                    jsonConfig = get_list_configuration(workflow['accountId'], workflow['listName'], passed_session)

                    # Process the JSON response
                    jsonConfigSaveByFields = None
                    jsonConfigFieldsToSaveBy = None

                    if 'columns' in jsonConfig and len(jsonConfig['columns']) > 0:
                        if len(jsonConfig['columns'][0]) > 3:
                            jsonConfigSaveByFields = jsonConfig['columns'][0][3]
                        if len(jsonConfig['columns'][0]) > 4:
                            jsonConfigFieldsToSaveBy = jsonConfig['columns'][0][4]

                    new_request_data = {
                        "id": workflow['id'],
                        "status": workflow['status'],
                        "type": workflow['type'],
                        "listName": workflow['listName'],
                        "saveByFields": jsonConfigSaveByFields,
                        "fieldsToSaveBy": jsonConfigFieldsToSaveBy,
                        "files_details": "",
                        "site_ids": site_ids,
                        "list_item_url_path": list_page_url,
                        "list_feed_path": list_feed,
                        "publication_date": publication_date,
                        "accountId": int(workflow['accountId']),
                        "user_id": workflow['assignEditor']
                    }

                    # Simulate a request object
                    class MockRequest:
                        def __init__(self, form_data):
                            self.form = MultiDict(form_data)

                    # print(new_request_data)
                    # Create a mock request object
                    mock_request = MockRequest(new_request_data)
                    new_action_workflow = proceed_action_workflow(mock_request, True)

                else:
                    print(site_ids + " has no publication date defined!", flush=True)

            else:
                print(workflow['listName'] + " as no template defined!", flush=True)
    except Exception as e:
        # Log the error or handle it as needed

        raise e
    finally:
        mydb.close()
