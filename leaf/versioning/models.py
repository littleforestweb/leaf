import datetime
import os

from leaf import Config
from leaf.pages.models import get_page_details


def get_versions(page_id):
    page_details = get_page_details(page_id)
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
