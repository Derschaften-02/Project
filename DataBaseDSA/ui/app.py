"""PySide6 window: your Designer UI (ui_mainwindow.py) wired to the adaptive database.

Replaces the old PyQt6 ui/app.py. cli.py / main.py still call run_ui() unchanged.
"""
import sys

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QDockWidget, QFileDialog, QListWidget, QMainWindow,
                               QMessageBox, QTableView, QVBoxLayout)

from core.importer import import_file
from core.indexer import load_rows
from core.registry import all_models, get_model, unregister_model
from core.searchcode import entry_search, exclusion_search
from ui.ui_mainwindow import Ui_MainWindow

ROW_LIMIT = 1000  # rows drawn at once


# ---------- background work (keeps the window responsive, drives the progress bar) ----------
class Worker(QThread):
    progress = Signal(int)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn  # fn(progress_callback) -> result

    def run(self):
        try:
            self.done.emit(self.fn(self.progress.emit))
        except Exception as e:
            self.failed.emit(str(e))


# ---------- table model ----------
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


# ---------- main window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.cache = {}      # table name -> rows loaded by Index
        self.worker = None
        self._on_done = None

        self._add_widgets()
        self._connect()
        self.reload_tables()

    # ----- setup -----
    def _add_widgets(self):
        ui = self.ui

        # table list in a dock on the left
        self.table_list = QListWidget()
        dock = QDockWidget("Tables", self)
        dock.setWidget(self.table_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        # results table
        self.rows_model = RowsModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.rows_model)
        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
        self.view.setAlternatingRowColors(True)
        self.view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        # the .ui uses fixed geometry; a layout on the central widget makes it resizable
        layout = QVBoxLayout(ui.centralwidget)
        layout.addWidget(ui.splitter_4)
        layout.addWidget(self.view, 1)
        layout.addWidget(ui.textBrowser)
        ui.splitter_4.setMaximumHeight(60)
        ui.textBrowser.setMaximumHeight(90)
        ui.lineEdit.setPlaceholderText("Search...  (add -word to exclude, e.g.  python -java)")
        self.resize(1000, 650)

        # the two empty menus from the .ui
        self.act_import = ui.menuDownload_new_files.addAction("Import file...")
        self.act_delete = ui.menuEdit_file.addAction("Delete current table")

    def _connect(self):
        ui = self.ui
        ui.pushButton.clicked.connect(self.search)        # Search
        ui.lineEdit.returnPressed.connect(self.search)
        ui.comboBox.activated.connect(self.search)        # picking a column re-runs the search
        ui.pushButton_2.clicked.connect(self.browse)      # Browse files -> import into the database
        ui.pushButton_3.clicked.connect(self.index)       # Index
        self.act_import.triggered.connect(self.browse)
        self.act_delete.triggered.connect(self.delete_table)
        self.table_list.currentItemChanged.connect(self.on_table_changed)

    # ----- helpers -----
    def log(self, text):
        self.ui.textBrowser.setPlainText(text)

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
            self.on_table_changed()

    def show_rows(self, model, rows):
        self.rows_model.set_data(model, rows[:ROW_LIMIT])
        self.view.resizeColumnsToContents()
        extra = f" (first {ROW_LIMIT} shown)" if len(rows) > ROW_LIMIT else ""
        self.statusBar().showMessage(f"{len(rows)} rows{extra}  |  {model.count()} in table")

    def on_table_changed(self, *_):
        model = self.current_model()
        combo = self.ui.comboBox  # search modes = "All" + this table's columns
        combo.clear()
        combo.addItem("All", "all")
        if not model:
            self.rows_model.clear()
            self.log("No tables yet. Click 'Browse files' to import a CSV.")
            return
        for col in model.fields:
            combo.addItem(model.labels.get(col, col), col)
        self.show_rows(model, model.all(limit=ROW_LIMIT))
        self.log(f"Table '{model.table}': {model.count()} rows.")

    def rows_for(self, model):
        """Rows searchcode scans. Uses the Index cache; builds it if Index wasn't pressed."""
        if model.table not in self.cache:
            self.cache[model.table] = load_rows(model)
        return self.cache[model.table]

    # ----- actions -----
    def search(self, *_):
        model = self.current_model()
        if not model:
            self.log("Import a table first (Browse files).")
            return
        words = self.ui.lineEdit.text().split()
        term = " ".join(w for w in words if not (w.startswith("-") and len(w) > 1))
        excluded = [w[1:] for w in words if w.startswith("-") and len(w) > 1]

        mode = self.ui.comboBox.currentData() or "all"
        columns = list(model.fields) if mode == "all" else [mode]
        label = self.ui.comboBox.currentText()

        hits, exact = entry_search(self.rows_for(model), columns, term)
        for word in excluded:
            hits = exclusion_search(hits, columns, word)

        self.show_rows(model, hits)
        msg = f"Searching '{term}' in {label}: {len(hits)} result(s)."
        if term and not exact:
            msg += " No exact match - showing closest, ranked by words matched."
        if excluded:
            msg += f" Excluded: {', '.join(excluded)}."
        self.log(msg)

    def browse(self, *_):
        path, _ = QFileDialog.getOpenFileName(self, "Import file", "", "CSV files (*.csv);;All files (*)")
        if path:
            self.run_job(lambda progress: import_file(path), self._imported, busy=True)

    def _imported(self, model):
        self.log(f"Imported {model.count()} rows into '{model.table}'.")
        self.reload_tables(select=model.table)

    def index(self, *_):
        model = self.current_model()
        if not model:
            self.log("Nothing to index - import a table first.")
            return
        self.cache.pop(model.table, None)
        self.run_job(lambda progress: load_rows(model, progress),
                     lambda rows: self._indexed(model, rows))

    def _indexed(self, model, rows):
        self.cache[model.table] = rows
        self.log(f"Indexed '{model.table}': {len(rows)} rows ready to search.")

    def delete_table(self, *_):
        model = self.current_model()
        if not model:
            return
        answer = QMessageBox.question(self, "Delete table",
                                      f"Delete '{model.table}' and all {model.count()} rows?")
        if answer == QMessageBox.StandardButton.Yes:
            model.drop()
            unregister_model(model.table)
            self.cache.pop(model.table, None)
            self.reload_tables()

    # ----- background jobs -----
    def run_job(self, fn, on_done, busy=False):
        if self.worker and self.worker.isRunning():
            self.log("Still working on the previous task...")
            return
        bar = self.ui.progressBar
        bar.setRange(0, 0 if busy else 100)  # (0, 0) = animated "working" bar when % is unknown
        bar.setValue(0)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self._on_done = on_done
        self.worker = Worker(fn, self)
        # bound methods of QObjects -> Qt delivers these on the GUI thread
        self.worker.progress.connect(bar.setValue)
        self.worker.done.connect(self._job_done)
        self.worker.failed.connect(self._job_failed)
        self.worker.start()

    def _job_finished(self):
        bar = self.ui.progressBar
        bar.setRange(0, 100)
        self.ui.pushButton_2.setEnabled(True)
        self.ui.pushButton_3.setEnabled(True)
        return bar

    def _job_done(self, result):
        self._job_finished().setValue(100)
        self._on_done(result)

    def _job_failed(self, message):
        self._job_finished().setValue(0)
        self.log(f"[error] {message}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.wait()  # let the job finish so the window closes cleanly
        super().closeEvent(event)


def run_ui():
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = MainWindow()
    window.show()
    return app.exec()
