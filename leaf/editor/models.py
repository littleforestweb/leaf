import datetime
import os
import re

import mysql.connector
from bs4 import BeautifulSoup

from leaf.config import Config
from leaf.decorators import db_connection


# Function to get the HTML path for the specified page
def get_page_html_path(page_id):
    """
    Get the HTML path for the specified page.

    Args:
        page_id (int): ID of the page.

    Returns:
        str: HTML path for the specified page.
    """
    try:
        # Connect to the database
        mydb, mycursor = db_connection()

        # Execute SQL query to fetch HTML path
        mycursor.execute("SELECT HTMLpath FROM site_meta WHERE id=%s", (page_id,))
        html_path = os.path.join(Config.WEBSERVER_FOLDER, mycursor.fetchone()[0])

        # Close the database connection
        mydb.close()
        return html_path
    except (mysql.connector.Error, FileNotFoundError):
        raise


def replace_ssi(html_path):
    """
    Replace Server Side Includes (SSI) directives in an HTML file with their actual content.

    Args:
        html_path (str): The path to the HTML file containing SSI directives.

    Returns:
        str: The modified content of the HTML file with SSI directives replaced with actual content.
    """
    with open(html_path, 'r') as f:
        content = f.read()

    # Regular expression to match SSI include directives
    ssi_pattern = re.compile(r'<!--#include\s+virtual="(.*?)"\s+-->')

    def replace_match(match):
        include_path = match.group(1)
        # Resolve virtual path to the actual file path
        include_file_path = os.path.join(os.path.dirname(html_path), include_path[1:])
        # Read the content of the included file
        with open(include_file_path, 'r') as include_file:
            return include_file.read()

    # Replace SSI includes with actual content
    replaced_content = ssi_pattern.sub(replace_match, content)

    return replaced_content


# Function to add base href to the HTML file
def add_base_href(data):
    """
    Add base href to the HTML file.

    Args:
        data (str): html content.

    Returns:
        str: HTML content with added base href.
    """
    try:
        soup = BeautifulSoup(data, "html5lib")

        # Find the head tag and add base tag
        head_tag = soup.find("head")
        base_tag = soup.new_tag("base", href=Config.PREVIEW_SERVER)
        head_tag.insert(0, base_tag)

        # Prettify the HTML content
        data = soup.prettify()
        return data
    except (FileNotFoundError, Exception):
        raise


# Function to remove base href from the HTML content
def remove_base_href(data):
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
def save_html_to_disk(html_path, data):
    """
    Save HTML content to the specified path.

    Args:
        html_path (str): Path to save the HTML file.
        data (str): HTML content to be saved.
    """
    try:
        # Open the file and write the HTML content
        with open(html_path, "w") as outFile:
            data = BeautifulSoup(data, "html5lib").prettify()
            outFile.write(data)
    except (FileNotFoundError, Exception):
        raise


# Function to update the modified date of the specified page
def update_modified_date(page_id):
    """
    Update the modified date of the specified page.

    Args:
        page_id (str): ID of the page.
    """
    try:
        # Connect to the database
        mydb, mycursor = db_connection()

        # Get the current date and time
        modified_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update the modified date in the database
        sql = "UPDATE site_meta SET modified_date = %s WHERE id = %s"
        val = (modified_date, page_id)
        mycursor.execute(sql, val)
        mydb.commit()

        # Close the database connection
        mydb.close()
    except mysql.connector.Error:
        raise
    except Exception:
        raise
