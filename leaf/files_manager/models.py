import os
from flask import Blueprint, session
import werkzeug.utils

from leaf import decorators
from leaf.config import Config

def list_all_files(site_id):
    """
    Retrieve files from the specified site.

    Uses a database connection obtained with the 'db_connection' decorator to execute
    a parameterized query to fetch files from the 'site_meta' table. Returns the files
    data in a list of dictionaries.

    Args:
        site_id (str): The ID of the site for which to retrieve files.

    Returns:
        list: A list of dictionaries containing files data.
    """

    try:
        # Get a database connection using the 'db_connection' decorator
        mydb, mycursor = decorators.db_connection()

        # Get User Access folders
        folder_paths = set(get_user_access_folder(mycursor))

        userUsernameEmail = 'CONCAT(user.id, ", ", user.username, ", ", user.email)'
        # Get files from the site
        query = f"SELECT site_assets.id, site_assets.path, site_assets.filename, site_assets.mimeType, {userUsernameEmail}, site_assets.created FROM site_assets INNER JOIN user ON site_assets.modified_by = user.id WHERE site_id = %s"
        mycursor.execute(query, [site_id])
        site_files = mycursor.fetchall()

        # Filter files based on user access
        if session["is_admin"] == 0:
            access_files = [{"id": file[0], "Path": os.path.join("/", file[1]), "Filename": file[2], "Mime Type": file[3], "Created By": file[4], "Created": file[5]} for file in site_files if any(file[1].startswith(path.lstrip("/")) for path in folder_paths)]
        else:
            access_files = [{"id": file[0], "Path": os.path.join("/", file[1]), "Filename": file[2], "Mime Type": file[3], "Created By": file[4], "Created": file[5]} for file in site_files]

        return access_files

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching files: {str(e)}")

def insert_file_into_db(accountId, site_id, filename, folder, mime_type, status):
    """
    Insert file for a specific site in the database.

    Args:
        site_id (str): The site ID associated with the file.
        filename (str): The filename for the specific file.
        folder (str): The folder for the specific file.
        mime_type (str): The mime_type for the specific file.
        status (str): The status code for the specific file.

    Returns:
        str: Last row id inserted in the database.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = decorators.db_connection()

    try:

        if isinstance(int(accountId), int):
            query = f"INSERT INTO site_assets (site_id, filename, path, mimeType, status, modified_by) VALUES (%s, %s, %s, %s, %s, %s)"
            mycursor.execute(query, (site_id, filename, folder, mime_type, status, session['id']))
            mydb.commit()
        else:
            print("Invalid accountId")

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
    return folder_paths


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
