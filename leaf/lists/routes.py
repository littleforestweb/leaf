import sys

from flask import Blueprint, render_template, request

from leaf.decorators import login_required
from .models import *

csv.field_size_limit(sys.maxsize)

lists = Blueprint('lists', __name__)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route("/lists")
@login_required
def view_lists():
    """
    Renders the 'lists.html' template with user-specific data.

    Returns:
        HTML template with user-specific data.
    """
    return render_template('lists.html', userId=session['id'], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], site_notice=Config.SITE_NOTICE, page_extension=Config.PAGES_EXTENSION)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route("/manage_templates")
@login_required
def view_manage_templates():
    """
    Renders the 'manage_templates.html' template with specific data.

    Returns:
        HTML template with specific data.
    """
    return render_template('manage_templates.html', userId=session['id'], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], site_notice=Config.SITE_NOTICE, page_extension=Config.PAGES_EXTENSION)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_lists/<accountId>/<userId>/<isAdmin>')
@login_required
def api_get_lists(accountId: str, userId: str, isAdmin: str):
    """
    Retrieves lists data based on account, user, and admin status.

    Args:
        accountId (str): Account ID.
        userId (str): User ID.
        isAdmin (str): Admin status.

    Returns:
        JSON response with lists data.
    """
    return get_lists_data(accountId, userId, isAdmin)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route("/list/<reference>")
@login_required
def view_dynamic_list(reference: str):
    """
    Renders the 'dynamic_list.html' template with dynamic list data.

    Args:
        reference (str): Reference parameter.

    Returns:
        HTML template with dynamic list data.
    """
    referenceNoUnderscores = reference.replace("_", " ")
    preview_server = Config.PREVIEW_SERVER
    dynamic_path = Config.DYNAMIC_PATH
    return render_template('dynamic_list.html', preview_server=preview_server, dynamic_path=dynamic_path, reference=reference, referenceNoUnderscores=referenceNoUnderscores, userId=session['id'], email=session["email"], username=session["username"], first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'], site_notice=Config.SITE_NOTICE, page_extension=Config.PAGES_EXTENSION)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list/<accountId>/<reference>')
@login_required
def api_get_list(accountId: str, reference: str):
    """
    Retrieves data for a single list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response with data for the specified list.
    """
    return get_list_data(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list_columns/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_list_columns(accountId: str, reference: str):
    """
    Retrieves columns for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response with list columns.
    """
    return get_list_columns(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list_columns_with_returned_id/<accountId>/<reference>/<fieldToReturn>/<linkedFieldToReturn>/<linkedFieldLabelToReturn>', methods=['GET', 'POST'])
@login_required
def api_get_list_columns_with_returned_id(accountId: str, reference: str, fieldToReturn: str, linkedFieldToReturn: str, linkedFieldLabelToReturn: str):
    """
    Retrieves columns with returned ID for a specific list based on account, reference, and field parameters.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.
        fieldToReturn (str): Field to return.
        linkedFieldToReturn (str): Linked field to return.
        linkedFieldLabelToReturn (str): Linked field label to return.

    Returns:
        JSON response with list columns.
    """
    return get_list_columns_with_returned_id(accountId, reference, fieldToReturn, linkedFieldToReturn, linkedFieldLabelToReturn)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list_columns_with_properties/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_list_columns_with_properties(accountId: str, reference: str):
    """
    Retrieves columns with properties for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response with list columns and their properties.
    """
    return get_list_columns_with_properties(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list_configuration/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_list_configuration(accountId: str, reference: str):
    """
    Retrieves configuration for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response with list configuration.
    """
    return get_list_configuration(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/set/configuration/<accountId>/<reference>', methods=['POST'])
@login_required
def set_configuration(accountId: str, reference: str):
    """
    Sets configuration for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return set_list_configuration(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_all_templates/<accountId>', methods=['GET', 'POST'])
@login_required
def api_get_all_templates(accountId: str):
    """
    Retrieves templates based on account.

    Args:
        accountId (str): Account ID.

    Returns:
        JSON response with list templates.
    """
    return get_all_templates(request, accountId)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list_template/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_list_template(accountId: str, reference: str):
    """
    Retrieves template for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response with list template.
    """
    return get_list_template(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/set/template/<accountId>/<reference>', methods=['POST'])
@login_required
def set_template(accountId: str, reference: str):
    """
    Sets template for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return set_list_template(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/delete/template/<accountId>', methods=['POST'])
@login_required
def delete_template(accountId: str):
    """
    Deletes template based on account.

    Args:
        accountId (str): Account ID.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_templates(request, accountId)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_available_fields/<accountId>/<reference>', methods=['GET'])
@login_required
def api_get_available_fields(accountId: str, reference: str):
    """
    Gets available fields for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'GET':
        return get_available_fields(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_value_columns_with_index/<accountId>/<reference>/<fieldToGet>/<fieldToLabel>/<indexToKeep>/<indexToKeepForAccountSettings>', methods=['GET', 'POST'])
@login_required
def api_get_value_columns_with_index(accountId: str, reference: str, fieldToGet: str, fieldToLabel: str, indexToKeep: str, indexToKeepForAccountSettings: str):
    """
    Retrieves columns with index for a specific list based on account, reference, and field parameters.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.
        fieldToGet (str): Field to retrieve.
        fieldToLabel (str): Field to label.
        indexToKeep (str): Index to keep.
        indexToKeepForAccountSettings (str): Index to keep for account settings.

    Returns:
        JSON response with columns.
    """
    return get_value_columns_with_index(accountId, reference, fieldToGet, fieldToLabel, indexToKeep, indexToKeepForAccountSettings)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/upload/dynamic_list', methods=['GET', 'POST'])
@login_required
def upload_dynamic_list():
    """
    Handles the upload of a dynamic list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return upload_dynamic_lists(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/upload/create_middle_tables/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def upload_create_middle_tables(accountId: str, reference: str):
    """
    Handles the creation of middle tables for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        String indicating success.
    """
    if request.method == 'POST':
        return create_middle_tables(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/settings/<accountId>')
@login_required
def api_settings(accountId: str):
    """
    Retrieves settings based on account ID.

    Args:
        accountId (str): Account ID.

    Returns:
        JSON response with settings.
    """
    return get_settings(accountId)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_all_lists/<accountId>')
@login_required
def api_get_all_lists(accountId: str):
    """
    Retrieves all lists based on account ID.

    Args:
        accountId (str): Account ID.

    Returns:
        JSON response with all lists.
    """
    return get_all_lists(accountId)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/publish/<account_list>/<accountId>/<reference>/<env>', methods=['POST'])
@login_required
def publish_dynamic_list(account_list: str, accountId: str, reference: str, env: str):
    """
    Publishes a dynamic list based on account, reference, and environment.

    Args:
        account_list (str): Account list.
        accountId (str): Account ID.
        reference (str): List reference.
        env (str): Environment.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return publish_dynamic_lists(request, account_list, accountId, reference, env)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/save_jsons_by_fields/<account_list>/<accountId>/<reference>', methods=['POST'])
@login_required
def save_jsons_by_fields(account_list: str, accountId: str, reference: str):
    """
    Save a dynamic list based on account and reference.

    Args:
        account_list (str): Account list.
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return generate_all_json_files_by_fields(request, account_list, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/update/<accountId>/<account_list>', methods=['POST'])
@login_required
def update_dynamic_list(accountId: str, account_list: str):
    """
    Updates a dynamic list based on account list.

    Args:
        accountId (str): Account ID.
        account_list (str): Account list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return update_dynamic_lists(request, accountId, account_list)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/addnew/<accountId>/<account_list>', methods=['POST'])
@login_required
def addnew_dynamic_list(accountId: str, account_list: str):
    """
    Adds a new dynamic list based on account list.

    Args:
        accountId (str): Account ID.
        account_list (str): Account list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return add_dynamic_lists(request, accountId, account_list)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/delete/<accountId>/<account_list>', methods=['POST'])
@login_required
def delete_dynamic_list(accountId: str, account_list: str):
    """
    Deletes a dynamic list based on account list.

    Args:
        accountId (str): Account ID.
        account_list (str): Account list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_dynamic_lists(request, accountId, account_list)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@lists.route('/add/list', methods=['POST'])
@login_required
def add_list():
    """
    Adds a new list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return add_single_list(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/update/list', methods=['POST'])
@login_required
def update_list():
    """
    Updates a list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return update_single_list(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/delete/lists', methods=['POST'])
@login_required
def delete_lists():
    """
    Deletes multiple lists.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_multiple_lists(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/delete/list', methods=['POST'])
@login_required
def delete_list():
    """
    Deletes a dynamic list.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_single_list(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/scrape/list_data', methods=['POST'])
@login_required
def api_scrape_list_data():

    if request.method == 'POST':
        return scrape_list_data(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/get_list_scrape_settings/<accountId>/<reference>', methods=['GET'])
@login_required
def api_get_list_scrape_settings(accountId: str, reference: str):

    if request.method == 'GET':
        return get_list_scrape_settings(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/set/scrape_settings/<accountId>/<reference>', methods=['POST'])
@login_required
def set_scrape_settings(accountId: str, reference: str):
    """
    Sets scrape settings for a specific list based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): List reference.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return set_list_scrape_settings(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@lists.route('/api/trigger_new_scrape', methods=['POST'])
@login_required
def api_trigger_new_scrape():
    if request.method == 'POST':
        return trigger_new_scrape(request)
