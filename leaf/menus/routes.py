from flask import Blueprint, redirect, url_for, render_template, session, request
import sys
import csv
from .models import *
from leaf.decorators import login_required

csv.field_size_limit(sys.maxsize)

menus = Blueprint('menus', __name__)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route("/menus")
@login_required
def view_menus():
    """
    Renders the 'menus.html' template with user-specific data.

    Returns:
        HTML template with user-specific data.
    """
    return render_template('menus.html', userId=session['id'], username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'])

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_menus/<accountId>/<userId>/<isAdmin>')
@login_required
def api_get_menus(accountId: str, userId: str, isAdmin: str):
    """
    Retrieves menus data based on account, user, and admin status.

    Args:
        accountId (str): Account ID.
        userId (str): User ID.
        isAdmin (str): Admin status.

    Returns:
        JSON response with menus data.
    """
    return get_menus_data(accountId, userId, isAdmin)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route("/menu/<reference>")
@login_required
def view_dynamic_menu(reference: str):
    """
    Renders the 'dynamic_menu.html' template with dynamic menu data.

    Args:
        reference (str): Reference parameter.

    Returns:
        HTML template with dynamic menu data.
    """
    referenceNoUnderscores = reference.replace("_", " ")
    preview_server = Config.PREVIEW_SERVER
    dynamic_path = Config.DYNAMIC_PATH
    return render_template('dynamic_menu.html', preview_server=preview_server, dynamic_path=dynamic_path, reference=reference, referenceNoUnderscores=referenceNoUnderscores, username=session['username'], user_image=session['user_image'], accountId=session['accountId'], is_admin=session['is_admin'], is_manager=session['is_manager'])


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_menu/<accountId>/<reference>')
@login_required
def api_get_menu(accountId: str, reference: str):
    """
    Retrieves data for a single menu based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.

    Returns:
        JSON response with data for the specified menu.
    """
    return get_menu_data(request, accountId, reference)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_menu_columns/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_menu_columns(accountId: str, reference: str):
    """
    Retrieves columns for a specific menu based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.

    Returns:
        JSON response with menu columns.
    """
    return get_menu_columns(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_menu_columns_with_returned_id/<accountId>/<reference>/<fieldToReturn>/<linkedFieldToReturn>/<linkedFieldLabelToReturn>', methods=['GET', 'POST'])
@login_required
def api_get_menu_columns_with_returned_id(accountId: str, reference: str, fieldToReturn: str, linkedFieldToReturn: str, linkedFieldLabelToReturn: str):
    """
    Retrieves columns with returned ID for a specific menu based on account, reference, and field parameters.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.
        fieldToReturn (str): Field to return.
        linkedFieldToReturn (str): Linked field to return.
        linkedFieldLabelToReturn (str): Linked field label to return.

    Returns:
        JSON response with menu columns.
    """
    return get_menu_columns_with_returned_id(accountId, reference, fieldToReturn, linkedFieldToReturn, linkedFieldLabelToReturn)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_menu_columns_with_properties/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_menu_columns_with_properties(accountId: str, reference: str):
    """
    Retrieves columns with properties for a specific menu based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.

    Returns:
        JSON response with menu columns and their properties.
    """
    return get_menu_columns_with_properties(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_menu_configuration/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def api_get_menu_configuration(accountId: str, reference: str):
    """
    Retrieves configuration for a specific menu based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.

    Returns:
        JSON response with menu configuration.
    """
    return get_menu_configuration(accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/set/configuration/<accountId>/<reference>', methods=['POST'])
@login_required
def set_configuration(accountId: str, reference: str):
    """
    Sets configuration for a specific menu based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return set_menu_configuration(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/get_value_columns_with_index/<accountId>/<reference>/<fieldToGet>/<fieldToLabel>/<indexToKeep>/<indexToKeepForAccountSettings>', methods=['GET', 'POST'])
@login_required
def api_get_value_columns_with_index(accountId: str, reference: str, fieldToGet: str, fieldToLabel: str, indexToKeep: str, indexToKeepForAccountSettings: str):
    """
    Retrieves columns with index for a specific menu based on account, reference, and field parameters.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.
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

@menus.route('/upload/dynamic_menu', methods=['GET', 'POST'])
@login_required
def upload_dynamic_menu():
    """
    Handles the upload of a dynamic menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return upload_dynamic_menus(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@menus.route('/upload/create_middle_tables/<accountId>/<reference>', methods=['GET', 'POST'])
@login_required
def upload_create_middle_tables(accountId: str, reference: str):
    """
    Handles the creation of middle tables for a specific menu based on account and reference.

    Args:
        accountId (str): Account ID.
        reference (str): Menu reference.

    Returns:
        String indicating success.
    """
    if request.method == 'POST':
        return create_middle_tables(request, accountId, reference)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/api/settings/<accountId>')
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

@menus.route('/api/get_all_menus/<accountId>')
@login_required
def api_get_all_menus(accountId: str):
    """
    Retrieves all menus based on account ID.

    Args:
        accountId (str): Account ID.

    Returns:
        JSON response with all menus.
    """
    return get_all_menus(accountId)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@menus.route('/publish/<account_menu>/<accountId>/<reference>/<env>', methods=['POST'])
@login_required
def publish_dynamic_menu(account_menu: str, accountId: str, reference: str, env: str):
    """
    Publishes a dynamic menu based on account, reference, and environment.

    Args:
        account_menu (str): Account menu.
        accountId (str): Account ID.
        reference (str): Menu reference.
        env (str): Environment.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return publish_dynamic_menus(request, account_menu, accountId, reference, env)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@menus.route('/update/<accountId>/<account_menu>', methods=['POST'])
@login_required
def update_dynamic_menu(accountId: str, account_menu: str):
    """
    Updates a dynamic menu based on account menu.

    Args:
        accountId (str): Account ID.
        account_menu (str): Account menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return update_dynamic_menus(request, accountId, account_menu)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@menus.route('/addnew/<accountId>/<account_menu>', methods=['POST'])
@login_required
def addnew_dynamic_menu(accountId: str, account_menu: str):
    """
    Adds a new dynamic menu based on account menu.

    Args:
        accountId (str): Account ID.
        account_menu (str): Account menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return add_dynamic_menus(request, accountId, account_menu)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@menus.route('/delete/<accountId>/<account_menu>', methods=['POST'])
@login_required
def delete_dynamic_menu(accountId: str, account_menu: str):
    """
    Deletes a dynamic menu based on account menu.

    Args:
        accountId (str): Account ID.
        account_menu (str): Account menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_dynamic_menus(request, accountId, account_menu)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #@

@menus.route('/add/menu', methods=['POST'])
@login_required
def add_menu():
    """
    Adds a new menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return add_single_menu(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/update/menu', methods=['POST'])
@login_required
def update_menu():
    """
    Updates a menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return update_single_menu(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/delete/menus', methods=['POST'])
@login_required
def delete_menus():
    """
    Deletes multiple menus.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_multiple_menus(request)

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@menus.route('/delete/menu', methods=['POST'])
@login_required
def delete_menu():
    """
    Deletes a dynamic menu.

    Returns:
        JSON response indicating success or failure.
    """
    if request.method == 'POST':
        return delete_single_menu(request)