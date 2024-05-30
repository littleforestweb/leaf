import datetime
import os.path
import traceback

import werkzeug.utils
from flask import render_template, Blueprint, jsonify, request, session

from leaf import Config
from leaf.decorators import login_required
from leaf.serverside import table_schemas
from leaf.serverside.serverside_table import ServerSideTable
from .models import get_page, get_screenshot, duplicate_page, get_site_id, get_page_details
from ..sites.models import user_has_access_page

# Create a Blueprint for the pages routes
pages = Blueprint('pages', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@pages.route('/get_page')
@login_required
def get_page_route():
    """
    Route to get a specific page.

    Returns:
        get_page: Send HTML file from the directory.
    """
    try:
        pageId = int(werkzeug.utils.escape(request.args.get('id', type=str)))
        return get_page(pageId)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@pages.route('/api/get_site_id')
@login_required
def api_get_site_id():
    """
    Check if the site id related to a page.

    Returns:
        get_site_id: Send site id based on the page id.
    """
    try:
        pageId = int(werkzeug.utils.escape(request.args.get('page_id', type=str)))
        return get_site_id(pageId)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@pages.route('/api/get_page_details')
@login_required
def api_get_page_details():
    """
    Get page details.

    Returns:
        get_page_details: Get all page details.
    """
    try:
        pageId = int(werkzeug.utils.escape(request.args.get('page_id', type=str)))
        return get_page_details(pageId)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@pages.route('/get_screenshot')
@login_required
def get_screenshot_route():
    """
    Route to get the screenshot of a specific page.

    Returns:
        get_screenshot: Send screenshot file from the directory.
    """
    try:
        pageId = int(werkzeug.utils.escape(request.args.get('id', type=str)))
        return get_screenshot(pageId)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #


@pages.route("/api/duplicate_page", methods=["POST"])
@login_required
def duplicate_page_route():
    """
    Route to duplicate a page.

    Returns:
        jsonify: JSON response indicating the success of the duplication.
    """
    try:
        site_id = int(werkzeug.utils.escape(request.form.get("site_id", type=str)))
        ogPageId = int(werkzeug.utils.escape(request.form.get("ogPageId", type=str)))
        ogURL = str(werkzeug.utils.escape(request.form.get("ogURL", type=str)))
        newURL = str(werkzeug.utils.escape(request.form.get("newURL", type=str)))
        newTitle = str(werkzeug.utils.escape(request.form.get("newTitle", type=str)))

        return duplicate_page(site_id, ogPageId, ogURL, newTitle, newURL)

    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@pages.route('/page_versions')
@login_required
def get_page_versions():
    """
    Renders the page versions template.

    This endpoint renders the page versions template, which displays
    the version history of a specific page. The request must include
    the page ID as a query parameter. The user must have the necessary
    permissions to view the page versions.

    Returns:
        HTML template for displaying page versions.

    Query Parameters:
        - page_id (int): The ID of the page whose versions are to be displayed.

    Responses:
        - If the user has access permissions:
            HTML template with necessary variables for rendering the page.
        - If the user does not have access permissions:
            JSON error response with status code 403 (Forbidden).

    """

    page_id = int(werkzeug.utils.escape(request.args.get('page_id', type=str)))

    # Check for user permissions
    if not user_has_access_page(page_id):
        return jsonify({"error": "Forbidden"}), 403

    page_details = get_page_details(page_id)
    page_url = page_details["url"]

    return render_template("versioning.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE, preview_webserver=Config.PREVIEW_SERVER, page_id=page_id, page_url=page_url)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #


@pages.route("/api/page_versions")
@login_required
def page_versions():
    """
    Retrieves a list of versions (commits) for a specified page.

    This endpoint returns a list of all commits related to a given page.
    The request must include the page ID as a query parameter.
    The user must have the necessary permissions to view the page versions.

    Returns:
        JSON response containing the list of page versions or an error
        message with the appropriate HTTP status code.

    Query Parameters:
        - page_id (int): The ID of the page whose versions are to be retrieved.

    Responses:
        - 200: JSON object containing the list of versions in a format suitable
               for server-side processing tables.
        - 403: {"error": "Forbidden"} if the user does not have access to the page.
        - 500: {"error": "error_message"} if an internal server error occurs.

    Exceptions:
        - Handles all exceptions, prints the traceback for debugging, and
          returns a JSON error response with status code 500.
    """

    try:
        page_id = int(werkzeug.utils.escape(request.args.get('page_id', type=str)))

        # Check for user permissions
        if not user_has_access_page(page_id):
            return jsonify({"error": "Forbidden"}), 403

        page_details = get_page_details(page_id)
        page_HTMLPath = page_details["HTMLPath"]
        commits = list(Config.GIT_REPO.iter_commits(paths=os.path.join(Config.WEBSERVER_FOLDER, page_HTMLPath)))
        total_commits = len(commits)
        versions = [{
            "version": total_commits - idx,
            "commit": commit.hexsha,
            "message": commit.message,
            "author": commit.author.name,
            "date": datetime.datetime.fromtimestamp(commit.authored_date).strftime('%Y/%m/%d %H:%M:%S')
        } for idx, commit in enumerate(commits)]

        # Define columns for the ServerSideTable
        columns = table_schemas.SERVERSIDE_TABLE_COLUMNS["get_page_versions"]

        # Generate ServerSideTable data
        data = ServerSideTable(request, versions, columns).output_result()

        return jsonify(data)
    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #


@pages.route("/api/page_revert", methods=["POST"])
@login_required
def page_revert():
    """
    Reverts a page to a previous commit.

    This endpoint is used to revert the content of a page to a specified
    commit. The request must include the page ID and the commit hash.
    The user must have the necessary permissions to revert the page.

    Returns:
        JSON response indicating success or an error message with
        the appropriate HTTP status code.

    Request Data:
        - page_id (int): The ID of the page to revert.
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
        page_id = int(werkzeug.utils.escape(request_data.get("page_id")))

        # Check for user permissions
        if not user_has_access_page(page_id):
            return jsonify({"error": "Forbidden"}), 403

        commit = str(werkzeug.utils.escape(request_data.get("commit")))
        page_HTMLPath = get_page_details(page_id)["HTMLPath"]
        Config.GIT_REPO.git.checkout(commit, os.path.join(Config.WEBSERVER_FOLDER, page_HTMLPath))
        return jsonify({"message": "success"})
    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@pages.route('/page_versions_diff')
@login_required
def get_page_diff():
    """
    Renders a page showing the differences between two versions of a page.

    This endpoint requires the user to be logged in. It retrieves the page ID and the
    commit IDs of the two versions to be compared from the request arguments. It then
    checks if the user has access to the specified page. If the user has access, it
    renders a template displaying the differences between the specified versions. If
    not, it returns a 403 Forbidden error.

    Parameters:
    - page_id (int): The ID of the page.
    - commit_id_1 (str): The ID of the first commit.
    - commit_id_2 (str): The ID of the second commit.

    Returns:
    - A rendered template showing the differences between the two versions of the page,
      or a JSON response with an error message and a 403 status code if the user does
      not have access.
    """

    page_id = int(werkzeug.utils.escape(request.args.get('page_id', type=str)))
    commit_id_1 = str(werkzeug.utils.escape(request.args.get('cid_1', type=str)))
    commit_id_2 = str(werkzeug.utils.escape(request.args.get('cid_2', type=str)))

    # Check for user permissions
    if not user_has_access_page(page_id):
        return jsonify({"error": "Forbidden"}), 403

    return render_template("versioning_diff.html", userId=session["id"], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session["user_image"], accountId=session["accountId"], is_admin=session["is_admin"], is_manager=session["is_manager"], site_notice=Config.SITE_NOTICE, preview_webserver=Config.PREVIEW_SERVER, page_id=page_id, commit_id_1=commit_id_1, commit_id_2=commit_id_2)


@pages.route('/api/page_versions_diff', methods=["POST"])
@login_required
def api_get_page_diff():
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
        "page_id": 123,
        "cid_1": "commit1",
        "cid_2": "commit2"
    }
    """

    try:
        request_data = request.get_json()
        page_id = int(werkzeug.utils.escape(request_data['page_id']))
        commit_id_1 = str(werkzeug.utils.escape(request_data['cid_1']))
        commit_id_2 = str(werkzeug.utils.escape(request_data['cid_2']))

        # Check for user permissions
        if not user_has_access_page(page_id):
            return jsonify({"error": "Forbidden"}), 403

        # Get Page Details
        page_details = get_page_details(page_id)
        page_HTMLPath = page_details["HTMLPath"]

        # Get Commit Diff
        diff_text = Config.GIT_REPO.git.diff(commit_id_1, commit_id_2, '--', os.path.join(Config.WEBSERVER_FOLDER, page_HTMLPath))

        return jsonify({"message": "success", "diff_text": diff_text})
    except Exception as e:
        print(traceback.format_exc())
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
