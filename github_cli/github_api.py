import os
from github import Github
from models import Repository
from github import GithubException


# def get_repo_info(repo_name):
#     g = Github(os.getenv("GITHUB_TOKEN"))
#     repo = g.get_repo(repo_name)
#     return {
#         "name": repo.full_name,
#         "url": repo.html_url,
#         "stars": repo.stargazers_count
#     }


def fetch_repo_data(repo_name: str) -> Repository:
    try:
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(repo_name)
        return Repository(
            name=repo.full_name,
            url=repo.html_url,
            description=repo.description,
            stars=repo.stargazers_count
        )
    except GithubException as e:
        raise Exception(f"GitHub API error: {e.data.get('message', 'Unknown error')}")


def fetch_commits(repo_name: str, search_phrase: str = None):
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    commits = repo.get_commits()
    return commits


def fetch_issues_stats(repo_name: str):
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    issues = repo.get_issues(state='all')
    stats = {}
    for issue in issues:
        for label in issue.labels:
            stats[label.name] = stats.get(label.name, {'open': 0, 'closed': 0})
            stats[label.name]['open' if issue.state == 'open' else 'closed'] += 1
    return stats
