"""PyQt6 window: table list on the left, searchable/sortable data on the right."""
import sys

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QApplication, QFileDialog, QLineEdit, QListWidget, QMainWindow,
                             QMessageBox, QSplitter, QTableView, QToolBar, QVBoxLayout, QWidget)

from core.importer import import_file
from core.registry import all_models, get_model, unregister_model

ROW_LIMIT = 1000  # rows shown at once; search narrows the rest


class RowsModel(QAbstractTableModel):
    """Feeds a list of row dicts to a QTableView."""

    def __init__(self):
        super().__init__()
        self.columns, self.headers, self.rows = [], [], []

    def set_data(self, model, rows):
        self.beginResetModel()
        self.columns = list(model.fields)
        self.headers = [model.labels.get(c, c) for c in self.columns]
        self.rows = rows
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self.columns, self.headers, self.rows = [], [], []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self.rows[index.row()][self.columns[index.column()]]
        if role == Qt.ItemDataRole.DisplayRole:
            return "" if value is None else value
        if role == Qt.ItemDataRole.TextAlignmentRole and isinstance(value, (int, float)):
            return (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter).value
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adaptive DB")
        self.resize(1100, 650)

        # widgets
        self.table_list = QListWidget()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search all columns...")
        self.search_box.setClearButtonEnabled(True)

        self.rows_model = RowsModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.rows_model)
        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
        self.view.setAlternatingRowColors(True)
        self.view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        # layout
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.addWidget(self.search_box)
        layout.addWidget(self.view)
        splitter = QSplitter()
        splitter.addWidget(self.table_list)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 880])
        self.setCentralWidget(splitter)

        # toolbar
        bar = QToolBar()
        self.addToolBar(bar)
        import_action = QAction("Import file...", self)
        import_action.triggered.connect(self.import_dialog)
        delete_action = QAction("Delete table", self)
        delete_action.triggered.connect(self.delete_table)
        bar.addAction(import_action)
        bar.addAction(delete_action)

        # search waits 250 ms after typing stops
        self.timer = QTimer(self, singleShot=True, interval=250)
        self.timer.timeout.connect(self.refresh)
        self.search_box.textChanged.connect(self.timer.start)
        self.table_list.currentItemChanged.connect(lambda *_: self.refresh())

        self.reload_tables()

    # ----- helpers -----
    def current_model(self):
        item = self.table_list.currentItem()
        return get_model(item.text()) if item else None

    def reload_tables(self, select=None):
        self.table_list.clear()
        names = sorted(all_models())
        self.table_list.addItems(names)
        if names:
            self.table_list.setCurrentRow(names.index(select) if select in names else 0)
        else:
            self.refresh()

    def refresh(self):
        model = self.current_model()
        if not model:
            self.rows_model.clear()
            self.statusBar().showMessage("No tables yet. Use 'Import file...'")
            return
        keyword = self.search_box.text().strip()
        rows = model.search(keyword, limit=ROW_LIMIT) if keyword else model.all(limit=ROW_LIMIT)
        self.rows_model.set_data(model, rows)
        self.view.resizeColumnsToContents()
        note = f" matching '{keyword}'" if keyword else ""
        self.statusBar().showMessage(f"{len(rows)} rows shown{note}  |  {model.count()} in table")

    # ----- actions -----
    def import_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import file", "", "CSV files (*.csv);;All files (*)")
        if not path:
            return
        try:
            model = import_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Import failed", str(e))
            return
        self.reload_tables(select=model.table)

    def delete_table(self):
        model = self.current_model()
        if not model:
            return
        answer = QMessageBox.question(self, "Delete table",
                                      f"Delete '{model.table}' and all {model.count()} rows?")
        if answer == QMessageBox.StandardButton.Yes:
            model.drop()
            unregister_model(model.table)
            self.reload_tables()


def run_ui():
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = MainWindow()
    window.show()
    return app.exec()