import urllib3
import werkzeug.utils
from flask import render_template, Blueprint, request, jsonify, session

from leaf.config import Config
from leaf.decorators import login_required
from leaf.serverside import table_schemas
from leaf.serverside.serverside_table import ServerSideTable
from leaf.sites import models

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sites = Blueprint('sites', __name__)


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route("/sites")
@login_required
def view_sites():
    """
    Render the 'sites.html' template with user information.

    Requires the user to be logged in. Retrieves user information from the session
    and passes it to the template for rendering.

    Returns:
        flask.Response: Rendered HTML template with user information.
    """
    try:
        # Retrieve user information from the session
        username = session['username']
        email = session['email']
        first_name = session['first_name']
        last_name = session['last_name']
        display_name = session['display_name']
        user_image = session['user_image']
        account_id = session['accountId']
        is_admin = session['is_admin']
        is_manager = session['is_manager']

        # Render the template with user information
        return render_template('sites.html', email=email, username=username, first_name=first_name, last_name=last_name, display_name=display_name, user_image=user_image, accountId=account_id, is_admin=is_admin, is_manager=is_manager, site_notice=Config.SITE_NOTICE)
    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


@sites.route("/api/get_sites/")
@login_required
def api_get_sites():
    """
    Retrieve a list of sites via API.

    Requires the user to be logged in. Uses the 'getSitesList' function from the 'models'
    module to fetch the list of sites. Returns the site information in JSON format.

    Returns:
        flask.Response: JSON response containing a list of sites.
    """
    try:
        # Retrieve a list of sites using the 'getSitesList' function
        sites_list = models.getSitesList()

        # Create JSON response
        json_response = {"sites": sites_list}
        return jsonify(json_response)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code


# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/get_site')
@login_required
def view_get_site():
    """
    Render the 'get_site.html' template with user and site information.

    Requires the user to be logged in. Retrieves user information from the session
    and site ID from the request arguments. Passes user and site information to the
    template for rendering.

    Returns:
        flask.Response: Rendered HTML template with user and site information.
    """
    try:
        # Retrieve user information from the session
        user_id = session['id']
        email = session['email']
        username = session['username']
        first_name = session['first_name']
        last_name = session['last_name']
        display_name = session['display_name']
        user_image = session['user_image']
        account_id = session['accountId']
        is_admin = session['is_admin']
        is_manager = session['is_manager']

        # Retrieve site ID from request arguments
        site_id = werkzeug.utils.escape(request.args.get('id', type=str))

        # Get Folders that the user has access to
        user_access_folder = models.get_user_access_folder()

        # Render the template with user and site information
        return render_template('get_site.html', user_id=user_id, email=email, username=username, first_name=first_name, last_name=last_name, display_name=display_name, user_image=user_image, accountId=account_id, is_admin=is_admin, is_manager=is_manager, id=site_id, preview_webserver=Config.PREVIEW_SERVER, site_notice=Config.SITE_NOTICE, user_access_folder=user_access_folder)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/api/check_if_page_locked_by_me')
@login_required
def api_check_if_page_locked_by_me():
    """
    Checks if a specific page is currently locked by the user making the request. 
    This endpoint verifies if the specified site associated with the page belongs to the user's account 
    and checks if the page is locked by this user.

    This function is called via a GET request where `page_id` and `site_id` are required parameters.

    Parameters:
    - page_id (str): The unique identifier of the page to check. It is expected to be a string parameter 
      passed in the query string.
    - site_id (str): The unique identifier of the site that the page belongs to. This is used to 
      verify that the user has the right to view the lock status of the page.

    Returns:
    - JSON response:
        - If successful, returns a JSON object that indicates whether the page is locked by the user,
          along with additional information if applicable.
        - If the user does not have permission to access the site, returns a JSON object with an
          "error" key and "Forbidden" as the message, with a 403 status code.
        - If an error occurs during processing, returns a JSON object with an "error" key describing 
          the error, with a 500 status code.

    Raises:
    - HTTP 403: Returned if the specified site does not belong to the user's account, indicating
      forbidden access.
    - HTTP 500: Returned if there is any exception during the processing of the request, indicating 
      an internal server error.
    """
    try:
        page_id = werkzeug.utils.escape(request.args.get("page_id", type=str))
        site_id = werkzeug.utils.escape(request.args.get("site_id", type=str))


        # Check if the specified site belongs to the user's account
        if not models.site_belongs_to_account(int(site_id)):
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(models.check_if_page_locked_by_me(page_id))

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/api/lock_unlock_page', methods=['POST'])
@login_required
def api_lock_unlock_page():
    """
    API endpoint to lock or unlock a page on a site. It processes user input from POST data,
    checks if the site belongs to the user's account, and then performs the lock or unlock action.

    This route expects JSON payload with 'page_id', 'site_id', and 'action'. The 'action' can be
    either "lock" or "unlock". It ensures that the request comes from an authenticated user and
    that the site_id is associated with the user's account.

    Payload:
    - page_id (int): Identifier of the page to be modified.
    - site_id (int): Identifier of the site where the page resides.
    - action (str): Specifies the action to perform ("lock" or "unlock").

    Returns:
    - JSON response with success message or error details.
    - HTTP status code indicating the outcome (200 for success, 403 for forbidden access, 500 for internal errors).

    Raises:
    - HTTP 403: If the site does not belong to the user's account.
    - HTTP 500: If an unexpected error occurs during the process.
    """
    try:
        data = request.json
        page_id = data['page_id']
        site_id = data['site_id']
        action = data['action']

        # Check if the specified site belongs to the user's account
        if not models.site_belongs_to_account(int(site_id)):
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(models.lock_unlock_page(page_id, site_id, action))

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/api/get_site')
@login_required
def api_get_site():
    """
    API endpoint to retrieve site data.

    Requires the user to be logged in. Retrieves the 'id' parameter from the request
    arguments, checks if the specified site belongs to the user's account, and then
    retrieves pages from the site using a parameterized query. Returns the site data
    in JSON format.

    Returns:
        flask.Response: JSON response containing site data.
    """
    try:
        # Retrieve the 'id' parameter from the request arguments
        site_id = werkzeug.utils.escape(request.args.get("id", type=str))

        # Check if the specified site belongs to the user's account
        if not models.site_belongs_to_account(int(site_id)):
            return jsonify({"error": "Forbidden"}), 403

        # Get pages from the site using a parameterized query
        pages = models.get_site_data(site_id)

        # Define columns for the ServerSideTable
        columns = table_schemas.SERVERSIDE_TABLE_COLUMNS["get_site"]

        # Generate ServerSideTable data
        data = ServerSideTable(request, pages, columns).output_result()

        return jsonify(data)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/api/get_site_log')
@login_required
def api_get_site_log():
    """
    API endpoint to retrieve the crawl log of a specified site.

    Requires the user to be logged in. Retrieves the 'id' parameter from the request
    arguments, checks if the specified site belongs to the user's account, and then
    fetches the crawl log from the corresponding job in Heritrix. Returns the crawl log
    in JSON format.

    Returns:
        flask.Response: JSON response containing the crawl log.
    """
    try:
        site_id = werkzeug.utils.escape(request.args.get('id', type=str))

        # Check if the specified site belongs to the user's account
        if not models.site_belongs_to_account(int(site_id)):
            return jsonify({"error": "Forbidden"}), 403

        # Fetch the crawl log using a model function
        crawl_log = models.get_site_log(site_id)

        # Create JSON response
        json_response = {"crawlLogTail": crawl_log}
        return jsonify(json_response)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/add/site', methods=['POST'])
@login_required
def add_site():
    """
    Endpoint to add a new site.

    This route extracts site information from the request form and calls a model function to handle the addition
    of a new site. The extracted data includes site URL, label, ignore robots setting, maximum URLs, generate screenshots,
    allowed domains, and rejected paths.

    Returns:
        JSON response indicating the success or failure of the operation.
    """

    try:
        # Extract parameters from the request form
        site_data = {
            "site_url": werkzeug.utils.escape(request.form.get("site_url").strip()),
            "site_label": werkzeug.utils.escape(request.form.get("site_label").strip()),
            "site_ignore_robots": werkzeug.utils.escape(request.form.get("site_ignore_robots")),
            "site_max_urls": werkzeug.utils.escape(request.form.get("site_max_urls")),
            "site_gen_screenshots": werkzeug.utils.escape(request.form.get("site_gen_screenshots")),
            "site_allowed_domains": werkzeug.utils.escape(request.form.get("site_allowed_domains").split("\n")),
            "site_reject_paths": werkzeug.utils.escape(request.form.get("site_reject_paths").split("\n")),
        }

        # Call the model function to handle site addition
        result = models.add_new_site(site_data)

        return jsonify(result)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/update/site', methods=['POST'])
@login_required
def update_site():
    """
    Update the information of an existing site.

    This route handles the updating of an existing site's information, such as base URL and base folder, in the database.

    Parameters:
        original_site_id (str): The original ID of the site to be updated.
        new_site_url (str): The new base URL for the site.
        new_site_folder (str): The new base folder for the site.

    Returns:
        JSON response: A JSON response indicating the success of the update and providing information about the updated site.
    """
    try:

        # Get parameters from the post request
        original_site_id = werkzeug.utils.escape(request.form.get("original_site_id"))
        new_site_url = werkzeug.utils.escape(request.form.get("new_site_url"))
        new_site_folder = werkzeug.utils.escape(request.form.get("new_site_folder"))

        # Check if the specified site belongs to the user's account
        if not models.site_belongs_to_account(int(original_site_id)):
            return jsonify({"error": "Forbidden"}), 403

        # Call the model function to update the site information in the database
        result = models.update_site_info(original_site_id, new_site_url, new_site_folder)

        return jsonify(result)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

@sites.route('/delete/sites', methods=['POST'])
@login_required
def delete_sites():
    """
    Delete multiple sites.

    This route handles the deletion of multiple sites. It deletes each specified site from the database, performs
    actions in Heritrix (if applicable), and returns information about the deleted sites.

    Parameters:
        sites_to_delete (str): A comma-separated string containing the IDs of the sites to be deleted.

    Returns:
        JSON response: A JSON response indicating the success of the delete operation and providing information about the deleted sites.
    """
    try:
        # Get sites_to_delete from post params
        sites_to_delete = werkzeug.utils.escape(request.form.get("sites_to_delete"))

        # Check if the specified site belongs to the user's account
        for site_id in sites_to_delete.split(","):
            if not models.site_belongs_to_account(int(site_id)):
                return jsonify({"error": "Forbidden"}), 403

        # Call the model function to delete sites
        result = models.delete_sites(sites_to_delete)

        return jsonify(result)

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500  # Return a 500 Internal Server Error status code
