PdCommPy
========

A Python wrapper for Nortek's PdCommATL -- still in its fledgling stages.


Installation
============
  * Install Nortek's PdCommATL library (contact Nortek to obtain the necessary installer)
  * Run win32com's `makepy.py` module (located, for example, at `C:\python27\Lib\site-packages\win32com\client`),
    selecting "PdCommATL 1.0 Type Library (1.0)" from the list.
  * `git clone` this repository, and inside run `python setup.py install` from a command prompt.

Usage
=====

```python
from pdcommpy import PdControl

pdcontrol = PdControl()
pdcontrol.set_serial_port("COM2")
print pdcontrol.inquire_state()
pdcontrol.set_sample_rate(200)
print pdcontrol.get_coordinate_system()
```
