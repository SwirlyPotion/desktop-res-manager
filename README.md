# Desktop Reservations Manager

A starter Python desktop application for reservations management built with **PyQt6** for GUI and **SQLAlchemy** for ORM, configured for a **MySQL** backend.

## Project layout

- `reservation_manager/` - Application package
  - `main.py` - PyQt6 app startup
  - `ui/main_window.py` - Main window scaffold
  - `config.py` - Environment-driven DB settings
  - `database.py` - SQLAlchemy engine/session/bootstrap
  - `models.py` - ORM entities for properties, rental units, reservations
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
   pip install -r requirements.txt
   ```

4. Copy environment variables and edit as needed:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Run application:

   ```powershell
   python -m reservation_manager
   ```

## Notes

- On startup, the app attempts to create tables in the configured MySQL database.
- Current UI is intentionally minimal and ready for iterative feature development (CRUD screens, availability checks, validation, etc.).
