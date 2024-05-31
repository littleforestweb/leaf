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
from leaf.sites.models import user_has_access_page
from leaf.versioning import models

# Create a Blueprint for the versioning routes
versioning = Blueprint('versioning', __name__)


@versioning.route('/versions')
@login_required
def get_versions():
    """
    Renders the page versions template.

    This endpoint renders the page versions template, which displays
    the version history of a specific page. The request must include
    the page ID as a query parameter. The user must have the necessary
    permissions to view the page versions.

    Returns:
        HTML template for displaying page versions.

    Query Parameters:
        - file_id (int): The ID of the page whose versions are to be displayed.

    Responses:
        - If the user has access permissions:
            HTML template with necessary variables for rendering the page.
        - If the user does not have access permissions:
            JSON error response with status code 403 (Forbidden).

    """

    file_id = int(werkzeug.utils.escape(request.args.get('file_id', type=str)))

    # Check for user permissions
    if not user_has_access_page(file_id):
        return jsonify({"error": "Forbidden"}), 403

    page_details = get_page_details(file_id)
    page_HTMLPath = page_details["HTMLPath"]
    page_URL = urllib.parse.urljoin(Config.PREVIEW_SERVER, page_HTMLPath)

    return render_template("versioning.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE, preview_webserver=Config.PREVIEW_SERVER, file_id=file_id, page_HTMLPath=page_HTMLPath, page_URL=page_URL)


@versioning.route("/api/versions")
@login_required
def api_versions():
    """
    Endpoint to retrieve versions of a specific page.

    This endpoint handles GET requests to fetch versions of a page specified by the 'file_id'
    parameter in the query string. It requires the user to be authenticated and have the necessary
    permissions to access the page.

    Returns:
        JSON response containing the versions of the specified page if successful,
        or an error message with the appropriate HTTP status code if an error occurs.

    Query Parameters:
        file_id (str): The ID of the page whose versions are to be retrieved.

    Responses:
        200: A JSON object containing the version data of the specified page.
        403: A JSON object with an error message if the user does not have permission to access the page.
        500: A JSON object with an error message if an exception occurs during the process.
    """

    try:
        file_id = int(werkzeug.utils.escape(request.args.get('file_id', type=str)))

        # Check for user permissions
        if not user_has_access_page(file_id):
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
    Reverts a page to a previous commit.

    This endpoint is used to revert the content of a page to a specified
    commit. The request must include the page ID and the commit hash.
    The user must have the necessary permissions to revert the page.

    Returns:
        JSON response indicating success or an error message with
        the appropriate HTTP status code.

    Request Data:
        - file_id (int): The ID of the page to revert.
        - commit (str): The commit hash to revert the page to.

    Responses:
        - 200: {"message": "success"} if the page is successfully reverted.
        - 403: {"error": "Forbidden"} if the user does not have access to the page.
        - 500: {"error": "error_message"} if an internal server error occurs.

    Exceptions:
        - Handles all exceptions, prints the traceback for debugging, and
          returns a JSON error response with status code 500.
    """

    try:
        request_data = request.get_json()
        file_id = int(werkzeug.utils.escape(request_data.get("file_id")))
        commit = str(werkzeug.utils.escape(request_data.get("commit")))

        # Check for user permissions
        if not user_has_access_page(file_id):
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
    Renders a page showing the differences between two versions of a page.

    This endpoint requires the user to be logged in. It retrieves the page ID and the
    commit IDs of the two versions to be compared from the request arguments. It then
    checks if the user has access to the specified page. If the user has access, it
    renders a template displaying the differences between the specified versions. If
    not, it returns a 403 Forbidden error.

    Parameters:
    - file_id (int): The ID of the page.
    - commit_id_1 (str): The ID of the first commit.
    - commit_id_2 (str): The ID of the second commit.

    Returns:
    - A rendered template showing the differences between the two versions of the page,
      or a JSON response with an error message and a 403 status code if the user does
      not have access.
    """

    file_id = int(werkzeug.utils.escape(request.args.get('file_id', type=str)))
    commit_id_1 = str(werkzeug.utils.escape(request.args.get('commit_id_1', type=str)))
    commit_id_2 = str(werkzeug.utils.escape(request.args.get('commit_id_2', type=str)))

    # Check for user permissions
    if not user_has_access_page(file_id):
        return jsonify({"error": "Forbidden"}), 403

    return render_template("versioning_diff.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE, preview_webserver=Config.PREVIEW_SERVER, file_id=file_id, commit_id_1=commit_id_1, commit_id_2=commit_id_2)


@versioning.route('/api/versions_diff', methods=["POST"])
@login_required
def api_versions_diff():
    """
    Returns the differences between two versions of a page as a JSON response.

    This endpoint requires the user to be logged in and uses a POST request to retrieve
    the page ID and the commit IDs of the two versions to be compared from the request
    JSON data. It then checks if the user has access to the specified page. If the user
    has access, it retrieves the HTML path of the page, computes the diff between the
    specified versions using Git, and returns the diff as a JSON response. If the user
    does not have access, it returns a 403 Forbidden error. In case of an exception, it
    returns a 500 error with the exception message.

    Returns:
    - JSON response containing the diff text between the two versions of the page or an
      error message.
    - Status code 403 if the user does not have access to the page.
    - Status code 500 if an exception occurs.

    Example:
    {
        "file_id": 123,
        "commit_id_1": "commit1",
        "commit_id_2": "commit2"
    }
    """

    try:
        request_data = request.get_json()
        file_id = int(werkzeug.utils.escape(request_data['file_id']))
        commit_id_1 = str(werkzeug.utils.escape(request_data['commit_id_1']))
        commit_id_2 = str(werkzeug.utils.escape(request_data['commit_id_2']))

        # Check for user permissions
        if not user_has_access_page(file_id):
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
    Retrieve the full content of a file as it was in a specific commit.

    Parameters:
    - repo_path (str): The path to the Git repository.
    - commit_id (str): The commit ID.
    - file_path (str): The path to the file within the repository.

    Returns:
    - str: The content of the file at the specified commit.
    """

    try:
        request_data = request.get_json()
        file_id = int(werkzeug.utils.escape(request_data['file_id']))
        commit_id = str(werkzeug.utils.escape(request_data['commit']))

        # Check for user permissions
        if not user_has_access_page(file_id):
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
