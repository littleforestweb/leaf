import traceback

import werkzeug.utils
from flask import Blueprint, render_template, request, jsonify, session, current_app

from leaf import Config
from leaf.decorators import login_required
from leaf.sites.models import getSiteFromPageId, user_has_access_page, site_belongs_to_account
from .models import get_page_details, remove_base_href, save_html_to_disk, update_modified_date, add_base_href

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
        page_id = werkzeug.utils.escape(request.args.get('page_id', type=str))

        # Check if the specified page to the user's account
        siteId = getSiteFromPageId(int(page_id))
        hasAccess = user_has_access_page(int(page_id))
        if not site_belongs_to_account(siteId) or not hasAccess:
            return jsonify({"error": "Forbidden"}), 403

        return render_template('editor.html', email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], page_id=page_id, site_notice=Config.SITE_NOTICE, is_source_editor=session["is_source_editor"], editor_allow_scripts_regex_patters=Config.EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS)
    except Exception as e:
        current_app.logger.error(traceback.format_exc())
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
        siteId = getSiteFromPageId(int(page_id))
        hasAccess = user_has_access_page(int(page_id))
        if not site_belongs_to_account(siteId) or not hasAccess:
            return jsonify({"error": "Forbidden"}), 403

        # Get HTML path for the page
        html_path = get_page_details(int(page_id))
        with open(html_path, 'r') as in_file:
            content = in_file.read()

        # Add base href to HTML
        content = add_base_href(content)

        # Create json
        json_response = {"data": content}
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
        data = request.form.get("data", type=str)
        page_id = werkzeug.utils.escape(request.form.get("page_id", type=str))

        # Check if the specified page to the user's account
        siteId = getSiteFromPageId(int(page_id))
        hasAccess = user_has_access_page(int(page_id))
        if not site_belongs_to_account(siteId) or not hasAccess:
            return jsonify({"error": "Forbidden"}), 403

        # Get HTML path from page_id
        html_path = get_page_details(int(page_id))

        # Remove base href from HTML
        data = remove_base_href(data)

        # Save HTML code to disk
        save_html_to_disk(html_path, data)

        # Update modified_date
        update_modified_date(page_id)

        # Set previewURL
        previewURL = html_path.replace(Config.WEBSERVER_FOLDER.rstrip("/"), Config.PREVIEW_SERVER.rstrip("/"))

        # Return info back to view
        json_response = {"message": "success", "previewURL": previewURL}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
