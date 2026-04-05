"""Registration request dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.database import SessionLocal, init_db
from app.db.models import UserRegistrationRequest, UserRole, hash_password


class RegistrationRequestDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Request Registration")
        self.setModal(True)
        self.resize(440, 320)

        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "Submit your details and an admin can approve your account."
            )
        )

        form = QFormLayout()
        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_input = QComboBox()
        self.role_input.addItem("Owner", UserRole.OWNER)
        self.role_input.addItem("Manager", UserRole.MANAGER)
        self.role_input.addItem("Personnel", UserRole.PERSONNEL)

        form.addRow("Username", self.username_input)
        form.addRow("Email", self.email_input)
        form.addRow("Name", self.name_input)
        form.addRow("Phone Number", self.phone_input)
        form.addRow("Password", self.password_input)
        form.addRow("Confirm Password", self.confirm_password_input)
        form.addRow("Requested Role", self.role_input)
        root.addLayout(form)

        buttons = QHBoxLayout()
        self.submit_button = QPushButton("Submit Request")
        self.cancel_button = QPushButton("Cancel")
        self.submit_button.clicked.connect(self._submit)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.submit_button)
        buttons.addWidget(self.cancel_button)
        root.addLayout(buttons)

    def _submit(self) -> None:
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        name = self.name_input.text().strip()
        phone_number = self.phone_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        requested_role = self.role_input.currentData()

        if not all([username, email, name, phone_number, password]):
            QMessageBox.warning(
                self, "Invalid Input", "All fields are required."
            )
            return

        if password != confirm_password:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Password and confirmation do not match.",
            )
            return

        if requested_role == UserRole.ADMIN:
            QMessageBox.warning(
                self,
                "Invalid Role",
                "Admin registration requests are not allowed.",
            )
            return

        request = UserRegistrationRequest(
            username=username,
            email=email,
            name=name,
            phone_number=phone_number,
            requested_role=requested_role,
            password_hash=hash_password(password),
        )

        try:
            init_db()
            with SessionLocal() as session:
                session.add(request)
                session.commit()
        except IntegrityError:
            QMessageBox.warning(
                self,
                "Request Failed",
                (
                    "A request or user with that username/email may already "
                    "exist."
                ),
            )
            return
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "Request Failed",
                f"Could not submit registration request.\n\nDetails: {exc}",
            )
            return

        QMessageBox.information(
            self,
            "Request Sent",
            "Your registration request was submitted for admin approval.",
        )
        self.accept()
