# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 17:16:04 2013

@author: Pete

To-do:
  * Alphabetize functions

"""
from __future__ import print_function
import win32com.client as _wc
import numpy as np

# Device states dict
states = {0 : "Firmware upgrade mode",
          1 : "Measurement mode",
          2 : "Command mode",
          4 : "Data retrieval mode",
          5 : "Confirmation mode",
          -1 : "Not connected"}

# Instruments dict
instruments = {0 : "Aquadopp",
               1 : "Vector",
               2 : "Aquapro",
               3 : "AWAC",
               4 : "EasyQ",
               5 : "Continental",
               6 : "Vectrino"}
    
# Dictionary of velocity ranges (in m/s)
velranges = {"Vector" : {0 : 7.0,
                         1 : 4.0,
                         2 : 2.0,
                         3 : 1.0,
                         4 : 0.3,
                         5 : 0.1,
                         6 : 0.01},
             "Vectrino" : {0 : 4.0,
                           1 : 2.5,
                           2 : 1.0,
                           3 : 0.3,
                           4 : 0.1,
                           5 : 0.03}}

def list_serial_ports():
    """List serial ports on current machine."""
    import os
    import serial
    from serial.tools import list_ports
    # Windows
    if os.name == 'nt':
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append('COM'+str(i + 1))
                s.close()
            except serial.SerialException:
                pass
        return available
    else:
        # Mac / Linux
        return [port[0] for port in list_ports.comports()]           


class PdControl(object):
    """A PdComm control object. When data is being acquired, Numpy arrays
    are being appended to in memory."""
    def __init__(self):
        self.pdx = _wc.DispatchWithEvents('PdCommATL.PdCommX.1', self.PdEvents)
        
        # Set data associated with callback functions
        self.data = self.pdx.data

        # Set default instrument as Vectrino
        self.pdx.DefaultInstrument = 6

    class PdEvents(object):
        """OnNewData event handler."""
        def __init__(self):
            self.data = {"t" : np.array([]),
                         "u" : np.array([]),
                         "v" : np.array([]),
                         "w" : np.array([]),
                         "w2" : np.array([]),
                         "snr_u" : np.array([]),
                         "snr_v" : np.array([]),
                         "snr_w" : np.array([]),
                         "corr_u" : np.array([]),
                         "corr_v" : np.array([]),
                         "corr_w" : np.array([])}
            self.sample = 0
        def append_data(self):
            """Append data to arrays in dict. It seems that the first 3 samples
            should be thrown away to match output of *.vno files."""
            self.data["u"] = np.append(self.data["u"], self.u)
            self.data["v"] = np.append(self.data["v"], self.v)
            self.data["w"] = np.append(self.data["w"], self.w)
            self.data["corr_u"] = np.append(self.data["corr_u"], self.corr_u)
            self.data["corr_v"] = np.append(self.data["corr_v"], self.corr_v)
            self.data["corr_w"] = np.append(self.data["corr_v"], self.corr_w)
            self.data["snr_u"] = np.append(self.data["snr_u"], self.snr_u)
            self.data["snr_v"] = np.append(self.data["snr_u"], self.snr_v)
            self.data["snr_w"] = np.append(self.data["snr_u"], self.snr_w)
            self.data["t"] = np.arange(len(self.data["u"]), dtype=float)\
            /float(self.SamplingRate)
        def OnNewData(self, hType=1):
            self.sample += 1
            self.u = self.GetVel(1,1)
            self.v = self.GetVel(1,2)
            self.w = self.GetVel(1,3)
#            self.w2 = self.GetVel(2,3)
            self.snr_u = self.GetSNR(1,1)
            self.snr_v = self.GetSNR(1,2)
            self.snr_w = self.GetSNR(1,3)
#            self.snr_w2 = self.snr[4]
            self.corr_u = self.GetCorr(1,1)
            self.corr_v = self.GetCorr(1,2)
            self.corr_w = self.GetCorr(1,3)
#            self.corr_w2 = self.GetCorr(1,4)
            # Only append data from the 4th sample onward
            if self.sample >= 4:
                self.append_data()
            
    def connect(self):
        """Connects to the instrument and checks its status."""
        self.pdx.Connect()
        
    @property
    def serial_port(self):
        return str(self.pdx.SerialPort)
    @serial_port.setter
    def serial_port(self, port):
        """Sets serial port."""
        self.pdx.SerialPort = port
    
    @property
    def firmware_version(self):
        """Returns the firmware version. Must be called after connect(), which 
        reads the hardware and software configuration from the instrument."""
        return self.pdx.GetFirmwareVersion()
    
    @property
    def head_serialno(self):
        """Returns the head serial number."""
        return self.pdx.GetHeadSerialNo()
    
    @property
    def start_on_sync(self):
        return bool(self.pdx.StartOnSynch)
    @start_on_sync.setter
    def start_on_sync(self, choice):
        self.pdx.StartOnSynch = int(choice)
    
    @property
    def sample_on_sync(self):
        return bool(self.pdx.SampleOnSynch)
    @sample_on_sync.setter
    def sample_on_sync(self, choice):
        """Sets sample on synch parameter, meaning device will sample at each
        pulse received."""
        self.pdx.SampleOnSynch = int(choice)
    
    @property
    def sync_master(self):
        return bool(self.pdx.SynchMaster)
    @sync_master.setter
    def sync_master(self, choice):
        """Set the device as a sync master."""
        self.pdx.SynchMaster = int(choice)
    
    @property
    def sample_rate(self):
        return self.pdx.SamplingRate
    @sample_rate.setter
    def sample_rate(self, rate):
        """Set sample rate in Hz"""
        self.pdx.SamplingRate = rate
        
    @property
    def transmit_length(self):
        return self.pdx.TransmitLength
    @transmit_length.setter
    def transmit_length(self, val=3):
        """Sets transmit length."""
        if self.instrument == "Vectrino" and type(val) is float:
            if val == 0.3:
                self.pdx.TransmitLength = 0
            elif val == 0.6:
                self.pdx.TransmitLength = 1
            elif val == 1.2:
                self.pdx.TransmitLength = 2
            elif val == 1.8:
                self.pdx.TransmitLength = 3
            elif val == 2.4:
                self.pdx.TransmitLength = 4
            else:
                raise ValueError("Invalid transmit length specified")
        elif val in range(5):
            self.pdx.TransmitLength = val
        else:
            raise ValueError("Invalid transmit length specified")
        
    @property
    def sampling_volume(self):
        return self.pdx.SamplingVolume
    @sampling_volume.setter
    def sampling_volume(self, val):
        """Sets sampling volume."""
        if self.instrument == "Vectrino" and type(val) is float:
            if val == 2.5:
                self.pdx.SamplingVolume = 0
            elif val == 4.0:
                self.pdx.SamplingVolume = 1
            elif val == 5.5:
                self.pdx.SamplingVolume = 2
            elif val == 7.0:
                self.pdx.SamplingVolume = 3
            elif val == 8.5:
                self.pdx.SamplingVolume = 4
            else:
                raise ValueError("Invalid sampling volume specified")
        elif val in range(5):
            self.pdx.SamplingVolume = val
        else:
            raise ValueError("Invalid sampling volume specified")
        
    @property
    def salinity(self):
        return self.pdx.Salinity
    @salinity.setter
    def salinity(self, value=0.0):
        """Sets salinity in ppt."""
        self.pdx.Salinity = value
        
    @property
    def power_level(self):
        pl = self.pdx.PowerLevel
        if pl == 0:
            return "High"
        elif pl == 1:
            return "HighLow"
        elif pl == 2:
            return "LowHigh"
        elif pl == 3: 
            return "Low"
        else: return pl
    @power_level.setter
    def power_level(self, val):
        """Sets the power level according to the index or string.
        0 = High
        1 = HighLow
        2 = LowHigh
        3 = Low"""
        if val in [0, 1, 2, 3]:
            self.pdx.PowerLevel = val
        elif type(val) is str:
            if val.lower() == "high":
                self.pdx.PowerLevel = 0
            elif val.lower() == "highlow":
                self.pdx.PowerLevel = 1
            elif val.lower() == "lowhigh":
                self.pdx.PowerLevel = 2
            elif val.lower() == "low":
                self.pdx.PowerLevel = 3
        else:
            raise ValueError("Not a valid power level")
    
    @property
    def connected(self):
        """Returns a bool indicating connection status."""
        return bool(self.pdx.IsConnected())
        
    @property
    def vel_range(self):
        return self.pdx.VelRange
    @vel_range.setter
    def vel_range(self, index):
        """Sets instrument velocity range. Takes an integer index as
        an argument.
        Nominal velocity range should be set to cover the range of the
        velocities anticipated during the deployment. A higher velocity
        range give more noise in the data and vice versa. See the
        User Guide for more information.
        Values are:
            Vector
            0 = 7.0 m/s, 1 = 4.0 m/s, 2 = 2.0 m/s, 3 = 1.0 m/s, 4 = 0.3 m/s,
            5 = 0.1 m/s, 6 = 0.01 m/s
            Vectrino
            0 = 4.0 m/s, 1 = 2.5 m/s, 2 = 1.0 m/s, 3 = 0.3 m/s, 4 = 0.1 m/s,
            5 = 0.03 m/s"""
        self.pdx.VelRange = index
        
    @property
    def coordinate_system(self):
        csi = self.pdx.CoordinateSystem
        if csi == 0: 
            return "ENU"
        elif csi == 1:
            return "XYZ"
        elif csi == 2:
            return "Beam"
    @coordinate_system.setter
    def coordinate_system(self, coordsys):
        """Sets instrument coordinate system. Accepts an int or string."""
        if coordsys.upper() == "ENU":
            ncs = 0
        elif coordsys.upper() == "XYZ":
            ncs = 1
        elif coordsys.upper() == "BEAM":
            ncs = 2
        elif coordsys in [0, 1, 2]:
            ncs = coordsys
        else:
            raise ValueError("Invalid coordinate system selection")
        self.pdx.CoordinateSystem = ncs
    
    def set_config(self):
        """Writes the configuration (properties) to the instrument.
        Note that for most of the property settings to take effect, the 
        SETCONFIG method must be called prior to Start command. See also 
        CONNECT."""
        self.pdx.SetConfig()    
    
    def start(self, brecorder=False):
        """Starts online measurements based on the current configuration
        of the instrument. If :code:`brecorder = True` data is stored to 
        a new file in the recorder."""
        self.pdx.Start(brecorder)
        
    def start_disk_recording(self, filename, autoname=False):
        """Starts data recording to disk. Specify the filename without extension. 
        If autoname = True a new file will be opened for data recording each time 
        the specified time interval has elapsed. The current date and time is then 
        automatically added to the filename."""
        self.pdx.StartDiskRecording(filename, autoname)
    
    def stop_disk_recording(self):
        """Stops data recording to disk."""
        self.pdx.StopDiskRecording()
    
    def disconnect(self):
        """Disconnects device."""
        self.pdx.Disconnect()
    
    def stop(self):
        """Stops data collection."""
        self.pdx.Stop()    
    
    @property
    def prod_conf(self):
        """Returns the hardware configuration structure as a VARIANT array. 
        See the Paradopp system integrators manual for a description of the 
        binary data structures."""
        return self.pdx.GetProdConf()
    
    def get_vel(self, cell, beam):
        """Gets the most recent velocity data for the specified cell and beam
        (m/s). Cell and beam numbering start at 1."""
        return self.pdx.GetVel(cell, beam)
    
    def get_velocity(self, cell):
        """Gets the most recent velocity data for the specified cell number.
        Cell numbering starts at 1."""
        return self.pdx.GetVelocity(cell)
        
    def get_var_velocity(self):
        """Gets the most recent velocity data as a variant type array."""
        return self.pdx.GetVarVelocity

    def get_snr(self, cell, other=1):
        """Gets the most recent SNR data for the specified cell number."""
        return self.pdx.GetSNR(cell, other)
        
    def _sampling_volume_value(self, nSVIndex, nTLIndex):
        """Returns the Sampling Volume corresponding to the Sampling Volume and 
        Transmit Length indices."""
        return self.pdx.SamplingVolumeValue(nSVIndex, nTLIndex)
    
    @property
    def sampling_volume_value(self):
        """Returns the device samping volume value in m."""
        svi = self.pdx.SamplingVolume
        tli = self.pdx.TransmitLength
        return self._sampling_volume_value(svi, tli)

    @property
    def transmit_length_value(self):
        """Returns the device transmit length."""
        tli = self.pdx.TransmitLength
        return self._transmit_length_value(tli)
        
    def _transmit_length_value(self, index):
        """Returns the transmit length value corresponding to the given
        index."""
        return self.pdx.TransmitLengthValue(index)
    
    def get_clock(self):
        """Returns the current date and time of the RTC in the instrument."""
        return self.pdx.GetClock()
           
    def get_corr(self, cell, beam):
        """Returns the most recent correlation data for the specified cell 
        and beam number. Cell and beam numbering start at 1."""
        return self.pdx.GetCorr(cell, beam)
        
    @property
    def instrument(self):
        """Returns the instrument type."""
        return instruments[self.pdx.GetInstrument()]
    
    def get_data_block(self, hType=1):
        """Returns the most recent measurement data structure as a VARIANT array. 
        See the Paradopp system integrators manual for a description of the 
        binary data structures."""
        return self.pdx.GetDataBlock(hType)
        
    @property
    def vertical_vel_prec(self):
        """Returns the vertical velocity precision."""
        return self.pdx.GetVerticalVelPrec()
    
    @property
    def horizontal_vel_prec(self):
        """Returns the horizontal velocity precision."""
        return self.pdx.GetHorizontalVelPrec()
        
    @property
    def last_error_message(self):
        """Gets the most recent error message."""
        return self.pdx.GetErrorMessage()
    
    def start_distance_check(self):
        """Starts distance measurements."""
        self.pdx.StartDistanceCheck()
    
    def validate_config(self):
        """Returns True if the instrument configuration is valid."""
        return bool(self.pdx.ValidateConfig())
    
    @property
    def state(self):
        """Returns the device state. If as_string is false, returns an int."""
        return states[self.pdx.InquireState()]
        
    @property
    def state_index(self):
        return self.pdx.InquireState()

def main():
    vec = PdControl()
    vec.sample_rate = 200
    vec.transmit_length = 1.8
    vec.sampling_volume = 7.0
    print(vec.instrument)
    print(vec.transmit_length_value)
    print(vec.sampling_volume_value)
    vec.coordinate_system = "xyz"
    print(vec.coordinate_system)
    
if __name__ == "__main__":
    main()
