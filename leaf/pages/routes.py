from flask import render_template, Blueprint, jsonify, redirect, session, url_for, request
from leaf.decorators import login_required
from .models import get_all_pages_data, get_page, get_screenshot, duplicate_page
import werkzeug.utils

# Create a Blueprint for the pages routes
pages = Blueprint('pages', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@pages.route('/all_pages')
@login_required
def view_all_pages():
    """
    View all pages route.

    Returns:
        render_template: Rendered template for all pages.
    """
    try:
        # Render the template with user information
        return render_template('all_pages.html', username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'])
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@pages.route("/api/all_pages")
@login_required
def api_all_pages():
    """
    API endpoint to fetch all pages data.

    Returns:
        jsonify: JSON response containing all pages data.
    """
    try:
        all_pages_data = get_all_pages_data()
        return jsonify(all_pages_data)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@pages.route('/get_page')
@login_required
def get_page_route():
    """
    Route to get a specific page.

    Returns:
        send_from_directory: Send HTML file from the directory.
    """
    try:
        pid = werkzeug.utils.escape(request.args.get('id', type=str))
        return get_page(pid)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@pages.route('/get_screenshot')
@login_required
def get_screenshot_route():
    """
    Route to get the screenshot of a specific page.

    Returns:
        send_from_directory: Send screenshot file from the directory.
    """
    try:
        pageId = werkzeug.utils.escape(request.args.get('id', type=str))
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
        site_id = werkzeug.utils.escape(request.form.get("site_id", type=str))
        ogPageId = werkzeug.utils.escape(request.form.get("ogPageId", type=str))
        ogURL = werkzeug.utils.escape(request.form.get("ogURL", type=str))
        ogURL = ogURL.lstrip("/") if ogURL.startswith("/") else ogURL
        newTitle = werkzeug.utils.escape(request.form.get("newTitle", type=str))
        newUrl = werkzeug.utils.escape(request.form.get("newUrl", type=str))
        newUrl = newUrl.lstrip("/") if newUrl.startswith("/") else newUrl
        return duplicate_page(site_id, ogPageId, ogURL, newTitle, newUrl)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
