import datetime
import os

from leaf import Config
from leaf.pages.models import get_page_details, get_asset_details


def get_versions(file_type, file_id):
    """
    Retrieve the version history of a specific page.

    This function fetches the version history of a page identified by `file_id` from a Git repository.
    It constructs a list of versions with details about each commit affecting the specified page.

    Args:
        file_type (str): The type of the file ("page" or "asset").
        file_id (int): The ID of the page for which the version history is to be retrieved.

    Returns:
        list: A list of dictionaries, each containing information about a version of the page,
              including version number, whether it is the latest version, commit hash, commit message,
              author, and date.

    Each dictionary in the returned list contains the following keys:
        - version (int): The version number, calculated based on the total number of commits.
        - is_latest (bool): True if the version is the latest, False otherwise.
        - commit (str): The commit hash.
        - message (str): The commit message.
        - author (str): The name of the author of the commit.
        - date (str): The date and time when the commit was authored, formatted as 'YYYY/MM/DD HH:MM:SS'.
    """

    # Get File Path
    file_path = ""
    if file_type == "page":
        file_details = get_page_details(file_id)
        file_path = file_details["HTMLPath"]
    elif file_type == "asset":
        file_details = get_asset_details(file_id)
        file_path = file_details["path"]

    # Get Commits
    commits = list(Config.GIT_REPO.iter_commits(paths=os.path.join(Config.WEBSERVER_FOLDER, file_path)))
    total_commits = len(commits)
    versions = [{
        "version": total_commits - idx,
        "is_latest": True if idx == total_commits - 1 else False,
        "commit": commit.hexsha,
        "message": commit.message,
        "author_name": commit.author.name,
        "author_email": commit.author.email,
        "date": datetime.datetime.fromtimestamp(commit.authored_date).strftime('%Y/%m/%d %H:%M:%S')
    } for idx, commit in enumerate(commits)]

    return versions


def get_file_details(file_type, file_id):
    """
    Retrieve the file details for a given file type and file ID.

    This function determines the file details based on the type of the file (either "page" or "asset")
    and the file ID. It fetches the details of the file from the appropriate function and extracts
    the file path.

    Parameters:
        file_type (str): The type of the file ("page" or "asset").
        file_id (int): The ID of the file.

    Returns:
        dict: The details of the file.

    Raises:
        KeyError: If the file type is not "page" or "asset" or if the required file details are missing.
        ValueError: If the file_id is invalid.
    """

    # Get File Details
    file_path, file_mime_type = "", ""
    if file_type == "page":
        file_details = get_page_details(file_id)
        file_path = file_details["HTMLPath"]
        file_mime_type = "text/html"
    elif file_type == "asset":
        file_details = get_asset_details(file_id)
        file_path = file_details["path"]
        file_mime_type = file_details["mime_type"]

    return {"path": file_path, "mime_type": file_mime_type}
