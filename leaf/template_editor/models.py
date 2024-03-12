import re

from flask import jsonify, session, current_app
from leaf.decorators import db_connection
import datetime
import os
import mysql.connector
from leaf.config import Config
from bs4 import BeautifulSoup


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
    try:
        # Open and read the HTML file
        soup = BeautifulSoup(template_html, "html5lib")

        # Find the head tag and add base tag
        head_tag = soup.find("head")
        base_tag = soup.new_tag("base", href=Config.PREVIEW_SERVER)
        head_tag.insert(0, base_tag)

        # Prettify the HTML content
        template_html = soup.prettify()
        return template_html
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


def clean_up_html_elements(list_template_html: str):
    # Remove any HTML elements that contain {{ITEM}} placeholders
    list_template_html = re.sub(r'<[^>]*{{.*?}}[^>]*>.*?</[^>]*>', '', list_template_html)

    return list_template_html