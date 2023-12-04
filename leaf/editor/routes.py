from flask import Blueprint, render_template, request, jsonify, session

import leaf.sites.models
from leaf.decorators import login_required
from .models import get_page_html_path, add_base_href, remove_base_href, save_html_to_disk, update_modified_date
from leaf import Config
import werkzeug.utils

# Create a Blueprint for the editor routes
editor = Blueprint('editor', __name__)


# ---------------------------------------------------------------------------------------------------------- #

@editor.route("/editor")
@login_required
def view_editor():
    """
    View editor route.

    Returns:
        render_template: Rendered template for the editor.
    """
    try:
        pageId = werkzeug.utils.escape(request.args.get('page_id', type=str))

        # Check if the specified page to the user's account
        siteId = leaf.sites.models.getSiteFromPageId(int(pageId))
        if not leaf.sites.models.site_belongs_to_account(siteId):
            return jsonify({"error": "Forbidden"}), 403

        return render_template('editor.html', username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], page_id=pageId)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@editor.route("/editor/getPageCode")
@login_required
def get_htmlCode():
    """
    Get HTML code for the specified page route.

    Returns:
        jsonify: JSON response containing HTML code.
    """
    try:
        # Get page_id from the request
        page_id = werkzeug.utils.escape(request.args.get('page_id', type=str))

        # Check if the specified page to the user's account
        siteId = leaf.sites.models.getSiteFromPageId(int(page_id))
        if not leaf.sites.models.site_belongs_to_account(siteId):
            return jsonify({"error": "Forbidden"}), 403

        # Get HTML path for the page
        html_path = get_page_html_path(int(page_id))

        # Add base href to HTML
        data = add_base_href(html_path)

        # Create json
        json_response = {"data": data}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@editor.route("/api/editor/save", methods=["POST"])
@login_required
def save_page():
    """
    Save page route.

    Returns:
        jsonify: JSON response indicating the success of the save operation.
    """
    try:
        # Get data and page_id from the form
        data = werkzeug.utils.escape(request.form.get("data", type=str))
        page_id = werkzeug.utils.escape(request.form.get("page_id", type=str))

        # Check if the specified page to the user's account
        siteId = leaf.sites.models.getSiteFromPageId(int(page_id))
        if not leaf.sites.models.site_belongs_to_account(siteId):
            return jsonify({"error": "Forbidden"}), 403

        # Get HTML path from page_id
        html_path = get_page_html_path(int(page_id))

        # Remove base href from HTML
        data = remove_base_href(data)

        # Save HTML code to disk
        save_html_to_disk(html_path, data)

        # Update modified_date
        update_modified_date(page_id)

        # Set previewURL
        previewURL = html_path.replace(Config.WEBSERVER_FOLDER, Config.PREVIEW_SERVER + '/')

        # Return info back to view
        json_response = {"message": "success", "previewURL": previewURL}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
