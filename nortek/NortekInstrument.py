from UserDict import UserDict
import os
import re
import NortekDataStructure
import logging
import errno
import pdb
import struct 
import numpy
import math
from math import sin, cos, radians
import matplotlib

reload( NortekDataStructure )
nortekLogger = logging.getLogger( "Nortek" )
nortekLogger.setLevel( logging.DEBUG )

nortekLog_FID = logging.FileHandler( os.path.join( os.getcwd(), "pyNortek.log" ), 'w' )
nortekLog_FID.setLevel( logging.DEBUG )
nortekLog_formatter = logging.Formatter( '%(asctime)s - %(name)12s - %(levelname)8s - %(message)s' )
nortekLog_FID.setFormatter( nortekLog_formatter )
nortekLogger.addHandler( nortekLog_FID )

nortekLogger.info( "Nortek Python Library log started." )

class Instrument( dict ):
	instrumentType = 'unknown'
	
	def __init__( self, sourceDataFileWithPath = None ):
		super( Instrument, self ).__init__()
		self.logger = logging.getLogger( "Nortek." + self.instrumentType )
		
		self.sourceReachable = False
		if sourceDataFileWithPath:        
			try:
				sourceDataFile = open( sourceDataFileWithPath, 'rb' )
			except IOError as ioe:
				self.logger.debug( "%d", ioe.errno )
				if ioe.errno == errno.EACCES:
					self.logger.error( "Unable to access the file due to file permissions." )
				#elif ioe.errno == errno.
				raise
			except:
				self.sourceReachable = False
				self.logger.error( '%s in file %s is unreachable.', self.instrumentType, self.filename )
			else:
				sourceDataFile.close()
				self.sourceReachable = True
				self.sourceSizeInBytes = os.path.getsize( sourceDataFileWithPath )
				self.pathToSource, self.filename = os.path.split( sourceDataFileWithPath )
				self.filename, self.sourceExtension = os.path.splitext( self.filename )
				self.logger.info( 'Reading configuration information for %s from file %s', self.instrumentType, self.filename )
				self.readInstrumentHeader()
				try:
					if self.userConfiguration.sampleMode == 'burst':
						self._burstMode = True
				except:
					pass
				self.logger.info( 'Reading data for %s from file %s', self.instrumentType, self.filename )
				self.readInstrumentData( assignToArrays = False )
				self.readInstrumentData( assignToArrays = True )
				self.cleanUpInstrument()
		else:
			self.logger.warning( "Error generated in class Instrument( dict )" )
			self.logger.error( 'No source file specified.' )

	def reportChecksum( self, instrumentDataFile, id ):
		checksumErrorReadPosition = instrumentDataFile.tell() - self[ id ]._sizeInBytes			
		try:
			self.logger.info( "Checksum error in file %s at byte %d, structure type is %s", 
				self.filename, 
				checksumErrorReadPosition,
				self._structureName[ id ] )
		except KeyError as currentError:
			pass
			#pdb.set_trace()
		instrumentDataFile.seek( checksumErrorReadPosition + 1 )

	def readInstrumentHeader( self ):
	# Hardware configuration A505
	# Head configuration A504
	# User configuration A500
		with open( os.path.join( self.pathToSource, 
				self.filename + self.sourceExtension ), 'rb' ) as instrumentDataFile:
			while True:
				sync = instrumentDataFile.read( 1 )
				if not sync:
					break
				elif sync == '\xa5':
					id = instrumentDataFile.read( 1 )
					if id == '\x05':
						instrumentDataFile.seek( instrumentDataFile.tell() - 2 )
						hardwareConfiguration = NortekDataStructure.Header(
							instrumentDataFile.read( 48 ) ) # always
						headConfiguration = NortekDataStructure.Header(
							instrumentDataFile.read( 224 ) ) # always
						userConfiguration = NortekDataStructure.Header(
							instrumentDataFile.read( 512 ) ) # always
						self.endOfConfiguration = instrumentDataFile.tell()
						if ( hardwareConfiguration.checksum and 
							 headConfiguration.checksum and 
							 userConfiguration.checksum ):
							 self.hardwareConfiguration = hardwareConfiguration
							 self.headConfiguration = headConfiguration
							 self.userConfiguration = userConfiguration
							 self.intrumentType = self.hardwareConfiguration.interpretBinaryData()
							 self.headConfiguration.interpretBinaryData( self.intrumentType )
							 self.userConfiguration.interpretBinaryData( self.intrumentType )
							 break
						else:
							#pdb.set_trace()
							# there were problems, try to figure out what
							self.logger.warning( """Checksum failure in the header. Checksum values are 
								hardware: {}
								head: {}
								user: {}
								Data file position is {}""".format( 
									self[ 'hardwareConfiguration' ].checksum,
									self[ 'headConfiguration' ].checksum,
									self[ 'userConfiguration' ].checksum,
									instrumentDataFile.tell() ) )

	def cleanUpInstrument( self ):
		pass
		
	def exportToMatlabV5( self, matlabFile = None ):
		pass

	def exportToMatlabV7p3( self, matlabFile = None ):
		pass

	def exportToHDF5( self, hdf5File = None ):
		pass
