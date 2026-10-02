# Validation results

- Five automated tests passed on Python 3.12 using an isolated SQLite test database.
- Covered registration, scrypt password hashes, duplicate emails, invalid passwords, login/logout, session revocation, CSRF rejection, invalid inputs, rate limits, protected routes, private per-account watchlists, repeated adds, watched/unwatched updates, removal, and persistence after sign-out/sign-in.
- The application defaults to MySQL through PyMySQL. MySQL schema and Docker Compose are included.
- Live MySQL/MariaDB testing could not be completed in the build environment because the database server could not create a UNIX socket. Run the provided tests against a disposable MySQL database before submission.
- Browser visual checks could not be completed because browser downloads failed. Templates were rendered in functional tests; responsive CSS is included.
- No public deployment has been created. A hosting connection is required.
