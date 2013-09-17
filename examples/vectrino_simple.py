# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 16:18:56 2013

This program collects data from a Nortek Vectrino+

@author: Pete
"""
import win32com.client as wc
import time
import matplotlib.pyplot as plt
import numpy as np
import binascii

class PdEvents:
    def __init__(self):
        print "Initializing event handler..."
    def OnNewData(self, hType=1):
        global u, v, w
        vel = pdcommx.GetVel(1,1)
        u.append(vel)
        print "New Data!"

pdcommx = wc.DispatchWithEvents('PdCommATL.PdCommX.1', PdEvents)

u = []
v = []
w = []

pdcommx.SerialPort = "COM2"
pdcommx.StartOnSynch = 0
pdcommx.SynchMaster = 1
pdcommx.SamplingRate = 10
pdcommx.VelRange = 2

pdcommx.Connect()

connected = 0

while connected != 1:
    connected = pdcommx.IsConnected()
    print "Connecting..."
    time.sleep(0.5)
    
print "Connected!"

pdcommx.SetConfig()
conf = pdcommx.GetProdConf()
conf = binascii.b2a_qp(conf)
pdcommx.Stop()
pdcommx.Start(False)
pdcommx.StartDiskRecording("test", False)

state = pdcommx.InquireState()

while state != 5:
    time.sleep(0.1)
    state = pdcommx.InquireState()
    
print "Collecting data..."

i = 0
t0 = time.time()
t = 0

while t < 20:
    i += 1
    t = time.time() - t0
    time.sleep(0.1)
    
pdcommx.Stop()
pdcommx.StopDiskRecording()
pdcommx.Disconnect()

print "Disconnected"

u1 = np.asarray(u[3:])
plt.close('all')
plt.plot(u1)