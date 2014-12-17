# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 18:24:36 2014

@author: Pete
"""

from __future__ import print_function, division
from nortek.files import VectrinoFile
import matplotlib.pyplot as plt

vec = VectrinoFile("examples/test.vno")

print(vec.keys())

u = vec["velocity"]["data"][0,:,0]
print(vec["velocityHeader"])
print(vec["hardwareConfiguration"])


plt.plot(u)
plt.show()