import os
import sqlite3
import requests
from models import Repository, IssueLabelStats, Commit
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = "/app/github_cli/github_repos.db"


# database.py
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repos (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        url TEXT,
        description TEXT,
        stars INTEGER
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issues_stats (
        id INTEGER PRIMARY KEY,
        repo_id INTEGER,
        label TEXT,
        open_count INTEGER,
        closed_count INTEGER,
        FOREIGN KEY(repo_id) REFERENCES repos(id),
        UNIQUE(repo_id, label)
    )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            sha TEXT PRIMARY KEY,
            repo_id INTEGER,
            url TEXT,
            author TEXT,
            date TEXT,
            message TEXT,
            FOREIGN KEY(repo_id) REFERENCES repos(id)
        )""")
    conn.commit()
    conn.close()


# def get_db_connection():
#     return sqlite3.connect('github_repos.db')


def get_repo_info(repo_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM repos WHERE name = ?", (repo_name,))
    repo_data = cursor.fetchone()
    conn.close()

    if not repo_data:
        return None

    return {
        "name": repo_data[1],
        "url": repo_data[2],
        "description": repo_data[3],
        "stars": repo_data[4]
    }


def save_repo(repo: Repository):
    print(f"Сохранение репозитория: {repo.name}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO repos (name, url, description, stars)
    VALUES (?, ?, ?, ?)
    """, (repo.name, repo.url, repo.description, repo.stars))
    conn.commit()
    conn.close()


def delete_repo(repo_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM repos WHERE name = ?", (repo_name,))
    repo_id = cursor.fetchone()
    if repo_id:
        cursor.execute("DELETE FROM issues_stats WHERE repo_id = ?", (repo_id[0],))
        cursor.execute("DELETE FROM repos WHERE name = ?", (repo_name,))
    conn.commit()
    conn.close()


def save_issues_stats(repo_name: str, stats: List[IssueLabelStats]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM repos WHERE name = ?", (repo_name,))
    repo_id = cursor.fetchone()
    if not repo_id:
        conn.close()
        raise ValueError(f"Репозиторий {repo_name} не найден в базе данных")
    cursor.execute("DELETE FROM issues_stats WHERE repo_id = ?", (repo_id[0],))
    for stat in stats:
        cursor.execute("""
        INSERT INTO issues_stats (repo_id, label, open_count, closed_count)
        VALUES (?, ?, ?, ?)
        """, (repo_id[0], stat.label, stat.open_count, stat.closed_count))

    conn.commit()
    conn.close()


def get_issues_stats(repo_name: str) -> List[IssueLabelStats]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM repos WHERE name = ?", (repo_name,))
    repo_id = cursor.fetchone()

    if not repo_id:
        conn.close()
        return []
    cursor.execute("""
    SELECT label, open_count, closed_count 
    FROM issues_stats 
    WHERE repo_id = ?
    ORDER BY (open_count + closed_count) DESC
    """, (repo_id[0],))
    stats = [
        IssueLabelStats(label=row[0], open_count=row[1], closed_count=row[2])
        for row in cursor.fetchall()
    ]
    conn.close()
    return stats


def save_commits(repo_name: str, commits: List[Commit]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем ID репозитория
    cursor.execute("SELECT id FROM repos WHERE name = ?", (repo_name,))
    repo_id = cursor.fetchone()

    if not repo_id:
        conn.close()
        raise ValueError(f"Репозиторий {repo_name} не найден в базе данных")

    for commit in commits:
        cursor.execute("""
        INSERT OR REPLACE INTO commits 
        (sha, repo_id, url, author, date, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            commit.sha,
            repo_id[0],
            commit.url,
            commit.author,
            commit.date.isoformat(),
            commit.message
        ))

    conn.commit()
    conn.close()


def get_commits(repo_name: str,
                start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None) -> List[Commit]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM repos WHERE name = ?", (repo_name,))
    repo_id = cursor.fetchone()

    if not repo_id:
        conn.close()
        return []

    # Формируем запрос с учетом фильтрации по дате
    query = "SELECT sha, url, author, date, message FROM commits WHERE repo_id = ?"
    params = [repo_id[0]]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat())

    query += " ORDER BY date DESC"

    cursor.execute(query, tuple(params))

    commits = []
    for row in cursor.fetchall():
        commits.append(Commit(
            sha=row[0],
            url=row[1],
            author=row[2],
            date=datetime.fromisoformat(row[3]),
            message=row[4]
        ))

    conn.close()
    return commits


def search_commits_db(repo_name: str, search_term: str) -> List[Commit]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM repos WHERE name = ?", (repo_name,))
    repo_id = cursor.fetchone()

    if not repo_id:
        conn.close()
        return []

    cursor.execute("""
    SELECT sha, url, author, date, message 
    FROM commits 
    WHERE repo_id = ? AND message LIKE ?
    ORDER BY date DESC
    """, (repo_id[0], f"%{search_term}%"))

    results = []
    for row in cursor.fetchall():
        results.append(Commit(
            sha=row[0],
            url=row[1],
            author=row[2],
            date=datetime.fromisoformat(row[3]),
            message=row[4]
        ))

    conn.close()
    return results


def fetch_commits_from_github(repo_name: str) -> List[Commit]:
    """Получает коммиты из GitHub API"""
    url = f"https://api.github.com/repos/{repo_name}/commits"
    headers = {}

    # Добавляем токен, если он есть в переменных окружения
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    commits_data = response.json()
    commits = []

    for commit_data in commits_data:
        commit_info = commit_data['commit']
        author = commit_info['author']['name'] or commit_info['author']['email']

        commits.append(Commit(
            sha=commit_data['sha'],
            url=commit_data['html_url'],
            author=author,
            date=datetime.strptime(commit_info['author']['date'], '%Y-%m-%dT%H:%M:%SZ'),
            message=commit_info['message']
        ))

    return commits


def fetch_issues_stats(repo_name: str) -> List[IssueLabelStats]:
    url = f"https://api.github.com/repos/{repo_name}/issues?state=all"
    headers = {}

    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    issues_data = response.json()
    stats = {}

    for issue in issues_data:
        for label in issue['labels']:
            label_name = label['name']
            if label_name not in stats:
                stats[label_name] = {'open': 0, 'closed': 0}

            stats[label_name]['open' if issue['state'] == 'open' else 'closed'] += 1

    return [
        IssueLabelStats(label=label, open_count=counts['open'], closed_count=counts['closed'])
        for label, counts in stats.items()
    ]