# Netflix-inspired website — Flask + MySQL

A full-stack student project built with **HTML, CSS, vanilla JavaScript, Python/Flask, and MySQL**. No React, Node backend, or localStorage account database.

## Included features

- Responsive landing page, sign-up page, and sign-in page.
- Real account creation; case-normalized unique emails; server-side validation.
- Passwords salted and hashed with Werkzeug scrypt.
- Signed, HttpOnly, SameSite cookies with opaque session tokens. Session hashes are stored in the database and revoked on sign-out; sessions expire after seven days.
- Per-user My List: add/read/remove titles and mark watched/unwatched.
- CSRF protection, parameterized queries via SQLAlchemy, security headers, and a database-backed limit of ten authentication attempts per email per 15 minutes.
- MySQL persistence, SQL schema, Docker Compose, Gunicorn production entry point, and Railway configuration.
- Educational recreation disclosure. No streaming, Netflix login integration, payments, email verification, or password reset.

## 1. Run in VS Code on Windows (without Docker)

Install **Python 3.12** and **MySQL 8.x**, including MySQL Workbench. Start the MySQL service. Extract this ZIP, then open the `netflix-flask-mysql` folder in VS Code.

In the VS Code terminal (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated key into `SECRET_KEY` in `.env`. These commands call the virtual environment directly, so PowerShell activation policy does not matter. If you have another compatible Python installed, use its command instead of `py -3.12`.

In **MySQL Workbench**, connect as an administrator and execute the following, replacing the sample database password with a unique password:

```sql
CREATE DATABASE IF NOT EXISTS netflix_clone
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'netflix_app'@'localhost'
  IDENTIFIED BY 'REPLACE_WITH_A_DATABASE_PASSWORD';
GRANT ALL PRIVILEGES ON netflix_clone.* TO 'netflix_app'@'localhost';
```

Keep `CREATE DATABASE`, `CHARACTER SET`, and `COLLATE` in the **same statement**, with the semicolon only at the end. If the user already exists, use `ALTER USER ... IDENTIFIED BY ...` to change its password.

Update `.env`:

```dotenv
SECRET_KEY=your-generated-random-key
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=netflix_clone
MYSQL_USER=netflix_app
MYSQL_PASSWORD=your-database-password
APP_ENV=development
SECURE_COOKIES=false
```

Then create the tables and start Flask:

```powershell
.\.venv\Scripts\python.exe -m flask --app wsgi init-db
.\.venv\Scripts\python.exe -m flask --app wsgi run --port 5000
```

Open **http://127.0.0.1:5000**. Do not open the HTML files directly or run VS Code Live Server; Flask renders the templates and handles authentication. Stop with Ctrl+C.

`init-db` creates missing tables without deleting existing data. Alternatively, run `schema.sql` in Workbench to create them. The catalog itself is static sample data; accounts, sessions, and user watchlists are in MySQL.

## 2. macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
# Configure MySQL and .env as above.
flask --app wsgi init-db
flask --app wsgi run --port 5000
```

## 3. Optional Docker setup

Install Docker Desktop, copy `.env.example` to `.env`, set a generated `SECRET_KEY`, set `MYSQL_PASSWORD`, and add a separate `MYSQL_ROOT_PASSWORD` value. Run:

```bash
docker compose up --build
```

Open **http://localhost:8000**. The database is not exposed on a host port, and data persists in the `mysql_data` volume. `docker compose down` preserves accounts; `docker compose down -v` destroys the database. Local Compose uses HTTP cookies intentionally. Use the separate production settings below for HTTPS hosting.

## 4. Public deployment with Railway

**The source package is ready for deployment; it is not itself a live website.** Public deployment requires your hosting account, a MySQL service, and a generated domain. Hosting may incur charges; review your provider's displayed plan before provisioning.

1. Create a GitHub repository and push the contents of this folder. Do not upload `.env`, `.venv`, test databases, or credentials.
2. In Railway, create a project and add a **MySQL** database service. Keep its persistent volume attached.
3. Add an application service from your GitHub repository. The included Dockerfile installs Python dependencies, and `start.sh` initializes the schema before launching Gunicorn.
4. In the **application service** variables, set:

```dotenv
SECRET_KEY=<a-new-random-key-of-at-least-32-characters>
APP_ENV=production
SECURE_COOKIES=true
MYSQL_HOST=${{MySQL.MYSQLHOST}}
MYSQL_PORT=${{MySQL.MYSQLPORT}}
MYSQL_USER=${{MySQL.MYSQLUSER}}
MYSQL_PASSWORD=${{MySQL.MYSQLPASSWORD}}
MYSQL_DATABASE=${{MySQL.MYSQLDATABASE}}
```

`MySQL` must match the database service's actual name. Use Railway's reference-variable picker if your service has a different name. Do not type literal sample credentials. Alternatively set `DATABASE_URL` to your real MySQL connection URL; the application accepts `mysql://` and `mysql+pymysql://`. Separate variables avoid URL-encoding issues with special characters in passwords.

5. Deploy. `/health` checks database connectivity and schema readiness. Once healthy, generate a public domain in the application service's Networking settings. The process uses Railway's `PORT` automatically.
6. Open that HTTPS URL in a private browser window. Create an account, add a title, sign out, sign back in, and confirm the title remains. Test with a second account to confirm isolation. Submit this URL with the source repository.

Official deployment documentation:
- https://docs.railway.com/guides/flask
- https://docs.railway.com/databases/mysql
- https://flask.palletsprojects.com/en/stable/deploying/

GitHub Pages cannot run Flask or MySQL. Do not deploy just the HTML there and expect authentication to work.

## Deploy on Render

For a Render **Web Service**, use the repository root as the root directory, `pip install -r requirements.txt` as the build command, and `sh start.sh` as the start command. Do not use `gunicorn app:app`: `app.py` defines the `create_app()` factory and does not export an `app` object. The WSGI application is exported by `wsgi.py`; `start.sh` initializes the schema and starts Gunicorn with `wsgi:app` on Render's `PORT`.

Set `SECRET_KEY` to a newly generated random value of at least 32 characters, `APP_ENV=production`, and `SECURE_COOKIES=true` in the Render service's environment. Configure `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` to reach your MySQL server from Render. Keep credentials in Render's environment settings, not in GitHub or `.env` committed to the repository. Redeploy after changing the start command and environment.

## Assignment demonstration

1. Visit `/`, `/signup`, and `/login` to show the required three pages.
2. Register a new account; show the MySQL `users` row containing `scrypt:` in `password_hash` (do not share real hashes publicly).
3. Sign out, submit a wrong password, then sign in correctly.
4. Add two titles; open `/my-list`; mark one as watched; remove another.
5. Restart the app and sign in again to show persistence.
6. Create another account to demonstrate each watchlist is private.
7. Show the public deployment URL from a separate browser/device.

## Project structure

```text
app.py                 Flask routes, SQLAlchemy models, authentication
catalog.py             Sample title catalog
wsgi.py                Application factory entry point
schema.sql             MySQL schema
requirements.txt       Runtime dependencies
requirements-dev.txt   Test dependencies
.env.example           Environment variable template
static/styles.css      Responsive visual design
static/app.js          Password visibility and form interactions
static/images/         Local movie artwork
templates/            Jinja HTML pages
tests/test_app.py      Authentication, security and CRUD tests
Dockerfile             Python production container
compose.yaml           Local app + MySQL 8.4 with a persistent volume
start.sh               Database setup + Gunicorn
railway.json           Deployment health check configuration
ASSETS.md              Image sources and rights notes
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Default tests use temporary SQLite databases for portable automated checks. The shipped app uses MySQL. To exercise the same tests on a MySQL-compatible server, create an **empty, disposable test database**, set `TEST_DATABASE_URL` to its `mysql+pymysql://...` URL, and run pytest. **Tests recreate tables in that database. Never use your application database for this setting.**

## Troubleshooting

- `ModuleNotFoundError`: use the `.venv` Python commands shown above and install requirements into that same environment.
- `Access denied`: confirm the MySQL user, password, host, and database grants.
- `Can't connect to MySQL server`: start MySQL and check its host/port.
- `Table doesn't exist`: run `flask --app wsgi init-db`.
- Secret key error: replace the placeholder in `.env` with a generated key.
- Sign-in loops on localhost: use `APP_ENV=development` and `SECURE_COOKIES=false`; secure cookies require HTTPS.
- Expired form error: refresh the page and resubmit. CSRF protection is intentional.
- Too many attempts: wait 15 minutes before retrying that email.
- Database changes: `create_all()` creates missing tables; it does not migrate existing columns. Introduce versioned migrations for future schema changes.

This is an assignment-scale app. Email verification, account recovery, distributed IP-based abuse controls, database backups, and operational monitoring should be added before a real commercial launch.
