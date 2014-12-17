# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 22:59:01 2013

@author: Pete
"""
from __future__ import division
from nortek.controls import PdControl
import time
import matplotlib.pyplot as plt
import numpy as np

vec = PdControl()

vec.serial_port = "COM8"
vec.start_on_sync = False
vec.sync_master = True
vec.sample_rate = 100
vec.vel_range = 2
vec.transmit_length = 3
vec.sampling_volume = 3
vec.salinity = 0.0
vec.power_level = "High"
vec.connect()

while not vec.connected:
    print "Connecting..."
    time.sleep(0.5)    
print "Connected!"

vec.set_config()
vec.stop()
vec.start_disk_recording("test/test", False)
vec.start()

while vec.state != "Confirmation mode":
    time.sleep(0.2)
print "Collecting data..."

i = 0
t0 = time.time()
t = 0

while t < 10:
    print "Signal to noise ratio (dB):", vec.get_snr(1,1)
    i += 1
    t = time.time() - t0
    time.sleep(0.5)
    
vec.stop()
vec.stop_disk_recording()
vec.disconnect()

print "Disconnected"

plt.close('all')
plt.plot(vec.data["u"])
plt.show()