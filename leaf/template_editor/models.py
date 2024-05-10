import os
import re

import werkzeug.utils
from bs4 import BeautifulSoup
from flask import jsonify, session

from leaf.config import Config
from leaf.decorators import db_connection


def templates_get_template_html(accountId, template_id):
    """
    Get HTML code for the specified page route.

    Returns:
        jsonify: JSON response containing HTML code.
    """
    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    template_info = []

    try:

        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_list_template"

            # Retrieve templates information
            get_templates_query = f"SELECT * FROM {tableName} WHERE id = %s"
            mycursor.execute(get_templates_query, (template_id,))
            template_info = mycursor.fetchall()
            with open(Config.TEMPLATES_FOLDER + "/" + accountId + "/" + template_info[0][2], 'r') as file:
                # Read the contents of the file
                file_contents = file.read()

        else:
            print("Invalid accountId")

        return file_contents
    except Exception as e:
        # Handle exceptions and return an error response with status code 500
        return jsonify({"error": str(e)}), 500


# Function to add base href to the HTML file
def add_tempalte_base_href(template_html):
    """
    Add base href to the HTML file.

    Args:
        html_path (str): Path of the HTML file.

    Returns:
        str: HTML content with added base href.
    """
    template_html_to_return = ""

    try:
        if template_html and template_html != "":
            # Open and read the HTML file
            soup = BeautifulSoup(str(template_html), "html5lib")

            # Find the head tag and add base tag
            head_tag = soup.find("head")
            base_tag = soup.new_tag("base", href=Config.PREVIEW_SERVER)
            head_tag.insert(0, base_tag)

            # Prettify the HTML content
            template_html_to_return = soup.prettify()

        return template_html_to_return
    except (FileNotFoundError, Exception):
        raise


# Function to remove base href from the HTML content
def remove_template_base_href(data):
    """
    Remove base href from the HTML content.

    Args:
        data (str): HTML content.

    Returns:
        str: HTML content with base href removed.
    """
    try:
        # Parse the HTML content
        soup = BeautifulSoup(data, "html5lib")

        # Find and remove the base tag
        base_tag = soup.find("base")
        if base_tag:
            base_tag.extract()  # Remove the base tag if it exists
        return soup.prettify()
    except Exception:
        raise


def template_save(request, accountId):
    """
    Save Template HTML content.

    Args:
        request: Including the data to save and the template ID
    """

    json_response = {}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_template"

        if isinstance(int(accountId), int):

            # Get data, page_id and template_url_pattern from the form
            data = request.form.get("data", type=str)
            template_id = werkzeug.utils.escape(request.form.get("template_id", type=str))
            template_url_pattern = werkzeug.utils.escape(request.form.get("template_url_pattern", type=str))
            template_feed_url_pattern = werkzeug.utils.escape(request.form.get("template_feed_url_pattern", type=str))
            template_name = request.form.get("template_name", type=str)
            template_name = template_name.lower()
            template_name = ''.join(c if c.isalnum() else '_' for c in template_name)
            template_name = werkzeug.utils.escape(template_name)

            if not template_name.endswith("_html"):
                template_name += ".html"
            template_name = template_name.replace("_html", ".html")

            # Remove base href from HTML
            data = remove_base_href_from_template(data)

            get_templates_query = f"SELECT * FROM {tableName} WHERE id = %s"
            mycursor.execute(get_templates_query, (template_id,))
            template_info = mycursor.fetchall()
            template_file = template_info[0][2]

            update_templates_query = f"UPDATE {tableName} SET template = %s, template_location = %s, feed_location = %s, modified_by = %s, modified = CURRENT_TIMESTAMP WHERE id = %s"
            mycursor.execute(update_templates_query, (template_name, template_url_pattern, template_feed_url_pattern, session["id"], str(template_id)))
            mydb.commit()

            file_to_save = os.path.join(Config.TEMPLATES_FOLDER, str(accountId), template_file)
            folder_to_save_item = os.path.dirname(file_to_save)

            os.makedirs(folder_to_save_item, exist_ok=True)
            with open(file_to_save, 'w') as out_file:
                out_file.write(data)

            json_response = {"message": "success"}

        else:
            print("Invalid accountId")
    except Exception as e:
        print("template_save model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


# Function to save HTML content to the specified path
def save_template_html_to_disk(html_path, data):
    """
    Save HTML content to the specified path.

    Args:
        html_path (str): Path to save the HTML file.
        data (str): HTML content to be saved.
    """
    try:
        # Open the file and write the HTML content
        with open(html_path, "w") as outFile:
            outFile.write(data)
    except (FileNotFoundError, Exception):
        raise


def get_template_by_id(accountId: str, template_id: str):
    """
    Get template information from the database.

    Args:
        accountId (str): The account ID associated with the template.
        template_id (str): The id for the specific template.

    Returns:
        dict: A JSON response containing template information for the specified list.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    if isinstance(int(accountId), int):

        field_list_for_config = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                                 'in_lists VARCHAR(255) DEFAULT NULL',
                                 'template VARCHAR(255) DEFAULT NULL',
                                 'template_location VARCHAR(255) DEFAULT NULL',
                                 'feed_location VARCHAR(255) DEFAULT NULL',
                                 'modified_by INT(11) DEFAULT NULL',
                                 'created DATETIME NULL DEFAULT CURRENT_TIMESTAMP',
                                 'modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP']
        field_query_for_config = " (" + ", ".join(field_list_for_config) + ")"

        tableName = f"account_{accountId}_list_template"

        # Create table if not exists
        create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} {field_query_for_config}"
        mycursor.execute(create_table_query, )
        mydb.commit()

        # Retrieve templates information
        get_templates_query = f"SELECT * FROM {tableName} WHERE id = %s"
        mycursor.execute(get_templates_query, (template_id,))
        template_info = mycursor.fetchall()

        jsonR['columns'] = template_info
    else:
        print("Invalid accountId")

    return jsonify(jsonR)


# Function to remove base href from the HTML content
def remove_base_href_from_template(data):
    """
    Remove base href from the HTML content.

    Args:
        data (str): HTML content.

    Returns:
        str: HTML content with base href removed.
    """
    try:
        # Parse the HTML content
        soup = BeautifulSoup(data, "html5lib")

        # Find and remove the base tag
        base_tag = soup.find("base")
        if base_tag:
            base_tag.extract()  # Remove the base tag if it exists
        return soup.prettify()
    except Exception:
        raise


def clean_up_html_elements(list_template_html: str):
    # Remove any HTML elements that contain {{ITEM}} placeholders
    list_template_html = re.sub(r'<[^>]*{{.*?}}[^>]*>.*?</[^>]*>', '', list_template_html)

    return list_template_html
