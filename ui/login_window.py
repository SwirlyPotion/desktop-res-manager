"""Login window shown before entering the main app."""

from __future__ import annotations

import keyring
from keyring.errors import KeyringError, PasswordDeleteError
from PyQt6.QtCore import QSettings, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal, init_db
from models import User
from ui.registration_request_window import RegistrationRequestDialog

APP_ORG = "DesktopReservationsManager"
APP_NAME = "DesktopReservationsManager"
KEYRING_SERVICE = "desktop-res-manager"
SPINNER_FRAMES = ["|", "/", "-", "\\"]


class LoginWindow(QWidget):
    authenticated = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Reservations Manager Login")
        self.resize(420, 230)

        self._spinner_index = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(120)
        self._spinner_timer.timeout.connect(self._tick_spinner)

        self._build_ui()
        self._load_saved_credentials()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(
            QLabel("Sign in to connect to the reservations database.")
        )

        form = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Username", self.username_input)
        form.addRow("Password", self.password_input)
        root.addLayout(form)

        self.remember_checkbox = QCheckBox("Remember login on this device")
        root.addWidget(self.remember_checkbox)

        self.status_label = QLabel("")
        root.addWidget(self.status_label)

        button_row = QHBoxLayout()
        self.request_button = QPushButton("Request Registration")
        self.connect_button = QPushButton("Connect")
        self.request_button.clicked.connect(self._open_registration_dialog)
        self.connect_button.clicked.connect(self._connect)

        button_row.addWidget(self.request_button)
        button_row.addWidget(self.connect_button)
        root.addLayout(button_row)

    def _load_saved_credentials(self) -> None:
        settings = QSettings(APP_ORG, APP_NAME)
        saved_username = settings.value("saved_username", "", str)
        if not saved_username:
            return

        self.username_input.setText(saved_username)
        try:
            saved_password = keyring.get_password(
                KEYRING_SERVICE, saved_username
            )
        except KeyringError:
            saved_password = None
        if saved_password:
            self.password_input.setText(saved_password)
            self.remember_checkbox.setChecked(True)

    def _set_inputs_enabled(self, enabled: bool) -> None:
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        self.request_button.setEnabled(enabled)
        self.connect_button.setEnabled(enabled)

    def _open_registration_dialog(self) -> None:
        dialog = RegistrationRequestDialog(self)
        dialog.exec()

    def _connect(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Username and password are required.",
            )
            return

        try:
            init_db()
            with SessionLocal() as session:
                user = session.query(User).filter_by(username=username).first()
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "Database Error",
                f"Could not connect to database.\n\nDetails: {exc}",
            )
            return

        if user is None or not user.verify_password(password):
            QMessageBox.warning(
                self,
                "Invalid Credentials",
                "Incorrect username or password.",
            )
            return

        self._persist_credentials(username, password)
        self._set_inputs_enabled(False)
        self._spinner_index = 0
        self.status_label.setText("Connecting to database")
        self._spinner_timer.start()
        QTimer.singleShot(2000, self._finish_connect)

    def _persist_credentials(self, username: str, password: str) -> None:
        settings = QSettings(APP_ORG, APP_NAME)
        if self.remember_checkbox.isChecked():
            try:
                keyring.set_password(KEYRING_SERVICE, username, password)
            except KeyringError as exc:
                QMessageBox.warning(
                    self,
                    "Secure Storage Error",
                    "Could not save password securely in keyring. "
                    f"Credentials will not be remembered.\n\nDetails: {exc}",
                )
                settings.remove("saved_username")
                return

            settings.setValue("saved_username", username)
            return

        saved_username = settings.value("saved_username", "", str)
        if saved_username:
            try:
                keyring.delete_password(KEYRING_SERVICE, saved_username)
            except PasswordDeleteError:
                pass
            except KeyringError:
                pass
        settings.remove("saved_username")

    def _tick_spinner(self) -> None:
        frame = SPINNER_FRAMES[self._spinner_index % len(SPINNER_FRAMES)]
        self._spinner_index += 1
        self.status_label.setText(f"Connecting to database {frame}")

    def _finish_connect(self) -> None:
        if not self._spinner_timer.isActive():
            return

        self._spinner_timer.stop()
        self.status_label.setText("Connected")
        self.authenticated.emit()
