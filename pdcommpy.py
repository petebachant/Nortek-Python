# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 17:16:04 2013

@author: Pete
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
        self.u = self.pdx.u
        self.v = self.pdx.v
        
        # Set connected and state variables
        self.is_connected()
        self.inquire_state()
        
        self.sample_rate = self.pdx.SamplingRate

    class PdEvents(object):
        """OnNewData event handler."""
        def __init__(self):
            self.data = {"t" : np.array([]),
                         "u" : np.array([]),
                         "v" : np.array([]),
                         "w" : np.array([]),
                         "w2" : np.array([]),
                         "snr_u" : np.array([])}
            self.u = 0.0
            self.v = 0.0
            self.w = 0.0
        def append_data(self):
            self.data["u"] = np.append(self.data["u"], self.u)
            self.data["v"] = np.append(self.data["v"], self.v)
            self.data["w"] = np.append(self.data["w"], self.w)
            self.data["corr_u"] = np.append(self.data["corr_u"], self.corr_u)
            self.data["corr_v"] = np.append(self.data["corr_v"], self.corr_v)
#            self.data["w2"] = np.append(self.data["w2"], self.w2)
#            self.data["snr_u"] = np.append(self.data["snr_u"], self.snr_u)
            self.data["t"] = np.arange(len(self.data["u"]))/self.SamplingRate
        def OnNewData(self, hType=1):
#            self.snr = self.GetSNR(1)
            self.u = self.GetVel(1,1)
            self.v = self.GetVel(1,2)
            self.w = self.GetVel(1,3)
#            self.w2 = self.GetVel(2,3)
#            self.snr_u = self.snr[0]
#            self.snr_v = self.snr[1]
#            self.snr_w = self.snr[3]
#            self.snr_w2 = self.snr[4]
            self.corr_u = self.GetCorr(1,1)
            self.corr_v = self.GetCorr(1,2)
            self.corr_w = self.GetCorr(1,3)
            self.corr_w2 = self.GetCorr(1,4)
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
    
    def is_connected(self):
        """Returns a bool indicating connection status."""
        self.connected = bool(self.pdx.IsConnected())
        return self.connected
    
    def set_vel_range(self, velrange):
        """Sets instrument velocity range."""
        self.pdx.VelRange = int(velrange)
        
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
        
    def get_vel_range(self):
        """Returns instrument velocity range."""
        return self.pdx.VelRange
        
    def get_snr(self, cell, other):
        """Gets the most recent SNR data for the specified cell number."""
        return self.pdx.GetSNR(cell, other)
        
    def get_sampling_volume_value(self, nSVIndex, nTLIndex):
        """Returns the Sampling Volume corresponding to the Sampling Volume and 
        Transmit Length indices."""
        return self.pdx.GetSamplingVolumeValue(nSVIndex, nTLIndex)
        
    def get_sampling_volume(self):
        """Returns the device samping volume."""
        return self.pdx.GetSamplingVolume()
    
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
        """Returns the device coordinate system."""
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
    pdcontrol = PdControl()
    pdcontrol.set_serial_port("COM2")
    print pdcontrol.inquire_state()
    pdcontrol.set_sample_rate(200)
    print pdcontrol.get_coordinate_system()