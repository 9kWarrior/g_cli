import click
import matplotlib.pyplot as plt
from github_api import fetch_repo_data, fetch_commits, fetch_issues_stats
from database import save_repo, delete_repo, get_repo_info, save_issues_stats,fetch_issues_stats, get_issues_stats, init_db, get_commits, fetch_commits_from_github, save_commits, search_commits_db
from models import Commit
from typing import List
from datetime import datetime
import os
import shutil
import plotext as plot
@click.group()
def cli():
    init_db()


@cli.command()
@click.argument('repo_name')
def add(repo_name):
    try:
        repo = fetch_repo_data(repo_name)
        save_repo(repo)
        issues_stats = fetch_issues_stats(repo_name)
        save_issues_stats(repo_name, issues_stats)
        click.echo(f"Репозиторий {repo_name} сохранен!")
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)


@cli.command()
@click.argument('repo_name')
@click.argument('search_phrase')
def search(repo_name, search_phrase):
    commits = fetch_commits(repo_name)
    for commit in commits:
        if search_phrase.lower() in commit.commit.message.lower():
            click.echo(f"""
            SHA: {commit.sha}
            Автор: {commit.commit.author.name}
            Дата: {commit.commit.author.date}
            Сообщение: {commit.commit.message}
            URL: {commit.html_url}
            """)


@cli.command()
@click.argument('repo_name')
def remove(repo_name):
    try:
        delete_repo(repo_name)  # Функция из database.py
        click.echo(f"Репозиторий {repo_name} удалён")
    except Exception as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
@click.argument('repo_name')
def info(repo_name):
    repo = get_repo_info(repo_name)
    if not repo:
        click.echo(f"Репозиторий {repo_name} не найден в БД", err=True)
        return

    issues_stats = get_issues_stats(repo_name)
    click.echo(f"""
    Название: {repo['name']}
    URL: {repo['url']}
    Описание: {repo['description']}
    Звёзды: {repo['stars']}
    """)
    if issues_stats:
        click.echo("\nСтатистика по задачам:")
        click.echo("{:<20} {:<10} {:<10}".format("Метка", "Открыто", "Закрыто"))
        for stat in issues_stats:
            click.echo("{:<20} {:<10} {:<10}".format(
                stat.label, stat.open_count, stat.closed_count))
    else:
        click.echo("\nНет данных о задачах для этого репозитория")


@cli.command()
@click.argument('repo_name')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]),
              help="Начальная дата (формат: ГГГГ-ММ-ДД)")
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]),
              default=datetime.now().strftime("%Y-%m-%d"),
              help="Конечная дата (формат: ГГГГ-ММ-ДД)")
@click.option('--output-dir', default="output",
              help="Директория для сохранения графиков")
def commit_stats(repo_name: str, start_date: datetime, end_date: datetime, output_dir: str):
    commits = get_commits(repo_name, start_date, end_date)

    if not commits:
        click.echo(f"Для репозитория {repo_name} нет коммитов в указанный период")
        return

    # Группируем коммиты по дате
    commit_dates = [commit.date.date() for commit in commits]
    date_counts = {}

    for date in commit_dates:
        date_counts[date] = date_counts.get(date, 0) + 1

    # Сортируем даты
    sorted_dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in sorted_dates]

    # Строим график
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_dates, counts)
    plt.title(f"Частота коммитов для {repo_name}")
    plt.xlabel("Дата")
    plt.ylabel("Количество коммитов")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Сохраняем график в файл
    os.makedirs(output_dir, exist_ok=True)
    filename = f"commit_stats_{repo_name.replace('/', '_')}.png"
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path)
    plt.close()
    click.echo(f"График сохранен в : {output_path}")
    click.echo(f"График сохранен в файл: {filename}")
    #Вывод в терминале
    date_strings = [date.strftime("%Y-%m-%d") for date in sorted_dates]

    plot.bar(date_strings, counts)
    plot.title(f"Коммиты в {repo_name}")
    plot.xlabel("Дата")
    plot.ylabel("Количество")
    plot.theme('pro')  # Выбираем красивую тему

    plot.plotsize(300, 60)

    plot.show()


@cli.command()
@click.argument('repo_name')
@click.argument('search_term', nargs=-1)
def search_commits(repo_name: str, search_term: tuple):
    search_query = ' '.join(search_term)

    results = search_commits_db(repo_name, search_query)  # Убедитесь, что функция имеет такое имя

    if not results:
        click.echo(f"По фразе '{search_query}' ничего не найдено в репозитории {repo_name}")
        return

    click.echo(f"Найдено {len(results)} коммитов по фразе '{search_query}':\n")

    for commit in results:
        click.echo(f"Хеш: {commit.sha}")
        click.echo(f"Ссылка: {commit.url}")
        click.echo(f"Автор: {commit.author}")
        click.echo(f"Дата: {commit.date.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"Сообщение: {commit.message}\n{'-' * 50}")


@cli.command()
@click.argument('repo_name')
def fetch_commits(repo_name):
    try:
        # Проверяем, есть ли репозиторий в БД
        repo = get_repo_info(repo_name)
        if not repo:
            click.echo(f"Репозиторий {repo_name} не найден в БД. Сначала добавьте его командой add.", err=True)
            return

        click.echo(f"Загрузка коммитов для {repo_name}...")
        commits = fetch_commits_from_github(repo_name)
        save_commits(repo_name, commits)
        click.echo(f"Успешно сохранено {len(commits)} коммитов.")

    except Exception as e:
        click.echo(f"Ошибка при загрузке коммитов: {str(e)}", err=True)
if __name__ == '__main__':
    cli()