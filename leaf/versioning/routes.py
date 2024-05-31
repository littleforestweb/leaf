import os.path
import traceback
import urllib.parse

import werkzeug.utils
from flask import render_template, Blueprint, jsonify, request, session

from leaf import Config
from leaf.decorators import login_required
from leaf.editor.models import add_base_href
from leaf.pages.models import get_page_details
from leaf.serverside import table_schemas
from leaf.serverside.serverside_table import ServerSideTable
from leaf.sites.models import user_has_access_page, user_has_access_asset
from leaf.versioning import models

# Create a Blueprint for the versioning routes
versioning = Blueprint('versioning', __name__)


@versioning.route('/versions')
@login_required
def get_versions():
    """
    Endpoint to render the page displaying the versions of a specified file.

    This function handles a GET request to render a template that displays the versions of a
    specified file (page or asset). It first checks if the necessary parameters are provided
    and if the user has the required permissions to access the file. If the user has access,
    it retrieves the file details and constructs the URL for the file preview. It then renders
    the "versioning.html" template with user and file information. If the user does not have access
    or if required parameters are missing, it returns an appropriate error message.

    Query Parameters:
        file_type (str): The type of the file ("page" or "asset").
        file_id (int): The ID of the file.

    If the user does not have access, returns:
        JSON response containing:
        - "error": "Forbidden", with HTTP status code 403.
        - "error": "Bad Request" and "message": "file_type and file_id is required", with HTTP status code 400.
    """

    file_type = str(werkzeug.utils.escape(request.args.get('file_type', type=str)))
    file_id = int(werkzeug.utils.escape(request.args.get('file_id', type=str)))

    # Check for user inputs
    if file_type is None or file_id is None:
        return jsonify({"error": "Bad Request", "message": "file_type and file_id is required"}), 400

    # Check for user permissions
    user_has_access = False
    if file_type == "page":
        user_has_access = user_has_access_page(file_id)
    elif file_type == "asset":
        user_has_access = user_has_access_asset(file_id)
    if not user_has_access:
        return jsonify({"error": "Forbidden"}), 403

    page_details = get_page_details(file_id)
    page_HTMLPath = page_details["HTMLPath"]
    page_URL = urllib.parse.urljoin(Config.PREVIEW_SERVER, page_HTMLPath)

    return render_template("versioning.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE, preview_webserver=Config.PREVIEW_SERVER, file_type=file_type, file_id=file_id, page_HTMLPath=page_HTMLPath, page_URL=page_URL)


@versioning.route("/api/versions")
@login_required
def api_versions():
    """
    API endpoint to retrieve the versions of a specified file.

    This function handles a GET request to fetch the versions of a specified file (page or asset).
    It first checks if the necessary parameters are provided and if the user has the required
    permissions to access the file. If the user has access, it retrieves the versions of the file
    from the database and returns them in a paginated format suitable for DataTables. If the user
    does not have access or if required parameters are missing, it returns an appropriate error
    message. In case of any exceptions, it returns a 500 Internal Server Error.

    Query Parameters:
        file_type (str): The type of the file ("page" or "asset").
        file_id (int): The ID of the file.

    Returns:
        JSON response containing:
        - Data for DataTables if the operation is successful,
        - "error": error message and HTTP status code in case of failure:
            - 400 Bad Request if required parameters are missing,
            - 403 Forbidden if the user does not have access,
            - 500 Internal Server Error in case of exceptions.
    """

    try:
        file_type = str(werkzeug.utils.escape(request.args.get('file_type', type=str)))
        file_id = int(werkzeug.utils.escape(request.args.get('file_id', type=str)))

        # Check for user inputs
        if file_type is None or file_id is None:
            return jsonify({"error": "Bad Request", "message": "file_type and file_id is required"}), 400

        # Check for user permissions
        user_has_access = False
        if file_type == "page":
            user_has_access = user_has_access_page(file_id)
        elif file_type == "asset":
            user_has_access = user_has_access_asset(file_id)
        if not user_has_access:
            return jsonify({"error": "Forbidden"}), 403

        # Get Versions
        versions = models.get_versions(file_id)

        # Define columns for the ServerSideTable
        columns = table_schemas.SERVERSIDE_TABLE_COLUMNS["get_versions"]

        # Generate ServerSideTable data
        data = ServerSideTable(request, versions, columns).output_result()

        return jsonify(data)
    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@versioning.route("/api/version_revert", methods=["POST"])
@login_required
def api_version_revert():
    """
    API endpoint to revert a file to a specified commit.

    This function handles a POST request to revert a file (page or asset) to a specified commit.
    It first checks if the necessary parameters are provided and if the user has the required
    permissions to access and revert the file. If the user has access, it reverts the file to the
    specified commit in the Git repository and returns a success message. If the user does not have
    access or if required parameters are missing, it returns an appropriate error message. In case
    of any exceptions, it returns a 500 Internal Server Error.

    Request JSON structure:
    {
        "file_type": "page" or "asset",
        "file_id": <integer>,
        "commit": <string>
    }

    Returns:
        JSON response containing:
        - "message": "success" if the operation is successful,
        - "error": error message and HTTP status code in case of failure:
            - 400 Bad Request if required parameters are missing,
            - 403 Forbidden if the user does not have access,
            - 500 Internal Server Error in case of exceptions.
    """

    try:
        request_data = request.get_json()
        file_type = str(werkzeug.utils.escape(request_data['file_type']))
        file_id = int(werkzeug.utils.escape(request_data['file_id']))
        commit = str(werkzeug.utils.escape(request_data['commit']))

        # Check for user inputs
        if file_type is None or file_id is None or commit is None:
            return jsonify({"error": "Bad Request", "message": "file_type, file_id and commit are required"}), 400

        # Check for user permissions
        user_has_access = False
        if file_type == "page":
            user_has_access = user_has_access_page(file_id)
        elif file_type == "asset":
            user_has_access = user_has_access_asset(file_id)
        if not user_has_access:
            return jsonify({"error": "Forbidden"}), 403

        page_HTMLPath = get_page_details(file_id)["HTMLPath"]
        Config.GIT_REPO.git.checkout(commit, os.path.join(Config.WEBSERVER_FOLDER, page_HTMLPath))
        return jsonify({"message": "success"})
    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@versioning.route('/versions_diff')
@login_required
def versions_diff():
    """
    Endpoint to render the page for viewing differences between two versions of a file.

    This function handles a GET request to render a template that displays the diff between two
    specified commit IDs for a given file. It first checks if the user has the necessary permissions
    to access the requested file type and file ID. If the user has access, it renders the
    "versioning_diff.html" template with user and file information. If the user does not have access,
    it returns a 403 Forbidden error.

    Query Parameters:
        file_type (str): The type of the file ("page" or "asset").
        file_id (int): The ID of the file.
        commit_id_1 (str): The ID of the first commit.
        commit_id_2 (str): The ID of the second commit.

    If the user does not have access, returns:
        JSON response containing:
        - "error": "Forbidden", with HTTP status code 403.
    """

    file_type = str(werkzeug.utils.escape(request.args.get('file_type', type=str)))
    file_id = int(werkzeug.utils.escape(request.args.get('file_id', type=str)))
    commit_id_1 = str(werkzeug.utils.escape(request.args.get('commit_id_1', type=str)))
    commit_id_2 = str(werkzeug.utils.escape(request.args.get('commit_id_2', type=str)))

    # Check for user permissions
    user_has_access = False
    if file_type == "page":
        user_has_access = user_has_access_page(file_id)
    elif file_type == "asset":
        user_has_access = user_has_access_asset(file_id)
    if not user_has_access:
        return jsonify({"error": "Forbidden"}), 403

    return render_template("versioning_diff.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE, preview_webserver=Config.PREVIEW_SERVER, file_type=file_type, file_id=file_id, commit_id_1=commit_id_1, commit_id_2=commit_id_2)


@versioning.route('/api/versions_diff', methods=["POST"])
@login_required
def api_versions_diff():
    """
    API endpoint to retrieve the differences between two versions of a file.

    This function handles a POST request to fetch the diff between two specified commit IDs for a
    given file. It first checks if the user has the necessary permissions to access the requested
    file type and file ID. If the user has access, it retrieves the diff of the file between the
    two specified commits from the Git repository and returns it in the response. If the user does
    not have access, it returns a 403 Forbidden error. In case of any exceptions, it returns a 500
    Internal Server Error.

    Request JSON structure:
    {
        "file_type": "page" or "asset",
        "file_id": <integer>,
        "commit_id_1": <string>,
        "commit_id_2": <string>
    }

    Returns:
        JSON response containing:
        - "message": "success" if the operation is successful,
        - "diff_text": diff text of the file between the specified commits,
        - "error": error message in case of failure.
    """

    try:
        request_data = request.get_json()
        file_type = str(werkzeug.utils.escape(request_data['file_type']))
        file_id = int(werkzeug.utils.escape(request_data['file_id']))
        commit_id_1 = str(werkzeug.utils.escape(request_data['commit_id_1']))
        commit_id_2 = str(werkzeug.utils.escape(request_data['commit_id_2']))

        # Check for user permissions
        user_has_access = False
        if file_type == "page":
            user_has_access = user_has_access_page(file_id)
        elif file_type == "asset":
            user_has_access = user_has_access_asset(file_id)
        if not user_has_access:
            return jsonify({"error": "Forbidden"}), 403

        # Get Page Details
        page_details = get_page_details(file_id)
        page_HTMLPath = page_details["HTMLPath"]

        # Get Commit Diff
        diff_text = Config.GIT_REPO.git.diff(commit_id_1, commit_id_2, '--', os.path.join(Config.WEBSERVER_FOLDER, page_HTMLPath))

        return jsonify({"message": "success", "diff_text": diff_text})
    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@versioning.route('/api/get_file_content_from_commit', methods=["POST"])
@login_required
def api_get_file_content_from_commit():
    """
    API endpoint to retrieve the content of a file from a specific commit.

    This function handles a POST request to fetch the content of a file from a given commit ID.
    It first checks if the user has the necessary permissions to access the requested file type
    and file ID. If the user has access, it retrieves the content of the file from the specified
    commit in the Git repository and returns it in the response. If the user does not have access,
    it returns a 403 Forbidden error. In case of any exceptions, it returns a 500 Internal Server
    Error.

    Request JSON structure:
    {
        "file_type": "page" or "asset",
        "file_id": <integer>,
        "commit_id": <string>
    }

    Returns:
        JSON response containing:
        - "message": "success" if the operation is successful,
        - "file_content": content of the file from the specified commit,
        - "error": error message in case of failure.
    """

    try:
        request_data = request.get_json()
        file_type = str(werkzeug.utils.escape(request_data['file_type']))
        file_id = int(werkzeug.utils.escape(request_data['file_id']))
        commit_id = str(werkzeug.utils.escape(request_data['commit_id']))

        # Check for user permissions
        user_has_access = False
        if file_type == "page":
            user_has_access = user_has_access_page(file_id)
        elif file_type == "asset":
            user_has_access = user_has_access_asset(file_id)
        if not user_has_access:
            return jsonify({"error": "Forbidden"}), 403

        # Get Page Details
        page_details = get_page_details(file_id)
        page_HTMLPath = page_details["HTMLPath"]

        # Get File Content from Commit
        file_content = Config.GIT_REPO.git.show(f'{commit_id}:{page_HTMLPath}')
        file_content = add_base_href(file_content)
        return jsonify({"message": "success", "file_content": file_content})

    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
