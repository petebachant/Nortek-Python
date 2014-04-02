PdCommPy
========

A Python wrapper for Nortek's PdCommATL COM library.


Installation
------------
  * Install Nortek's PdCommATL library (contact Nortek to obtain the necessary installer).
  * Run win32com's `makepy.py` module (located, for example, at `C:\python27\Lib\site-packages\win32com\client`),
    selecting "PdCommATL 1.0 Type Library (1.0)" from the list.
  * `git clone` this repository, and inside run `python setup.py install` from a command prompt.

Usage
-----

```python
>>> from pdcommpy import PdControl
>>> pdcontrol = PdControl()
>>> pdcontrol.serial_port = "COM2"
>>> pdcontrol.state
'Not connected'
>>> pdcontrol.sample_rate = 200
>>> pdcontrol.coordinate_system
'ENU'
```

Known issues
------------
  * Salinity in data files is indicated as "N/A". According to Nortek, this should not affect the measurements.


License
-------

PdCommPy Copyright (c) 2013-2014 Peter Bachant

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
