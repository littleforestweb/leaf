import mimetypes
import os
import re

import werkzeug.utils
from flask import render_template, Blueprint, jsonify, request, session

from leaf.config import Config
from leaf.decorators import login_required
from leaf.files_manager import models
from leaf.pages import models as pages_models
from leaf.serverside import table_schemas
from leaf.serverside.serverside_table import ServerSideTable
from leaf.sites import models as site_models
from leaf.sites.models import get_user_access_folder

files_manager = Blueprint('files_manager', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@files_manager.route("/files/fileupload", methods=['GET'])
@login_required
def files_view_upload():
    """
    Render the template for temporary file upload view.

    This route renders the HTML template "temp_fileupload.html" when accessed via
    a GET request. The route requires the user to be logged in.

    Returns:
    - Response: The rendered template for the temporary file upload view.
    """
    site_id = werkzeug.utils.escape(request.args.get("siteId", type=str))
    archive = werkzeug.utils.escape(request.args.get("archive", type=str))
    return render_template("files_manager.html", userId=session['id'], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], id=site_id, archive=archive, preview_webserver=Config.PREVIEW_SERVER.strip("/"), site_notice=Config.SITE_NOTICE)

@files_manager.route("/files/browser_img", methods=['GET'])
@login_required
def files_browser_img():
    """
    Render the template for files view.

    This route renders the HTML template "browser.html" when accessed via
    a GET request. The route requires the user to be logged in.

    Returns:
    - Response: The rendered template for the temporary file upload view.
    """
    site_id = werkzeug.utils.escape(request.args.get("siteId", type=str))
    archive = werkzeug.utils.escape(request.args.get("archive", type=str))
    return render_template("browser_img.html", userId=session['id'], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], id=site_id, archive=archive, preview_webserver=Config.PREVIEW_SERVER.strip("/"), site_notice=Config.SITE_NOTICE)

@files_manager.route("/files/browser_all_files", methods=['GET'])
@login_required
def files_browser_all_files():
    """
    Render the template for files view.

    This route renders the HTML template "browser.html" when accessed via
    a GET request. The route requires the user to be logged in.

    Returns:
    - Response: The rendered template for the temporary file upload view.
    """
    site_id = werkzeug.utils.escape(request.args.get("siteId", type=str))
    archive = werkzeug.utils.escape(request.args.get("archive", type=str))
    return render_template("browser_all_files.html", userId=session['id'], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], id=site_id, archive=archive, preview_webserver=Config.PREVIEW_SERVER.strip("/"), site_notice=Config.SITE_NOTICE)



@files_manager.route("/files/fileupload_api", methods=["POST"])
@login_required
def files_api_upload():
    """
    Handle the API endpoint for uploading files to temporary storage.

    This route processes a POST request containing a file upload. It retrieves
    the folder and file information from the request, sanitizes the names, creates
    a local folder if it doesn't exist, and saves the file to disk. It then
    transfers the file to deployment servers using SCP (Secure Copy Protocol).

    Parameters:
    - account_id (str): The account_id for the uploaded file.
    - site_id (str): The site_id for the uploaded file.
    - folder (str): The destination folder for the uploaded file.
    - file (FileStorage): The uploaded file.

    Returns:
    - str: A message indicating the success of the file upload, along with local,
      remote, and live URLs for reference.
    """
    account_id = werkzeug.utils.escape(request.form.get("account_id"))
    if request.form.get("site_id"):
        site_id = werkzeug.utils.escape(request.form.get("site_id"))
    else:
        site_id = False
    folder = werkzeug.utils.escape(request.form.get("folder"))
    file = request.files["file"]
    filename = file.filename

    folder = re.sub(r'[^a-zA-Z0-9\-._\/]', '_', folder)
    filename = re.sub(r'[^a-zA-Z0-9\-._\/]', '_', filename)

    # Remove "/"
    folder = folder.lstrip("/") if folder.startswith("/") else folder
    filename = filename.lstrip("/") if filename.startswith("/") else filename

    # Create local folder if it does not exist
    folder_path = os.path.join(Config.WEBSERVER_FOLDER, folder)
    os.makedirs(folder_path, exist_ok=True)

    # Save file to disk
    local_path = os.path.join(folder_path, filename)
    file.save(local_path)

    # Set Preview URL
    preview_url = Config.PREVIEW_SERVER + "/" if not Config.PREVIEW_SERVER.endswith("/") else Config.PREVIEW_SERVER
    preview_url = preview_url + os.path.join(folder, filename)
    mime_type = mimetypes.guess_type(preview_url)[0]
    if not mime_type or mime_type == "":
        mime_type = file.mimetype

    models.insert_file_into_db(account_id, site_id, filename, folder, mime_type, "200")

    return "File uploaded successfully.<br>" + local_path + "<br>" + preview_url


@files_manager.route("/files/remove_files", methods=["POST"])
@login_required
def files_remove_files():
    """
    Remove specified files associated with a given account.

    This function handles a POST request to remove files. It retrieves JSON data from the request, 
    extracts and sanitizes the account ID and file entries designated for deletion, and then 
    delegates the actual deletion of files to the `remove_files` method of the models module.

    Returns:
        Response object: Returns the result of the `models.remove_files` method, which could
        include details about the deletion process or an error message.

    Raises:
        KeyError: If the necessary keys ('account_id' or 'entries_to_delete') are missing in the JSON data.
        TypeError: If the input types for the JSON keys are not as expected.
    """
    return models.remove_files(request)


@files_manager.route("/files/list_all_files", methods=["GET"])
@login_required
def files_list_all_files():
    """
    API endpoint to retrieve site files.

    Requires the user to be logged in. Retrieves the 'id' parameter from the request
    arguments, checks if the specified site belongs to the user's account, and then
    retrieves files from the site using a parameterized query. Returns the site files
    in JSON format.

    Returns:
        flask.Response: JSON response containing site data.
    """
    try:
        # Retrieve the 'id' parameter from the request arguments
        site_id = False
        if request.args.get("id"):
            site_id = werkzeug.utils.escape(request.args.get("id", type=str))
        # Retrieve the 'archive' parameter from the request arguments
        archive = werkzeug.utils.escape(request.args.get("archive", type=str))

        if site_id != False:
            # Check if the specified site belongs to the user's account
            if not site_models.site_belongs_to_account(int(site_id)):
                return jsonify({"error": "Forbidden"}), 403

        # Get files from the site using a parameterized query
        files = models.list_all_files(site_id, archive)

        # Define columns for the ServerSideTable
        columns = table_schemas.SERVERSIDE_TABLE_COLUMNS["get_site_files"]

        # Generate ServerSideTable data
        data = ServerSideTable(request, files, columns).output_result()

        return jsonify(data)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


@files_manager.route("/files/list_rss_files", methods=["GET"])
@login_required
def files_list_rss_files():
    """
    API endpoint to retrieve site rss files.

    Requires the user to be logged in. Retrieves the 'id' parameter from the request
    arguments, checks if the specified site belongs to the user's account, and then
    retrieves files from the site using a parameterized query. Returns the site files
    in JSON format.

    Returns:
        flask.Response: JSON response containing site data.
    """
    try:
        # Retrieve the 'id' parameter from the request arguments
        site_id = False
        if request.args.get("id"):
            site_id = werkzeug.utils.escape(request.args.get("id", type=str))
        # Retrieve the 'archive' parameter from the request arguments
        archive = werkzeug.utils.escape(request.args.get("archive", type=str))

        if site_id != False:
            # Check if the specified site belongs to the user's account
            if not site_models.site_belongs_to_account(int(site_id)):
                return jsonify({"error": "Forbidden"}), 403

        # Get files from the site using a parameterized query
        files = models.list_rss_files(site_id, archive)

        return jsonify(files)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

@files_manager.route("/files/list_img_files", methods=["GET"])
@login_required
def files_list_img_files():
    """
    API endpoint to retrieve site img files.

    Requires the user to be logged in. Retrieves the 'id' parameter from the request
    arguments, checks if the specified site belongs to the user's account, and then
    retrieves files from the site using a parameterized query. Returns the site files
    in JSON format.

    Returns:
        flask.Response: JSON response containing site data.
    """
    try:
        # Retrieve the 'id' parameter from the request arguments
        site_id = False
        if request.args.get("id"):
            site_id = werkzeug.utils.escape(request.args.get("id", type=str))
        # Retrieve the 'archive' parameter from the request arguments
        archive = werkzeug.utils.escape(request.args.get("archive", type=str))

        if site_id != False:
            # Check if the specified site belongs to the user's account
            if not site_models.site_belongs_to_account(int(site_id)):
                return jsonify({"error": "Forbidden"}), 403

        # Get files from the site using a parameterized query
        files = models.list_img_files(site_id, archive)

        return jsonify(files)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


@files_manager.route("/files/restore_deleted_assets", methods=["POST"])
@login_required
def restore_deleted_assets():
    """
    Restore a deleted asset based on the provided asset ID.

    This endpoint handles the restoration of a deleted asset. It requires the user to be authenticated
    and ensures the user has access to the folder containing the asset. If the user does not have access
    or if any other error occurs, an appropriate error message and status code are returned.

    Request Parameters:
    - assetId (str): The ID of the asset to be restored.

    Returns:
    - JSON response indicating success or error message.
    """

    try:
        # Retrieve and sanitize the assetId from the POST request
        assetId = int(werkzeug.utils.escape(request.form.get("assetId", type=str)))

        # Fetch asset details using the assetId
        asset_details = pages_models.get_asset_details(assetId)
        user_access_folder = get_user_access_folder()

        # Check if the asset path belongs to any of the folders the user has access to
        if not any(("/" + asset_details["path"]).startswith(folder) for folder in user_access_folder):
            return {"error": "Forbidden"}, 403

        # Restore the deleted asset
        models.restore_deleted_assets(assetId)
        return jsonify({"message": "success"})

    except Exception as e:
        # Handle exceptions and log the error if necessary
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code
