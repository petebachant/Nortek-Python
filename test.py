# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 18:24:36 2014

@author: Pete
"""

from __future__ import print_function, division
from nortek.files import VectrinoFile
from nortek.controls import PdControl
import matplotlib.pyplot as plt

def test_vectrino_file():
    vec = VectrinoFile("examples/test.vno")
    print(vec.keys())
    u = vec["velocity"]["data"][0,:,0]
    print(vec["velocityHeader"])
    print(vec["hardwareConfiguration"])
    plt.plot(u)
    plt.show()
    
def test_pdcontrol():
    vec = PdControl()
    print(vec.sound_speed_mode)
    print(vec.sound_speed)
    print(vec.salinity)
    
if __name__ == "__main__":
    test_pdcontrol()