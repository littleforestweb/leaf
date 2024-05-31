import os

import werkzeug.utils
from flask import session, jsonify, current_app

from leaf import decorators
from leaf.config import Config
from leaf.sites.models import get_user_access_folder


def list_all_files(site_id, archive):
    """
    Retrieve files from the specified site.

    Uses a database connection obtained with the 'db_connection' decorator to execute
    a parameterized query to fetch files from the 'site_meta' table. Returns the files
    data in a list of dictionaries.

    Args:
        site_id (str): The ID of the site for which to retrieve files.
        archive (str): The archive variable to understand if it's archived files or not.

    Returns:
        list: A list of dictionaries containing files data.
    """
    access_files = []
    site_files = False

    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get User Access folders
        folder_paths = get_user_access_folder(mycursor)

        # Get first admin user
        query = f"SELECT user.id, user.username, user.email FROM user WHERE user.is_admin = 1"
        mycursor.execute(query)
        first_user_admin = mycursor.fetchall()[0]

        # Get files from the site
        userUsernameEmail = 'CONCAT(user.id, ", ", user.username, ", ", user.email)'

        if site_id == False:
            # Execute query to get the site IDs associated with the account
            mycursor.execute("SELECT id FROM sites WHERE accountId = %s", (session["accountId"],))
            sites_result = mycursor.fetchall()

            # Extract site IDs from the result and format them for the IN clause
            site_ids = [str(site[0]) for site in sites_result]
            sites_result_placeholder = ','.join(site_ids)

            # Tuple of parameters, where the first_user_admin values are joined into a single string
            modified_by_default = f"{first_user_admin[0]}, {first_user_admin[1]}, {first_user_admin[2]}"

            if archive != "1":
                files_query = f"""
                SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, 
                       IFNULL({userUsernameEmail}, %s) AS modified_by, site_assets.created 
                FROM site_assets 
                LEFT JOIN user ON site_assets.modified_by = user.id 
                WHERE site_id IN ({sites_result_placeholder}) AND site_assets.status <> -1
                """
            else:
                files_query = f"""
                SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, 
                       IFNULL({userUsernameEmail}, %s) AS modified_by, site_assets.created 
                FROM site_assets 
                LEFT JOIN user ON site_assets.modified_by = user.id 
                WHERE site_id IN ({sites_result_placeholder}) AND site_assets.status = -1
                """

            # Execute the query with the modified_by_default parameter
            mycursor.execute(files_query, (modified_by_default,))

        else:
            if archive != "1":
                files_query = f"SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, IFNULL({userUsernameEmail}, '{first_user_admin[0]}, {first_user_admin[1]}, {first_user_admin[2]}') AS modified_by, site_assets.created FROM site_assets LEFT JOIN user ON site_assets.modified_by = user.id WHERE site_id = %s AND site_assets.status <> -1"
            else:
                files_query = f"SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, IFNULL({userUsernameEmail}, '{first_user_admin[0]}, {first_user_admin[1]}, {first_user_admin[2]}') AS modified_by, site_assets.created FROM site_assets LEFT JOIN user ON site_assets.modified_by = user.id WHERE site_id = %s AND site_assets.status = -1"
            mycursor.execute(files_query, [site_id])

        site_files = mycursor.fetchall()

        if folder_paths:
            # Filter files based on user access
            if session["is_admin"] == 0:
                access_files = [{"id": file[0], "Path": os.path.join("/", file[1]), "Filename": file[2], "Mime Type": file[3], "Created By": file[4], "Created": file[5]} for file in site_files if any(file[1].startswith(path.lstrip("/")) for path in folder_paths)]
            else:
                access_files = [{"id": file[0], "Path": os.path.join("/", file[1]), "Filename": file[2], "Mime Type": file[3], "Created By": file[4], "Created": file[5]} for file in site_files]

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching files: {str(e)}")
    finally:
        mydb.close()
        return access_files

def list_rss_files(site_id, archive):
    """
    Retrieve rss files from the specified site.

    Uses a database connection obtained with the 'db_connection' decorator to execute
    a parameterized query to fetch files from the 'site_meta' table. Returns the files
    data in a list of dictionaries.

    Args:
        site_id (str): The ID of the site for which to retrieve files.
        archive (str): The archive variable to understand if it's archived files or not.

    Returns:
        list: A list of dictionaries containing files data.
    """
    access_files = []
    site_files = False

    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get User Access folders
        folder_paths = get_user_access_folder(mycursor)

        # Get first admin user
        query = f"SELECT user.id, user.username, user.email FROM user WHERE user.is_admin = 1"
        mycursor.execute(query)
        first_user_admin = mycursor.fetchall()[0]

        # Get files from the site
        userUsernameEmail = 'CONCAT(user.id, ", ", user.username, ", ", user.email)'

        if site_id == False:
            # Execute query to get the site IDs associated with the account
            mycursor.execute("SELECT id FROM sites WHERE accountId = %s", (session["accountId"],))
            sites_result = mycursor.fetchall()

            # Extract site IDs from the result and format them for the IN clause
            site_ids = [str(site[0]) for site in sites_result]
            sites_result_placeholder = ','.join(site_ids)

            # Tuple of parameters, where the first_user_admin values are joined into a single string
            modified_by_default = f"{first_user_admin[0]}, {first_user_admin[1]}, {first_user_admin[2]}"

            if archive != "1":
                files_query = f"""
                SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, 
                       IFNULL({userUsernameEmail}, %s) AS modified_by, site_assets.created 
                FROM site_assets 
                LEFT JOIN user ON site_assets.modified_by = user.id 
                WHERE site_id IN ({sites_result_placeholder}) AND site_assets.mimeType = 'text/xml' AND site_assets.status <> -1
                """
            else:
                files_query = f"""
                SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, 
                       IFNULL({userUsernameEmail}, %s) AS modified_by, site_assets.created 
                FROM site_assets 
                LEFT JOIN user ON site_assets.modified_by = user.id 
                WHERE site_id IN ({sites_result_placeholder}) AND site_assets.mimeType = 'text/xml' AND site_assets.status = -1
                """

            # Execute the query with the modified_by_default parameter
            mycursor.execute(files_query, (modified_by_default,))

        else:
            if archive != "1":
                files_query = f"SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, IFNULL({userUsernameEmail}, '{first_user_admin[0]}, {first_user_admin[1]}, {first_user_admin[2]}') AS modified_by, site_assets.created FROM site_assets LEFT JOIN user ON site_assets.modified_by = user.id WHERE site_id = %s AND site_assets.mimeType = 'text/xml' AND site_assets.status <> -1"
            else:
                files_query = f"SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, IFNULL({userUsernameEmail}, '{first_user_admin[0]}, {first_user_admin[1]}, {first_user_admin[2]}') AS modified_by, site_assets.created FROM site_assets LEFT JOIN user ON site_assets.modified_by = user.id WHERE site_id = %s AND site_assets.mimeType = 'text/xml' AND site_assets.status = -1"
            mycursor.execute(files_query, [site_id])

        site_files = mycursor.fetchall()

        rss_feeds = []

        for file in site_files:
            file_path = file[1]  # Assuming the path is in the second column
            if is_rss_feed(file_path):
                rss_feeds.append(file)

        if folder_paths:
            # Filter files based on user access
            if session["is_admin"] == 0:
                access_files = [{"id": file[0], "Path": os.path.join("/", file[1]), "Filename": file[2], "Mime Type": file[3], "Created By": file[4], "Created": file[5]} for file in rss_feeds if any(file[1].startswith(path.lstrip("/")) for path in folder_paths)]
            else:
                access_files = [{"id": file[0], "Path": os.path.join("/", file[1]), "Filename": file[2], "Mime Type": file[3], "Created By": file[4], "Created": file[5]} for file in rss_feeds]

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching files: {str(e)}")
    finally:
        mydb.close()
        return access_files

# Function to check if a file starts with <rss> tag
def is_rss_feed(file_path):
    full_file_path = os.path.join(Config.WEBSERVER_FOLDER, file_path)
    try:
        with open(full_file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            return first_line.startswith('<?xml') and '<rss' in file.read()
    except Exception as e:
        current_app.logger.debug(f"Error reading file {full_file_path}: {e}")
        return False

def insert_file_into_db(accountId, site_id, filename, folder, mime_type, status):
    """
    Insert file for a specific site in the database.

    Args:
        accountId: Users Account Id
        site_id (str): The site ID associated with the file.
        filename (str): The filename for the specific file.
        folder (str): The folder for the specific file.
        mime_type (str): The mime_type for the specific file.
        status (str): The status code for the specific file.

    Returns:
        str: Last row id inserted in the database.
    """
    accountId = int(accountId)

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = decorators.db_connection()

    try:

        path = os.path.join(folder, filename)
        query = f"INSERT INTO site_assets (site_id, filename, path, mimeType, status, modified_by) VALUES (%s, %s, %s, %s, %s, %s)"
        mycursor.execute(query, (site_id, filename, path, mime_type, status, session['id']))
        mydb.commit()

    except Exception as e:
        print("insert_file_into_db model")
        print(e)
    finally:
        mydb.close()
        return mycursor.lastrowid


def remove_files(request):
    """
    Remove files for a specific site in the database and on disc.

    Args:
        request (Request): The HTTP request object.

    Returns:
        JSON: Deleted rows in the database.
    """

    thisRequest = request.get_json()
    accountId = werkzeug.utils.escape(thisRequest.get("account_id"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    entries_to_delete = thisRequest.get("entries_to_delete")

    validate_files_entries_to_delete(entries_to_delete, accountId)

    mydb, mycursor = decorators.db_connection()

    try:
        if isinstance(int(accountId), int):

            # Retrieve files information one by one to delete it in disk
            for entry in entries_to_delete:
                get_query = f"SELECT path, filename FROM site_assets WHERE id = %s"
                mycursor.execute(get_query, (entry,))
                file_info = mycursor.fetchall()
                file_path = file_info[0][0]
                file_name = file_info[0][1]

                # Delete existing template
                file_to_delete = os.path.join(Config.WEBSERVER_FOLDER, file_path, file_name)
                if os.path.exists(file_to_delete):
                    os.remove(file_to_delete)
                    print(f"File '{file_to_delete}' deleted successfully.")
                else:
                    print(f"File '{file_to_delete}' does not exist.")

            # Create a string with placeholders
            placeholders = ', '.join(['%s'] * len(entries_to_delete))

            query = f"DELETE FROM site_assets WHERE id IN ({placeholders})"

            mycursor.execute(query, tuple(entries_to_delete))
            mydb.commit()

        else:
            print("Invalid accountId")

    except Exception as e:
        print("delete_templates model")
        print(e)
    finally:
        mydb.close()
        return entries_to_delete


def validate_files_entries_to_delete(entries_to_delete, accountId):
    """
    Validate the entries_to_delete parameter to prevent SQL injection.

    Args:
        entries_to_delete (str): The string containing IDs of entries to be deleted.
        accountId (str): The account ID associated with the entries to delete.

    Raises:
        ValueError: If entries_to_delete contains invalid characters.
    """

    for entry in entries_to_delete:
        if not entry.isdigit() or ";" in entry:
            print("validate_files_entries_to_delete model")
            raise ValueError("Invalid parameter: contains invalid characters or not all digits.")
