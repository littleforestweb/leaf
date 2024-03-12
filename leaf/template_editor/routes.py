from flask import Blueprint, render_template, request, jsonify, session

import leaf.sites.models
from leaf.decorators import login_required
from .models import *
from leaf import Config
import werkzeug.utils

# Create a Blueprint for the template_editor routes
template_editor = Blueprint('template_editor', __name__)


# ---------------------------------------------------------------------------------------------------------- #

@template_editor.route("/templates/<template_id>")
@login_required
def view_template_editor(template_id):
    """
    View template_editor route.

    Returns:
        render_template: Rendered template for the template_editor.
    """
    try:
        return render_template('template_editor.html', username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], template_id=template_id)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@template_editor.route("/api/templates/get_template_id/<accountId>/<template_id>")
@login_required
def api_templates_get_template_id(accountId, template_id):
    """
    Get HTML code for the specified page route.

    Returns:
        jsonify: JSON response containing HTML code.
    """
    template_html = templates_get_template_html(accountId, template_id)
    html_to_return = add_tempalte_base_href(template_html)

    return html_to_return


@template_editor.route("/api/templates/save", methods=["POST"])
@login_required
def api_templates_save():
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

@template_editor.route('/api/get_template_by_id/<accountId>/<template_id>', methods=['GET', 'POST'])
@login_required
def api_get_template_by_id(accountId: str, template_id: str):
    """
    Retrieves template based on account and template_id.

    Args:
        accountId (str): Account ID.
        template_id (str): Template ID.

    Returns:
        JSON response with template.
    """
    return get_template_by_id(accountId, template_id)
