# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 17:16:04 2013

@author: Pete

To-do:
  * Alphabetize functions

"""
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
        # Set connected and state variables
        self.is_connected()
        self.inquire_state()
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
        
    def set_serial_port(self, port):
        """Sets serial port (input as a string)."""
        self.pdx.SerialPort = port
    
    def get_serial_port(self):
        """Get current serial port."""
        return str(self.pdx.SerialPort)
    
    def get_firmware_version(self):
        """Returns the firmware version. Must be called after connect(), which 
        reads the hardware and software configuration from the instrument."""
        return self.pdx.GetFirmwareVersion()
    
    def get_head_serialno(self):
        """Returns the head serial number."""
        return self.pdx.GetHeadSerialNo()
    
    def set_start_on_synch(self, choice):
        self.pdx.StartOnSynch = int(choice)
        
    def set_sample_on_synch(self, choice):
        """Sets sample on synch parameter, meaning device will sample at each
        pulse received."""
        self.pdx.SampleOnSynch = int(choice)
    
    def set_synch_master(self, choice):
        """Set the device as a synch master."""
        self.pdx.SynchMaster = int(choice)
    
    def set_sample_rate(self, rate):
        """Set sample rate in Hz"""
        self.pdx.SamplingRate = rate
        self.sample_rate = self.pdx.SamplingRate
        
    def set_transmit_length(self, index=3):
        """Sets transmit length."""
        self.pdx.TransmitLength = index
        
    def set_sampling_volume(self, index=3):
        """Sets sampling volume."""
        self.pdx.SamplingVolume = index
        
    def set_salinity(self, value=0.0):
        """Sets salinity in ppt."""
        self.pdx.Salinity = value
        
    def set_power_level(self, index=0):
        """Sets the power level according to the index.
        0 = High
        1 = HighLow
        2 = LowHigh
        3 = Low"""
        self.pdx.PowerLevel = index
    
    def is_connected(self):
        """Returns a bool indicating connection status."""
        self.connected = bool(self.pdx.IsConnected())
        return self.connected
    
    def set_vel_range(self, index):
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
        
    def set_coordinate_system(self, coordsys):
        """Sets instrument coordinate system. Accepts an int or string."""
        if coordsys == "ENU":
            ncs = 0
        elif coordsys == "XYZ":
            ncs = 1
        elif coordsys == "Beam":
            ncs = 2
        else:
            ncs = coordsys
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
    
    def get_prod_conf(self):
        """Returns the hardware configuration structure as a VARIANT array. 
        See the Paradopp system integrators manual for a description of the 
        binary data structures."""
        return self.pdx.GetProdConf()
    
    def get_start_on_synch(self):
        """Returns start on synch option value."""
        return bool(self.pdx.StartOnSynch)
    
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
        
    def get_vel_range(self, instrument="Vectrino", as_float=True):
        """Returns instrument velocity range. If as_float, velocity range
        is returned as an instrument dependent float with units (m/s)."""
        if as_float:
            return velranges[instrument][self.pdx.VelRange]
        else:
            return self.pdx.VelRange
            
    def get_power_level(self, as_string=True):
        """Returns the instrument's power level as a string by default
        optionally as integer index."""
        pl = self.pdx.PowerLevel
        if as_string:
            if pl == 0:
                return "High"
            elif pl == 1:
                return "HighLow"
            elif pl == 2:
                return "LowHigh"
            elif pl == 3: 
                return "Low"
        else: return pl
        
    def get_snr(self, cell, other=1):
        """Gets the most recent SNR data for the specified cell number."""
        return self.pdx.GetSNR(cell, other)
        
    def get_salinity(self):
        """Returns salinity value in ppt."""
        return self.pdx.Salinity
        
    def get_sampling_volume_value(self, nSVIndex, nTLIndex):
        """Returns the Sampling Volume corresponding to the Sampling Volume and 
        Transmit Length indices."""
        return self.pdx.SamplingVolumeValue(nSVIndex, nTLIndex)
        
    def get_sampling_volume(self, as_float=True):
        """Returns the device samping volume."""
        svi = self.pdx.SamplingVolume
        tli = self.pdx.TransmitLength
        if as_float:
            return self.get_sampling_volume_value(svi, tli)
        else:
            return svi
        
    def get_transmit_length(self, as_float=True):
        """Returns the device transmit length."""
        tli = self.pdx.TransmitLength
        if as_float:
            return self.get_transmit_length_value(tli)
        else:
            return tli
        
    def get_transmit_length_value(self, index):
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
        
    def get_instrument(self, as_string=True):
        """Returns the instrument type."""
        if as_string:
            return instruments[self.pdx.GetInstrument()]
        else:
            return self.pdx.GetInstrument()
    
    def get_data_block(self, hType=1):
        """Returns the most recent measurement data structure as a VARIANT array. 
        See the Paradopp system integrators manual for a description of the 
        binary data structures."""
        return self.pdx.GetDataBlock(hType)
        
    def get_vertical_vel_prec(self):
        """Returns the vertical velocity precision."""
        return self.pdx.GetVerticalVelPrec()
    
    def get_horizontal_vel_prec(self):
        """Returns the horizontal velocity precision."""
        return self.pdx.GetHorizontalVelPrec()
        
    def get_coordinate_system(self):
        """Returns the device coordinate system as a string."""
        csys = self.pdx.CoordinateSystem
        if csys == 0:
            return "ENU"
        elif csys == 1:
            return "XYZ"
        elif csys == 2:
            return "Beam"
        
    def get_error_message(self):
        """Gets the most recent error message."""
        return self.pdx.GetErrorMessage()
    
    def start_distance_check(self):
        """Starts distance measurements."""
        self.pdx.StartDistanceCheck()
    
    def validate_config(self):
        """Returns True if the instrument configuration is valid."""
        return bool(self.pdx.ValidateConfig())
    
    def inquire_state(self, as_string=True):
        """Returns the device state. If as_string is false, returns an int."""
        if as_string:
            self.state = states[self.pdx.InquireState()]
        else:
            self.state = self.pdx.InquireState()
        return self.state
    

if __name__ == "__main__":
    vec = PdControl()
    vec.set_transmit_length(3)
    vec.set_sampling_volume(3)
    print vec.get_transmit_length()
    print vec.get_sampling_volume()
    vec.set_vel_range(0.5)
    print vec.get_vel_range()
