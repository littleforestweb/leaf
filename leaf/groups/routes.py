from flask import render_template, Blueprint, jsonify, session

from leaf.decorators import login_required, admin_required
from leaf.groups.models import get_groups
from leaf import Config

groups = Blueprint('groups', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@groups.route("/groups")
@login_required
@admin_required
def view_groups():
    """
    Render the groups page.

    Returns:
        flask.Response: Rendered HTML page with groups information.
    """
    try:
        return render_template('groups.html', username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], site_notice=Config.SITE_NOTICE)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


@groups.route("/api/get_groups")
@login_required
@admin_required
def api_get_groups():
    """
    API endpoint to fetch groups.

    Returns:
        jsonify: JSON response containing groups.
    """
    try:
        # Fetch deployments data from the model
        groups_data = get_groups()

        # Create JSON response
        json_response = {"groups": groups_data}
        return jsonify(json_response)
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500
