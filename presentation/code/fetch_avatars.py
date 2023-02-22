"""
Fetch GitHub avatars of Fatiando authors
"""
import re
import requests
from pathlib import Path

BRANCH = "main"
PROJECTS = ["harmonica", "verde", "boule", "pooch", "ensaio"]


def _parse_authors_file(package, branch):
    """
    Returns a dict with information about the author of the package

    Parameters
    ----------
    package : str
        Name of the Fatiando a Terra package.

    Returns
    -------
    authors : list
        List of tuples. Each tuple contains the ``full_name`` and the
        ``github_handle`` of each user.
    """
    response = requests.get(
        f"https://raw.githubusercontent.com/fatiando/{package}/{branch}/AUTHORS.md",
    )
    response.raise_for_status()
    markdown = response.text
    authors = re.findall(r"\[(.+?)\]\((?:https://github.com/)(.+?)/?\)", markdown)
    return authors


if __name__ == "__main__":

    # Get path of dir for this script
    filepath = Path(__file__).parent

    # Get authors of all Fatiando projects
    authors = []
    for project in PROJECTS:
        authors.extend(_parse_authors_file(project, BRANCH))

    # Get unique authors
    authors = list(set(authors))

    # Create directory for storing the avatar images
    avatars_dir = filepath / ".." / "figs" / "avatars"
    avatars_dir.mkdir()

    # Download the avatar images
    for _, handle in authors:
        with open(avatars_dir / f"{handle}.jpg", "wb") as outfile:
            response = requests.get(f"https://github.com/{handle}.png")
            if response.status_code != 200:
                print(f"Couldn't download avatar for {handle}")
                continue
            outfile.write(response.content)
