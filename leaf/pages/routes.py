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
