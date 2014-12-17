# contains C-style struct definitions and associated methods for various Nortek instruments
# The base class is "NortekDataStructure" which is itself a subclass of ctypes.Structure
# Individual data structures (e.g. velocity header) are a subclass of NortekDataStructure
# They will inherit the calculateChecksum method from NortekDataStructure and need to define
#
# 
from ctypes import *
from UserDict import UserDict
from collections import namedtuple
import struct
import re
import numpy
import pdb
import NortekDataArrays
import datetime
import pylab

reload( NortekDataArrays )
		
class ParaDoppErrorBitMask( Structure ):
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
	
class ParaDoppStatusBitMaskv1( Structure ):
		_fields_ = [ ( "unused", c_ushort, 4 ),
					 ( "wakeupState", c_ushort, 2 ),
					 ( "powerLevel", c_ushort, 2 ),
					 ( "unused", c_ushort, 8 ) ]

class Header( UserDict ):
	def __init__( self, binaryDataString ):
		UserDict.__init__( self )
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
			( syncByte, \
			dataStructureID, \
			sizeInWords, \
			self.serialNumber, \
			boardConfigurationBit0, \
			boardConfigurationBit1, \
			self.systemFrequency, \
			self.picVersion, \
			self.hardwareRevision, \
			self.recorderSize, \
			hardwareStatus, \
			hrFlag,
			spareWords, \
			self.firmwareVersion ) = \
			struct.unpack( '<ccH14sBBHHHHH2s10s4s', self.binaryData[ 0:-2 ] )
			
			self.serialNumber = self.serialNumber.rstrip()
			if ( re.search( 'VNO', self.serialNumber ) ):
				instrumentType = 'Vectrino'
			elif ( re.search( 'VEC', self.serialNumber ) ):
				instrumentType = 'Vector'
			elif ( re.search( 'AQD', self.serialNumber ) ):
				#if ( re.search( 'HR', self.firmwareVersion ) ):
				if ( hrFlag == '\x67\x67' ):
					instrumentType = 'HR Profiler'
				else:
					instrumentType = 'Aquadopp Profiler'
			elif ( re.search( 'WPR', self.serialNumber ) ):
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
			self.frequency, \
			self.headType, \
			self.serialNumber, \
			systemData1, \
			tempT, \
			systemData2, \
			distanceToSampleVolume, \
			spareWords, \
			self.numberOfBeams = \
			struct.unpack( '<ccHHHH12s8s32s136sH20sH', self.binaryData[ 0:-2 ] )
			self.frequency = self.frequency * 1000
			if instrumentType is 'Vectrino':
				tempT = struct.unpack( '<16h', tempT )
				self.transformationMatrix = \
					numpy.matrix( numpy.reshape( tempT, ( 4, 4 ) ) ) / 4096.0
				self.distanceToSampleVolume = \
					round( 10 * 0.5 * ( ( 1.5 * distanceToSampleVolume )**2 - 622.98 ) 
						/ ( 1.5 * distanceToSampleVolume - 5.7 ) ) / 10
		elif self.binaryData[ 0:2 ] == '\xa5\x00':
			# User Configuration
			syncByte, \
			dataStructureID, \
			sizeInWords, \
			self.T1, \
			self.T2, \
			self.T3, \
			self.T4, \
			self.T5, \
			self.numberOfPings, \
			self.averageInterval, \
			self.numberOfBeams, \
			timingControlRegister, \
			powerControlRegister, \
			self.A1, \
			self.B0, \
			self.B1, \
			self.compassUpdateRate, \
			coordinateSystem, \
			self.numberOfCells, \
			cellSize, \
			self.measurementInterval, \
			self.deploymentName, \
			self.recorderWrapMode, \
			self.deploymentStartTime, \
			self.diagnosticMeasurement_sampleInterval, \
			modeWord, \
			self.soundSpeedAdjustmentFactor, \
			self.dianosticMeasurement_numberOfSamples, \
			self.diagnosticMeasurementnumberOfBeamsOrCellNumber, \
			self.diagnosticMeasurement_NumberOfPings, \
			modeTestWord, \
			analogInputAddress, \
			hVersion, \
			spareWords, \
			velocityAdjustmentTable, \
			self.comments, \
			self.waveMeasurement_mode, \
			self.waveMeasurement_waveCellPositionPercent, \
			self.wave_T1, \
			self.wave_T2, \
			self.wave_T3, \
			self.wave_numberOfSamples, \
			self.A1_2, \
			self.B0_2, \
			B1_2, \
			spareWords2, \
			self.analogOutputScaleFactor, \
			self.ambiguityResolutionCorrelationThreshold, \
			spareWords3, \
			self.transmitPulseLengthSecondLag_counts, \
			spareWords3, \
			self.stageMatchFilterConstants = \
			struct.unpack( '<cc' + 'H' * 19 + '6sH6sL' + 'H' * 9 + '180s' * 2 + 'H' * 14 + '30s16s', self.binaryData[ 0:-2 ] )
			
			timingControlRegister = '{:016b}'.format( timingControlRegister )[ ::-1 ]
			powerControlRegister = '{:016b}'.format( powerControlRegister )[ ::-1 ]
			modeWord = '{:016b}'.format( modeWord )[ ::-1 ]
			if timingControlRegister[ 5:7 ] == '00' and powerControlRegister[ 5:7 ] == '00':
				self.powerLevel = 'High'
			elif timingControlRegister[ 5:7 ] == '10' and powerControlRegister[ 5:7 ] == '10':
				self.powerLevel = 'High-'
			elif timingControlRegister[ 5:7 ] == '01' and powerControlRegister[ 5:7 ] == '01':
				self.powerLevel = 'LOW+'
			elif timingControlRegister[ 5:7 ] == '11' and powerControlRegister[ 5:7 ] == '11':
				self.powerLevel = 'LOW'
			
			if timingControlRegister[ 1 ] is '1':
				self.sampleMode = 'burst'
			else:
				self.sampleMode = 'continuous'
				
			if coordinateSystem == 0:
				self.coordinateSystem = 'ENU'
			elif coordinateSystem == 1:
				self.coordinateSystem = 'XYZ'
			else:
				self.coordinateSystem = 'Beam'
			
			if instrumentType is 'Vectrino':
				self.sampleRate = round( 50000.0 / self.averageInterval )
				del self.averageInterval
			elif instrumentType is 'Vector':
				self.sampleVolumeSize = cellSize
				self.sampleRate = 512. / self.averageInterval
				if B1_2 > 0:
					self.samplesPerBurst = B1_2
					self.burstInterval = self.measurementInterval
				else:
					self.measurementInterval = 'Continuous'
			elif instrumentType is 'HR Profiler':
				self.sampleRate = 512. / self.T5
			
			if instrumentType is not 'Vectrino':
				self.cellSize = cellSize
			else:
				self.sampleVolumeSize = cellSize
				
			if instrumentType is 'Vector' or 'HR Profiler' or 'Vectrino':
				if modeWord[ 4 ] is '1':
					self.velocityScaling = 0.1 # mm/s
				else:
					self.velocityScaling = 1 # mm/s
			
			self.lag1 = struct.unpack( 'H', spareWords3[ 16:18 ] )[ 0 ]
			self.lag2 = struct.unpack( 'H', spareWords3[ 18:20 ] )[ 0 ]
			# lags can be scaled here for Vector and VectrinoDistanceMeasurement_binary
			# HR Profiler we need head frequency which is in the head configuration
			if instrumentType is 'Vector':
				self.lag1 = self.lag1 / 480000.
				self.lag2 = self.lag2 / 480000.
			elif instrumentType is 'Vectrino':
				self.lag1 = self.lag1 / 1000000.
				self.lag2 = self.lag2 / 1000000.
			
			formattedSoftwareVersion = str( hVersion/10000 ) + "." + str( (hVersion % 10000)/100 )
			if str(hVersion % 100):
				formattedSoftwareVersion + "." + str(hVersion % 100)
			self.softwareVersion = formattedSoftwareVersion.rstrip()
			
class NortekBinaryDataStructure( Structure ):
	_structureStart = 0
	_structureStop = 0
	_objectCounter = 0
	
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
		self._objectCounter += 1

	def resetCounters( self ):
		self._objectCounter = 0
		
	def allocateDataArrays( self, anInstrument ):
		pass
		
	def moveIntoDataArrays( self, anInstrument ):
		pass
