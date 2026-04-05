# Desktop Reservations Manager

A starter Python desktop application for reservations management built with **PyQt6** for GUI and **SQLAlchemy** for ORM, configured for a **MySQL** backend.

## Project layout

- `app/` - Application package root
   - `bootstrap.py` - App startup orchestration
   - `__main__.py` - Package module entrypoint
   - `db/config.py` - Environment-driven DB settings
   - `db/database.py` - SQLAlchemy engine/session/bootstrap
   - `db/models.py` - ORM entities for properties, rental units, reservations, users
   - `ui/login_window.py` - Initial login/connect window
   - `ui/registration_request_window.py` - Registration request dialog
   - `ui/main_window.py` - Main application window
- `pyproject.toml` - Packaging metadata and console script entrypoint
- `main.py` - Root compatibility launcher
- `.env.example` - Example environment variables for MySQL
- `requirements.txt` - Python dependencies

## Setup

1. Create virtual environment (already done in this repository):

   ```powershell
   py -3 -m venv .venv
   ```

2. Activate virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -e .
   ```

4. Copy environment variables and edit as needed:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Run application:

   ```powershell
   python -m app
   ```

   Or run the installed console command:

   ```powershell
   desktop-res-manager
   ```

   Compatibility launcher is still available:

   ```powershell
   python main.py
   ```

## Notes

- Users log in from an initial connect window before reaching the main app.
- The login flow supports secure local credential storage via OS keyring.
- Current UI is intentionally minimal and ready for iterative feature development (CRUD screens, availability checks, validation, etc.).
