"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.database import SessionLocal
from app.db.models import (
    RegistrationRequestStatus,
    User,
    UserRegistrationRequest,
    UserRole,
)

USER_ROLE_OPTIONS = [
    UserRole.ADMIN.value,
    UserRole.OWNER.value,
    UserRole.MANAGER.value,
    UserRole.PERSONNEL.value,
]


class AdminDataLoader(QThread):
    loaded = pyqtSignal(list, list, str)

    def run(self) -> None:
        try:
            with SessionLocal() as session:
                users = session.query(User).order_by(User.id.asc()).all()
                requests = (
                    session.query(UserRegistrationRequest)
                    .order_by(UserRegistrationRequest.created_at.desc())
                    .all()
                )
        except SQLAlchemyError as exc:
            self.loaded.emit([], [], str(exc))
            return

        users_data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "role": user.role.value,
                "created_at": user.created_at,
            }
            for user in users
        ]

        requests_data = [
            {
                "id": request.id,
                "username": request.username,
                "email": request.email,
                "name": request.name,
                "phone_number": request.phone_number,
                "requested_role": request.requested_role.value,
                "status": request.status.value,
                "created_at": request.created_at,
            }
            for request in requests
        ]

        self.loaded.emit(users_data, requests_data, "")


class MainWindow(QMainWindow):
    def __init__(self, role_value: str = "") -> None:
        super().__init__()
        self.setWindowTitle("Reservations Manager")
        self.resize(1100, 700)

        self.current_role = role_value
        self.tabs = QTabWidget()
        self.users_table: QTableWidget | None = None
        self.requests_table: QTableWidget | None = None
        self._loading_index = 0
        self._admin_loader: AdminDataLoader | None = None
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(120)
        self._loading_timer.timeout.connect(self._tick_loading_spinner)

        if self.current_role == UserRole.ADMIN.value:
            self.tabs.addTab(self._build_users_tab(), "Users")
            self.tabs.addTab(self._build_user_requests_tab(), "User Requests")

        self.tabs.addTab(self._build_properties_tab(), "Properties")
        self.tabs.addTab(self._build_units_tab(), "Rental Units")
        self.tabs.addTab(self._build_reservations_tab(), "Reservations")

        self.setCentralWidget(self.tabs)

        status = QStatusBar()
        self.loading_label = QLabel("")
        status.addPermanentWidget(self.loading_label)
        status.showMessage("Ready")
        self.setStatusBar(status)

        if self.current_role == UserRole.ADMIN.value:
            self._load_admin_data_async()

    def _build_users_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Manage users and update account details."))

        self.users_table = QTableWidget(0, 7)
        self.users_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Username",
                "Email",
                "Name",
                "Phone",
                "Role",
                "Created",
            ]
        )
        header = self.users_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)

        layout.addWidget(self.users_table)

        actions = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        save_button = QPushButton("Save Changes")
        revoke_button = QPushButton("Revoke User")
        refresh_button.clicked.connect(self._load_admin_data_async)
        save_button.clicked.connect(self._save_user_changes)
        revoke_button.clicked.connect(self._revoke_selected_user)
        actions.addWidget(refresh_button)
        actions.addWidget(save_button)
        actions.addWidget(revoke_button)
        layout.addLayout(actions)

        return widget

    def _build_user_requests_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Review user registration requests."))

        self.requests_table = QTableWidget(0, 8)
        self.requests_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Username",
                "Email",
                "Name",
                "Phone",
                "Role",
                "Status",
                "Requested",
            ]
        )
        header = self.requests_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)

        layout.addWidget(self.requests_table)

        actions = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        approve_button = QPushButton("Approve")
        decline_button = QPushButton("Decline")
        refresh_button.clicked.connect(self._load_admin_data_async)
        approve_button.clicked.connect(self._approve_selected_request)
        decline_button.clicked.connect(self._decline_selected_request)
        actions.addWidget(refresh_button)
        actions.addWidget(approve_button)
        actions.addWidget(decline_button)
        layout.addLayout(actions)

        return widget

    def _tick_loading_spinner(self) -> None:
        frame = ["|", "/", "-", "\\"][self._loading_index % 4]
        self._loading_index += 1
        self.loading_label.setText(f"Loading... {frame}")

    def _set_loading_state(self, loading: bool) -> None:
        if loading:
            self._loading_index = 0
            self.loading_label.setText("Loading... |")
            self._loading_timer.start()
            return

        self._loading_timer.stop()
        self.loading_label.setText("")

    def _load_admin_data_async(self) -> None:
        if self.current_role != UserRole.ADMIN.value:
            return

        if self._admin_loader is not None and self._admin_loader.isRunning():
            return

        self._set_loading_state(True)
        self._admin_loader = AdminDataLoader()
        self._admin_loader.loaded.connect(self._on_admin_data_loaded)
        self._admin_loader.start()

    def _on_admin_data_loaded(
        self,
        users_data: list,
        requests_data: list,
        error_message: str,
    ) -> None:
        self._set_loading_state(False)

        if error_message:
            QMessageBox.warning(
                self,
                "Database",
                f"Could not load admin data.\n\nDetails: {error_message}",
            )
            return

        self._populate_users_table(users_data)
        self._populate_requests_table(requests_data)

    def _populate_users_table(self, users_data: list) -> None:
        if self.users_table is None:
            return

        self.users_table.setRowCount(len(users_data))
        for row, user in enumerate(users_data):
            self._set_table_text(
                self.users_table,
                row,
                0,
                str(user["id"]),
                editable=False,
            )
            self._set_table_text(
                self.users_table,
                row,
                1,
                user["username"],
                editable=True,
            )
            self._set_table_text(
                self.users_table,
                row,
                2,
                user["email"],
                editable=True,
            )
            self._set_table_text(
                self.users_table,
                row,
                3,
                user["name"],
                editable=True,
            )
            self._set_table_text(
                self.users_table,
                row,
                4,
                user["phone_number"],
                editable=True,
            )

            role_combo = QComboBox()
            for role in USER_ROLE_OPTIONS:
                role_combo.addItem(role.capitalize(), role)
            role_combo.setCurrentIndex(USER_ROLE_OPTIONS.index(user["role"]))
            self.users_table.setCellWidget(row, 5, role_combo)

            self._set_table_text(
                self.users_table,
                row,
                6,
                user["created_at"].strftime("%Y-%m-%d %H:%M"),
                editable=False,
            )

    def _populate_requests_table(self, requests_data: list) -> None:
        if self.requests_table is None:
            return

        self.requests_table.setRowCount(len(requests_data))
        for row, request in enumerate(requests_data):
            self._set_table_text(
                self.requests_table,
                row,
                0,
                str(request["id"]),
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                1,
                request["username"],
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                2,
                request["email"],
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                3,
                request["name"],
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                4,
                request["phone_number"],
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                5,
                request["requested_role"],
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                6,
                request["status"],
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                7,
                request["created_at"].strftime("%Y-%m-%d %H:%M"),
                editable=False,
            )

    def _set_table_text(
        self,
        table: QTableWidget,
        row: int,
        col: int,
        text: str,
        editable: bool,
    ) -> None:
        item = QTableWidgetItem(text)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, col, item)

    def _reload_users(self) -> None:
        if self.users_table is None:
            return

        try:
            with SessionLocal() as session:
                users = session.query(User).order_by(User.id.asc()).all()
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "Users",
                f"Could not load users.\n\nDetails: {exc}",
            )
            return

        self.users_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self._set_table_text(
                self.users_table, row, 0, str(user.id), editable=False
            )
            self._set_table_text(
                self.users_table,
                row,
                1,
                user.username,
                editable=True,
            )
            self._set_table_text(
                self.users_table,
                row,
                2,
                user.email,
                editable=True,
            )
            self._set_table_text(
                self.users_table,
                row,
                3,
                user.name,
                editable=True,
            )
            self._set_table_text(
                self.users_table,
                row,
                4,
                user.phone_number,
                editable=True,
            )

            role_combo = QComboBox()
            for role in USER_ROLE_OPTIONS:
                role_combo.addItem(role.capitalize(), role)
            role_combo.setCurrentIndex(
                USER_ROLE_OPTIONS.index(user.role.value)
            )
            self.users_table.setCellWidget(row, 5, role_combo)

            self._set_table_text(
                self.users_table,
                row,
                6,
                user.created_at.strftime("%Y-%m-%d %H:%M"),
                editable=False,
            )

    def _selected_user_id(self) -> int | None:
        if self.users_table is None:
            return None

        row = self.users_table.currentRow()
        if row < 0:
            return None

        item = self.users_table.item(row, 0)
        if item is None:
            return None
        return int(item.text())

    def _save_user_changes(self) -> None:
        if self.users_table is None:
            return

        try:
            with SessionLocal() as session:
                for row in range(self.users_table.rowCount()):
                    id_item = self.users_table.item(row, 0)
                    username_item = self.users_table.item(row, 1)
                    email_item = self.users_table.item(row, 2)
                    name_item = self.users_table.item(row, 3)
                    phone_item = self.users_table.item(row, 4)
                    role_widget = self.users_table.cellWidget(row, 5)

                    if (
                        id_item is None
                        or username_item is None
                        or email_item is None
                        or name_item is None
                        or phone_item is None
                        or not isinstance(role_widget, QComboBox)
                    ):
                        continue

                    user = session.get(User, int(id_item.text()))
                    if user is None:
                        continue

                    user.username = username_item.text().strip()
                    user.email = email_item.text().strip()
                    user.name = name_item.text().strip()
                    user.phone_number = phone_item.text().strip()
                    user.role = UserRole(role_widget.currentData())

                session.commit()
        except (IntegrityError, ValueError):
            QMessageBox.warning(
                self,
                "Users",
                "Could not save changes. Check for duplicate usernames/"
                "emails and valid values.",
            )
            return
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "Users",
                f"Could not save user changes.\n\nDetails: {exc}",
            )
            return

        QMessageBox.information(self, "Users", "User changes saved.")
        self._load_admin_data_async()

    def _revoke_selected_user(self) -> None:
        user_id = self._selected_user_id()
        if user_id is None:
            QMessageBox.information(
                self,
                "Users",
                "Select a user row to revoke.",
            )
            return

        if (
            QMessageBox.question(
                self,
                "Revoke User",
                "Revoke selected user? This removes the account.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            with SessionLocal() as session:
                user = session.get(User, user_id)
                if user is None:
                    QMessageBox.information(
                        self, "Users", "User no longer exists."
                    )
                    self._load_admin_data_async()
                    return

                session.delete(user)
                session.commit()
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "Users",
                f"Could not revoke user.\n\nDetails: {exc}",
            )
            return

        self._load_admin_data_async()
        QMessageBox.information(self, "Users", "User revoked.")

    def _reload_requests(self) -> None:
        if self.requests_table is None:
            return

        try:
            with SessionLocal() as session:
                requests = (
                    session.query(UserRegistrationRequest)
                    .order_by(UserRegistrationRequest.created_at.desc())
                    .all()
                )
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "User Requests",
                f"Could not load requests.\n\nDetails: {exc}",
            )
            return

        self.requests_table.setRowCount(len(requests))
        for row, request in enumerate(requests):
            self._set_table_text(
                self.requests_table, row, 0, str(request.id), editable=False
            )
            self._set_table_text(
                self.requests_table,
                row,
                1,
                request.username,
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                2,
                request.email,
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                3,
                request.name,
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                4,
                request.phone_number,
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                5,
                request.requested_role.value,
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                6,
                request.status.value,
                editable=False,
            )
            self._set_table_text(
                self.requests_table,
                row,
                7,
                request.created_at.strftime("%Y-%m-%d %H:%M"),
                editable=False,
            )

    def _selected_request_id(self) -> int | None:
        if self.requests_table is None:
            return None

        row = self.requests_table.currentRow()
        if row < 0:
            return None

        id_item = self.requests_table.item(row, 0)
        if id_item is None:
            return None
        return int(id_item.text())

    def _approve_selected_request(self) -> None:
        request_id = self._selected_request_id()
        if request_id is None:
            QMessageBox.information(
                self,
                "User Requests",
                "Select a request row to approve.",
            )
            return

        try:
            with SessionLocal() as session:
                request = session.get(UserRegistrationRequest, request_id)
                if request is None:
                    QMessageBox.information(
                        self, "User Requests", "Request no longer exists."
                    )
                    self._load_admin_data_async()
                    return

                if request.status != RegistrationRequestStatus.PENDING:
                    QMessageBox.information(
                        self,
                        "User Requests",
                        "Only pending requests can be approved.",
                    )
                    return

                user = User(
                    username=request.username,
                    email=request.email,
                    name=request.name,
                    phone_number=request.phone_number,
                    role=request.requested_role,
                    password_hash=request.password_hash,
                )
                request.status = RegistrationRequestStatus.APPROVED
                session.add(user)
                session.commit()
        except IntegrityError:
            QMessageBox.warning(
                self,
                "User Requests",
                "Could not approve request because username/email already "
                "exists.",
            )
            return
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "User Requests",
                f"Could not approve request.\n\nDetails: {exc}",
            )
            return

        self._load_admin_data_async()
        QMessageBox.information(
            self,
            "User Requests",
            "Request approved and user created.",
        )

    def _decline_selected_request(self) -> None:
        request_id = self._selected_request_id()
        if request_id is None:
            QMessageBox.information(
                self,
                "User Requests",
                "Select a request row to decline.",
            )
            return

        try:
            with SessionLocal() as session:
                request = session.get(UserRegistrationRequest, request_id)
                if request is None:
                    QMessageBox.information(
                        self, "User Requests", "Request no longer exists."
                    )
                    self._load_admin_data_async()
                    return

                request.status = RegistrationRequestStatus.REJECTED
                session.commit()
        except SQLAlchemyError as exc:
            QMessageBox.warning(
                self,
                "User Requests",
                f"Could not decline request.\n\nDetails: {exc}",
            )
            return

        self._load_admin_data_async()
        QMessageBox.information(self, "User Requests", "Request declined.")

    def _build_properties_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Property list will be loaded from MySQL."))
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["ID", "Name", "Address"])
        header = table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(table)

        return widget

    def _build_units_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Rental units grouped by property."))
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(
            ["ID", "Property", "Unit Code", "Nightly Rate"]
        )
        header = table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(table)

        return widget

    def _build_reservations_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        helper = QLabel("Reservations timeline and booking operations.")
        helper.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(helper)

        table = QTableWidget(1, 5)
        table.setHorizontalHeaderLabels(
            ["ID", "Guest", "Unit", "Check-in", "Check-out"]
        )
        header = table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        table.setItem(0, 0, QTableWidgetItem("Sample"))
        layout.addWidget(table)

        return widget
