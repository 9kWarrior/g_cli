1. Клонируйте репозиторий:
  git clone https://github.com/yourusername/yourproject.git
  cd yourproject
2. Создайте файл .env с вашим GitHub токеном:
  GITHUB_TOKEN=your_personal_access_token_here
3. Соберите и запустите контейнер
  docker-compose up --build

Использование

1. Добавление репозитория
  docker-compose run gh-client add <repo_name>
Пример:
  docker-compose run gh-client add pallets/flask
2. Удаление репозитория
  docker-compose run gh-client remove <repo_name>
3. Получение информации о репозитории
  docker-compose run gh-client info <repo_name>
4. Загрузка коммитов из GitHub
  docker-compose run gh-client fetch-commits <repo_name>
5. Поиск коммитов
  docker-compose run gh-client search-commits <repo_name> [search_term] [options]
Опции:
--start-date: Начальная дата (формат: ГГГГ-ММ-ДД)
--end-date: Конечная дата (по умолчанию: сегодня)
6. Статистика коммитов (график)
  docker-compose run gh-client commit-stats <repo_name> [--start-date=<date>] [--end-date=<date>]

Для работы с GitHub API требуется личный токен доступа
Создайте токен на странице https://github.com/settings/tokens
  
