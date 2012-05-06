from backend.libgphoto2 import wrapper
from PIL import Image
import threading
import time

import log
log.configureLogging(fileLevel=log.DEBUG,screenLevel=log.DEBUG)


api = wrapper.API(db={})

api.open()

log.info('Testing backend wrapper: %s'%api.getName())

log.info('  cameras available = %s'%(', '.join([camera.getName() for camera in api.getCameras()])))


class TimerThread(threading.Thread):
	def __init__(self,camera):
		super(TimerThread,self).__init__()
		self.camera = camera
		self.stopped = False
	
	def run(self):
		while 1:
			if self.stopped:
				break
			time.sleep(1)
			if self.stopped:
				break
			self.camera.ontimer()
			
	def stop(self):
		self.stopped = True
			

try:
	for ndx,camera in enumerate(api.getCameras()):
		log.info('  opening camera %s'%camera.getName())
	
		camera.open()
		
		t = TimerThread(camera)
		t.start()
		
		time.sleep(2.0)
		
		isCaptureDone = False
		
		def captureCallback(event):
			global isCaptureDone  
			print 'capture done'
			isCaptureDone = True
			fn = r'd:\temp\test%d.jpg'%(ndx+1)
			f = open(fn,'wb')
			f.write(event.data)
			f.close()
			
	
		def viewfinderCallback(event):
			fn = r'd:\temp\testvf%d.jpg'%(ndx+1)
			f = open(fn,'wb')
			f.write(event.data)
			f.close()
			#i = Image.open(fn)
			#i.show()
			
		log.info('  getting properties')
		properties = camera.getProperties()
	
		camera.captureComplete.connect(captureCallback)
		
		for i in range(2):	
			log.info('  capturing %d'%(i+1))
			isCaptureDone = False
			camera.capture()
			while not isCaptureDone:
				time.sleep(0.1)
			log.info('  %d done'%(i+1))
		log.info('  capturing done')
		log.info('  exit...')
	
finally:
	try: 
		t.stop()
		time.sleep(0.1)
	except: 
		pass
	api.close()			
		    
