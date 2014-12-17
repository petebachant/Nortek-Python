import numpy
import numpy.random
import scipy.stats
import scipy.signal
import scipy
import UserDict
import pdb
#import AuxiliaryFunctions as AF

# implement logging in this module

class Spectrum( object ):
	pass

class GenericDataArray( object ):
	# base class for single sample volume data (e.g. Vectrino, Vector, current meters)
	# sample rate is a scalar
	# shape is an tuple
	# ( components or beams, sample number, cell number )
	def __init__( self,
				  sampleRate = 1,
				  shape = ( 1, 1 ) ):
		self.sampleRate = sampleRate
		self.data = 0.0 * numpy.empty( shape )
		if len( shape ) == 1:
			self.numberOfSamples = shape[ 0 ]
		else:
			self.numberOfSamples = shape[ 1 ]
		try:
			self.calculateStatistics()
		except IndexError as currentError:
			# probably a 1D array
			self.calculateStatistics( onAxis = 0 )
		
	def calculateStatistics( self, onAxis = 1, useScreenedData = False ):
		if useScreenedData:
			try:
				self.mean = scipy.stats.nanmean( self.data[ self.goodIndices ], onAxis )
				self.median = scipy.stats.nanmedian( self.data[ self.goodIndices ], onAxis )
				self.var = scipy.stats.nanstd( self.data[ self.goodIndices ], onAxis )**2
			except IndexError:
				for currentChannel in range( 0, self.data.shape[ 0 ] ):
					try:
						self.mean[ currentChannel ] = scipy.stats.nanmean( 
							self.data[ currentChannel, self.goodIndices ] )
						self.median[ currentChannel ] = scipy.stats.nanmedian( 
							self.data[ currentChannel, self.goodIndices ] )
						self.var[ currentChannel ] = scipy.stats.nanstd( 
							self.data[ currentChannel, self.goodIndices ] )**2
					except IndexError:
						self.mean[ currentChannel ] = scipy.stats.nanmean( 
							self.data[ currentChannel, self.goodIndices[ currentChannel, : ] ] )
						self.median[ currentChannel ] = scipy.stats.nanmedian( 
							self.data[ currentChannel, self.goodIndices[ currentChannel, : ] ] )
						self.var[ currentChannel ] = scipy.stats.nanstd( 
							self.data[ currentChannel, self.goodIndices[ currentChannel, : ] ] )**2					
			except Exception as currentError:
				pdb.set_trace()
		else:
			self.mean = scipy.stats.nanmean( self.data, onAxis )
			self.median = scipy.stats.nanmedian( self.data, onAxis )
			self.var = scipy.stats.nanstd( self.data, onAxis )**2

	def calculateScreenedStatistics( self ):
		self.calculateStatistics( useScreenedData = True )
			
	def calculateHistograms( self, bins = None ):
		self.histograms = Histogram( self.data, bins )

	def orGoodIndices( self ):
		try:
			self.goodIndicesByBeam = self.goodIndices
			self.goodIndices = self.goodIndices.all( axis = 0 ).flatten()
		except AttributeError as currentError:
			pass

	def applyDataCutoff( self, hardLimit = None ):
		try:
			self.goodIndices[ abs( self.data ) >= hardLimit ] = False
			self.goodIndices[ abs( self.data ) <= hardLimit ] = True
		except AttributeError as currentError:
			self.goodIndices = numpy.isfinite( self.data )
			self.applyDataCutoff( hardLimit )
		except Exception as currentError:
			pdb.set_trace()

class Histogram ( object ):
	def __init__( self, dataArray, bins = None ):
		self.binEdges = []
		self.binCenters = []
		self.densityInBin = []
		if bins is 'correlation':
			bins = numpy.linspace( 0, 100, 101 )
		elif bins is 'vectrinoSNR':
			bins = numpy.linspace( 0, 35, 35 )
		elif bins is 'vectorSNR':
			bins = numpy.linspace( 0, 45, 45 )
		elif bins is 'vProSNR':
			bins = numpy.linspace( 1, 60, 60 )
		elif bins is 'amplitude':
			bins = numpy.linspace( 0, 255, 256 )
		for cellNumber in range( 0, dataArray.shape[ 0 ], 1 ):
			self.binEdges.append( [] )
			self.binCenters.append( [] )
			self.densityInBin.append( [] )
			for channelNumber in range( 0, dataArray.shape[ -1 ], 1 ):
				if bins == None:
					binEdges, binCenters = self.optimalHistogramBins( dataArray[ cellNumber, :, channelNumber ] )
					densityInBin, otherBinEdges = numpy.histogram( 
							dataArray[ cellNumber, :, channelNumber ], 
							binEdges, 
							density = True )			
				elif isinstance( bins, ( int, numpy.ndarray ) ): # number of bins or binEdges specified
					densityInBin, binEdges = numpy.histogram( 							
							dataArray[ cellNumber, :, channelNumber ], 
							bins, 
							density = True )
					binWidth = ( binEdges[ 1 ] - binEdges[ 0 ] ) / 2.
					binCenters = numpy.linspace( binEdges[ 0 ] + binWidth, 
												 binEdges[ -1 ] - binWidth, 
												 densityInBin.shape[ 0 ] )
				self.binEdges[ cellNumber ].append( binEdges )
				self.binCenters[ cellNumber ].append( binCenters )
				self.densityInBin[ cellNumber ].append( densityInBin )

	def optimalHistogramBins( self, data ):
		################################################################################
		# optimal histogram bin width as shown by
		# http://www.fmrib.ox.ac.uk/analysis/techrep/tr00mj2/tr00mj2/node24.html
		# Summary reference is:
		# Izenman, 1991
		# Izenman, A. J. 1991. 
		# Recent developments in nonparametric density estimation. 
		# Journal of the American Statistical Association, 86(413):205-224.
		################################################################################
		data = data.flatten()

		n = max(data.shape) - sum( numpy.isnan( data ) )

		# need to estimate the IQR
		interQuartileRange = AF.iqr( data )
		binwidth = 2.0 * interQuartileRange * n ** (-1.0 / 3.0 )
		# have one bin centered at the median and extend to either end of the data as
		# appropriate
		medianValue = numpy.median( data )
		dataMinimumValue = min( data )
		bins = int( ( medianValue - dataMinimumValue - binwidth / 2.0 ) / binwidth )
		binCenters = medianValue - numpy.arange( bins ) * binwidth

		dataMaximumValue = max( data )
		bins = int( ( medianValue + dataMaximumValue - binwidth / 2.0 ) / binwidth )
		binCenters2ndHalf = medianValue + numpy.arange( 1, bins + 1 ) * binwidth 
		binCenters = numpy.append( binCenters, binCenters2ndHalf )
	
		binCenters.sort( )
		binEdges = binCenters - binwidth / 2
		# add one last bin edge so we get the right values to plot against binCenters
		binEdges = numpy.append( binEdges, binEdges[-1] + binwidth/2 )
		return binEdges, binCenters

class ScalarDataArray( GenericDataArray ):
	def __init__( self,
				sampleRate = 1,
				arrayLength = 1 ):
		super( ScalarDataArray, self ).__init__( sampleRate, shape = ( arrayLength, ) )

class VelocityDataArray( GenericDataArray ):
	def __init__( self,
				  sampleRate = 1,
				  shape = ( 1, 1 ), 
				  coordinateSystem = None,
				  units = 'mm/s' ):
		super( VelocityDataArray, self ).__init__( shape = shape )
		self.isInCoordinateSystem = coordinateSystem
		self.units = units
		self.calculateStatistics()
