import os
import re
import nortek.structures
import logging
import pdb
import struct 
import numpy
import math
import matplotlib

class DataFile(dict):
    def __init__(self, filepath, instrument_type="unknown"):
        dict.__init__(self)
        self.instrument_type = instrument_type
        self.filesize = os.path.getsize(filepath)
        self.pathToSource, self.filename = os.path.split(filepath)
        self.filename, self.sourceExtension = os.path.splitext(self.filename)
        self.filepath = filepath
        self.read_header()
        self.read_data(assignToArrays=False)
        self.read_data(assignToArrays=True)
        self.cleanup()

    def reportChecksum(self, instrumentDataFile, id):
        checksumErrorReadPosition = instrumentDataFile.tell() - self[id]._sizeInBytes			
        self.logger.info("Checksum error in file %s at byte %d, structure type is %s", 
                         self.filename, 
                         checksumErrorReadPosition,
                         self._structureName[id])
        instrumentDataFile.seek(checksumErrorReadPosition + 1)

    def read_header(self):
        """Hardware configuration A505
        Head configuration A504
        User configuration A500"""
        with open(self.filepath, 'rb') as instrumentDataFile:
            while True:
                sync = instrumentDataFile.read(1)
                if not sync:
                    break
                elif sync == '\xa5':
                    id = instrumentDataFile.read(1)
                    if id == '\x05':
                        instrumentDataFile.seek(instrumentDataFile.tell() - 2)
                        hardwareConfiguration = nortek.structures.Header(
                                instrumentDataFile.read(48)) # always
                        headConfiguration = nortek.structures.Header(
                                instrumentDataFile.read(224)) # always
                        userConfiguration = nortek.structures.Header(
                                instrumentDataFile.read(512)) # always
                        self.endOfConfiguration = instrumentDataFile.tell()
                        if (hardwareConfiguration.checksum and 
                            headConfiguration.checksum and 
                            userConfiguration.checksum):
                            self[ 'hardwareConfiguration' ] = hardwareConfiguration
                            self[ 'headConfiguration' ] = headConfiguration
                            self[ 'userConfiguration' ] = userConfiguration
                            self[ 'type' ] = self[ 'hardwareConfiguration' ].interpretBinaryData()
                            self[ 'headConfiguration' ].interpretBinaryData(self[ 'type' ])
                            self[ 'userConfiguration' ].interpretBinaryData(self[ 'type' ])
                            break
                        else:
                            pdb.set_trace()
                            # there were problems, try to figure out what
                            print("""Checksum failure in the header. Checksum values are 
								hardware: {}
								head: {}
								user: {}
								Data file position is {}""".format(
									self[ 'hardwareConfiguration' ].checksum,
									self[ 'headConfiguration' ].checksum,
									self[ 'userConfiguration' ].checksum,
									instrumentDataFile.tell()))

    def cleanup(self):
        pass
    
    def exportToMatlabV5(self, matlabFile = None):
        pass

    def exportToMatlabV7p3(self, matlabFile = None):
        pass

    def exportToHDF5(self, hdf5File = None):
        pass

    def truncateDatasetBasedOnTimeRange(self, timeRange = (None,)):
        if len(timeRange) is not 1 and 'time' in self and 'velocity' in self:
            if 'goodIndices' not in self[ 'velocity' ]:
                self[ 'velocity' ][ 'goodIndices' ] = numpy.isfinite(self[ 'velocity' ][ 'data' ])
                self[ 'velocity' ][ 'goodIndices' ][ :,
                numpy.logical_or(self[ 'time' ] <= timeRange[ 0 ],
                                 self[ 'time' ] >= timeRange[ 1 ]), : ] = False

class VectrinoFile(DataFile):
    instrument_type = 'Vectrino'
    _structureName = {'\x51': 'Velocity Data',
                      '\x0f': 'File Info',
                      '\x07': 'Probe Check',
                      '\x02': 'Distance Measurement',
                      '\x50': 'Velocity Header'}
    _plotStyles = {'colors': { 0: 'black', 1: 'red', 2: 'green', 3: 'blue' },
                   'markers': { 0: '^', 1: '^', 2: '^', 3: '^' } }

    def read_data(self, assignToArrays = False):
        if assignToArrays is False:
            self[ '\x50' ] = nortek.structures.VectrinoVelocityHeader_binary()
            self[ '\x51' ] = nortek.structures.VectrinoVelocityData_binary()
            self[ '\x07' ] = nortek.structures.VectrinoProbeCheck_binary()
            self[ '\x0f' ] = nortek.structures.VectrinoFileInfo_binary()
            self[ '\x02' ] = nortek.structures.VectrinoDistanceMeasurement_binary()
        else:
            self['\x51'].allocateDataArrays(self)
            self['\x07'].allocateDataArrays(self)
            self['\x02'].allocateDataArrays(self)

        with open(os.path.join(self.pathToSource, self.filename + self.sourceExtension), 'rb') as instrumentDataFile:
            instrumentDataFile.seek(self.endOfConfiguration)
            while True:
                sync = instrumentDataFile.read(1)
                if not sync:
                    break
                elif sync == '\xa5':
                    id = instrumentDataFile.read(1)
                    if not id:
                        break
                    elif id in self._structureName:
                        if (instrumentDataFile.tell() + self[ id ]._sizeInBytes - 2) < self.filesize:
                            self[ id ]._structureStart = instrumentDataFile.tell() - 2
                            self[ id ]._structureStop = self[ id ]._structureStart + self[ id ]._sizeInBytes
                            instrumentDataFile.readinto(self[ id ])
                            if not self[ id ].calculateChecksum(instrumentDataFile):
                                if not assignToArrays: # only report these on the first pass
                                    self.reportChecksum(instrumentDataFile, id)
                            elif not assignToArrays:
                                self[ id ].incrementCounters()
                            elif assignToArrays:
                                self[ id ].moveIntoDataArrays(self)
            if assignToArrays and 'velocityHeader' in self:
                for beamNumber in range(4):
                    self[ 'snr' ][ 'data' ][ :, :, beamNumber ] = \
                    20 * numpy.log10(self[ 'amplitude' ][ 'data' ][ :, :, beamNumber ]) \
                    - numpy.log10(self[ 'velocityHeader' ][ 'noise' ][ 'amplitude' ][ beamNumber + 1 ])

    def cleanup(self):
        for key in ('\x51', '\x0f', '\x07', '\x02', '\x50'):
            if key in self:
                self.pop(key, None)

    def plotDataAgainstEnsemble(self, dataType = 'velocity'):
        if dataType in self:
            matplotlib.pyplot.figure(self.filename + " " + dataType)
            ensembleFrame = matplotlib.pyplot.subplot()
            for beamNumber in range(0, 4, 1):
                matplotlib.pyplot.plot(self[ 'ensemble' ], 
                                       self[ dataType ][ 'data' ][ :, :, beamNumber ].flatten(),
                                       color = self._plotStyles[ 'colors' ][ beamNumber ])
            ensembleFrame.set_xlim(self[ 'ensemble' ][ 0 ], self[ 'ensemble' ][ -1 ])
            ensembleFrame.grid(True)
            matplotlib.pyplot.show()

class AD2CP(DataFile):
	instrument_type = 'AD2CP'
	_structureName = {'\x15': 'Burst Data Record',
					  '\x16': 'Current Profile Data Record',
					  '\xa0': 'String Data Record' }
	
	def __init__(self, filepath = None):
		UserDict.UserDict.__init__(self)
		self.logger = logging.getLogger("Nortek." + self.instrument_type)
		self.sourceReachable = False
		if filepath:
			try:    
				with open(filepath, 'rb') as sourceDataFile:
					self.sourceReachable = True
					self.filesize = os.path.getsize(filepath)
					self.pathToSource, self.filename = os.path.split(filepath)
					self.filename, self.sourceExtension = os.path.splitext(self.filename)
				
					self.logger.info('Reading data for %s from file %s', self.instrument_type, self.filename)
					self.read_header(assignToArrays = False)
					self.read_header(assignToArrays = True)
			except EnvironmentError as error:
				self.logger.error("Looking for file %s, received error: " % error.filename + error.strerror)
		else:
			self.logger.error('No source file specified.')

	def read_header(self, assignToArrays = False):
		# each data record has it's own header
		with open(os.path.join(self.pathToSource, self.filename + self.sourceExtension), 'rb') as instrumentDataFile:
			while True:
				sync = instrumentDataFile.read(1)
				if not sync:
					break
				elif sync == '\xa5':
					sizeOfHeader = instrumentDataFile.read(1)
					sizeOfHeader = struct.unpack('<B', sizeOfHeader)
					self.sizeOfHeader = sizeOfHeader[ 0 ]
					if self.sizeOfHeader > 10:
						continue
					instrumentDataFile.seek(-2, 1)
					dataRecordHeader = nortek.structures.AD2CPHeader(
							instrumentDataFile.read(self.sizeOfHeader))
					dataRecordHeader[ 'version' ] = struct.unpack('<B', 
							instrumentDataFile.read(1))
					dataRecordHeader[ 'version' ] = dataRecordHeader[ 'version' ][ 0 ]
					instrumentDataFile.seek(-1, 1)
					numberOfBeams, numberOfCells = self.read_data(
															 instrumentDataFile,
															 dataRecordHeader[ 'id' ], 
															 dataRecordHeader[ 'version' ],
															 dataRecordHeader[ 'sizeInBytes' ],
															 dataRecordHeader[ 'checksum' ],
															 assignToArrays)

	def read_data(self, instrumentDataFile, 
								  id, 
								  version, 
								  sizeInBytes, 
								  checksum, 
								  assignToArrays = False):
		if assignToArrays is False and id not in self:
			binaryStructureGenerator = nortek.structures.generateAD2CP_DataRecord_binary(
				version,
				sizeInBytes)
			self[ id ] = binaryStructureGenerator()
		elif assignToArrays is True and not self[ id ].arraysAllocated:
			self[ id ].allocateDataArrays(version, self)

		if (instrumentDataFile.tell() + self[ id ]._sizeInBytes) < self.filesize:
			self[ id ]._structureStart = instrumentDataFile.tell() - self.sizeOfHeader
			self[ id ]._structureStop = self[ id ]._structureStart + self[ id ]._sizeInBytes + self.sizeOfHeader
			self[ id ].checksum = checksum
			instrumentDataFile.seek(self[ id ]._structureStop)
			if not self[ id ].calculateChecksum(instrumentDataFile):
				if not assignToArrays: # only report these on the first pass
					self.reportChecksum(instrumentDataFile, id)
			elif not assignToArrays:
				if self[ id ].ensembleCounter == 0:
					instrumentDataFile.seek(self[ id ]._structureStart + self.sizeOfHeader)
					instrumentDataFile.readinto(self[ id ])
					instrumentDataFile.seek(self[ id ]._structureStop)
					self[ id ].numberOfBeams = self[ id ].cellsCSbeams.numberOfBeams
					self[ id ].numberOfCells = self[ id ].cellsCSbeams.numberOfCells
				self[ id ].incrementCounters()
			elif assignToArrays:
				# grab the configuration and other ancillary data
				instrumentDataFile.seek(self[ id ]._structureStart + self.sizeOfHeader)
				instrumentDataFile.readinto(self[ id ])
				# now generate the data Structure
				dataBlockGenerator = nortek.structures.generateAD2CP_DataBlock_binary(
					self[ id ].configuration,
					self[ id ].cellsCSbeams.numberOfBeams,
					self[ id ].cellsCSbeams.numberOfCells) 
				dataBlock = dataBlockGenerator()
				instrumentDataFile.readinto(dataBlock)
				instrumentDataFile.seek(self[ id ]._structureStop)
				self[ id ].moveIntoDataArrays(version, dataBlock, self)
		else:
			logging.info('Truncated %s structure at file position %d.', self._structureName[ id ], instrumentDataFile.tell() - 2)

		return self[ id ].cellsCSbeams.numberOfBeams, self[ id ].cellsCSbeams.numberOfCells

	def cleanup(self):
		self.pop("\x15", None)
		self.pop("\x16", None)
		self.pop("\xa0", None)	

	def generateTransform_xyz(self):
		if 'datasetDescription' in self:
			beamVectorsSpherical = {}
			beamConfigurationRE = re.compile(
			 "BEAM=(?P<beamNumber>\d{1}),THETA=(?P<theta>-?\d{1,2}\.\d{1,2}),PHI=(?P<phi>-?\d{1,3}\.\d{1,2}),FREQ=(?P<frequency>\d{2,4})")
			with open(os.path.join(os.path.dirname(__file__), 'aquadoppII.cfg')) as ad2cp_beamConfig_FID:
				for line in ad2cp_beamConfig_FID:
					configMatch = beamConfigurationRE.search(line)
					if configMatch:
						beamVectorsSpherical[ int(configMatch.groupdict()[ 'beamNumber' ]) ] = \
						[ 1, 
							float(configMatch.groupdict()[ 'theta' ]) * numpy.pi / 180., 
							float(configMatch.groupdict()[ 'phi' ]) * numpy.pi / 180. ]
			# determine the number of active beams and create an empty matrix of the appropriate size
			numberOfBeams = len(self[ 'datasetDescription' ])
			beamVectorsCartesian = numpy.ndarray((numberOfBeams, numberOfBeams))
			for dataBeamNumber in self[ 'datasetDescription' ]:
				beamNumber = self[ 'datasetDescription' ][ dataBeamNumber ]
				if numberOfBeams is 4 and (beamNumber is 1 or beamNumber is 3):
					beamVectorsCartesian[ dataBeamNumber, : ] = [
						beamVectorsSpherical[ beamNumber ][ 0 ] * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 1 ]) * 
							math.cos(beamVectorsSpherical[ beamNumber ][ 2 ]), 
						beamVectorsSpherical[ beamNumber ][ 0 ] * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 1 ]) * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 2 ]),
						beamVectorsSpherical[ beamNumber ][ 0 ] * math.cos(beamVectorsSpherical[ beamNumber ][ 1 ]),
						0 ]
				if numberOfBeams is 4 and (beamNumber is 2 or beamNumber is 4):
					beamVectorsCartesian[ dataBeamNumber, : ] = [
						beamVectorsSpherical[ beamNumber ][ 0 ] * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 1 ]) * 
							math.cos(beamVectorsSpherical[ beamNumber ][ 2 ]), 
						beamVectorsSpherical[ beamNumber ][ 0 ] * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 1 ]) * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 2 ]),
						0,
						beamVectorsSpherical[ beamNumber ][ 0 ] * math.cos(beamVectorsSpherical[ beamNumber ][ 1 ]) ]
				#	this is for a single vertical velocity with three beams
				if numberOfBeams is 3:
					beamVectorsCartesian[ dataBeamNumber, : ] = [
						beamVectorsSpherical[ beamNumber ][ 0 ] * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 1 ]) * 
							math.cos(beamVectorsSpherical[ beamNumber ][ 2 ]), 
						beamVectorsSpherical[ beamNumber ][ 0 ] * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 1 ]) * 
							math.sin(beamVectorsSpherical[ beamNumber ][ 2 ]),
						beamVectorsSpherical[ beamNumber ][ 0 ] * math.cos(beamVectorsSpherical[ beamNumber ][ 1 ]) ]
			self.T = T()
			self.T.xyz2beam = numpy.matrix(beamVectorsCartesian)
			self.T.xyz2beam[ self.T.xyz2beam < 1e-15 ] = 0.0
			self.T.beam2xyz = numpy.matrix(numpy.linalg.pinv(beamVectorsCartesian))
			self.T.beam2xyz[ self.T.beam2xyz < 1e-15 ] = 0.0
		else:
			logging.warning('No mapping between physical beams and dataset provided. No coordinate transformation possible.')

	def generateTransform_XYZ(self):
		# generate the beam2xyz matrices
		self.generateTransform_xyz()
		# permute the beam2xyz matrix to get the beam2XYZ matrix
		numberOfBeams = len(self[ 'datasetDescription' ])
		if self.orientation is 'XUP':
			permutationMatrix = numpy.matrix(numpy.zeros((numberOfBeams, numberOfBeams)))
			# x becomes Z
			permutationMatrix[ 0, 2 ] = 1
			# y becomes -Y
			permutationMatrix[ 1, 1 ] = -1
			# z1 and z2 become X, only z1 shifted since this is usually a three beam system
			permutationMatrix[ 2, 0 ] = 1
			self.T.beam2XYZ = permutationMatrix * self.T.beam2xyz
			self.T.XYZ2beam = numpy.linalg.pinv(self.T.beam2XYZ)
		if self.orientation is 'XDOWN':
			permutationMatrix = numpy.matrix(numpy.zeros((numberOfBeams, numberOfBeams)))
			# x becomes -Z
			permutationMatrix[ 0, 2 ] = -1
			# y becomes Y
			permutationMatrix[ 1, 1 ] = 1
			# z1 and z2 become X, only z1 shifted since this is usually a three beam system
			permutationMatrix[ 2, 0 ] = 1
			self.T.beam2XYZ = permutationMatrix * self.T.beam2xyz
			self.T.XYZ2beam = numpy.linalg.pinv(self.T.beam2XYZ)
		if self.orientation is 'ZDOWN':
			permutationMatrix = numpy.matrix(numpy.zeros((numberOfBeams, numberOfBeams)))
			# x becomes X
			permutationMatrix[ 0, 0 ] = 1
			# y becomes -Y
			permutationMatrix[ 1, 1 ] = -1
			# z1 and z2 become -Z
			permutationMatrix[ 2, 2 ] = -1
			if numberOfBeams == 4:
				permutationMatrix[ 3, 3 ] = -1
			self.T.beam2XYZ = permutationMatrix * self.T.beam2xyz
			self.T.XYZ2beam = numpy.linalg.pinv(self.T.beam2XYZ)
		else:
			logging.warning('Orientation unknown, check the status message.')
			
class HRProfiler(DataFile):
	instrument_type = 'HR Profiler'
	_structureName = {'\x2a': 'HR Profiler Data' }
	
	def read_data(self, assignToArrays = False):
		if assignToArrays is False:
			binaryStructureGenerator = nortek.structures.generateHRProfiler_DataRecord_binary(
				self[ 'userConfiguration' ][ 'numberOfBeams' ],
				self[ 'userConfiguration' ][ 'numberOfCells' ])
			self[ '\x2a' ] = binaryStructureGenerator()
			self[ '\x2a' ].setSizeInBytes()
		else:
			self[ '\x2a' ].allocateDataArrays(self)
			
		with open(os.path.join(self.pathToSource, self.filename + self.sourceExtension), 'rb') as instrumentDataFile:
			instrumentDataFile.seek(self.endOfConfiguration)
			while True:
				sync = instrumentDataFile.read(1)
				if not sync:
					break
				elif sync == '\xa5':
					id = instrumentDataFile.read(1)
					if not id:
						break
					elif id in self._structureName:
						if (instrumentDataFile.tell() + self[ id ]._sizeInBytes - 2) < self.filesize:
							self[ id ]._structureStart = instrumentDataFile.tell() - 2
							self[ id ]._structureStop = self[ id ]._structureStart + self[ id ]._sizeInBytes
							# set FID to read checksum
							instrumentDataFile.seek(self[ id ]._structureStop - 2)
							self[ id ].checksum = struct.unpack('<H', instrumentDataFile.read(2))
							self[ id ].checksum = self[ id ].checksum[ 0 ]
							#pdb.set_trace()
							if not self[ id ].calculateChecksum(instrumentDataFile):
								pdb.set_trace()
								if not assignToArrays: # only report these on the first pass
									self.reportChecksum(instrumentDataFile, id)
							elif not assignToArrays:
								self[ id ].incrementCounters()
							elif assignToArrays:
								instrumentDataFile.seek(self[ id ]._structureStart + 2)
								instrumentDataFile.readinto(self[ id ])
								self[ id ].moveIntoDataArrays(self)
								instrumentDataFile.seek(self[ id ]._structureStop)
							#pdb.set_trace()
						else:
							logging.info('Truncated %s structure at file position %d.', self._structureName[ id ], instrumentDataFile.tell() - 2)


	def cleanup(self):
		pass

class T (object):
	pass
	# empty class to hold the transformation matrices