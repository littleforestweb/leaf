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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sites = Blueprint('sites', __name__)

HERITRIX_FOLDER = Config.HERITRIX_FOLDER
HERITRIX_PORT = Config.HERITRIX_PORT
HERITRIX_USER = Config.HERITRIX_USER
HERITRIX_PASS = Config.HERITRIX_PASS
HERITRIX_HEADERS = {"Accept": "application/xml"}


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


def get_user_access_folder(mycursor):
    """
    Retrieve the folder paths that a user has access to.

    Parameters:
    - mycursor: MySQL cursor object used to execute queries.

    Returns:
    - List of folder paths (strings) that the user has access to.
    """

    # Get User Access folders
    query = "SELECT ua.folder_path FROM leaf.user_access ua JOIN leaf.user_groups ug ON ua.group_id = ug.group_id JOIN leaf.group_member gm ON ug.group_id = gm.group_id WHERE gm.user_id = %s"
    mycursor.execute(query, (session["id"],))
    folder_paths = [folder_path[0] for folder_path in mycursor.fetchall()]
    return set(folder_paths)


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

        # Get User Access folders
        folder_paths = get_user_access_folder(mycursor)

        # Get pages from the site
        query = "SELECT id, id, title, HTMLPath, modified_date, id FROM site_meta WHERE status <> -1 AND site_id = %s"
        mycursor.execute(query, [site_id])
        site_pages = mycursor.fetchall()

        # Filter pages based on user access
        if session["is_admin"] == 0:
            access_pages = [{"id": page[0], "Screenshot": page[1], "Title": page[2], "URL": os.path.join(Config.PREVIEW_SERVER, page[3]), "Modified Date": page[4], "Action": page[5]} for page in site_pages if any(page[3].startswith(path.lstrip("/")) for path in folder_paths)]
        else:
            access_pages = [{"id": page[0], "Screenshot": page[1], "Title": page[2], "URL": os.path.join(Config.PREVIEW_SERVER, page[3]), "Modified Date": page[4], "Action": page[5]} for page in site_pages]

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
                    newProperty.set("value", os.path.join(HERITRIX_FOLDER, "jobs", site_data["site_label"]))
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
