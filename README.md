Nortek-Python
=============

A Python package for working with Nortek instruments and data.

Installation
------------
  * Install Nortek's PdCommATL library (contact Nortek to obtain the necessary installer).
  * Either run `pip install nortek`, or `git clone` this repository, and inside 
    run `python setup.py install` from a command prompt.

Usage
-----

```python
>>> from nortek.controls import PdControl
>>> vectrino = PdControl()
>>> vectrino.serial_port = "COM2"
>>> vectrino.state
'Not connected'
>>> vectrino.sample_rate = 200
>>> vectrino.coordinate_system
'ENU'
```

