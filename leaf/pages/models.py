import os
import shutil

from bs4 import BeautifulSoup
from flask import send_from_directory, session

from leaf.config import Config
from leaf.decorators import db_connection


def get_all_pages_data():
    """
    Get all pages data from the database.

    Returns:
        dict: Dictionary containing all pages data.
    """
    try:
        mydb, mycursor = db_connection()

        # Get all pages
        mycursor.execute("SELECT url, status, title FROM site_meta")
        results = mycursor.fetchall()
        pages_list = [{"url": page[0], "status": page[1], "title": page[2]} for page in results]

        # Create json
        json_response = {"pages": pages_list}
        return json_response
    except Exception as e:
        raise


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


def duplicate_page(site_id, ogPageId, ogURL, newTitle, newUrl):
    """
    Duplicate a page.

    Args:
        site_id (int): The ID of the site to which the new page will be added.
        ogPageId (int): The ID of the original page to be duplicated.
        ogURL (str): The original URL of the page to be duplicated.
        newTitle (str): The title for the duplicated page.
        newUrl (str): The new URL for the duplicated page.

    Returns:
        jsonify: JSON response indicating the success of the duplication.
    """
    try:
        # Connect to DB
        mydb, mycursor = db_connection()

        # Get the full original URL from ogPageId
        mycursor.execute("SELECT url FROM site_meta WHERE id=%s", (ogPageId,))
        fullOgURL = mycursor.fetchone()[0]
        fullOgURL = os.path.splitext(fullOgURL)[0] + ".html" if "." in fullOgURL else fullOgURL + ".html"

        # Set the new Full URL
        fullNewURL = fullOgURL.replace(ogURL, newUrl)

        # Add the new page to the Database
        url, status, mimeType, screenshotPath, userId = "", "200", "text/html", "NULL", session["id"]
        query = "INSERT INTO site_meta (site_id, url, status, title, mimeType, HTMLpath, screenshotPath, add_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        params = (site_id, fullNewURL, status, newTitle, mimeType, newUrl.lstrip("/") if newUrl.startswith("/") else newUrl, screenshotPath, session["id"])
        mycursor.execute(query, params)
        mydb.commit()

        # Duplicate the local HTML page with subfolder creation if needed
        source_file = os.path.join(Config.WEBSERVER_FOLDER, ogURL)
        destination_folder = os.path.join(Config.WEBSERVER_FOLDER, newUrl)

        # Ensure the destination folder exists, creating it if necessary
        os.makedirs(os.path.dirname(destination_folder), exist_ok=True)

        destination_file = os.path.join(os.path.dirname(destination_folder), os.path.basename(source_file))
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
