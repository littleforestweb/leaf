import traceback

import werkzeug.utils
from flask import Blueprint, jsonify, request

from leaf.decorators import login_required
from .models import get_page, get_screenshot, duplicate_page, get_site_id, get_page_details

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
