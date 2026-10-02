# Validation

Verified for the public submission on 2026-10-02:

- `python -m pytest -q`: **6 passed**.
- The WSGI entry point imports and exports the Flask application as `wsgi:app`.
- The deployed home page, `/signup`, and `/login` returned HTTP 200.
- The deployed `/health` endpoint returned `{"status":"ok"}`, confirming database connectivity.
- The public app uses a separate Railway MySQL service and a private service-to-service connection.

The automated suite uses isolated temporary SQLite databases by default. It covers account registration, scrypt password hashes, duplicate accounts, login/logout and session revocation, CSRF validation, input validation, authentication rate limiting, protected routes, and private watchlist create/read/update/delete behavior.

GitHub Actions runs the tests on pushes and pull requests targeting `main`. The live website is linked from the [README](./README.md).
