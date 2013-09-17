# -*- coding: utf-8 -*-
"""
This program collects data from a Nortek Vectrino+ using the pdcommpy module

@author: Pete
"""
from __future__ import division
import pdcommpy.pdcommpy as pd
import time
import matplotlib.pyplot as plt
import numpy as np

u = []
v = []
w = []

events = pd.EventHandler()
velocity = events.velocity

pd.set_serial_port("COM2")
pd.set_start_on_synch(False)
pd.set_synch_master(True)
pd.set_sampling_rate(10)
pd.set_vel_range(2)
pd.connect()
connected = False

while not connected:
    connected = pd.isconnected()
    print "Connecting..."
    time.sleep(0.5)    
print "Connected!"

pd.set_config()
pd.stop()
pd.start_disk_recording("test", False)
pd.start()
state = pd.inquire_state()

while state != "Confirmation mode":
    time.sleep(0.2)
    state = pd.inquire_state()
print "Collecting data..."

i = 0
t0 = time.time()
t = 0

while t < 20:
    print velocity
    i += 1
    t = time.time() - t0
    time.sleep(0.3)
    
pd.stop()
pd.stop_disk_recording()
pd.disconnect()

print "Disconnected"

u1 = np.asarray(u[3:])
plt.close('all')
plt.plot(u1)