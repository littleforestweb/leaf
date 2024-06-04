import os
import shutil
import urllib.parse

from bs4 import BeautifulSoup
from flask import send_from_directory, session

from leaf.config import Config
from leaf.decorators import db_connection
from leaf.sites.models import get_user_access_folder


def get_page(pid):
    """
    Get a specific page from the database and serve its HTML content.

    Args:
        pid (int): The ID of the page to retrieve.

    Returns:
        send_from_directory: A Flask function to send the HTML file from the directory.

    Raises:
        Exception: If there is an error during the retrieval or serving process.
    """
    try:
        # Search DB for local file
        mydb, mycursor = db_connection()
        query = "SELECT HTMLpath FROM site_meta WHERE id=%s"
        params = (pid,)
        mycursor.execute(query, params)
        HTMLpath = mycursor.fetchall()[0][0]

        folderPath = os.path.dirname(HTMLpath)
        filePath = os.path.basename(HTMLpath)
        return send_from_directory(folderPath, filePath)
    except Exception as e:
        raise


def get_site_id(page_id):
    """
    Get a specific page from the database and serve its site_id.

    Args:
        page_id (int): The ID of the page to retrieve.

    Returns:
        site_id: The site id related to that page id.

    Raises:
        Exception: If there is an error during the retrieval or serving process.
    """
    try:
        # Search DB for local file
        mydb, mycursor = db_connection()
        query = "SELECT site_id FROM site_meta WHERE id=%s"
        params = (page_id,)
        mycursor.execute(query, params)
        site_id = mycursor.fetchone()[0]
        return str(site_id)
    except Exception as e:
        raise


def get_page_details(page_id):
    """
    Get a specific page from the database and serve its details.

    Args:
        page_id (int): The ID of the page to retrieve.

    Returns:
        page_details: The page details related to this page id.

    Raises:
        Exception: If there is an error during the retrieval or serving process.
    """

    try:
        # Search DB for local file
        mydb, mycursor = db_connection()
        query = "SELECT id, title, HTMLPath FROM site_meta WHERE id=%s"
        params = (page_id,)
        mycursor.execute(query, params)
        page = mycursor.fetchone()

        return {"page_id": page[0], "url": urllib.parse.urljoin(Config.PREVIEW_SERVER, page[2]), "title": page[1], "HTMLPath": page[2]}
    except Exception as e:
        raise


def get_asset_details(asset_id):
    """
    Get a specific asset from the database and serve its details.

    Args:
        asset_id (int): The ID of the asset to retrieve.

    Returns:
        asset_details: The asset details related to this page id.

    Raises:
        Exception: If there is an error during the retrieval or serving process.
    """

    try:
        # Search DB for local file
        mydb, mycursor = db_connection()
        query = "SELECT id, path, mimeType FROM site_assets WHERE id=%s"
        params = (asset_id,)
        mycursor.execute(query, params)
        asset = mycursor.fetchone()

        return {"asset_id": asset[0], "path": asset[1], "url": urllib.parse.urljoin(Config.PREVIEW_SERVER, asset[1], ), "mime_type": asset[2]}
    except Exception as e:
        raise


def get_screenshot(pageId):
    """
    Get the screenshot of a specific page.

    Args:
        pageId (int): The ID of the page for which to retrieve the screenshot.

    Returns:
        send_from_directory: A Flask function to send the screenshot file from the directory.

    Raises:
        Exception: If there is an error during the retrieval or serving process.
    """
    try:
        # Search DB for local file
        mydb, mycursor = db_connection()
        mycursor.execute("SELECT screenshotPath FROM site_meta WHERE id=%s", (pageId,))
        screenshotPath = mycursor.fetchone()[0]

        # Check if screenshotPath is NULL, use a default image if so
        screenshotPath = os.path.join(Config.LEAFCMS_FOLDER, "leaf", "static", "images", "unavailable-image.jpg") if screenshotPath == "NULL" else os.path.join(Config.SCREENSHOTS_FOLDER, screenshotPath)

        folderPath = os.path.dirname(screenshotPath)
        filePath = os.path.basename(screenshotPath)
        return send_from_directory(folderPath, filePath)
    except Exception as e:
        raise


def duplicate_page(site_id, ogPageId, ogURL, newTitle, newURL):
    """
    Duplicate a page.

    Args:
        site_id (int): The ID of the site to which the new page will be added.
        ogPageId (int): The ID of the original page to be duplicated.
        ogURL (str): The original URL of the page to be duplicated.
        newTitle (str): The title for the duplicated page.
        newURL (str): The new URL for the duplicated page.

    Returns:
        jsonify: JSON response indicating the success of the duplication.
    """
    try:
        # Connect to DB
        mydb, mycursor = db_connection()

        # Get Folders that the user has access to
        user_access_folder = get_user_access_folder()

        # Check if newURL belongs to any of the auth folders
        if not any(newURL.startswith(folder) for folder in user_access_folder):
            return {"error": "Forbidden"}, 403

        # Parse ogURL and newURL
        ogURL = ogURL.lstrip("/")
        newURL = newURL.lstrip("/")

        # Set the new Full URL
        mycursor.execute("SELECT url, screenshotPath FROM site_meta WHERE id=%s", (ogPageId,))
        og_record = mycursor.fetchone()
        fullNewURL = og_record[0].replace(ogURL, newURL)

        # Get screenshot
        screenshotPath = og_record[1]

        # Duplicate the local HTML page with subfolder creation if needed
        source_file = os.path.join(Config.WEBSERVER_FOLDER, ogURL)
        destination_folder = os.path.dirname(os.path.join(Config.WEBSERVER_FOLDER, newURL))
        destination_file = os.path.join(destination_folder, os.path.basename(newURL))

        # Check if file already exists
        mycursor.execute("SELECT HTMLpath FROM site_meta WHERE HTMLpath=%s AND status = 200", (newURL,))
        if mycursor.fetchone():
            return {"message": "file already exists"}

        # Add the new page to the Database
        query = "INSERT INTO site_meta (site_id, url, status, title, mimeType, HTMLpath, screenshotPath, add_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        params = (site_id, fullNewURL, "200", newTitle, "text/html", newURL, screenshotPath, session["id"])
        mycursor.execute(query, params)
        mydb.commit()

        # Ensure the destination folder exists, creating it if necessary
        os.makedirs(destination_folder, exist_ok=True)
        shutil.copy2(source_file, destination_file)

        # Open the new page
        with open(destination_file) as inFile:
            data = inFile.read()
            soup = BeautifulSoup(data, "html5lib")

        # Find the title tag and change its content
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = newTitle

        # Find and clear the "keywords" meta tag
        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag:
            keywords_tag["content"] = ""

        # Find and clear the "description" meta tag
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag:
            description_tag["content"] = ""

        # Save the modified HTML content
        with open(destination_file, "w") as outFile:
            data = soup.prettify()
            outFile.write(data)

        # Return success message
        json_response = {"message": "success"}
        return json_response
    except Exception as e:
        raise
