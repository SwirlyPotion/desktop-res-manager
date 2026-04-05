"""Application entrypoint."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)

    login_window = LoginWindow()
    main_window: MainWindow | None = None

    def _open_main_window(role_value: str) -> None:
        nonlocal main_window
        login_window.close()
        main_window = MainWindow(role_value=role_value)
        main_window.show()

    login_window.authenticated.connect(_open_main_window)
    login_window.show()
    return app.exec()
