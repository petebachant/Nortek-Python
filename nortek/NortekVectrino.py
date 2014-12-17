# contains C-style struct definitions and associated methods for the Nortek Vectrino
# The base class is "NortekBinaryDataStructure" which is itself a subclass of ctypes.Structure
# Individual data structures (e.g. velocity header) are a subclass of NortekDataStructure
# They will inherit the calculateChecksum method from NortekDataStructure and need to define
#
# 
from ctypes import *
from collections import namedtuple
import re
import numpy
import pdb
import datetime
import logging
from NortekDataStructure import NortekBinaryDataStructure
from NortekInstrument import Instrument
import NortekDataArrays
reload( NortekDataArrays )

moduleLogger = logging.getLogger( __name__ )

class Vectrino( Instrument ):
	instrumentType = 'Vectrino'
	_structureName = { '\x51': 'Velocity Data',
					   '\x0f': 'File Info',
					   '\x07': 'Probe Check',
					   '\x02': 'Distance Measurement',
					   '\x50': 'Velocity Header' }
	_plotStyles = { 'colors': { 0: 'black', 1: 'red', 2: 'green', 3: 'blue' },
					'markers': { 0: '^', 1: '^', 2: '^', 3: '^' } }

	def readInstrumentData( self, assignToArrays = False ):
		import os
		if assignToArrays is False:
			self[ '\x50' ] = VelocityHeader_binary()
			self[ '\x51' ] = VelocityData_binary()
			self[ '\x07' ] = ProbeCheck_binary()
			self[ '\x0f' ] = FileInfo_binary()
			self[ '\x02' ] = DistanceMeasurement_binary()
		else:
			self[ '\x51' ].allocateDataArrays( self )
			self[ '\x07' ].allocateDataArrays( self )
			self[ '\x02' ].allocateDataArrays( self )
			
		with open( os.path.join( self.pathToSource, self.filename + self.sourceExtension ), 'rb' ) as instrumentDataFile:
			instrumentDataFile.seek( self.endOfConfiguration )
			while True:
				sync = instrumentDataFile.read( 1 )
				if not sync:
					break
				elif sync == '\xa5':
					id = instrumentDataFile.read( 1 )
					if not id:
						break
					elif id in self._structureName:
						if ( instrumentDataFile.tell() + self[ id ]._sizeInBytes - 2 ) <= self.sourceSizeInBytes:
							self[ id ]._structureStart = instrumentDataFile.tell() - 2
							self[ id ]._structureStop = self[ id ]._structureStart + self[ id ]._sizeInBytes
							instrumentDataFile.readinto( self[ id ] )
							if not self[ id ].calculateChecksum( instrumentDataFile ):
								if not assignToArrays: # only report these on the first pass
									self.reportChecksum( instrumentDataFile, id )
							elif not assignToArrays:
								self[ id ].incrementCounters()
							elif assignToArrays:
								self[ id ].moveIntoDataArrays( self )
						else:
							logging.info( 'Truncated %s structure at file position %d.', self._structureName[ id ], instrumentDataFile.tell() - 2 )
		if assignToArrays and hasattr( self, 'velocityHeader' ):
			#pdb.set_trace()
			for beamNumber in range( 0, 4, 1 ):
				self.snr.data[ beamNumber, : ] = \
				20 * numpy.log10( self.amplitude.data[ beamNumber, : ] ) \
				- numpy.log10( self.velocityHeader.noise.amplitude[ beamNumber + 1 ] )

	def cleanUpInstrument( self ):
		for key in ( '\x51', '\x0f', '\x07', '\x02', '\x50' ):
			if key in self:
				self.pop( key, None )

	def coordinateTransformation( self, transformDirection = None ):
		try:
			transformFrom = self.__getattribute__( 'velocity' )
			try:
				fromTo = re.search( '(?P<from>beam|xyz|XYZ)2(?P<to>beam|xyz|XYZ)', transformDirection )
				if fromTo.group( 'from' ) == transformFrom.isInCoordinateSystem.lower():
					transformedToData = numpy.zeros( ( self.T[ transformDirection ].shape[ 0 ],
													transformFrom.data.shape[ 1 ] ) )
					transformedToData = numpy.array( self.T[ transformDirection ] * transformFrom.data )
					transformFrom.data = transformedToData
					transformFrom.isInCoordinateSystem = fromTo.group( 'to' )
					self.__setattr__( 'velocity', transformFrom )
				else:
					logging.warning( 'Velocity data is not currently in coordinate system %s.', fromTo.group( 'from' ) )
			except TypeError as currentError:
				logging.warning( 'Transform direction is undefined.' )
			except AttributeError as currentError:
				if currentError.message == "'Vectrino' object has no attribute 'T'":
					from numpy import matrix
					from numpy.linalg import inv
					self.T = { 'beam2xyz': self.headConfiguration.transformationMatrix,
							   'xyz2beam': matrix( inv( self.headConfiguration.transformationMatrix ) ) }
					self.coordinateTransformation( transformDirection )
				else:
					pdb.set_trace()
			except Exception as currentError:
				pdb.set_trace()
		except AttributeError as currentError:
			logging.warning( 'Could not locate the data requested. Error message was: %s',
					currentError.message )

##########################################################################################
######################## Binary Data Structures ##########################################
##########################################################################################

class VelocityData_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "status", c_char ),
				 ( "count", c_ubyte ),
				 ( "velocity", c_short * 4 ),
				 ( "amplitude", c_ubyte * 4 ),
				 ( "correlation", c_ubyte * 4 ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 22
	ensembleCounter = 0
	ensembleCycleCounter = 0
	previousCounter = 0
	
	def incrementCounters( self ):
		if self.ensembleCounter > 1 and self.count < self.previousCounter:
			self.ensembleCycleCounter += 1
		self.ensembleCounter = self.ensembleCycleCounter * 256 + self.count
		self.previousCounter = self.count
	
	def resetCounters( self ):
		self.ensembleCounter = 0
		self.ensembleCycleCounter = 0
		
	def allocateDataArrays( self, vectrinoInstrument ):
		samepleRate = vectrinoInstrument.userConfiguration.sampleRate
		vectrinoInstrument.velocity = NortekDataArrays.VelocityDataArray( 
			samepleRate,
			shape = ( 4, self.ensembleCounter + 1 ),
			units = 'm/s'
			coordinateSystem = vectrinoInstrument.userConfiguration.coordinateSystem )
		vectrinoInstrument.amplitude = NortekDataArrays.GenericDataArray( 
			samepleRate,
			shape = ( 4, self.ensembleCounter + 1 ) )
		vectrinoInstrument.snr = NortekDataArrays.GenericDataArray( 
			samepleRate,
			shape = ( 4, self.ensembleCounter + 1 ) )
		vectrinoInstrument.correlation = NortekDataArrays.GenericDataArray( 
			samepleRate,
			shape = ( 4, self.ensembleCounter + 1 ) )
		vectrinoInstrument.ensemble = numpy.arange( 0, self.ensembleCounter, 1 )
		self.resetCounters()
		
	def moveIntoDataArrays( self, vectrinoInstrument ):
		try:
			self.incrementCounters()
			vectrinoInstrument.velocity.data[ :, self.ensembleCounter ] = self.velocity[ 0:4 ]
			vectrinoInstrument.velocity.data[ :, self.ensembleCounter ] *= vectrinoInstrument.userConfiguration.velocityScaling / 1000.0
			vectrinoInstrument.amplitude.data[ :, self.ensembleCounter ] = self.amplitude[ 0:4 ]
			vectrinoInstrument.correlation.data[ :, self.ensembleCounter ] = self.correlation[ 0:4 ]
		except IndexError as error:
			pdb.set_trace()
			
class FileInfo_binary( NortekBinaryDataStructure ):
	_fields_ = [ ( "sizeInWords", c_short ),
				 ( "field1", c_short ),
				 ( "field2", c_short ),
				 ( "field3", c_short ),
				 ( "fileInfo", c_char * 12 ),
				 ( "checksum", c_ushort ) ]
	_sizeInBytes = 24
	fileInfoCounter = 0
	
class VelocityHeader_binary( NortekBinaryDataStructure ):
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
		vectrinoInstrument.velocityHeader = VelocityHeader( 
			setDistance = ( self.distance, self.distanceQuality ),
			setLags = ( self.lag1 / 1e6, self.lag2 / 1e6 ),
			speedOfSound = self.speedOfSound / 10.0 )
				
		for beamNumber in range( 1, 5, 1 ):
			vectrinoInstrument.velocityHeader.noise.amplitude[ beamNumber ] \
				= self.noise[ beamNumber - 1 ]
			vectrinoInstrument.velocityHeader.noise.correlation[ beamNumber ] \
				= self.correlation[ beamNumber - 1 ]
			vectrinoInstrument.velocityHeader.sampleVolumeAmplitude[ beamNumber ] \
				= self.samplingVolumeAmplitude[ beamNumber - 1 ]
			vectrinoInstrument.velocityHeader.boundaryAmplitude[ beamNumber ] \
				= self.boundaryAmplitude[ beamNumber - 1 ]
			vectrinoInstrument.velocityHeader.z0PlusLag1[ beamNumber ] \
				= self.z0PlusLag1[ beamNumber - 1 ]
			vectrinoInstrument.velocityHeader.z0PlusLag2[ beamNumber ] \
				= self.z0PlusLag2[ beamNumber - 1 ]

class VelocityHeader( object ):
	__slots__ = [ 'noise', 'distance', 'lags', 'sampleVolumeAmplitude', 
				  'boundaryAmplitude', 'speedOfSound', 'z0PlusLag1', 'z0PlusLag2' ]
	Noise = namedtuple( 'Noise', [ 'amplitude', 'correlation' ] )
	noise = Noise( {}, {} )

	Distance = namedtuple( 'Distance', [ 'fromProbe', 'quality' ] )
	Lags = namedtuple( 'Lags', [ 'lag1', 'lag2' ] )

	sampleVolumeAmplitude = {}
	boundaryAmplitude = {}
	z0PlusLag1 = {}
	z0PlusLag2 = {}

	def __init__( self, setDistance = [ None, None ], setLags = [ None, None ], speedOfSound = 1500.0 ):
		self.distance = self.Distance( setDistance[ 0 ], setDistance[ 1 ] )
		self.lags = self.Lags( setLags[ 0 ], setLags[ 1 ] )
		self.speedOfSound = speedOfSound

class ProbeCheck_binary( NortekBinaryDataStructure ):
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
		vectrinoInstrument.probeCheck = {}
		vectrinoInstrument.probeCheck[ 'amplitude' ] = numpy.zeros( ( 4, self.samplesPerBeam, self.probeCheckCounter ) )
		self.resetCounters()
		
	def moveIntoDataArrays( self, vectrinoInstrument ):
		for beamNumber in range( 0, 4, 1 ):
			vectrinoInstrument.probeCheck[ 'amplitude' ][ beamNumber, :, self.probeCheckCounter ] = \
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
		vectrinoInstrument.probeCheck[ 'distance' ] = dSampleDist
		
class DistanceMeasurement_binary( NortekBinaryDataStructure ):
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
		vectrinoInstrument.distance = {}
		vectrinoInstrument.distance[ 'fromProbe' ] = numpy.zeros( ( self.distanceCounter, ) )
		vectrinoInstrument.distance[ 'quality' ] = numpy.zeros( ( self.distanceCounter, ) )
		self.resetCounters()
		
	def moveIntoDataArrays( self, vectrinoInstrument ):
		vectrinoInstrument.distance[ 'fromProbe' ][ self.distanceCounter ] = \
				self.distance / 10.0
		vectrinoInstrument.distance[ 'quality' ][ self.distanceCounter ] = \
				self.quality
		self.incrementCounters()