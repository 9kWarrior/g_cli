import matplotlib.pyplot as plt
import sqlite3
DB_PATH = "/app/github_cli/github_repos.db"

def plot_commits(repo_name: str, start_date: str, end_date: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT date, COUNT(*) FROM commits 
    WHERE repo_name = ? AND date BETWEEN ? AND ?
    GROUP BY date
    """, (repo_name, start_date, end_date))

    dates, counts = zip(*cursor.fetchall())
    plt.bar(dates, counts)
    plt.savefig(f"{repo_name}_commits.png")


import matplotlib.pyplot as plt
from datetime import datetime


def plot_daily_commits(repo_name: str, start_date: str, end_date: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT date(commit_date), COUNT(*) 
    FROM commits 
    WHERE repo_name = ? AND commit_date BETWEEN ? AND ?
    GROUP BY date(commit_date)
    """, (repo_name, start_date, end_date))

    dates, counts = zip(*cursor.fetchall())
    plt.figure(figsize=(10, 5))
    plt.bar(dates, counts)
    plt.title(f"Коммиты в {repo_name}")
    plt.savefig(f"{repo_name}_commits.png")