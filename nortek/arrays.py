from __future__ import print_function
import numpy
import numpy.random
import scipy.stats
import scipy.signal
import scipy
AF = None

# implement logging in this module

class GenericDataArray(dict):
	# base class for single sample volume data (e.g. Vectrino, Vector, current meters)
	# sample rate is a scalar
	# shape is an 2-tuple, the first entry is the number of cells, 
	# the second entry is the number of samples,
	# finel is the number of channels/beams/components
	def __init__( self,
				  sampleRate = 1,
				  shape = ( 1, 1, 1 ) ):
		#super( GenericDataArray, self ).__init__()
		dict.__init__( self )
		self.sampleRate = sampleRate
		self[ 'data' ] = numpy.empty( shape )
		if len( shape ) == 1:
			self.numberOfSamples = shape[ 0 ]
		else:
			self.numberOfSamples = shape[ 1 ]
		
	def calculateStatistics( self, onAxis = 1, useScreenedData = False ):
		self.mean = scipy.stats.nanmean( self[ 'data' ], onAxis )
		self.median = scipy.stats.nanmedian( self[ 'data' ], onAxis )
		self.var = scipy.stats.nanstd( self[ 'data' ], onAxis )**2

	def calculateHistograms( self, bins = None ):
		self.histograms = Histogram( self[ 'data' ], bins )

	def adaptiveOutlierRemoval( self, thresholdFactor = 3.5 ):
		if "mean" not in self:
			self.calculateStatistics()
		self[ 'goodIndices' ] = numpy.isfinite( self[ 'data' ] )
		for currentCell in range( 0, self[ 'data' ].shape[ 0 ], 1 ):
			for currentChannel in range( 0, self[ 'data' ].shape[ 2 ], 1 ):
				converge = False
				midpointWorking = self[ 'median' ][ currentCell, currentChannel ]
				# initilization for the first pass through the loop
				sortedIndices = self[ 'data' ][ currentCell, :, currentChannel ].argsort().flatten()
				numberOfGoodSamples = numpy.sum( self[ 'goodIndices' ][ currentCell, :, currentChannel ] )
			
				while converge is False and numberOfGoodSamples > 0.5 * self[ 'data' ].shape[ 1 ]:
					# estimate the standard deviation based on student's t distribution
					probabilityLow = scipy.stats.t.cdf( -1, numberOfGoodSamples )
					probabilityHi = scipy.stats.t.cdf( 1, numberOfGoodSamples )

					probabilityLowIndex = int( numpy.floor( probabilityLow * numberOfGoodSamples ) )
					probabilityHiIndex = int( numpy.ceil( probabilityHi * numberOfGoodSamples ) )

					if ( numpy.isfinite( probabilityLowIndex ) and numpy.isfinite( probabilityHiIndex ) ):
						belowMedianSTDEstimate = midpointWorking - \
							self[ 'data' ][ currentCell, sortedIndices[ probabilityLowIndex ], currentChannel ]
						aboveMedianSTDEstimate = self[ 'data' ][ currentCell, sortedIndices[ probabilityHiIndex ], currentChannel ] - \
							midpointWorking

						lowerLimit = midpointWorking - thresholdFactor * numpy.abs( aboveMedianSTDEstimate )
						upperLimit = midpointWorking + thresholdFactor * numpy.abs( belowMedianSTDEstimate )

						outlierIndices = numpy.logical_or( self[ 'data' ][ currentCell, 
																		   self[ 'goodIndices' ][ currentCell, :, currentChannel ], 
																		   currentChannel ] <= lowerLimit, 
														   self[ 'data' ][ currentCell, 
																		   self[ 'goodIndices' ][ currentCell, :, currentChannel ], 
																		   currentChannel ] >= upperLimit ).flatten()
						self[ 'goodIndices' ][ currentCell, outlierIndices, currentChannel ] = False

						formerNumberOfGoodSamples = numberOfGoodSamples
						numberOfGoodSamples = numpy.sum( self[ 'goodIndices' ][ currentCell, :, currentChannel ] )
						numberOfPointsRemoved = int( formerNumberOfGoodSamples - numberOfGoodSamples )
						#print "Removed %i points" , numberOfPointsRemoved
						if numberOfPointsRemoved is 0:
							converge = True

	def calculateTemporalSpectrum( self, numberOfWindows = 1 ):
		if "mean" not in self:
			self.calculateStatistics()
		self[ 'spectrum' ] = {}
		ensemble = numpy.arange( 0, self[ 'data' ].shape[ 1 ], 1 )
		windowLength = self[ 'data' ].shape[ 1 ] / numberOfWindows
		if self[ 'data' ].ndim == 3:
			numberOfChannels = self[ 'data' ].shape[ 2 ]
			self[ 'spectrum' ][ 'psd' ] = numpy.empty( ( self[ 'data' ].shape[ 0 ],
														 windowLength,
														 numberOfChannels ) )
			self[ 'spectrum' ][ 'psdCheck' ] = numpy.empty( ( self[ 'data' ].shape[ 0 ],
														  	  numberOfChannels ) )
		else:
			numberOfChannels = 1
			self[ 'spectrum' ][ 'psd' ] = numpy.empty( ( self[ 'data' ].shape[ 0 ],
														 windowLength ) )
			self[ 'spectrum' ][ 'psdCheck' ] = numpy.empty( ( self[ 'data' ].shape[ 0 ], ) )
		
		df = self.sampleRate / numpy.float( windowLength )
		self[ 'spectrum' ][ 'f' ] = numpy.linspace( 0, self.sampleRate, windowLength, endpoint = False )

		for currentCell in range( 0, self[ 'data' ].shape[ 0 ], 1 ):
			for currentChannel in range( 0, numberOfChannels, 1 ):
				T = self[ 'data' ][ currentCell, :, currentChannel ]
				if 'goodIndices' not in self:
					self[ 'goodIndices' ] = numpy.isfinite( self[ 'data' ] )
				if numpy.sum( self[ 'goodIndices' ][ currentCell, :, currentChannel ] ) != len( T ):
					interpolateT = scipy.interpolate.interp1d( ensemble[ self[ 'goodIndices' ][ currentCell, :, currentChannel ] ],
													T[ self[ 'goodIndices' ][ currentCell, :, currentChannel ] ],
													kind = 'linear',
													copy = False,
													bounds_error = False,
													fill_value = T[ self[ 'goodIndices' ][ currentCell, :, currentChannel ] ].mean() )
					T = interpolateT( ensemble )
				startIndexInWindow = 0
				endIndexInWindow = windowLength
				window = 0
				Stt = numpy.zeros( ( numberOfWindows, windowLength ) )
				for window in range( 0, numberOfWindows, 1 ): 
					subsetOfT = T[ startIndexInWindow:endIndexInWindow ]
					fftOfT = numpy.fft.fft( subsetOfT )
					windowStt = fftOfT * fftOfT.conjugate()
					Stt[ window, : ] = windowStt.real
					startIndexInWindow = endIndexInWindow
					endIndexInWindow = startIndexInWindow + windowLength
				Stt = numpy.mean( Stt, axis = 0 )
				# Normalize so that the integral equals the rms fluctuation squared (variance)
				self[ 'spectrum' ][ 'psd' ][ currentCell, :, currentChannel ] = Stt / ( self.sampleRate * windowLength )
				self[ 'spectrum' ][ 'psdCheck' ][ currentCell, currentChannel ] = ( numpy.sum( self[ 'spectrum' ][ 'psd' ][ currentCell, :, currentChannel ] ) * \
														df ) / T.var()
				self[ 'spectrum' ][ 'nyquistFrequency' ] = self.sampleRate / 2
				self[ 'spectrum' ][ 'nyquistIndex' ] = windowLength / 2

class Histogram(dict):
	def __init__(self, dataArray, bins = None ):
		dict.__init__( self )
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
#				if cellNumber == 0 and channelNumber == 0:
# 					self[ 'binEdges' ] = numpy.empty( ( dataArray.shape[ 0 ],
# 														  binEdges.shape[ 0 ],
# 														  dataArray.shape[ -1 ] ) )
# 					self[ 'binCenters' ] = numpy.empty( ( dataArray.shape[ 0 ],
# 														  binCenters.shape[ 0 ],
# 														  dataArray.shape[ -1 ] ) )
# 					self[ 'densityInBin' ] = numpy.empty( ( dataArray.shape[ 0 ],
# 														  densityInBin.shape[ 0 ],
# 														  dataArray.shape[ -1 ] ) )
# 				self[ 'binEdges' ][ cellNumber, :, channelNumber ] = binEdges
# 				self[ 'binCenters' ][ cellNumber, :, channelNumber ] = binCenters
# 				self[ 'densityInBin' ][ cellNumber, :, channelNumber ] = densityInBin
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

class VelocityDataArray(GenericDataArray):
	def __init__(self, sampleRate = 1, shape = (0, 0, 0), coordinateSystem = None ):
		dict.__init__( self )
		self.sampleRate = sampleRate
		self[ 'data' ] = numpy.nan * numpy.zeros( shape )
		self.numberOfSamples = shape[ 1 ]
		self.dataIsInCoordinateSystem = coordinateSystem
		self.calculateStatistics()

	def calculateScreenedStatistics( self ):
		self.screenedMean = {}
		self.screenedMedian = {}
		self.screenedStandardDeviation = {}
		if hasattr( self, "goodIndices" ):
			for component in self.componentNames:
				self.screenedMean[ component ] = numpy.mean( self.data[ component ][ self.goodIndices[ component ] ] )
				self.screenedMedian[ component ] = numpy.median( self.data[ component ][ self.goodIndices[ component ] ] )
				self.screenedStandardDeviation[ component ] = numpy.std( self.data[ component ][ self.goodIndices[ component ] ] )
		elif hasattr( self, "aorIndices" ):
			for component in self.componentNames:
				self.screenedMean[ component ] = numpy.mean( self.data[ component ][ self.aorIndices[ component ] ] )
				self.screenedMedian[ component ] = numpy.median( self.data[ component ][ self.aorIndices[ component ] ] )
				self.screenedStandardDeviation[ component ] = numpy.std( self.data[ component ][ self.aorIndices[ component ] ] )
		else:
			print("Velocity data has not been screened yet.")
