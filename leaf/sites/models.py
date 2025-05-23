import copy
import os
import re
import shutil
import urllib.parse
import xml.etree.ElementTree as ET

import requests
import urllib3
from flask import Blueprint, session
from requests.auth import HTTPDigestAuth

from leaf import decorators
from leaf.config import Config

sites = Blueprint('sites', __name__)


def getSiteFromPageId(pageId):
    """
    Get the site ID associated with a given page ID.

    Parameters:
        pageId (int): The ID of the page.

    Returns:
        int: The ID of the site to which the page belongs.
    """
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Retrieve the site ID using a SQL query
        query = "SELECT site_id FROM site_meta WHERE id = %s"
        params = (pageId,)
        mycursor.execute(query, params)
        site_id = mycursor.fetchone()[0]

        # Close the database connection
        mydb.close()

        return int(site_id)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while getting site ID from page ID: {str(e)}")


def site_belongs_to_account(site_id):
    """
    Check if the specified site ID belongs to the specified account ID.

    Args:
        site_id (int): The ID of the site to check.

    Returns:
        bool: True if the site belongs to the account, False otherwise.
    """
    try:
        accountId = session["accountId"]
        mydb, mycursor = decorators.db_connection()

        # Check if the site ID belongs to the specified account
        mycursor.execute("SELECT COUNT(*) FROM sites WHERE id = %s AND accountId = %s", (site_id, accountId))
        result = mycursor.fetchone()

        # If there is at least one matching record, the site belongs to the account
        return result[0] > 0

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        print(f"An error occurred: {str(e)}")
        return False

def getSitesList():
    """
    Retrieve a list of sites for the current user's account.

    Uses the account ID from the session to query the database and fetch
    site information. Returns the site information in a list of dictionaries.

    Returns:
        list: A list of dictionaries containing site information.
    """
    try:
        # Get the account ID from the session
        account_id = session['accountId']

        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Execute the SQL query to fetch site information
        mycursor.execute("SELECT id, base_url, base_folder, submitted_datetime, status FROM sites WHERE accountId = %s", [account_id])
        results = mycursor.fetchall()

        # Create a list of sites in a dictionary format
        sites_list = [{"id": site[0], "base_url": site[1], "base_folder": site[2], "submitted_datetime": site[3], "status": site[4]} for site in results]

        return sites_list

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching sites: {str(e)}")


# def get_user_access_folder(mycursor=None):
#     """
#     Retrieve the folder paths that a user has access to.

#     Parameters:
#     - mycursor: MySQL cursor object used to execute queries.

#     Returns:
#     - List of folder paths (strings) that the user has access to.
#     """

#     # Get a database connection using the 'db_connection' decorator
#     if mycursor is None:
#         mydb, mycursor = decorators.db_connection()

#     # Get User Access folders
#     if session["is_admin"] == 1:
#         query = "SELECT ua.folder_path FROM leaf.user_access ua"
#         mycursor.execute(query)
#     else:
#         query = "SELECT ua.folder_path FROM leaf.user_access ua JOIN leaf.user_groups ug ON ua.group_id = ug.group_id JOIN leaf.group_member gm ON ug.group_id = gm.group_id WHERE gm.user_id = %s"
#         mycursor.execute(query, (session["id"],))
#     return [folder_path[0] for folder_path in mycursor.fetchall()]

def get_user_access_folder(mycursor=None):
    """
    Retrieve the folder paths that a user has access to, removing duplicates and sorting alphabetically.

    Parameters:
    - mycursor: MySQL cursor object used to execute queries.

    Returns:
    - List of unique folder paths (strings) that the user has access to, sorted alphabetically.
    """

    # Get a database connection using the 'db_connection' decorator
    if mycursor is None:
        mydb, mycursor = decorators.db_connection()

    # Get User Access folders
    if session["is_admin"] == 1:
        query = "SELECT DISTINCT ua.folder_path FROM leaf.user_access ua ORDER BY ua.folder_path ASC"
        mycursor.execute(query)
    else:
        query = """
            SELECT DISTINCT ua.folder_path
            FROM leaf.user_access ua
            JOIN leaf.user_groups ug ON ua.group_id = ug.group_id
            JOIN leaf.group_member gm ON ug.group_id = gm.group_id
            WHERE gm.user_id = %s
            ORDER BY ua.folder_path ASC
        """
        mycursor.execute(query, (session["id"],))

    return [folder_path[0] for folder_path in mycursor.fetchall()]


def get_user_access_folder_for_lists(mycursor=None):
    """
    Retrieve the folder paths that a user has access to.

    Parameters:
    - mycursor: MySQL cursor object used to execute queries.

    Returns:
    - List of folder paths (strings) that the user has access to.
    """

    # Get a database connection using the 'db_connection' decorator
    if mycursor is None:
        mydb, mycursor = decorators.db_connection()

    # Get User Access folders
    if session["is_admin"] == 1:
        query = "SELECT ua.folder_path FROM leaf.user_access ua"
        mycursor.execute(query)
        folders_access = mycursor.fetchall()
    else:
        query = "SELECT ua.folder_path FROM leaf.user_access ua JOIN leaf.user_groups ug ON ua.group_id = ug.group_id JOIN leaf.group_member gm ON ug.group_id = gm.group_id WHERE gm.user_id = %s"
        mycursor.execute(query, (session["id"],))

        folders_access = mycursor.fetchall()
        if any(folder_path[0] == "/" for folder_path in folders_access):
            query = "SELECT ua.folder_path FROM leaf.user_access ua"
            mycursor.execute(query)
            folders_access = mycursor.fetchall()

    return [folder_path[0] for folder_path in folders_access]


def check_if_page_locked_by_me(page_id):
    """
    Checks if the specified page is locked by the current session user. It queries the database to find the user 
    who has locked the page and compares it with the current session user.

    Parameters:
    - page_id (int or str): The ID of the page whose lock status is being checked. Although typically an integer,
      it may be passed as a string if not cast beforehand.

    Returns:
    - dict: A dictionary containing the lock status and details of the user who locked the page. The dictionary 
      includes:
        - user_id (int or False): The user ID of the user who locked the page or False if no user found.
        - username (str or False): The username of the user who locked the page or False if no user found.
        - email (str or False): The email of the user who locked the page or False if no user found.
        - locked_by_me (bool): True if the current session user locked the page, False otherwise.

    Raises:
    - Exception: Propagates any exceptions that occur during database operations, including connection issues
      or SQL errors. The exception contains a message that can help identify the failure point.
    """
    user_id = session["id"]

    result = {
        'user_id': False,
        'username': False,
        'email': False,
        'locked_by_me': False
    }
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Query to check who locked the page
        mycursor.execute("""
            SELECT u.id, u.username, u.email
            FROM site_meta sa
            JOIN user u ON sa.locked_by = u.id
            WHERE sa.id = %s
        """, [page_id])

        row = mycursor.fetchone()
        if row:
            result = {
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'locked_by_me': (row[0] == session['id'])
            }

        mydb.commit()
    except Exception as e:
        mydb.rollback()
        raise
    finally:
        mydb.close()

    return result


def lock_unlock_page(page_id, site_id, action):
    """
    Locks or unlocks a page in the `site_meta` table based on the given action.

    Parameters:
    page_id (int): The unique identifier for the page.
    site_id (int): The identifier of the site where the page is located.
    action (str): Specifies the action to perform. Expected values are "lock" or "unlock".

    Returns:
    is_page_locked: True if the action was successfully executed, False otherwise.
    page_locked_status: The new page status

    Raises:
    ValueError: If 'action' is neither "lock" nor "unlock".
    Exception: If database queries fail or connections are problematic.
    """

    # Validate the action input
    if action not in ["lock", "unlock"]:
        raise ValueError("Action must be 'lock' or 'unlock'")

    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()
        # SQL to update the page state
        if action == "lock":
            sql = """
            UPDATE site_meta 
            SET locked = 1, locked_by = %s 
            WHERE id = %s AND site_id = %s
            """
            mycursor.execute(sql, (session["id"], page_id, site_id))
        elif action == "unlock":
            sql = """
            UPDATE site_meta 
            SET locked = 0, locked_by = NULL 
            WHERE id = %s AND site_id = %s
            """
            mycursor.execute(sql, (page_id, site_id))

        mydb.commit()
    except Exception as e:
        mydb.rollback()
        raise
    finally:
        mydb.close()

    if action == "lock":
        return {"is_page_locked": True, "page_locked_status": action}
    if action == "unlock":
        return {"is_page_locked": False, "page_locked_status": action}


def get_site_data(site_id):
    """
    Retrieve pages from the specified site.

    Uses a database connection obtained with the 'db_connection' decorator to execute
    a parameterized query to fetch pages from the 'site_meta' table. Returns the page
    data in a list of dictionaries.

    Args:
        site_id (str): The ID of the site for which to retrieve pages.

    Returns:
        list: A list of dictionaries containing page data.
    """

    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Create html_modules if does not exist
        accountId = session["accountId"]
        html_modules_table_name = f"account_{accountId}_html_modules"
        create_html_modules_query = f"CREATE TABLE IF NOT EXISTS {html_modules_table_name} (id INT AUTO_INCREMENT PRIMARY KEY UNIQUE, name VARCHAR(255) NOT NULL, html_content TEXT NOT NULL, modified_by INT(11) DEFAULT NULL, created DATETIME NULL DEFAULT CURRENT_TIMESTAMP, modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"
        mycursor.execute(create_html_modules_query)
        mydb.commit()

        # Get User Access folders
        folder_paths = get_user_access_folder(mycursor)

        # Get pages from the site
        query = "SELECT id, id, title, HTMLPath, modified_date, id, modified_by, locked, locked_by FROM site_meta WHERE status <> -1 AND site_id = %s"
        mycursor.execute(query, [site_id])
        site_pages = mycursor.fetchall()

        # Filter pages based on user access
        if session["is_admin"] == 0:
            access_pages = [{"id": page[0], "Screenshot": page[1], "Title": page[2], "URL": os.path.join(Config.PREVIEW_SERVER, page[3]), "Modified Date": page[4], "Action": page[5], "Modified By": page[6], "Locked": page[7], "Locked By": page[8]} for page in site_pages if any(page[3].startswith(path.lstrip("/")) for path in folder_paths)]
        else:
            access_pages = [{"id": page[0], "Screenshot": page[1], "Title": page[2], "URL": os.path.join(Config.PREVIEW_SERVER, page[3]), "Modified Date": page[4], "Action": page[5], "Modified By": page[6], "Locked": page[7], "Locked By": page[8]} for page in site_pages]

        return access_pages

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching sites: {str(e)}")


def get_site_log(site_id):
    """
    Retrieve the crawl log of a specified site.

    Args:
        site_id (str): The ID of the site for which to retrieve the crawl log.

    Returns:
        str: The crawl log content.
    """
    try:

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        HERITRIX_HEADERS = {"Accept": "application/xml"}

        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get Job name
        mycursor.execute("SELECT base_folder FROM sites WHERE id = %s", [site_id])
        base_folder = mycursor.fetchone()[0]
        job_name = base_folder

        # Get job log from Heritrix
        url = f"http://localhost:{Config.HERITRIX_PORT}/engine/job/{job_name}"
        auth = HTTPDigestAuth(Config.HERITRIX_USER, Config.HERITRIX_PASS)
        headers = HERITRIX_HEADERS

        response = requests.post(url=url, auth=auth, headers=headers, verify=False)
        response_xml = ET.fromstring(response.content.decode('UTF-8'))
        crawl_log_tail = "\n\n".join([line.text for line in response_xml.find("crawlLogTail").findall("value")])

        return crawl_log_tail

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching the crawl log: {str(e)}")


def add_new_site(site_data):
    """
    Add a new site to the system.

    This function performs the following actions:
    - Initiates a rescan action in Heritrix.
    - Creates a new job in Heritrix.
    - Modifies the configuration file for the created job in Heritrix, setting various parameters such as contact URL,
      seed URL, robots policy, boundaries, crawl limit, max toe threads, disposition processor, and warc writer.
    - Saves the modified configuration file.
    - Builds, launches, and unpauses the job in Heritrix.
    - Retrieves information about the newly added site from the database.

    Parameters:
        site_data (dict): A dictionary containing site information, including URL, label, ignore robots setting, maximum URLs,
                         generate screenshots, allowed domains, and rejected paths.

    Returns:
        dict: A JSON response indicating the success or failure of the operation and providing information about the added site.

    Raises:
        RuntimeError: If an error occurs during the process, a RuntimeError is raised.
    """

    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        HERITRIX_FOLDER = Config.HERITRIX_FOLDER
        HERITRIX_PORT = Config.HERITRIX_PORT
        HERITRIX_USER = Config.HERITRIX_USER
        HERITRIX_PASS = Config.HERITRIX_PASS
        HERITRIX_HEADERS = {"Accept": "application/xml"}

        # Rescan
        data = {"action": "rescan"}
        requests.post(url="https://localhost:" + HERITRIX_PORT + "/engine", auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

        # Create Job
        data = {"action": "create", "createpath": site_data["site_label"]}
        requests.post(url="https://localhost:" + HERITRIX_PORT + "/engine", auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

        # Rescan
        data = {"action": "rescan"}
        resp = requests.post(url="https://localhost:" + HERITRIX_PORT + "/engine", auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)
        resp = ET.fromstring(resp.content.decode("UTF-8"))

        # Modify Config File
        configFilePath = resp.find("jobs").find("value").find("primaryConfig").text

        ET.register_namespace("", "http://www.springframework.org/schema/beans")
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("context", "http://www.springframework.org/schema/context")
        ET.register_namespace("aop", "http://www.springframework.org/schema/aop")
        ET.register_namespace("tx", "http://www.springframework.org/schema/tx")

        with open(configFilePath, "r") as inFile:
            data = ET.fromstring(inFile.read())
            beans = data.findall("{http://www.springframework.org/schema/beans}bean")
            for entry in beans:
                beanId = entry.get("id")

                # Set CONTACT URL
                if beanId == "simpleOverrides":
                    valueText = entry[0][0].text
                    modValue = valueText.replace("ENTER_AN_URL_WITH_YOUR_CONTACT_INFO_HERE_FOR_WEBMASTERS_AFFECTED_BY_YOUR_CRAWL", site_data["site_url"])
                    entry[0][0].text = modValue

                # Set SEED URL
                elif beanId == "longerOverrides":
                    valueText = entry[0][0][0].text
                    modValue = valueText.replace("http://example.example/example", site_data["site_url"])
                    entry[0][0][0].text = modValue

                # Set ROBOTS
                elif beanId == "metadata":
                    newEntry = ET.Element("property")
                    newEntry.set("name", "robotsPolicyName")
                    newEntry.set("value", site_data["site_ignore_robots"])
                    entry.append(newEntry)

                # Set BOUNDARIES
                elif beanId == "scope":
                    entry = entry[0][0]
                    while len(entry) != 0:
                        entry.remove(entry[0])

                    newBean = ET.Element("bean")
                    newBean.set("class", "org.archive.modules.deciderules.RejectDecideRule")
                    entry.append(newBean)

                    newBean = ET.Element("bean")
                    newBean.set("class", "org.archive.modules.deciderules.TooManyHopsDecideRule")
                    newProperty = ET.Element("property")
                    newProperty.set("name", "maxHops")
                    newProperty.set("value", "1")
                    newBean.append(newProperty)
                    entry.append(newBean)

                    newBean = ET.Element("bean")
                    newBean.set("class", "org.archive.modules.deciderules.MatchesListRegexDecideRule")

                    newProperty = ET.Element("property")
                    newProperty.set("name", "decision")
                    newProperty.set("value", "ACCEPT")
                    newBean.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "listLogicalOr")
                    newProperty.set("value", "true")
                    newBean.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "regexList")

                    newList = ET.Element("list")

                    # Set Allowed Domain
                    site_data["site_allowed_domains"].append(site_data["site_url"])
                    for domain in site_data["site_allowed_domains"]:
                        newValue = ET.Element("value")
                        newValue.text = r"^(?:https?://)?(www\.)?" + re.escape(urllib.parse.urlparse(domain).netloc) + r".*$"
                        newList.append(newValue)

                    newValue = ET.Element("value")
                    newValue.text = "^dns.*$"
                    newList.append(newValue)

                    newProperty.append(newList)
                    newBean.append(newProperty)
                    entry.append(newBean)

                    newBean = ET.Element("bean")
                    newBean.set("class", "org.archive.modules.deciderules.MatchesListRegexDecideRule")

                    newProperty = ET.Element("property")
                    newProperty.set("name", "decision")
                    newProperty.set("value", "REJECT")
                    newBean.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "listLogicalOr")
                    newProperty.set("value", "true")
                    newBean.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "regexList")

                    newList = ET.Element("list")

                    # Set Rejected
                    site_reject_paths_BAK = copy.deepcopy(site_reject_paths)
                    site_reject_paths = [(".*/" + path + "/.*").replace("//", "/") for path in site_reject_paths]
                    site_reject_paths_BAK = [(".*/" + path.rstrip("/") + "?").replace("//", "/") for path in site_reject_paths_BAK]
                    site_reject_paths = site_reject_paths + site_reject_paths_BAK
                    for path in site_reject_paths:
                        newValue = ET.Element("value")
                        newValue.text = path
                        newList.append(newValue)

                    newProperty.append(newList)
                    newBean.append(newProperty)
                    entry.append(newBean)

                # Set CRAWL LIMIT
                elif beanId == "crawlLimiter" and site_data["site_max_urls"] != 0:
                    newProperty = ET.Element("property")
                    newProperty.set("name", "maxDocumentsDownload")
                    newProperty.set("value", str(site_data["site_max_urls"]))
                    entry.append(newProperty)

                # Set maxToeThreads
                elif beanId == "crawlController":
                    newProperty = ET.Element("property")
                    newProperty.set("name", "maxToeThreads")
                    newProperty.set("value", "50")
                    entry.append(newProperty)

                # Set DispositionProcessor
                elif beanId == "disposition":
                    newProperty = ET.Element("property")
                    newProperty.set("name", "delayFactor")
                    newProperty.set("value", "0")
                    entry.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "minDelayMs")
                    newProperty.set("value", "1")
                    entry.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "maxDelayMs")
                    newProperty.set("value", "1")
                    entry.append(newProperty)

                    newProperty = ET.Element("property")
                    newProperty.set("name", "maxPerHostBandwidthUsageKbSec")
                    newProperty.set("value", "0")
                    entry.append(newProperty)

                elif beanId == "warcWriter":
                    newProperty = ET.Element("property")
                    newProperty.set("name", "directory")
                    newProperty.set("value", str(os.path.join(HERITRIX_FOLDER, "jobs", site_data["site_label"])))
                    entry.append(newProperty)

        # Save ConfigFile
        with open(configFilePath, "wb") as outFile:
            outFile.write(ET.tostring(data))

        # Build
        data = {"action": "build"}
        requests.post(url="https://localhost:" + HERITRIX_PORT + "/engine/job/" + site_data["site_label"], auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

        # Launch
        data = {"action": "launch"}
        requests.post(url="https://localhost:" + HERITRIX_PORT + "/engine/job/" + site_data["site_label"], auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

        # Unpause
        data = {"action": "unpause"}
        requests.post(url="https://localhost:" + HERITRIX_PORT + "/engine/job/" + site_data["site_label"], auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get fields from inserted row
        query = "SELECT id, base_url, base_folder, submitted_datetime, status FROM sites WHERE id=%s"
        params = (site_data["site_id"],)
        mycursor.execute(query, params)
        site = mycursor.fetchone()

        # Return
        return {"message": "success", "id": site[0], "base_url": site[1], "base_folder": site[2], "submitted_datetime": site[3], "status": site[4]}
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while adding a new crawl: {str(e)}")


def update_site_info(original_site_id, new_site_url, new_site_folder):
    """
    Update the information of an existing site in the database.

    This function performs the following actions:
    - Gets a database connection using the 'db_connection' decorator.
    - Executes an SQL UPDATE query to update the base URL and base folder of the specified site.
    - Commits the changes to the database.

    Parameters:
        original_site_id (str): The original ID of the site to be updated.
        new_site_url (str): The new base URL for the site.
        new_site_folder (str): The new base folder for the site.

    Returns:
        dict: A JSON response indicating the success of the update and providing information about the updated site.
    """
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Execute SQL UPDATE query to update site information
        query = "UPDATE sites SET base_url=%s, base_folder=%s WHERE id=%s"
        params = (new_site_url, new_site_folder, original_site_id)
        mycursor.execute(query, params)

        # Commit the changes to the database
        mydb.commit()

        # Return information about the updated site
        result = {"site_to_update": original_site_id, "action": "updated"}

        mydb.close()
        return result

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while updating site information: {str(e)}")


def delete_sites(sites_to_delete):
    """
    Delete multiple sites.

    This function performs the following actions:
    - Deletes each specified site from the database.
    - Rescans Heritrix.
    - Pauses, terminates, and tears down the job in Heritrix.
    - Deletes the job folder from Heritrix.
    - Returns information about the deleted sites.

    Parameters:
        sites_to_delete (str): A comma-separated string containing the IDs of the sites to be deleted.

    Returns:
        dict: A JSON response indicating the success of the delete operation and providing information about the deleted sites.
    """
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        HERITRIX_FOLDER = Config.HERITRIX_FOLDER
        HERITRIX_PORT = Config.HERITRIX_PORT
        HERITRIX_USER = Config.HERITRIX_USER
        HERITRIX_PASS = Config.HERITRIX_PASS
        HERITRIX_HEADERS = {"Accept": "application/xml"}

        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Delete each site
        for site_id in sites_to_delete.split(","):
            # Get jobName
            query = "SELECT base_folder FROM sites WHERE id = %s"
            params = (site_id,)
            mycursor.execute(query, params)
            site_base_folder = mycursor.fetchone()[0]

            # Delete SQL entry
            query = "DELETE FROM sites WHERE id = %s"
            params = (site_id,)
            mycursor.execute(query, params)
            mydb.commit()

            # Rescan Heritrix
            data = {"action": "rescan"}
            requests.post(url=f"https://localhost:{HERITRIX_PORT}/engine", auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

            # Pause, Terminate Job, Teardown
            job_name = f"{session['accountId']}_{site_base_folder}"
            actions = ["pause", "terminate", "teardown"]
            for action in actions:
                data = {"action": action}
                requests.post(url=f"https://localhost:{HERITRIX_PORT}/engine/job/{job_name}", auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

            # Delete from Heritrix if exists
            job_folder = os.path.join(HERITRIX_FOLDER, "jobs", job_name)
            if os.path.exists(job_folder):
                shutil.rmtree(job_folder)

            # Rescan Heritrix
            data = {"action": "rescan"}
            requests.post(url=f"https://localhost:{HERITRIX_PORT}/engine", auth=HTTPDigestAuth(HERITRIX_USER, HERITRIX_PASS), data=data, headers=HERITRIX_HEADERS, verify=False)

        # Close the database connection
        mydb.close()

        # Return information about the deleted sites
        result = {"sites_to_delete": sites_to_delete, "action": "deleted"}
        return result

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while deleting sites: {str(e)}")


def user_has_access_page(page_id):
    """
    Checks if a user has access to a specific page based on their permissions.

    Args:
        page_id (int): The ID of the page to check access for.

    Returns:
        bool: True if the user has access to the page, False otherwise.

    Raises:
        RuntimeError: If an error occurs while checking for page access.
    """

    try:

        # Check if admin
        if session["is_admin"] == 1:
            return True

        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get User Access folders
        folder_paths = get_user_access_folder(mycursor)

        # Get URL from PageID
        mycursor.execute("SELECT HTMLPath FROM site_meta WHERE id=%s", (page_id,))
        HTMLPath = os.path.join(mycursor.fetchone()[0])

        for path in folder_paths:
            if HTMLPath.startswith(path.lstrip("/")):
                return True
        mydb.close()
        return False
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while checking for page access: {str(e)}")


def user_has_access_asset(asset_id):
    """
    Checks if a user has access to a specific asset based on their permissions.

    Args:
        asset_id (int): The ID of the asset to check access for.

    Returns:
        bool: True if the user has access to the asset, False otherwise.

    Raises:
        RuntimeError: If an error occurs while checking for asset access.
    """

    try:

        # Check if admin
        if session["is_admin"] == 1:
            return True

        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get User Access folders
        folder_paths = get_user_access_folder(mycursor)

        # Get URL from PageID
        mycursor.execute("SELECT path FROM site_assets WHERE id=%s", (asset_id,))
        asset_path = os.path.join(mycursor.fetchone()[0])

        for path in folder_paths:
            if asset_path.startswith(path.lstrip("/")):
                return True
        mydb.close()
        return False
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while checking for page access: {str(e)}")

def get_all_modules(request):
    if request.args.get("sEcho", type=str):
        jsonR = {'data': [], 'recordsTotal': 0, 'recordsFiltered': 0}
    else:
        jsonR = {'data': []}
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        limit = False
        skip = False
        direction = "-1"
        sortingColumn = False
        if request.args.get("iDisplayLength"):
            limit = int(request.args.get("iDisplayLength"))
        if request.args.get("iDisplayStart"):
            skip = int(request.args.get("iDisplayStart"))
        if request.args.get("sSortDir_0"):
            direction = request.args.get("sSortDir_0").upper()
        if request.args.get("iSortCol_0"):
            sortingColumn = request.args.get("iSortCol_0")


        accountId = session["accountId"]
        html_modules_table_name = f"account_{accountId}_html_modules"

        if sortingColumn:
            searchColumnsFields = []
            field_list = []

            search_value_1 = request.args.get(f"sSearch_1")
            search_value_2 = request.args.get(f"sSearch_2")
            search_value_3 = request.args.get(f"sSearch_3")
            if search_value_1:
                searchColumnsFields.append({"field": "name", "value": search_value_1.replace("((((", "").replace("))))", "")})
            if search_value_2:
                searchColumnsFields.append({"field": "modified_by", "value": search_value_2.replace("((((", "").replace("))))", "")})
            if search_value_3:
                searchColumnsFields.append({"field": "modified", "value": search_value_3.replace("((((", "").replace("))))", "")})

            for searchColumnsField in searchColumnsFields:
                searchColumnsFieldValue = searchColumnsField['value'].replace('"', "'")
                field_list.append(f"{searchColumnsField['field']} LIKE %s")

            userUsernameEmail = 'CONCAT(user.id, ", ", user.username, ", ", user.email)'

            where_clause = " AND ".join(field_list)

            order_by = "name"
            if int(sortingColumn) == 2:
                order_by = "modified_by"
            if int(sortingColumn) == 3:
                order_by = "modified"

            if field_list:
                query_params = list(f"%{searchColumnsField['value']}%" for searchColumnsField in searchColumnsFields)
                get_templates_query = f'SELECT {html_modules_table_name}.id, name, CONCAT(user.id, ", ", user.username, ", ", user.email), modified FROM {html_modules_table_name} INNER JOIN user ON {html_modules_table_name}.modified_by = user.id WHERE {where_clause} ORDER BY {order_by} {direction} LIMIT %s, %s'
                mycursor.execute(get_templates_query, query_params + [skip, limit])
            else:
                get_templates_query = f'SELECT {html_modules_table_name}.id, name, CONCAT(user.id, ", ", user.username, ", ", user.email), modified FROM {html_modules_table_name} INNER JOIN user ON {html_modules_table_name}.modified_by = user.id ORDER BY {order_by} {direction} LIMIT %s, %s'
                mycursor.execute(get_templates_query, (skip, limit))

            modules = mycursor.fetchall()

            mycursor.execute(f"SELECT COUNT(*) FROM {html_modules_table_name}")
            listCount = mycursor.fetchone()[0]

            jsonR['data'] = modules
            jsonR['recordsTotal'] = listCount
            jsonR['recordsFiltered'] = len(modules)

        else:

            mycursor.execute(f"SELECT id, name, modified_by, modified FROM {html_modules_table_name}")
            modules = mycursor.fetchall()

            jsonR = modules
        

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while retrieve modules: {str(e)}")
    finally:
        mydb.close()
        return jsonR

def get_single_modules(module_id):
    module = []
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        accountId = session["accountId"]
        html_modules_table_name = f"account_{accountId}_html_modules"

        mycursor.execute(f"SELECT * FROM {html_modules_table_name} WHERE id = %s", (module_id,))
        module = mycursor.fetchone()

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while retrieve modules: {str(e)}")
    finally:
        mydb.close()
        return module


def add_module(name, html_content):
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        accountId = session["accountId"]
        html_modules_table_name = f"account_{accountId}_html_modules"
        session_user_id = session["id"]

        mycursor.execute(f"INSERT INTO {html_modules_table_name} (name, html_content, modified_by) VALUES (%s, %s, %s)", (name, html_content, session_user_id))
        mydb.commit()
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while retrieve modules: {str(e)}")
        return False
    finally:
        mydb.close()
        return True

def update_module(module_id, name, html_content):
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        accountId = session["accountId"]
        html_modules_table_name = f"account_{accountId}_html_modules"
        session_user_id = session["id"]

        mycursor.execute(f"UPDATE {html_modules_table_name} SET name = %s, html_content = %s, modified_by = {session_user_id} WHERE id = %s", (name, html_content, module_id))
        mydb.commit()
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while retrieve modules: {str(e)}")
        return False
    finally:
        mydb.close()
        return True

def delete_module(module_to_delete):
    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        accountId = session["accountId"]
        html_modules_table_name = f"account_{accountId}_html_modules"

        module_to_delete = module_to_delete.split(",")

        for module_id in module_to_delete:
            mycursor.execute(f"DELETE FROM {html_modules_table_name} WHERE id = %s", (module_id,))
            mydb.commit()
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while retrieve modules: {str(e)}")
        return False
    finally:
        mydb.close()
        return True
