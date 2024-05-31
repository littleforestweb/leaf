import datetime
import os

from leaf import Config
from leaf.pages.models import get_page_details


def get_versions(file_id):
    """
    Retrieve the version history of a specific page.

    This function fetches the version history of a page identified by `file_id` from a Git repository.
    It constructs a list of versions with details about each commit affecting the specified page.

    Args:
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
    
    page_details = get_page_details(file_id)
    page_HTMLPath = page_details["HTMLPath"]
    commits = list(Config.GIT_REPO.iter_commits(paths=os.path.join(Config.WEBSERVER_FOLDER, page_HTMLPath)))
    total_commits = len(commits)
    versions = [{
        "version": total_commits - idx,
        "is_latest": True if idx == total_commits - 1 else False,
        "commit": commit.hexsha,
        "message": commit.message,
        "author": commit.author.name,
        "date": datetime.datetime.fromtimestamp(commit.authored_date).strftime('%Y/%m/%d %H:%M:%S')
    } for idx, commit in enumerate(commits)]

    return versions
