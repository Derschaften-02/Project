# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt,Signal)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QProgressBar, QPushButton,
    QSizePolicy, QSplitter, QStatusBar, QTextBrowser,
    QWidget)
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(709, 232)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.splitter_4 = QSplitter(self.centralwidget)
        self.splitter_4.setObjectName(u"splitter_4")
        self.splitter_4.setGeometry(QRect(50, 10, 571, 48))
        self.splitter_4.setOrientation(Qt.Orientation.Horizontal)
        self.splitter_2 = QSplitter(self.splitter_4)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Vertical)
        self.pushButton = QPushButton(self.splitter_2)
        self.pushButton.setObjectName(u"pushButton")
        self.splitter_2.addWidget(self.pushButton)
        self.comboBox = QComboBox(self.splitter_2)
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        self.splitter_2.addWidget(self.comboBox)
        self.splitter_4.addWidget(self.splitter_2)
        self.splitter = QSplitter(self.splitter_4)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.lineEdit = QLineEdit(self.splitter)
        self.lineEdit.setObjectName(u"lineEdit")
        self.splitter.addWidget(self.lineEdit)
        self.progressBar = QProgressBar(self.splitter)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.splitter.addWidget(self.progressBar)
        self.splitter_4.addWidget(self.splitter)
        self.splitter_3 = QSplitter(self.splitter_4)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Vertical)
        self.pushButton_2 = QPushButton(self.splitter_3)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.splitter_3.addWidget(self.pushButton_2)
        self.pushButton_3 = QPushButton(self.splitter_3)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.splitter_3.addWidget(self.pushButton_3)
        self.splitter_4.addWidget(self.splitter_3)
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(10, 120, 691, 61))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 709, 19))
        self.menuDownload_new_files = QMenu(self.menuBar)
        self.menuDownload_new_files.setObjectName(u"menuDownload_new_files")
        self.menuEdit_file = QMenu(self.menuBar)
        self.menuEdit_file.setObjectName(u"menuEdit_file")
        self.menuEdit_file.setSeparatorsCollapsible(False)
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.menuBar.addAction(self.menuEdit_file.menuAction())
        self.menuBar.addAction(self.menuDownload_new_files.menuAction())

        self.retranslateUi(MainWindow)
        
        self.pushButton_3.clicked.connect(self.progressBar.reset)
        self.pushButton.setDefault(True)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Search", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Search by tag...", None))

        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Browse files", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"Index", None))
        self.textBrowser.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Error/Output Messages box</p></body></html>", None))
        self.menuDownload_new_files.setTitle(QCoreApplication.translate("MainWindow", u"Download new files", None))
        self.menuEdit_file.setTitle(QCoreApplication.translate("MainWindow", u"Edit file", None))
    # retranslateUi

