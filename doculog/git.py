"""
Utility code for parsing git history.
"""
import re
import subprocess
from typing import List, Optional, Tuple

leading_4_spaces = re.compile("^    ")


def get_commits(
    since_date: Optional[str] = None, until_date: Optional[str] = None
) -> List:
    """
    Get commit information (title, author, files changes etc.)

    Optionally get the commits between given dates.
    Retrieve the entire git history if only 0 or 1 dates are given.

    Parameters
    ----------
    since_date : str, default = None
        If provided (and `until_date` is provided), the beginning of the date range
        in which to retrieve commits
    until_date : str, default = None
        If provided (and `since_date` is provided), the end of the date range
        in which to retrieve commits

    Returns
    -------
    list of dicts
        List of commit information (in the date range if given),
        earliest commits first.
        Commit information is a dict containing "title", "date", "files" and more.
    """
    if since_date and until_date:
        command = ["git", "log", "--stat", "--since", since_date, "--until", until_date]
    else:
        command = ["git", "log", "--stat"]

    try:
        lines = (
            subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            .decode("utf-8")
            .split("\n")
        )
    except subprocess.CalledProcessError:
        return []

    commits = []
    current_commit = {}

    def save_current_commit():
        title = current_commit["message"][0]
        message = current_commit["message"][1:]
        changed_files = []

        if message and message[0] == "":
            del message[0]

        current_commit["title"] = title
        current_commit["message"] = "\n".join(message)
        current_commit["files"] = [
            _m.split("|")[0].strip() for _m in message if "|" in _m
        ]
        commits.append(current_commit)

    for line in lines:
        if not line.startswith(" "):
            if line.startswith("commit "):
                if current_commit:
                    save_current_commit()
                    current_commit = {}
                current_commit["hash"] = line.split("commit ")[1]
            else:
                try:
                    key, value = line.split(":", 1)
                    current_commit[key.lower()] = value.strip()
                except ValueError:
                    pass
        else:
            current_commit.setdefault("message", []).append(
                leading_4_spaces.sub("", line)
            )

    if current_commit:
        save_current_commit()

    commits.reverse()  # earliest commit first
    return commits


def _get_tag_date(tag_name: str) -> str:
    return (
        subprocess.check_output(
            ["git", "log", "-1", "--format=%ai", tag_name],
            stderr=subprocess.STDOUT,
            shell=True,
        )
        .decode("utf-8")
        .split(" ")[0]
    )


def list_tags() -> List[Tuple[str, str]]:
    """
    List tags of git project.

    Returns
    -------
    list of (str, str)
        List of (tag title, tag date) present in the git project
    """
    try:
        tags = (
            subprocess.check_output(
                ["git", "tag", "-n"], stderr=subprocess.STDOUT, shell=True
            )
            .decode("utf-8")
            .split("\n")
        )
        tags.reverse()
    except subprocess.CalledProcessError:
        return []

    tags = [t.split(" ")[0] for t in tags]
    tags = [(t, _get_tag_date(t)) for t in tags if t]
    return tags


def has_git() -> bool:
    try:
        subprocess.check_output(["git", "log"], stderr=subprocess.STDOUT, shell=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    else:
        return True
