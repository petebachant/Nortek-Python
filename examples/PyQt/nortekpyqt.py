# -*- coding: utf-8 -*-
"""
Created on Wed May 29 18:17:57 2013

@author: Pete
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
import PyQt4.Qwt5 as Qwt
from mainwindow import *
import sys
import time
import os
import serial
from serial.tools import list_ports

import win32com.client as wc
import comtypes

import matplotlib.pyplot as plt
import numpy as np

class constants:
    states = {0 : "Firmware upgrade mode",
              1 : "Measurement mode",
              2 : "Command mode",
              4 : "Data retreival mode",
              5 : "Confirmation mode"}


pdcommx = wc.Dispatch('PdCommATL.PdCommX.1')


def safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')


def list_serial_ports():
    # Windows
    if os.name == 'nt':
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append('COM'+str(i + 1))
                s.close()
            except serial.SerialException:
                pass
        return available
    else:
        # Mac / Linux
        return [port[0] for port in list_ports.comports()]

# Set up a thread for the connection process
class ConThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        finished = QtCore.pyqtSignal()
        global shit
        shit = "piss"

        
    def run(self):
        pdcommx.Connect()
        self.isconnected = pdcommx.IsConnected()
        self.finished.emit()
        

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Setup a timer and connect appropriate slot
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        
        # Connect signals to appropriate slots
        self.ui.connect_button.clicked.connect(self.on_connect_click)
        self.ui.start_button.clicked.connect(self.on_start)
        self.ui.stop_button.clicked.connect(self.on_stop)
        self.ui.getconfig_button.clicked.connect(self.on_getconfig)
        self.ui.actionMatplotlib.triggered.connect(self.on_mpl)
        
        # Add some labels to the status bar
        self.clabel = QLabel()
        self.clabel.setText("Not connected ")
        self.ui.statusbar.addWidget(self.clabel)
        self.vel_label = QLabel()
        self.ui.statusbar.addWidget(self.vel_label)
        self.st_label = QLabel()
        self.ui.statusbar.addWidget(self.st_label)
        
        # Disable buttons and initialize connect variable
        self.isconnected = False
        self.ui.start_button.setDisabled(True)
        self.ui.stop_button.setDisabled(True)
        self.ui.getconfig_button.setEnabled(False)
        
        # Set up velocity as a variant
        self.vel = QVariant()
        
        # Create plot
        self.create_plot()
        
        # List available COM ports
        self.comports = list_serial_ports()
        self.ui.comport_combobox.addItems(QStringList(self.comports))
        
        # Set some stuff up
        pdcommx.StartOnSynch = 0
        pdcommx.SynchMaster = 1
        pdcommx.CoordinateSystem = 1
        pdcommx.DiagnosticsMode = 0

        
    def on_connect_click(self):
        comport = self.ui.comport_combobox.currentText()
        pdcommx.SerialPort = str(comport)
        self.clabel.setText("Attempting to connect via " + comport + "... ")
        self.conthread = ConThread()
        self.conthread.finished.connect(self.on_con_finish)
        self.conthread.start()
        
    
    def on_mpl(self):
        plt.figure()
        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x)
        plt.plot(x, y)
        plt.show()
        
        
    def on_con_finish(self):
        
        if self.conthread.isconnected == True:
            text = QString("Connected ")
            self.isconnected = True
            self.timer.start(300)
            
        else: 
            text = QString("Could not connect ")
            self.isconnected = False
        
        self.clabel.setText(text)
        
        self.ui.start_button.setEnabled(self.isconnected)
        self.ui.stop_button.setEnabled(self.isconnected)
        self.ui.getconfig_button.setEnabled(self.isconnected)
        
        
    def on_start(self):
        if self.isconnected == True:
            pdcommx.Stop()
            pdcommx.SetConfig()
            pdcommx.StartDiskRecording("test", False)
            pdcommx.Start(False)
        
        
    def on_stop(self):
        if self.isconnected == True:
            pdcommx.Stop()
            pdcommx.StopDiskRecording()

    
    def create_plot(self):
        self.plot = self.ui.plot
        self.plot.setCanvasBackground(Qt.white)
        self.grid = Qwt.QwtPlotGrid()
        self.grid.attach(self.plot)
        self.grid.setPen(QPen(Qt.black, 0, Qt.DotLine))
        self.curve = Qwt.QwtPlotCurve('')
        self.curve.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        self.pen = QPen(QColor('black'))
        self.pen.setWidth(0)
        self.curve.setPen(self.pen)
        self.curve.attach(self.plot)
        
    
    def on_getconfig(self):
        config = pdcommx.GetHeadConf()
        print config.encode('utf-8', 'replace')
        
    def on_timer(self):
        st = pdcommx.InquireState()
        self.st_label.setText(constants.states[st] + " ")
        
        vel = pdcommx.GetVarVelocity()    
        
        self.vel_label.setText("Velocity: " + str(vel[0]) + " ")

        
    def closeEvent(self, event):
        if self.isconnected == True:
            pdcommx.Stop()
            pdcommx.Disconnect()
            pdcommx.StopDiskRecording()
            
        plt.close('all')
        

def main():
    
    app = QtGui.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()