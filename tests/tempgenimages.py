from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
i = Image.open(r'test-image.jpg')
f = ImageFont.truetype(r'c:\windows\fonts\arialbd.ttf',int(i.size[0]/5))
i = i.resize((i.size[0]//1,i.size[1]//1))
for x in range(100):
	for side in ['L','R']:
		i2 = i.copy()
		if x != 0:
			draw = ImageDraw.Draw(i2)
			draw.setfont(f)
			draw.text((10,100),'%d%s'%(x+1,side))
		i2.save(r'd:\temp\captured\page%04d%s.jpg'%(x+1,side))
		print('%d%s'%(x+1,side))
"""
i = Image.open(r'test-image.jpg')
f = ImageFont.truetype(r'c:\windows\fonts\arialbd.ttf',100)
i = i.resize((i.size[0]//4,i.size[1]//4))
for x in range(19,30):
	for side in ['L','R']:
		i2 = i.copy()
		draw = ImageDraw.Draw(i2)
		draw.setfont(f)
		draw.text((10,100),'+%d%s'%(x+1,side))
		if side == 'L':
			i2.save(r'd:\temp\captured\camera1\newCapture%04d.jpg'%(x+1))
		else:
			i2.save(r'd:\temp\captured\camera2\newCapture%04d.jpg'%(x+1))
		print('+%d%s'%(x+1,side))
"""