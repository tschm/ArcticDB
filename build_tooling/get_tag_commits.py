"""Script to get git tags and their corresponding commits."""
import os
import re
import subprocess
from argparse import ArgumentParser


def get_git_tags():
    """Get a list of git tags in the repository.

    Returns:
        list: A list of git tags.
    """
    result = subprocess.run(["git", "tag", "--list"], capture_output=True, text=True)

    # Filter the tags using a regular expression
    pattern = r"^v[0-9]+\.[0-9]+\.[0-9]+$"
    tags = [tag for tag in result.stdout.splitlines() if re.match(pattern, tag)]
    # We are only interested in tags with version 3.0.0 or higher
    # Because there are strange bugs with the lower versions
    filtered_tags = [
        tag for tag in tags if int(tag.split(".")[0].replace("v", "")) >= 3
    ]
    return filtered_tags


def get_commit_from_tag(tag):
    """Get the commit hash corresponding to a git tag.

    Args:
        tag (str): The git tag.

    Returns:
        str: The commit hash.
    """
    result = subprocess.run(
        ["git", "rev-list", "-n", "1", tag], capture_output=True, text=True
    )
    return result.stdout.strip()


# Parse the command line arguments
parser = ArgumentParser(description="Get git tags and their corresponding commits.")
parser.add_argument(
    "--run_all_benchmarks",
    help="Should we get the tags and commits for all benchmarks, or just the current one",
    action="store_true",
)

args = parser.parse_args()

if args.run_all_benchmarks:
    tags = get_git_tags()
    commits = [get_commit_from_tag(tag) for tag in tags]
else:
    # Get the current git commit hash
    tags = ["HEAD"]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    )
    commits = [result.stdout.strip()]

short_commits = [commit[:8] for commit in commits]

print(
    "Git tags and their corresponding commits: " + str(list(zip(tags, short_commits)))
)

# Catch so this only runs in GitHub Actions
if "GITHUB_OUTPUT" in os.environ:
    # Write to GITHUB_OUTPUT
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        print(f"commits={str(short_commits)}", file=fh)
