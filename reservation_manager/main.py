"""Application entrypoint."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from reservation_manager.database import init_db
from reservation_manager.ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)

    try:
        init_db()
    except Exception as exc:  # pragma: no cover
        QMessageBox.warning(
            None,
            "Database Initialization",
            "Could not initialize database tables. "
            "Check your MySQL connection settings in .env.\n\n"
            f"Details: {exc}",
        )

    window = MainWindow()
    window.show()
    return app.exec()
