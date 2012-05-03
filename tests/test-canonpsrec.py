from backend.libgphoto2 import wrapper
from PIL import Image

api = wrapper.API(db={})

api.open()

try:
	for ndx,camera in enumerate(api.getCameras()):
		print(camera.getName())
		viewfinderComplete = [False]
		camera.open()
		
		def captureCallback(event):
			f = open(r'd:\temp\test%d.jpg'%(ndx+1),'wb')
			f.write(event.data)
			f.close()
			#i = Image.open(r'd:\temp\test.jpg')
			#i.show()

		def viewfinderCallback(event):
			f = open(r'd:\temp\testvf%d.jpg'%(ndx+1),'wb')
			f.write(event.data)
			f.close()
			i = Image.open(r'd:\temp\testvf.jpg')
			i.show()
			viewfinderComplete[0] = True
			
		"""
		properties = camera.getProperties()
		
		print(properties[0].getRawValue())
		properties[0].setRawValue(1)
	
		camera.captureComplete.connect(captureCallback)	
		camera.capture()
		
		if camera.hasViewfinder():
			camera.viewfinderFrame.connect(viewfinderCallback)
			camera.startViewfinder()
		
		t = time.time()
		while 1:
			if viewfinderComplete[0]:
				break
			if time.time() - t > 5:
				print('timed out waiting for viewfinder data')
				break
		#camera.stopViewfinder()
		#camera.camera.stopRemote()
		"""
	
	print('capturing on both')
	for ndx,camera in enumerate(api.getCameras()):
		print('capture on',camera.getName())
		camera.capture()
			

finally:
	api.close()
	    
