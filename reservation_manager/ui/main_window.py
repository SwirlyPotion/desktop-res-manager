"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Reservations Manager")
        self.resize(1100, 700)

        tabs = QTabWidget()
        tabs.addTab(self._build_properties_tab(), "Properties")
        tabs.addTab(self._build_units_tab(), "Rental Units")
        tabs.addTab(self._build_reservations_tab(), "Reservations")

        self.setCentralWidget(tabs)

        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

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
