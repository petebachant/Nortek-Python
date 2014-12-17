# contains C-style struct definitions and associated methods for various Nortek instruments
# The base class is "NortekDataStructure" which is itself a subclass of ctypes.Structure
# Individual data structures (e.g. velocity header) are a subclass of NortekDataStructure
# They will inherit the calculateChecksum method from NortekDataStructure and need to define
#
# 
from ctypes import *
import UserDict
import struct
import re
import numpy
import pdb
from nortek import arrays as NortekDataArrays
import datetime
import pylab
import logging

moduleLogger = logging.getLogger( "Nortek." + __name__ )


class BCDTimeWord( Structure ):
	_fields_ = [ ( "minute", c_ubyte ),
				 ( "second", c_ubyte ),
				 ( "hour", c_ubyte ),
				 ( "year", c_ubyte ),
				 ( "month", c_ubyte ),
				 ( "day", c_ubyte ) ]

class Header( UserDict.UserDict ):
	def __init__( self, binaryDataString ):
		UserDict.UserDict.__init__( self )
		self.binaryData = binaryDataString
		self.length = len( self.binaryData ) - 2
		self.calculateChecksum()
		if self.checksum:
			self.interpretBinaryData()
			
	def calculateChecksum( self ):
		if self.length >= 4:
			reportedChecksum = struct.unpack( '<H', self.binaryData[ -2: ] )
			checksumFormatString = '<' + 'h' * ( self.length / 2 )
			if struct.calcsize( checksumFormatString ) == self.length:
				calculatedChecksum = ( int( 'b58c', base = 16 ) 
											+ sum( struct.unpack( checksumFormatString,
										self.binaryData[ 0:-2 ] ) ) ) % 65536
			else:
				self.checksum = False
			if calculatedChecksum != reportedChecksum[ 0 ]:
				self.checksum = False
			else:
				self.checksum = True
		else:
			self.checksum = False

	def interpretBinaryData( self, instrumentType = None ):
		if self.binaryData[ 0:2 ] == '\xa5\x05':
			# Hardware Configuration
			syncByte, \
			dataStructureID, \
			sizeInWords, \
			self[ 'serialNumber' ], \
			boardConfigurationBit0, \
			boardConfigurationBit1, \
			self[ 'systemFrequency' ], \
			self[ 'picVersion' ], \
			self[ 'hardwareRevision' ], \
			self[ 'recorderSize' ], \
			hardwareStatus, \
			spareWords, \
			self[ 'firmwareVersion' ] = \
			struct.unpack( '<ccH14sBBHHHHH12s4s', self.binaryData[ 0:-2 ] )
			
			self[ 'serialNumber' ] = self[ 'serialNumber' ].rstrip()
			if ( re.search( 'VNO', self[ 'serialNumber' ] ) ):
				instrumentType = 'Vectrino'
			elif ( re.search( 'VEC', self[ 'serialNumber' ] ) ):
				instrumentType = 'Vector'
			elif ( re.search( 'AQD', self[ 'serialNumber' ] ) ):
				#if ( re.search( 'HR', self[ 'firmwareVersion' ] ) ):
				if ( float( self[ 'firmwareVersion' ] ) < 3.3 ):
					instrumentType = 'HR Profiler'
				else:
					instrumentType = 'Aquadopp Profiler'
			elif ( re.search( 'WPR', self[ 'hardwareConfiguration' ][ 'serialNumber' ] ) ):
				instrumentType = 'AWAC'
			else:
				instrumentType = 'unknown'
				
			if instrumentType is not 'Vectrino':
				if boardConfigurationBit0:
					# if True, there's a recorder
					self[ 'recorderInstalled' ] = True
				else:
					self[ 'recorderInstalled' ] = False
					self[ 'recorderSize' ] = 0
				if boardConfigurationBit1:
					# if True, there's a compass
					self[ 'compassInstalled' ] = True
				else:
					self[ 'compassInstalled' ] = False
			return instrumentType
			
		elif self.binaryData[ 0:2 ] == '\xa5\x04':
			# head configuration
			syncByte, \
			dataStructureID, \
			sizeInWords, \
			headConfiguration, \
			self[ 'frequency' ], \
			self[ 'headType' ], \
			self[ 'serialNumber' ], \
			systemData1, \
			tempT, \
			systemData2, \
			distanceToSampleVolume, \
			spareWords, \
			self[ 'numberOfBeams' ] = \
			struct.unpack( '<ccHHHH12s8s32s136sH20sH', self.binaryData[ 0:-2 ] )
			if instrumentType is 'Vectrino':
				tempT = struct.unpack( '<16h', tempT )
				self[ 'transformationMatrix' ] = \
					numpy.matrix( numpy.reshape( tempT, ( 4, 4 ) ) ) / 4096.0
				self[ 'distanceToSampleVolume' ] = \
					round( 10 * 0.5 * ( ( 1.5 * distanceToSampleVolume )**2 - 622.98 ) 
						/ ( 1.5 * distanceToSampleVolume - 5.7 ) ) / 10
		elif self.binaryData[ 0:2 ] == '\xa5\x00':
			# User Configuration
			syncByte, \
			dataStructureID, \
			sizeInWords, \
			self[ 'T1' ], \
			self[ 'T2' ], \
			self[ 'T3' ], \
			self[ 'T4' ], \
			self[ 'T5' ], \
			self[ 'numberOfPings' ], \
			self[ 'averageInterval' ], \
			self[ 'numberOfBeams' ], \
			timingControlRegister, \
			powerControlRegister, \
			self[ 'A1' ], \
			self[ 'B0' ], \
			self[ 'B1' ], \
			self[ 'compassUpdateRate' ], \
			coordinateSystem, \
			self[ 'numberOfCells' ], \
			cellSize, \
			self[ 'measurementInterval' ], \
			self[ 'deploymentName' ], \
			self[ 'recorderWrapMode' ], \
			self[ 'deploymentStartTime' ], \
			self[ 'diagnosticMeasurement_sampleInterval' ], \
			modeWord, \
			self[ 'soundSpeedAdjustmentFactor' ], \
			self[ 'dianosticMeasurement_numberOfSamples' ], \
			self[ 'diagnosticMeasurementnumberOfBeamsOrCellNumber' ], \
			self[ 'diagnosticMeasurement_NumberOfPings' ], \
			modeTestWord, \
			analogInputAddress, \
			hVersion, \
			spareWords, \
			velocityAdjustmentTable, \
			self[ 'comments' ], \
			self[ 'waveMeasurement_mode' ], \
			self[ 'waveMeasurement_waveCellPositionPercent' ], \
			self[ 'wave_T1' ], \
			self[ 'wave_T2' ], \
			self[ 'wave_T3' ], \
			self[ 'wave_numberOfSamples' ], \
			self[ 'A1_2' ], \
			self[ 'B0_2' ], \
			self[ 'B1_2' ], \
			spareWords2, \
			self[ 'analogOutputScaleFactor' ], \
			self[ 'ambiguityResolutionCorrelationThreshold' ], \
			spareWords3, \
			self[ 'transmitPulseLengthSecondLag_counts' ], \
			spareWords3, \
			self[ 'stageMatchFilterConstants' ] = \
			struct.unpack( '<cc' + 'H' * 19 + '6sH6sL' + 'H' * 9 + '180s' * 2 + 'H' * 14 + '30s16s', self.binaryData[ 0:-2 ] )
			
			timingControlRegister = '{:016b}'.format( timingControlRegister )[ ::-1 ]
			powerControlRegister = '{:016b}'.format( powerControlRegister )[ ::-1 ]
			modeWord = '{:016b}'.format( modeWord )[ ::-1 ]
			if timingControlRegister[ 5:7 ] == '00' and powerControlRegister[ 5:7 ] == '00':
				self[ 'powerLevel' ] = 'High'
			elif timingControlRegister[ 5:7 ] == '10' and powerControlRegister[ 5:7 ] == '10':
				self[ 'powerLevel' ] = 'High-'
			elif timingControlRegister[ 5:7 ] == '01' and powerControlRegister[ 5:7 ] == '01':
				self[ 'powerLevel' ] = 'LOW+'
			elif timingControlRegister[ 5:7 ] == '11' and powerControlRegister[ 5:7 ] == '11':
				self[ 'powerLevel' ] = 'LOW'
			
			if timingControlRegister[ 1 ] is '1':
				self[ 'sampleMode' ] = 'burst'
			else:
				self[ 'sampleMode' ] = 'continuous'
				
			if coordinateSystem == 0:
				self[ 'coordinateSystem' ] = 'ENU'
			elif coordinateSystem == 1:
				self[ 'coordinateSystem' ] = 'XYZ'
			else:
				self[ 'coordinateSystem' ] = 'Beam'
			
			if instrumentType is 'Vectrino':
				self[ 'sampleRate' ] = round( 50000.0 / self[ 'averageInterval' ] )
				del self[ 'averageInterval' ]
			elif instrumentType is 'Vector':
				self[ 'sampleVolumeSize' ] = cellSize
				self[ 'sampleRate' ] = 512. / self[ 'averageInterval' ]
			elif instrumentType is 'HR Profiler':
				self[ 'sampleRate' ] = 512. / self[ 'T5' ]
			
			if instrumentType is not 'Vectrino':
				self[ 'cellSize' ] = cellSize
			else:
				self[ 'sampleVolumeSize' ] = cellSize
				
			if instrumentType is 'Vector' or 'HR Profiler':
				if modeWord[ 4 ] is '1':
					self[ 'velocityScaling' ] = 0.1 # mm/s
				else:
					self[ 'velocityScaling' ] = 1 # mm/s

			formattedSoftwareVersion = str( hVersion/10000 ) + "." + str( (hVersion % 10000)/100 )
			if str(hVersion % 100):
				formattedSoftwareVersion + "." + str(hVersion % 100)
			self[ 'softwareVersion' ] = formattedSoftwareVersion
			
class NortekBinaryDataStructure( Structure ):
	_structureStart = 0
	_structureStop = 0
	
	def calculateChecksum( self, openDataFile ):
		originalPosition = openDataFile.tell()
		openDataFile.seek( originalPosition - self._sizeInBytes )
		checksumDataType = c_short * ( self._sizeInBytes / 2 - 1 )
		checksumData = checksumDataType()
		openDataFile.readinto( checksumData )
		openDataFile.seek( originalPosition )
		calculatedChecksum = int( 'b58c', base = 16 )
		for aShort in checksumData:
			calculatedChecksum += aShort
		self.calculatedChecksum = calculatedChecksum % 65536
		if self.checksum == self.calculatedChecksum:
			self.checksumResult = True
			return True
		else:
			self.checksumResult = False
			return False

	def incrementCounters( self ):
		pass		

	def resetCounters( self ):
		pass
		
	def allocateDataArrays( self, anInstrument ):
		pass
		
	def moveIntoDataArrays( self, anInstrument ):
		pass
	
class VectrinoVelocityData_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "status", c_char ),
				 ( "count", c_ubyte ),
				 ( "velocity", c_short * 4 ),
				 ( "amplitude", c_ubyte * 4 ),
				 ( "correlation", c_ubyte * 4 ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 22
	ensembleCounter = 0
	ensembleCycleCounter = 0
	
	def incrementCounters( self ):
		if self.ensembleCounter > 1 and self.count == 0:
			self.ensembleCycleCounter += 1
		self.ensembleCounter = self.ensembleCycleCounter * 255 + self.count + self.ensembleCycleCounter
# 		moduleLogger.info( 'Counter is {} and ensemble is {}'.format( 
# 			self.count,
# 			self.ensembleCounter ) )
		#self.ensembleCounter += 1
		#while self.ensembleCounter != self.ensembleCycleCounter * 255 + self.count:
		#	self.ensembleCounter += 1
	
	def resetCounters( self ):
		self.ensembleCounter = 0
		self.ensembleCycleCounter = 0
		
	def allocateDataArrays( self, vectrinoInstrument ):
		samepleRate = vectrinoInstrument[ 'userConfiguration' ][ 'sampleRate' ]
		vectrinoInstrument[ 'velocity' ] = NortekDataArrays.VelocityDataArray( 
			samepleRate,
			shape = ( 1, self.ensembleCounter, 4 ) )
		vectrinoInstrument[ 'amplitude' ] = NortekDataArrays.GenericDataArray( 
			samepleRate,
			shape = ( 1, self.ensembleCounter, 4 ) )
		vectrinoInstrument[ 'snr' ] = NortekDataArrays.GenericDataArray( 
			samepleRate,
			shape = ( 1, self.ensembleCounter, 4 ) )
		vectrinoInstrument[ 'correlation' ] = NortekDataArrays.GenericDataArray( 
			samepleRate,
			shape = ( 1, self.ensembleCounter, 4 ) )
		vectrinoInstrument[ 'ensemble' ] = numpy.arange( 0, self.ensembleCounter, 1 )
		self.resetCounters()
		
	def moveIntoDataArrays( self, vectrinoInstrument ):
		try:
			vectrinoInstrument[ 'velocity' ][ 'data' ][ 0, self.ensembleCounter, : ] = self.velocity[ 0:4 ]
			vectrinoInstrument[ 'amplitude' ][ 'data' ][ 0, self.ensembleCounter, : ] = self.amplitude[ 0:4 ]
			vectrinoInstrument[ 'correlation' ][ 'data' ][ 0, self.ensembleCounter, : ] = self.correlation[ 0:4 ]
			self.incrementCounters()
		except IndexError as error:
			pdb.set_trace()
			
class VectrinoFileInfo_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "sizeInWords", c_short ),
				 ( "field1", c_short ),
				 ( "field2", c_short ),
				 ( "field3", c_short ),
				 ( "fileInfo", c_char * 14 ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 26
	fileInfoCounter = 0
	
class VectrinoVelocityHeader_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "sizeInWords", c_short ),
				 ( "distance", c_short ),
				 ( "distanceQuality", c_short ),
				 ( "lag1", c_short ),
				 ( "lag2", c_short ),
				 ( "noise", c_ubyte * 4 ),
				 ( "correlation", c_ubyte * 4 ),
				 ( "temperature", c_short ),
				 ( "speedOfSound", c_short ),
				 ( "samplingVolumeAmplitude", c_ubyte * 4 ),
				 ( "boundaryAmplitude", c_ubyte * 4 ),
				 ( "z0PlusLag1", c_ubyte * 4 ),
				 ( "z0PlusLag2", c_ubyte * 4 ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 42
	velocityHeaderCounter = 0
	
	def moveIntoDataArrays( self, vectrinoInstrument ):
			vectrinoInstrument[ 'velocityHeader' ] = {}
			vectrinoInstrument[ 'velocityHeader' ][ 'noise' ] = { 'amplitude': {}, 'correlation': {} }
			vectrinoInstrument[ 'velocityHeader' ][ 'distance' ] = {}
			vectrinoInstrument[ 'velocityHeader' ][ 'sampleVolumeAmplitude' ] = {}
			vectrinoInstrument[ 'velocityHeader' ][ 'boundaryAmplitude' ] = {}
			# Vectrino velocity data header
			vectrinoInstrument[ 'distance' ][ 'measurement' ] = self.distance
			vectrinoInstrument[ 'distance' ][ 'quality' ] = self.distanceQuality
			vectrinoInstrument[ 'velocityHeader' ][ 'lag1' ] = self.lag1 / 1e6
			vectrinoInstrument[ 'velocityHeader' ][ 'lag2' ] = self.lag2 / 1e6
			for beamNumber in range( 1, 5, 1 ):
				vectrinoInstrument[ 'velocityHeader' ][ 'noise' ][ 'amplitude' ][ beamNumber ] \
					= self.noise[ beamNumber - 1 ]
				vectrinoInstrument[ 'velocityHeader' ][ 'noise' ][ 'correlation' ][ beamNumber ] \
					= self.correlation[ beamNumber - 1 ]
				vectrinoInstrument[ 'velocityHeader' ][ 'sampleVolumeAmplitude' ][ beamNumber ] \
					= self.samplingVolumeAmplitude[ beamNumber - 1 ]
				vectrinoInstrument[ 'velocityHeader' ][ 'boundaryAmplitude' ][ beamNumber ] \
					= self.boundaryAmplitude[ beamNumber - 1 ]
	
class VectrinoProbeCheck_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "sizeInWords", c_short ),
				 ( "samplesPerBeam", c_short ),
				 ( "firstSampleNumber", c_short ),
				 ( "bermudaShorts", c_short * 3 ),
				 ( "amplitude", c_ubyte * 512 * 4 ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 1032 * 2
	probeCheckCounter = 0
		
	def incrementCounters( self ):
		self.probeCheckCounter += 1
	
	def resetCounters( self ):
		self.probeCheckCounter = 0
		
	def allocateDataArrays( self, vectrinoInstrument ):
		vectrinoInstrument[ 'probeCheck' ] = {}
		vectrinoInstrument[ 'probeCheck' ][ 'amplitude' ] = numpy.zeros( ( 4, self.samplesPerBeam, self.probeCheckCounter ) )
		self.resetCounters()
		
	def moveIntoDataArrays( self, vectrinoInstrument ):
		for beamNumber in range( 0, 4, 1 ):
			vectrinoInstrument[ 'probeCheck' ][ 'amplitude' ][ beamNumber, :, self.probeCheckCounter ] = \
				self.amplitude[ beamNumber ][ : ]
		self.generateDistances( vectrinoInstrument, vectrinoInstrument[ '\x50' ].speedOfSound )
		self.incrementCounters()
		
	def generateDistances( self, vectrinoInstrument, speedOfSound = 1500.0 ):
		dVertDist = 5.7 # mm
		dHorzDist = 24.3 # mm
		dSoundSpeed = 1500.0 # m/s
		dCountToDist = dSoundSpeed / 1000.0
		dDist2 = dHorzDist * dHorzDist + dVertDist * dVertDist
		dMinDist = numpy.sqrt( dDist2 )
		dConst = dHorzDist * dHorzDist - dVertDist * dVertDist
		dTotalDist = dCountToDist * numpy.arange( 0, self.samplesPerBeam, 1 )
		dSampleDist = 0.5 * ( dTotalDist * dTotalDist - dDist2 ) / \
							  ( dTotalDist - dVertDist )
		dSampleDist[ dTotalDist < dMinDist ] = numpy.nan
		vectrinoInstrument[ 'probeCheck' ][ 'distance' ] = dSampleDist
		
class VectrinoDistanceMeasurement_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "sizeInWords", c_short ),
				 ( "temperature", c_short ),
				 ( "speedOfSound", c_short ),
				 ( "distance", c_short ),
				 ( "quality", c_short ),
				 ( "spare", c_short ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 16
	distanceCounter = 0
		
	def incrementCounters( self ):
		self.distanceCounter += 1
	
	def resetCounters( self ):
		self.distanceCounter = 0
		
	def allocateDataArrays( self, vectrinoInstrument ):
		vectrinoInstrument[ 'distance' ] = {}
		vectrinoInstrument[ 'distance' ][ 'fromProbe' ] = numpy.zeros( ( self.distanceCounter, ) )
		vectrinoInstrument[ 'distance' ][ 'quality' ] = numpy.zeros( ( self.distanceCounter, ) )
		self.resetCounters()
		
	def moveIntoDataArrays( self, vectrinoInstrument ):
		vectrinoInstrument[ 'distance' ][ 'fromProbe' ][ self.distanceCounter ] = \
				self.distance / 10.0
		vectrinoInstrument[ 'distance' ][ 'quality' ][ self.distanceCounter ] = \
				self.quality
		self.incrementCounters()

class AD2CPHeader( Header ):
	def interpretBinaryData( self, instrumentType = None ):
		self[ 'id' ], \
		instrumentFamily, \
		self[ 'sizeInBytes' ], \
		self[ 'checksum' ] \
		 = \
		struct.unpack( '<cBHH', self.binaryData[ 2:-2 ] )
					
		if instrumentFamily == '\x10':
			instrumentType = 'AD2CP'
			
		return instrumentType

def generateAD2CP_DataRecord_binary( version, sizeInBytes ):
	class ConfigurationBitMask( Structure ):
		_fields_ = [ ( "validP", c_ubyte, 1 ), 
					 ( "validT", c_ubyte, 1 ),
					 ( "validCompass", c_ubyte, 1 ),
					 ( "validTilt", c_ubyte, 1 ),
					 ( "spare", c_ubyte, 1 ),
					 ( "includesVelocity", c_ubyte, 1 ),
					 ( "includesAmplitude", c_ubyte, 1 ),
					 ( "includesCorrelation", c_ubyte, 1 ),
					 ( "unused", c_ubyte, 8 ) ]
					 
	class ErrorBitMask( Structure ):
		_fields_ = [ ( "FIFO", c_ushort, 1 ),
					 ( "overflow", c_ushort, 1 ),
					 ( "underrun", c_ushort, 1 ),
					 ( "samplesMissing", c_ushort, 1 ),
					 ( "measurementDidNotFinish", c_ushort, 1 ),
					 ( "sensorReadFailure", c_ushort, 1 ),
					 ( "notUsed", c_ushort, 2 ),
					 ( "beam0inphase", c_ushort, 1 ),
					 ( "beam0quadrature", c_ushort, 1 ),
					 ( "beam1inphase", c_ushort, 1 ),
					 ( "beam1quadrature", c_ushort, 1 ),
					 ( "beam2inphase", c_ushort, 1 ),
					 ( "beam2quadrature", c_ushort, 1 ),
					 ( "beam3inphase", c_ushort, 1 ),
					 ( "beam3quadrature", c_ushort, 1 ) ]
		# beam error is always for four beams, regardless of actual number of beam?
	
	class StatusBitMaskv1( Structure ):
		_fields_ = [ ( "unused", c_ushort, 4 ),
					 ( "wakeupState", c_ushort, 2 ),
					 ( "powerLevel", c_ushort, 2 ),
					 ( "unused", c_ushort, 8 ) ]

	class StatusBitMaskv2( Structure ):
		_fields_ = [ ( "unused", c_ushort, 4 ),
					 ( "wakeupState", c_ushort, 2 ),
					 ( "unused", c_ushort, 10 ) ]

	class StatusBitMaskv3( Structure ):
		_fields_ = [ ( "unused", c_uint32, 21 ),
					 ( "previousWakeUpState", c_uint32, 1 ),
					 ( "autoOrientation", c_uint32, 3 ),
					 ( "orientation", c_uint32, 3 ),
					 ( "wakeupState", c_uint32, 4 ) ]

	class CellsCoordinateSystemBeamsMask( Structure ):
		_fields_ = [ ( "numberOfCells", c_ushort, 10 ),
					 ( "coordinateSystem", c_ushort, 2 ),
					 ( "numberOfBeams", c_ushort, 4 ) ]
	
	class DatasetDescription( Structure ):
		_fields_ = [ ( "physicalBeamDataSet1", c_ushort, 3 ),
					 ( "physicalBeamDataSet2", c_ushort, 3 ),
					 ( "physicalBeamDataSet3", c_ushort, 3 ),
					 ( "physicalBeamDataSet4", c_ushort, 3 ),
					 ( "physicalBeamDataSet5", c_ushort, 3 ),
					 ( "unused", c_ushort, 1 ) ]
					 
	class AD2CP_DataRecord_binary( NortekBinaryDataStructure ):
		if version == 1:
			_fields_ = [ ( "version", c_ubyte ),
						 ( "configuration", ConfigurationBitMask ),
						 ( "year", c_ubyte ),
						 ( "month", c_ubyte ),
						 ( "day", c_ubyte ),
						 ( "hour", c_ubyte ),
						 ( "minute", c_ubyte ),
						 ( "seconds", c_ubyte ),
						 ( "microseconds", c_ushort ),
						 ( "speedOfSound", c_ushort ),
						 ( "temperature", c_short ),
						 ( "pressure", c_uint32 ),
						 ( "heading", c_ushort ),
						 ( "pitch", c_short ),
						 ( "roll", c_short ),
						 ( "error", ErrorBitMask ),
						 ( "status", StatusBitMaskv1 ),
						 ( "cellsCSbeams", CellsCoordinateSystemBeamsMask ),
						 ( "cellSize", c_ushort ),
						 ( "blankingDistance", c_ushort ),
						 ( "velocityRange", c_ushort ),
						 ( "velocityScaling", c_byte ),
						 ( "battery", c_ushort ),
						 ( "fourBytesPadding", c_byte ) ]
		elif version == 2:
			_fields_ = [ ( "version", c_ubyte ),
						 ( "offsetToData", c_ubyte ),
						 ( "serialNumber", c_ushort * 2 ),
						 ( "configuration", ConfigurationBitMask ),
						 ( "year", c_ubyte ),
						 ( "month", c_ubyte ),
						 ( "day", c_ubyte ),
						 ( "hour", c_ubyte ),
						 ( "minute", c_ubyte ),
						 ( "seconds", c_ubyte ),
						 ( "microseconds", c_ushort ),
						 ( "speedOfSound", c_ushort ),
						 ( "temperature", c_short ),
						 ( "pressure", c_uint32 ),
						 ( "heading", c_ushort ),
						 ( "pitch", c_short ),
						 ( "roll", c_short ),
						 ( "error", ErrorBitMask ),
						 ( "status", StatusBitMaskv2 ),
						 ( "cellsCSbeams", CellsCoordinateSystemBeamsMask ),
						 ( "cellSize", c_ushort ),
						 ( "blankingDistance", c_ushort ),
						 ( "velocityRange", c_ushort ),
						 ( "battery", c_ushort ),
						 ( "magentometerRawData_x", c_short ),
						 ( "magentometerRawData_y", c_short ),
						 ( "magentometerRawData_z", c_short ),
						 ( "accelorometerRawData_x", c_short ),
						 ( "accelorometerRawData_y", c_short ),
						 ( "accelorometerRawData_z", c_short ),
						 ( "ambiguityVelocity", c_short ),
						 ( "datasetDescription", DatasetDescription ),
						 ( "transmitEnergy", c_ushort ),
						 ( "velocityScaling", c_byte ),
						 ( "powerLevel", c_byte ),
						 ( "fourBytesPadding", c_byte * 4 ) ]
		elif version == 3:
			_fields_ = [ ( "version", c_ubyte ),
						 ( "offsetToData", c_ubyte ),
						 ( "configuration", ConfigurationBitMask ),
						 ( "serialNumber", c_ushort * 2 ),
						 ( "year", c_ubyte ),
						 ( "month", c_ubyte ),
						 ( "day", c_ubyte ),
						 ( "hour", c_ubyte ),
						 ( "minute", c_ubyte ),
						 ( "seconds", c_ubyte ),
						 ( "microseconds", c_ushort ),
						 ( "speedOfSound", c_ushort ),
						 ( "temperature", c_short ),
						 ( "pressure", c_uint32 ),
						 ( "heading", c_ushort ),
						 ( "pitch", c_short ),
						 ( "roll", c_short ),
						 ( "cellsCSbeams", CellsCoordinateSystemBeamsMask ),
						 ( "cellSize", c_ushort ),
						 ( "blankingDistance", c_ushort ),
						 ( "unused", c_ushort ),
						 ( "battery", c_ushort ),
						 ( "magentometerRawData_x", c_short ),
						 ( "magentometerRawData_y", c_short ),
						 ( "magentometerRawData_z", c_short ),
						 ( "accelorometerRawData_x", c_short ),
						 ( "accelorometerRawData_y", c_short ),
						 ( "accelorometerRawData_z", c_short ),
						 ( "ambiguityVelocity", c_short ),
						 ( "datasetDescription", DatasetDescription ),
						 ( "transmitEnergy", c_ushort ),
						 ( "velocityScaling", c_byte ),
						 ( "powerLevel", c_byte ),
						 ( "magnetometerTemperature", c_ushort ),
						 ( "rtcTemperature", c_ushort ),
						 ( "error", ErrorBitMask ),
						 ( "status", StatusBitMaskv3 ),
						 ( "ensemble", c_uint ) ]
		ensembleCounter = 0
		ensembleCycleCounter = 0
		numberOfBeams = 0
		numberOfCells = 0
		arraysAllocated = False
		_sizeInBytes = sizeInBytes
		
		def calculateChecksum( self, openDataFile ):
			originalPosition = openDataFile.tell()
			openDataFile.seek( originalPosition - self._sizeInBytes )
			checksumDataType = c_short * ( self._sizeInBytes / 2 )
			checksumData = checksumDataType()
			openDataFile.readinto( checksumData )
			openDataFile.seek( originalPosition )
			calculatedChecksum = int( 'b58c', base = 16 )
			for aShort in checksumData:
				calculatedChecksum += aShort
			self.calculatedChecksum = calculatedChecksum % 65536
			if self.checksum == self.calculatedChecksum:
				self.checksumResult = True
				return True
			else:
				self.checksumResult = False
				return False
		
		def incrementCounters( self ):
			self.ensembleCounter += 1
		
		def resetCounters( self ):
			self.ensembleCounter = 0
				
		def allocateDataArrays( self, version, ad2cpInstrument ):
			if self.configuration.includesVelocity:
				ad2cpInstrument[ 'velocity' ] = NortekDataArrays.VelocityDataArray( shape = ( 
					self.numberOfCells, 
					self.ensembleCounter,
					self.numberOfBeams ) )
			if self.configuration.includesAmplitude:
				ad2cpInstrument[ 'amplitude' ] = NortekDataArrays.GenericDataArray( shape = ( 
					self.numberOfCells, 
					self.ensembleCounter,
					self.numberOfBeams ) )
			if self.configuration.includesCorrelation:
				ad2cpInstrument[ 'correlation' ] = NortekDataArrays.GenericDataArray( shape =( 
					self.numberOfCells, 
					self.ensembleCounter,
					self.numberOfBeams ) )
			ad2cpInstrument[ 'ensemble' ] = numpy.zeros( ( self.ensembleCounter,  ) )
			ad2cpInstrument[ 'time' ] = numpy.zeros( ( self.ensembleCounter,  ) )
			ad2cpInstrument[ 'temperature' ] = numpy.zeros( ( self.ensembleCounter,  ) )
			ad2cpInstrument[ 'battery' ] = numpy.zeros( ( self.ensembleCounter,  ) )
			ad2cpInstrument[ 'state' ] = { 'heading': NortekDataArrays.GenericDataArray( shape = ( 1, self.ensembleCounter ) ),
										   'pitch': NortekDataArrays.GenericDataArray( shape = ( 1, self.ensembleCounter ) ),
										   'roll': NortekDataArrays.GenericDataArray( shape = ( 1, self.ensembleCounter ) ) }
			if version is 2 or version is 3:
			   ad2cpInstrument[ 'state' ][ 'magnetometer' ] = NortekDataArrays.GenericDataArray( shape = ( 
								3, 
								self.ensembleCounter ) )
			   ad2cpInstrument[ 'state' ][ 'accelorometer' ] = NortekDataArrays.GenericDataArray( shape = ( 
								3, 
								self.ensembleCounter ) )
			self.arraysAllocated = True
			self.resetCounters()
		
		def moveIntoDataArrays( self, version, dataBlock, ad2cpInstrument ):
			if self.ensembleCounter == 0:
				self.moveHeader( ad2cpInstrument )
			for datasetNumber in ad2cpInstrument[ 'datasetDescription' ]:
				if self.configuration.includesVelocity:
					ad2cpInstrument[ 'velocity' ][ 'data' ][ :, self.ensembleCounter, datasetNumber ] \
						= dataBlock.velocity[ datasetNumber ][ : ]
					ad2cpInstrument[ 'velocity' ][ 'data' ][ :, self.ensembleCounter, datasetNumber ] *= 1000 * 10**self.velocityScaling
				if self.configuration.includesAmplitude:
					ad2cpInstrument[ 'amplitude' ][ 'data' ][ :, self.ensembleCounter, datasetNumber ] \
						= dataBlock.amplitude[ datasetNumber ][ : ]
				if self.configuration.includesCorrelation:
					ad2cpInstrument[ 'correlation' ][ 'data' ][ :, self.ensembleCounter, datasetNumber ] \
						= dataBlock.correlation[ datasetNumber ][ : ]
			ad2cpInstrument[ 'ensemble' ][ self.ensembleCounter, ] = self.ensembleCounter
			ensembleDateStr = datetime.datetime( self.year + 1900, 
												 self.month + 1, 
												 self.day, 
												 self.hour, 
												 self.minute, 
												 self.seconds, 
												 self.microseconds )
			ad2cpInstrument[ 'time' ][ self.ensembleCounter, ] = pylab.datestr2num( 
				'{:%Y-%m-%d %H:%M:%S}'.format( ensembleDateStr ) )
			ad2cpInstrument[ 'temperature' ][ self.ensembleCounter, ] = self.temperature
			ad2cpInstrument[ 'battery' ][ self.ensembleCounter, ] = self.battery
			ad2cpInstrument[ 'state' ][ 'heading' ][ 'data' ][ 0, self.ensembleCounter ] = self.heading
			ad2cpInstrument[ 'state' ][ 'pitch' ][ 'data' ][ 0, self.ensembleCounter ] = self.pitch
			ad2cpInstrument[ 'state' ][ 'roll' ][ 'data' ][ 0, self.ensembleCounter ] = self.roll
			if version is 2 or version is 3:
				ad2cpInstrument[ 'state' ][ 'magnetometer' ][ 'data' ][ :, self.ensembleCounter ] = [ 
					self.magentometerRawData_x,
					self.magentometerRawData_y,
					self.magentometerRawData_z ]
				ad2cpInstrument[ 'state' ][ 'accelorometer' ][ 'data' ][ :, self.ensembleCounter ] = [ 
					self.accelorometerRawData_x,
					self.accelorometerRawData_y,
					self.accelorometerRawData_z ]
			self.incrementCounters()
	
		def moveHeader( self, ad2cpInstrument ):
			ad2cpInstrument[ 'userConfiguration' ] = {	"numberOfCells": self.cellsCSbeams.numberOfCells,
														"numberOfBeams": self.cellsCSbeams.numberOfBeams,
														"coordinateSystem": self.cellsCSbeams.coordinateSystem,
														"cellSize": self.cellSize,
														"blankingDistance": self.blankingDistance,
														"ambiguityVelocity": self.ambiguityVelocity,
														"transmitEnergy": self.transmitEnergy,
														"powerLevel": self.powerLevel }
			for f, t in self._fields_:
				if re.search( f, "velocityRange" ):
					ad2cpInstrument[ 'userConfiguration' ] = self.velocityRange
			ad2cpInstrument[ 'datasetDescription' ] = {}
			for field, datasetNumber in zip( self.datasetDescription._fields_, range( 0, 5, 1 ) ):
				physicalBeam = self.datasetDescription.__getattribute__( field[ 0 ] )
				if physicalBeam != 0:
					ad2cpInstrument[ 'datasetDescription' ][ datasetNumber ] = physicalBeam

	return AD2CP_DataRecord_binary

def generateAD2CP_DataBlock_binary( configuration, numberOfBeams, numberOfCells ):
	adhoc_fields_ = []
	sizeInBytes = 0
	if configuration.includesVelocity:
		adhoc_fields_.append( ( "velocity", c_short * numberOfCells * numberOfBeams ) )
		sizeInBytes += numberOfBeams * numberOfCells * 2
	if configuration.includesAmplitude:
		adhoc_fields_.append( ( "amplitude", c_ubyte * numberOfCells * numberOfBeams ) )
		sizeInBytes += numberOfBeams * numberOfCells * 1
	if configuration.includesCorrelation:
		adhoc_fields_.append( ( "correlation", c_ubyte * numberOfCells * numberOfBeams ) )
		sizeInBytes += numberOfBeams * numberOfCells * 1
	class AD2CP_DataBlock_binary( Structure ):
		_fields_ = adhoc_fields_
		_sizeInBytes = sizeInBytes
	
	return AD2CP_DataBlock_binary

def generateHRProfiler_DataRecord_binary( numberOfBeams = 3, numberOfCells = 1 ):
	class HRProfiler_DataRecord_binary( NortekBinaryDataStructure ):
		_fields_ = [ ( "sizeInWords", c_ushort ),
					 ( "BCDtime", BCDTimeWord ),
					 ( "milliseconds", c_ushort ),
					 ( "error", c_short ),
					 ( "battery", c_ushort ),
					 ( "speedOfSound", c_ushort ),
					 ( "heading", c_short ),
					 ( "pitch", c_short ),
					 ( "roll", c_short ),
					 ( "pressureMSB", c_ubyte ),
					 ( "status", c_ubyte ),
					 ( "pressureLSW", c_ushort ),
					 ( "temperature", c_short ),
					 ( "analogInput1", c_short ),
					 ( "analogInput2", c_short ),
					 ( "numberOfBeams", c_ubyte ),
					 ( "numberOfCells", c_ubyte ),
					 ( "velocityLag2", c_short * numberOfBeams ),
					 ( "amplitudeLag2", c_ubyte * numberOfBeams ),
					 ( "correlationLag2", c_ubyte * numberOfBeams ),
					 ( "spare1", c_short ),
					 ( "spare2", c_short ),
					 ( "spare3", c_short ),
					 ( "velocity", c_short * numberOfCells * numberOfBeams ),
					 ( "amplitude", c_ubyte * numberOfCells * numberOfBeams ),
					 ( "correlation", c_ubyte * numberOfCells * numberOfBeams ) ]
					 #					 ( "checksum", c_ushort )
		ensembleCounter = 0

		def setSizeInBytes( self ):
			self._sizeInBytes = 0
			for field in HRProfiler_DataRecord_binary._fields_:
				currentField = getattr( HRProfiler_DataRecord_binary, field[ 0 ] )
				self._sizeInBytes += currentField.size
			self._sizeInBytes += 4

		def incrementCounters( self ):
			self.ensembleCounter += 1
	
		def resetCounters( self ):
			self.ensembleCounter = 0
		
		def allocateDataArrays( self, hrProfilerInstrument ):
			if 'sampleRate' in hrProfilerInstrument[ 'userConfiguration' ]:
				sampleRate = hrProfilerInstrument[ 'userConfiguration' ][ 'sampleRate' ]
			else:
				sampleRate = 1
			hrProfilerInstrument[ 'velocity' ] = NortekDataArrays.VelocityDataArray( 
				sampleRate,
				shape = ( 
					hrProfilerInstrument[ 'userConfiguration' ][ 'numberOfCells' ], 
					self.ensembleCounter,
					hrProfilerInstrument[ 'userConfiguration' ][ 'numberOfBeams' ] ) )
			hrProfilerInstrument[ 'amplitude' ] = NortekDataArrays.GenericDataArray( 
				sampleRate,
				shape = ( 
					hrProfilerInstrument[ 'userConfiguration' ][ 'numberOfCells' ], 
					self.ensembleCounter,
					hrProfilerInstrument[ 'userConfiguration' ][ 'numberOfBeams' ] ) )
			hrProfilerInstrument[ 'correlation' ] = NortekDataArrays.GenericDataArray( 
				sampleRate,
				shape = ( 
					hrProfilerInstrument[ 'userConfiguration' ][ 'numberOfCells' ], 
					self.ensembleCounter,
					hrProfilerInstrument[ 'userConfiguration' ][ 'numberOfBeams' ] ) )
			hrProfilerInstrument[ 'ensemble' ] = numpy.zeros( ( self.ensembleCounter,  ) )
			self.resetCounters()
		
		def moveIntoDataArrays( self, hrProfilerInstrument ):
			for beamNumber in range( 0, self.numberOfBeams, 1 ):
				hrProfilerInstrument[ 'velocity' ][ 'data' ][ :, self.ensembleCounter, beamNumber ] \
					= self.velocity[ beamNumber ][ : ]
				hrProfilerInstrument[ 'velocity' ][ 'data' ][ :, self.ensembleCounter, beamNumber ] \
					*= hrProfilerInstrument[ 'userConfiguration' ][ 'velocityScaling' ]
				hrProfilerInstrument[ 'amplitude' ][ 'data' ][ :, self.ensembleCounter, beamNumber ] \
					= self.amplitude[ beamNumber ][ : ]
				hrProfilerInstrument[ 'correlation' ][ 'data' ][ :, self.ensembleCounter, beamNumber ] \
					= self.correlation[ beamNumber ][ : ]
				hrProfilerInstrument[ 'ensemble' ][ self.ensembleCounter, ] = self.ensembleCounter
			self.incrementCounters()
	
	return HRProfiler_DataRecord_binary