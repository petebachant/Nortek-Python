PdCommPy
========

A Python wrapper for Nortek's PdCommATL -- still in its fledgling stages.

Usage
=====

    from pdcommpy import PdControl
    pdcontrol = PdControl()
    pdcontrol.set_serial_port("COM2")
    print pdcontrol.inquire_state()
    pdcontrol.set_sample_rate(200)
    print pdcontrol.get_coordinate_system()
