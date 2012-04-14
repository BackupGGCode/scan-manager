from calibrator import Calibrator
from PySide import QtGui
import numpy as np

class QTCalibrator(Calibrator):
	

	def calibrate(self,original,realSizeMM=[254.0,170.0],chessboardSize=[25,17],returnAnnotatedImage=False):
		rc = Calibrator.calibrate(self,original=self.QPixmapToImage(original),realSizeMM=realSizeMM,chessboardSize=chessboardSize,returnAnnotatedImage=returnAnnotatedImage)
		if type(rc) is not bool:
			return self.imageToQPixmap(rc)
		else:
			return rc
		

	def correct(self,qpixmap):
		image = self.QPixmapToImage(qpixmap)
		rc = Calibrator.correct(self,image) 
		return self.imageToQPixmap(rc)
		

	def imageToQPixmap(self,image):			
		qimage = QtGui.QImage(image.data,image.shape[1],image.shape[0],QtGui.QImage.Format_ARGB32)
		return QtGui.QPixmap.fromImage(qimage)
	
	
	def QPixmapToImage(self,pixmap):			
		qimage = pixmap.toImage()
		size = qimage.size()
		return np.frombuffer(qimage.constBits(),np.uint8).reshape((size.height(),size.width(),4))
