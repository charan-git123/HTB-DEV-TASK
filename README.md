# Netflix-Inspired Movie Discovery and Watchlist

An independent educational recreation built with Flask, MySQL, HTML, CSS, and JavaScript. It is not affiliated with Netflix and does not stream films or series.

**Live website:** [htb-dev-task-production.up.railway.app](https://htb-dev-task-production.up.railway.app)

**Health check:** [https://htb-dev-task-production.up.railway.app/health](https://htb-dev-task-production.up.railway.app/health)

**GitHub repository:** [charan-git123/HTB-DEV-TASK](https://github.com/charan-git123/HTB-DEV-TASK)

## Project brief

| Requirement | Implementation |
| --- | --- |
| Landing, sign-up, and log-in pages | `/`, `/signup`, and `/login` |
| Real account creation and authentication | Flask routes backed by SQLAlchemy and MySQL |
| Secure password storage | Werkzeug scrypt password hashes; plaintext passwords are not stored |
| Persistent data | MySQL stores users, login sessions, and watchlists |
| Additional working feature | Private per-user watchlist: add, remove, and mark titles watched or unwatched |
| Public deployment | Railway web service and MySQL service; `/health` checks database connectivity |

## Features

- Responsive Netflix-inspired home, registration, login, and browse pages.
- Case-normalized unique email addresses and server-side validation.
- Hashed passwords and persistent, revocable login sessions.
- Personal watchlists with add, remove, and watched/unwatched actions.
- CSRF protection, parameterized database queries, security headers, and database-backed sign-in rate limits.
- Locally styled poster artwork; no promotional image files are required to run the public app.

## Try the live app

1. Open the [home page](https://htb-dev-task-production.up.railway.app/).
2. Create an account from **Get Started** or visit `/signup`.
3. Sign in at `/login`, browse the titles, and add one to **My List**.
4. Mark it watched, remove it, sign out, then sign back in to verify your account and list persist.
5. Create a second account to verify that each account has a private list.

The deployment uses shared hosting capacity and may become unavailable if the hosting allowance expires. The home page, sign-up page, log-in page, and database health check were verified at the time of this update.

## Run locally with Docker

Requirements: Docker Desktop with Docker Compose.

1. Copy the environment template:

   ```powershell
   Copy-Item .env.example .env
   ```

   In `.env`, replace the `SECRET_KEY`, `MYSQL_PASSWORD`, and `MYSQL_ROOT_PASSWORD` placeholders with fresh values. Generate a secret key using:

   ```powershell
   py -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Start the app and its MySQL database:

   ```powershell
   docker compose up --build
   ```

3. Visit [http://localhost:8000](http://localhost:8000). Stop the containers with `Ctrl+C`.

The database is stored in the `mysql_data` volume. `docker compose down` preserves it; `docker compose down -v` deletes it.

## Run locally with an installed MySQL server

Requirements: Python 3.12 or newer and a running MySQL 8.x server.

1. Create a database and a dedicated application user in MySQL Workbench:

   ```sql
   CREATE DATABASE IF NOT EXISTS netflix_clone
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   CREATE USER IF NOT EXISTS 'netflix_app'@'localhost'
     IDENTIFIED BY 'choose-a-unique-password';
   GRANT ALL PRIVILEGES ON netflix_clone.* TO 'netflix_app'@'localhost';
   ```

2. Create the Python environment and install dependencies:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

3. In `.env`, set a fresh `SECRET_KEY` and set `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` to match the database user you created.
4. Initialize the schema and run Flask:

   ```powershell
   .\.venv\Scripts\python.exe -m flask --app wsgi init-db
   .\.venv\Scripts\python.exe -m flask --app wsgi run --port 5000
   ```

5. Visit [http://127.0.0.1:5000](http://127.0.0.1:5000). Stop the server with `Ctrl+C`.

The `.env` file is ignored by Git. Never commit real credentials.

## Deployment

The live app runs as a Railway web service alongside a separate Railway MySQL service. The app connects to MySQL over Railway's private network using service-reference variables; the database does not need public access.

- The web-service start command runs `sh start.sh`.
- `start.sh` creates any missing tables and starts Gunicorn using `wsgi:app` on Railway's `PORT`.
- `/health` returns `{"status":"ok"}` when the database is reachable.
- Railway variables and credentials are configured in the hosting dashboard, not in this repository.
- Hosting allowances and pricing can change; review the provider's dashboard for current usage and billing.

For another host, provide a reachable MySQL server and set `SECRET_KEY`, `APP_ENV=production`, `SECURE_COOKIES=true`, and the `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` environment variables. The application also accepts `DATABASE_URL` instead of individual MySQL settings. Do not use `localhost` or `127.0.0.1` for a database running in a different hosting service.

## Tests and continuous integration

Run the automated tests locally:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The default tests use isolated temporary SQLite databases; they do not need MySQL and do not change live accounts or watchlists. GitHub Actions runs the same tests on pushes and pull requests to `main`.

To test against MySQL, set `TEST_DATABASE_URL` to a **disposable, empty test database**. The test fixtures recreate its tables; never point it at the live application database.

## Project layout

```text
app.py                    Flask app factory, models, routes, and CLI
catalog.py                Sample movie and series catalog
wsgi.py                   WSGI entry point (wsgi:app)
templates/                Home, auth, browse, and error pages
static/                   Styles, JavaScript, and CSS artwork
tests/test_app.py         Authentication, session, security, and watchlist tests
schema.sql                MySQL schema
requirements.txt          Runtime dependencies
requirements-dev.txt      Test dependencies
Dockerfile                Container image for the web service
compose.yaml              Local Flask and MySQL stack
start.sh                  Schema initialization and Gunicorn startup
railway.json              Railway health check and deployment settings
.env.example              Local-development environment template
VALIDATION.md             Current test and deployment verification notes
```
