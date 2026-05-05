# Run This Project (Windows)

This project is a Django application that uses MySQL by default.

## 1) Open a terminal in the project root

Project root example:
D:\Development\Web\2026\Quiz

## 2) Create and activate virtual environment

If not created yet:
py -m venv .venv

Activate it:
.\.venv\Scripts\Activate.ps1

If PowerShell blocks activation, run once in this terminal:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

## 3) Install Python dependencies

pip install -r requirements\development.txt

## 4) Configure environment variables

Create a .env file in the project root and add values like below:

DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=django-insecure-change-this
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

FF_AI_EXPLANATIONS=True
FF_CONTESTS=False
FF_LEADERBOARD=True
FF_API=False
FF_SOCIAL_LOGIN=False

AI_ACTIVE_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3-coder:480b-cloud

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-pro
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

## 5) Configure MySQL access

This project reads MySQL credentials from my.cnf.
Current file expects:
- database: quizdb
- user: root
- password: (empty)
- host: 127.0.0.1
- port: 3306

Make sure your MySQL service is running and the database exists.

Example (inside MySQL shell):
CREATE DATABASE quizdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

## 6) Apply migrations

python manage.py migrate

## 7) (Optional) Create admin user

python manage.py createsuperuser

## 8) Run the development server

python manage.py runserver

Open in browser:
http://127.0.0.1:8000/

Admin:
http://127.0.0.1:8000/admin/

## 9) (Optional) Run Tailwind CSS watcher

In a second terminal (project root), with virtual environment active:
python manage.py tailwind start

If that command fails, install frontend packages first:
python manage.py tailwind install

## Quick start commands

.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
python manage.py migrate
python manage.py runserver

## Troubleshooting

- Error loading MySQL client: reinstall dependencies in active venv, and ensure MySQL/MariaDB client libraries are installed.
- Database connection refused: confirm MySQL is running on 127.0.0.1:3306 and my.cnf values are correct.
- If MySQL is unavailable, you can temporarily switch to SQLite by uncommenting the SQLite block in config/settings/development.py.
