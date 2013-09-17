# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created: Sat Jun 01 16:58:29 2013
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(451, 393)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.plot = Qwt5.QwtPlot(self.centralwidget)
        self.plot.setGeometry(QtCore.QRect(10, 40, 411, 181))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("MS Shell Dlg 2"))
        font.setPointSize(8)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.plot.setFont(font)
        self.plot.setStyleSheet(_fromUtf8("font: 8pt \"MS Shell Dlg 2\";"))
        self.plot.setFrameShape(QtGui.QFrame.NoFrame)
        self.plot.setFrameShadow(QtGui.QFrame.Plain)
        self.plot.setLineWidth(1)
        self.plot.setObjectName(_fromUtf8("plot"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(70, 20, 121, 21))
        self.label.setObjectName(_fromUtf8("label"))
        self.start_button = QtGui.QPushButton(self.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(270, 240, 75, 23))
        self.start_button.setObjectName(_fromUtf8("start_button"))
        self.stop_button = QtGui.QPushButton(self.centralwidget)
        self.stop_button.setGeometry(QtCore.QRect(350, 240, 75, 23))
        self.stop_button.setObjectName(_fromUtf8("stop_button"))
        self.getconfig_button = QtGui.QPushButton(self.centralwidget)
        self.getconfig_button.setGeometry(QtCore.QRect(60, 280, 75, 23))
        self.getconfig_button.setObjectName(_fromUtf8("getconfig_button"))
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setGeometry(QtCore.QRect(60, 240, 130, 23))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.comport_combobox = QtGui.QComboBox(self.splitter)
        self.comport_combobox.setObjectName(_fromUtf8("comport_combobox"))
        self.connect_button = QtGui.QPushButton(self.splitter)
        self.connect_button.setObjectName(_fromUtf8("connect_button"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 451, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuPlot = QtGui.QMenu(self.menubar)
        self.menuPlot.setObjectName(_fromUtf8("menuPlot"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionMatplotlib = QtGui.QAction(MainWindow)
        self.actionMatplotlib.setObjectName(_fromUtf8("actionMatplotlib"))
        self.menuPlot.addAction(self.actionMatplotlib)
        self.menubar.addAction(self.menuPlot.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Nortek PdCommX with PyQt", None))
        self.label.setText(_translate("MainWindow", "Vectrino velocity (m/s)", None))
        self.start_button.setText(_translate("MainWindow", "Start", None))
        self.stop_button.setText(_translate("MainWindow", "Stop", None))
        self.getconfig_button.setText(_translate("MainWindow", "Get Config", None))
        self.connect_button.setText(_translate("MainWindow", "Connect", None))
        self.menuPlot.setTitle(_translate("MainWindow", "Plot", None))
        self.actionMatplotlib.setText(_translate("MainWindow", "matplotlib", None))

from PyQt4 import Qwt5
