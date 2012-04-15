import cv, cv2
import numpy as np
import cPickle



class Calibrator(object):

	
	def isReady(self):
		return hasattr(self,'cameraMatrix')
			
			
	def findCorners(self,image):
		grayImage = cv2.cvtColor(image,cv.CV_BGR2GRAY)
		
		# find chessboard corners
		(found,corners) = cv2.findChessboardCorners(
			image = grayImage,
			patternSize = self.boardSize,
			flags = cv2.CALIB_CB_ADAPTIVE_THRESH|cv2.CALIB_CB_FILTER_QUADS|cv2.CALIB_CB_FAST_CHECK
		)
		
		if not found:
			return None
		
		# refine corner locations
		cv2.cornerSubPix(
			image = grayImage,  
			corners = corners,  
			winSize = (11,11),  
			zeroZone = (-1,-1),
			criteria = (cv.CV_TERMCRIT_EPS|cv.CV_TERMCRIT_ITER,30,0.1)  
		)
		
		return corners	 
	

	def calculateDistortion(self,image):
		
		size = image.shape[1],image.shape[0]
		
		corners = self.findCorners(image)
		
		self._corners = corners
		
		if corners is None:
			return None
	
		patternPoints = np.zeros( (np.prod(self.boardSize), 3), np.float32 )
		patternPoints[:,:2] = np.indices(self.boardSize).T.reshape(-1, 2)
		
		imagePoints = np.array([corners.reshape(-1, 2)])
		objectPoints = np.array([patternPoints])
		cameraMatrix = np.zeros((3, 3))
		distCoefs = np.zeros(4)
		rc,cameraMatrix,distCoeffs,rvecs,tvecs = cv2.calibrateCamera(
			objectPoints,
			imagePoints,
			self.boardSize,
			cameraMatrix,
			distCoefs
		)
		
		newCameraMatrix,newExtents = cv2.getOptimalNewCameraMatrix(cameraMatrix,distCoeffs,size,0.0)
		
		#
		# Calculate transformed corners (corners as they would be after the image went through distortion correction)
		#
		# Need to use a nasty old cv binding to do this since the function went missing in the new cv2 bindings
		dest = cv.fromarray(corners.copy())
		cv.UndistortPoints(
			cv.fromarray(corners),
			dest,
			cv.fromarray(cameraMatrix),
			cv.fromarray(distCoeffs),
			P = cv.fromarray(newCameraMatrix),
		)
		
		self.distCoeffs = distCoeffs
		self.cameraMatrix = cameraMatrix
		self.newCameraMatrix = newCameraMatrix
		
		undistortedCorners = np.array(dest)
		return undistortedCorners 

		
	def calculatePerspective(self,corners):
		
		# now a 3-d array -- a row is new[x] and a column is new [:,x]
		rcCorners = corners.reshape(self.boardHeight,self.boardWidth,2)
		
		# find top left corner point and bottom right corner point (NOT the same as min/max x and y):
		outerPoints = self.getOuterPoints(rcCorners)
		tl,tr,bl,br = outerPoints
		
		patternSize = np.array([
			np.sqrt(((tr - tl)**2).sum(0)),
			np.sqrt(((bl - tl)**2).sum(0)),
		])
		
		inQuad = np.array(outerPoints,np.float32)
		
		outQuad = np.array([
			tl,
			tl + np.array([patternSize[0],0.0]),
			tl + np.array([0.0,patternSize[1]]),
			tl + patternSize,
		],np.float32)
		
		perspectiveTransform = cv2.getPerspectiveTransform(inQuad,outQuad)
		self.perspectiveTransform = perspectiveTransform

		# calculate DPI for the transformed image
		transformedCorners = cv2.perspectiveTransform(corners,perspectiveTransform)
		rcTransformedCorners = transformedCorners.reshape(self.boardHeight,self.boardWidth,2)
		outerPoints = self.getOuterPoints(rcTransformedCorners)
		tl,tr,bl,br = outerPoints
		transformedPatternSize = np.array([
			np.sqrt(((tr - tl)**2).sum(0)),
			np.sqrt(((bl - tl)**2).sum(0)),
		])
		dpi = (transformedPatternSize / self.realSizeMM) * 25.4
		
		# correct aspect ratio (stretch the dimension with the lowest resolution so we don't loose data needlessly)
		if dpi[1] > dpi[0]:
			self.aspectScaleX = dpi[1]/dpi[0]
			self.aspectScaleY = 1.0
			self.dpi = dpi[1]
		else:
			self.aspectScaleX = 1.0
			self.aspectScaleY = dpi[0]/dpi[1]
			self.dpi = dpi[0]
			

		
	def correctPerspective(self,image):
		size = image.shape[1],image.shape[0]
		transformed = cv2.warpPerspective(image,self.perspectiveTransform,size)
		final = cv2.resize(transformed,None,fx=self.aspectScaleX,fy=self.aspectScaleY)
		return final


	def correctDistortion(self,image):
		return cv2.undistort(image,self.cameraMatrix,self.distCoeffs,newCameraMatrix=self.newCameraMatrix)
	

	def correctDistortionWithMapCaching(self,image):
		""" This doesn't really save much time so we don't use it by default """
		size = image.shape[1],image.shape[0]
		if not hasattr(self,'_mapx'):
			self._mapx, self._mapy = cv2.initUndistortRectifyMap(
				self.cameraMatrix,
				self.distCoeffs,
				None,
				self.newCameraMatrix,
				size,
				cv2.CV_32FC1
			)

		return cv2.remap(image,self._mapx,self._mapy,cv2.INTER_LINEAR)
		
	
	def correct(self,image):
		corrected = self.correctPerspective(image)
		return self.correctDistortion(corrected)


	def calibrate(self,original,realSizeMM=[254.0,170.0],chessboardSize=[25,17],returnAnnotatedImage=False):
		self.boardWidth = chessboardSize[0]
		self.boardHeight = chessboardSize[1]
		self.boardSize = (self.boardWidth,self.boardHeight)
		self.realSizeMM = np.array(realSizeMM)
		
		undistortedCorners = self.calculateDistortion(original)
		if undistortedCorners is None:
			return False
		self.calculatePerspective(undistortedCorners)
		if returnAnnotatedImage:
			annotatedImage = original.copy()
			cv2.drawChessboardCorners(annotatedImage,tuple(chessboardSize),self._corners,True)
			return annotatedImage
		else:
			return True


	def getOuterPoints(self,rcCorners):
		tl = rcCorners[0,0]
		tr = rcCorners[0,-1]
		bl = rcCorners[-1,0]
		br = rcCorners[-1,-1]
		if tl[0] > tr[0]:
			tr,tl = tl,tr
			br,bl = bl,br
		if tl[1] > bl[1]:
			bl,tl=tl,bl
			br,tr=tr,br
		return (tl,tr,bl,br)
	
	
	def __getstate__(self):
		nd = {}
		nd.update(self.__dict__)
		for k in nd.keys():
			if k.startswith('_'):
				del(nd[k])
		return nd

	
	def save(self,file):
		if type(file) in (str,unicode):
			file = open(file,'wb')
		cPickle.dump(self,file)


	@classmethod
	def load(self,file):
		if type(file) in (str,unicode):
			file = open(file,'rb')
		return cPickle.load(file)

	
	
if __name__ == '__main__':
	
	import time
	
	original = cv2.imread(r'calibration.jpg')
	c = Calibrator()
	annotated = c.calibrate(original,returnAnnotatedImage=True)
	cv2.imwrite('calibration-annoatated.jpg',annotated)
	final = c.correct(original)
	cv2.imwrite('corrected-both.jpg',final)
	print 'done'
	
