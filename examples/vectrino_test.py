# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 22:59:01 2013

@author: Pete
"""
from __future__ import division
from pdcommpy import PdControl
import time
import matplotlib.pyplot as plt
import numpy as np

vec = PdControl()

vec.set_serial_port("COM8")
vec.set_start_on_synch(False)
vec.set_synch_master(True)
vec.set_sample_rate(20)
vec.set_vel_range(2)
vec.set_transmit_length(3)
vec.set_sampling_volume(3)
vec.set_salinity(0.0)
vec.set_power_level(0)
vec.connect()
connected = False

while not vec.connected:
    print "Connecting..."
    vec.is_connected()
    time.sleep(0.5)    
print "Connected!"

vec.set_config()
vec.stop()
vec.start_disk_recording("test/test", False)
vec.start()

while vec.state != "Confirmation mode":
    time.sleep(0.2)
    vec.inquire_state()
print "Collecting data..."

i = 0
t0 = time.time()
t = 0

while t < 10:
    print vec.get_snr(1,1)
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