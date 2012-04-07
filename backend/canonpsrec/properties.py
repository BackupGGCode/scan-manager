from .defines import *
from collections import OrderedDict

__all__ = ['properties']

class PropertyDescriptions(object):

	def __init__(self):
		
		self.value2desc = {}
		self.name2desc = {}
	
	def __getitem__(self,k):
		if isinstance(k,str):
			return self.name2desc[k]
		else:
			return self.value2desc[k]

	def __getattr__(self,k):
		return self[k]
		
	def add(self,desc):
		self.value2desc[desc.code] = desc
		self.name2desc[desc.name] = desc
	
	def getValueName(self,k,v):
		if k in self:
			return self[k][v]

	def getDescription(self,k):
		if k in self:
			return self[k].description

	def getValue(self,k,v):
		if k in self:
			return self[k][v]
	
	def __contains__(self,k):
		if isinstance(k,str):
			return k in self.name2desc
		else:
			return k in self.value2desc
		
	def __iter__(self):
		for v in self.value2desc.values():
			yield v


		
properties = PropertyDescriptions()



class PropertyDescription(object):

	def __init__(self,**kargs):
		self.__dict__.update(kargs)
		self.name2value = {}
		for k,v in self.values.items():
			self.name2value[v] = k
		properties.add(self)
		
	def __getitem__(self,k):
		if isinstance(k,str):
			if k not in self.name2value: return None
			return self.name2value[k]
		else:
			if k not in self.values: return None
			return self.values[k]
			
	def __contains__(self,k):
		if isinstance(k,str):
			return k in self.name2value
		else:
			return k in self.values

	def __iter__(self):
		for v,k in self.values.items():
			yield (k,v)

		

PropertyDescription(
	code = DevicePropCode.PHOTO_EFFECT,
	name = 'PHOTO_EFFECT',
	description = 'Indicates the photo effect.',
	values = OrderedDict([
		(0x0000, 'Off'),
		(0x0001, 'Vivid'),
		(0x0002, 'Neutral'),
		(0x0003, 'Soft'),
		(0x0004, 'Sepia'),
		(0x0005, 'Monochrome'),
]))
PropertyDescription(
	code = DevicePropCode.AF_MODE,
	name = 'AF_MODE',
	description = 'Indicates the auto-focus mode set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Single Shot'),
		(0x01, 'AI Servo'),
		(0x02, 'AI Focus'),
		(0x03, 'Manual'),
		(0x04, 'Continuous'),
]))
PropertyDescription(
	code = DevicePropCode.PARAMETER_SET,
	name = 'PARAMETER_SET',
	description = 'Sets the selectable mode of development parameters.',
	values = OrderedDict([
		(0x0008, 'Standard Development Parameters'),
		(0x0010, 'Development Parameters 1'),
		(0x0020, 'Development Parameters 2'),
		(0x0040, 'Development Parameters 3'),
		(0xffff, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.SELFTIMER,
	name = 'SELFTIMER',
	description = 'Indicates the self-timer setting.',
	values = OrderedDict([
		(0, 'Self-timer Not Used'),
		(0x0064, 'Self-timer: 10 Seconds'),
		(0x0014, 'Self-timer: 2 Seconds'),
		(0xFFFF, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.BATTERY_KIND,
	name = 'BATTERY_KIND',
	description = 'Indicates the type of the battery installed in the device.',
	values = OrderedDict([
		(0x0000, 'Unknown'),
		(0x0001, 'AC power supply'),
		(0x0002, 'Lithium ion battery'),
		(0x0003, 'Nickel hydride battery'),
		(0x0004, 'Nickel cadmium battery'),
		(0x0005, 'Alkaline manganese battery'),
]))
PropertyDescription(
	code = DevicePropCode.BATTERY_STATUS,
	name = 'BATTERY_STATUS',
	description = 'Indicates the battery condition in the device.',
	values = OrderedDict([
		(0x00, 'Not defined.'),
		(0x01, 'Economy'),
		(0x02, 'Normal'),
		(0x03, 'Fine'),
		(0x04, 'Lossless'),
		(0x05, 'SuperFine'),
]))
PropertyDescription(
	code = DevicePropCode.WB_SETTING,
	name = 'WB_SETTING',
	description = 'Indicates the white balance set by a capture parameter.',
	values = OrderedDict([
		(0x0, 'Auto'),
		(0x1, 'Daylight'),
		(0x2, 'Cloudy'),
		(0x3, 'Tungsten'),
		(0x4, 'Fluorescent'),
		(0x6, 'Preset'),
		(0x7, 'Fluorescent H'),
		(0x9, 'Color Temperature'),
		(0x10, 'Custom White Balance PC-1'),
		(0x11, 'Custom White Balance PC-2'),
		(0x12, 'Custom White Balance PC-3'),
		(0x13, 'Missing number'),
		(0x14, 'Fluorescent H'),
		(0xff, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.TV,
	name = 'TV',
	description = 'Indicates the exposure compensation value.',
	values = OrderedDict([
		(0x04, 'Bulb'),
		(0x10, "30'"),
		(0x13, "25'"),
		(0x14, "20'"),
		(0x15, "20' (1/3)"),
		(0x18, "15'"),
		(0x1b, "13'"),
		(0x1c, "10'"),
		(0x1d, "10' (1/3)"),
		(0x20, "8'"),
		(0x23, "6' (1/3)"),
		(0x24, "6'"),
		(0x25, "5'"),
		(0x28, "4'"),
		(0x2b, "3'2"),
		(0x2c, "3'"),
		(0x2d, "2'5"),
		(0x30, "2'"),
		(0x33, "1'6"),
		(0x34, "1'5"),
		(0x35, "1'3"),
		(0x38, "1'"),
		(0x3b, "0'8"),
		(0x3c, "0'7"),
		(0x3d, "0'6"),
		(0x40, "0'5"),
		(0x43, "0'4"),
		(0x44, "0'3"),
		(0x45, "0'3 (1/3)"),
		(0x48, '1/4'),
		(0x4b, '1/5'),
		(0x4c, '1/6'),
		(0x4d, '1/6 (1/3)'),
		(0x50, '1/8'),
		(0x53, '1/10 (1/3)'),
		(0x54, '1/10'),
		(0x55, '1/13'),
		(0x58, '1/15'),
		(0x5b, '1/20 (1/3)'),
		(0x5c, '1/20'),
		(0x5d, '1/25'),
		(0x60, '1/30'),
		(0x63, '1/40'),
		(0x64, '1/45'),
		(0x65, '1/50'),
		(0x68, '1/60'),
		(0x6b, '1/80'),
		(0x6c, '1/90'),
		(0x6d, '1/100'),
		(0x70, '1/125'),
		(0x73, '1/160'),
		(0x74, '1/180'),
		(0x75, '1/200'),
		(0x78, '1/250'),
		(0x7b, '1/320'),
		(0x7c, '1/350'),
		(0x7d, '1/400'),
		(0x80, '1/500'),
		(0x83, '1/640'),
		(0x84, '1/750'),
		(0x85, '1/800'),
		(0x88, '1/1000'),
		(0x8b, '1/1250'),
		(0x8c, '1/1500'),
		(0x8d, '1/1600'),
		(0x90, '1/2000'),
		(0x93, '1/2500'),
		(0x94, '1/3000'),
		(0x95, '1/3200'),
		(0x98, '1/4000'),
]))
PropertyDescription(
	code = DevicePropCode.CAMERA_OUTPUT,
	name = 'CAMERA_OUTPUT',
	description = 'Indicates the destination of image signal output in the Viewfinder mode.',
	values = OrderedDict([
		(0x0000, 'Not defined.'),
		(0x0001, 'LCD'),
		(0x0002, 'Video OUT'),
		(0x0003, 'Off'),
]))
PropertyDescription(
	code = DevicePropCode.ML_SPOT_POS,
	name = 'ML_SPOT_POS',
	description = 'Indicates the spot metering position.',
	values = OrderedDict([
		(0x0, 'MlSpotPosCenter'),
		(0x1, 'MlSpotPosAfLink'),
]))
PropertyDescription(
	code = DevicePropCode.FOCUS_POINT_SETTING,
	name = 'FOCUS_POINT_SETTING',
	description = 'Set the selection mode for focusing point.',
	values = OrderedDict([
		(0x0000, 'Invalid or the setting is not changed.'),
		(0x1000, 'Focusing Point on Center Only, Manual'),
		(0x1001, 'Focusing Point on Center Only, Auto'),
		(0x3000, 'Multiple Focusing Points (No Specification), Manual'),
		(0x3001, 'Multiple Focusing Points, Auto'),
		(0x3002, 'Multiple Focusing Points (Right)'),
		(0x3003, 'Multiple Focusing Points (Center)'),
		(0x3004, 'Multiple Focusing Points (Left)'),
]))
PropertyDescription(
	code = DevicePropCode.ML_WEI_MODE,
	name = 'ML_WEI_MODE',
	description = 'Set the metering method.',
	values = OrderedDict([
		(0x00, 'Center-weighted Metering'),
		(0x01, 'Spot Metering'),
		(0x02, 'Average Metering'),
		(0x03, 'Evaluative Metering'),
		(0x04, 'Partial Metering'),
		(0x05, 'Center-weighted Average Metering'),
		(0x06, 'Spot Metering Interlocked with AF Frame'),
		(0x07, 'Multi-Spot Metering'),
		(0xFF, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.ISO,
	name = 'ISO',
	description = 'Indicates the ISO value set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Auto'),
		(0x28, '6'),
		(0x30, '12'),
		(0x38, '25'),
		(0x40, '50'),
		(0x43, '64'),
		(0x45, '80'),
		(0x48, '100'),
		(0x50, '200'),
		(0x58, '400'),
		(0x60, '800'),
		(0x68, '1600'),
		(0x70, '3200'),
		(0x78, '6400'),
]))
PropertyDescription(
	code = DevicePropCode.IMAGE_SIZE,
	name = 'IMAGE_SIZE',
	description = 'Indicates the image size set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Large'),
		(0x01, 'Medium 1'),
		(0x02, 'Small'),
		(0x03, 'Medium 2'),
		(0x07, 'Medium 3'),
]))
PropertyDescription(
	code = DevicePropCode.DISP_AV,
	name = 'DISP_AV',
	description = 'Indicates how to display the Av value as described in &quot;Reference&quot;.',
	values = OrderedDict([
		(0x0000, '1/3 Level'),
		(0x0001, 'A value corresponding to one-tenth the value retrieved by prPTP_DEV_PROP_AV_OPEN_APEX is displayed.'),
]))
PropertyDescription(
	code = DevicePropCode.BUZZER,
	name = 'BUZZER',
	description = 'Sets on/off of the device buzzer.',
	values = OrderedDict([
		(0x0000, 'On'),
		(0x0001, 'Off'),
]))
PropertyDescription(
	code = DevicePropCode.STROBE_SETTING,
	name = 'STROBE_SETTING',
	description = 'Indicates the flash set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Off'),
		(0x01, 'Auto'),
		(0x02, 'On'),
		(0x03, 'Red Eye Suppression'),
		(0x04, 'Low-speed Synchronization'),
		(0x05, 'Auto + Red Eye Suppression'),
		(0x06, 'On + Red Eye Suppression'),
]))
PropertyDescription(
	code = DevicePropCode.EZOOM,
	name = 'EZOOM',
	description = 'Indicates the starting position of electronic zoom set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Off'),
		(0x01, 'x2'),
		(0x02, 'x4'),
		(0x03, 'Smooth'),
]))
PropertyDescription(
	code = DevicePropCode.AV,
	name = 'AV',
	description = 'Indicates the aperture value.',
	values = OrderedDict([
		(0x08, '1.0'),
		(0x0b, '1.1'),
		(0x0c, '1.2'),
		(0x0d, '1.2 (1/3)'),
		(0x10, '1.4'),
		(0x13, '1.6'),
		(0x14, '1.8'),
		(0x15, '1.8 (1/3)'),
		(0x18, '2.0'),
		(0x1b, '2.2'),
		(0x1c, '2.5'),
		(0x1d, '2.5 (1/3)'),
		(0x20, '2.8'),
		(0x23, '3.2'),
		(0x24, '3.5'),
		(0x25, '3.5 (1/3)'),
		(0x28, '4.0'),
		(0x2b, '4.5 (1/3)'),
		(0x2c, '4.5'),
		(0x2d, '5.6 (1/3)'),
		(0x30, '5.6'),
		(0x33, '6.3'),
		(0x34, '6.7'),
		(0x35, '7.1'),
		(0x38, '8.0'),
		(0x3b, '9.0'),
		(0x3c, '9.5'),
		(0x3d, '10'),
		(0x40, '11'),
		(0x43, '13 (1/3)'),
		(0x44, '13'),
		(0x45, '14'),
		(0x48, '16'),
		(0x4b, '18'),
		(0x4c, '19'),
		(0x4d, '20'),
		(0x50, '22'),
		(0x53, '25'),
		(0x54, '27'),
		(0x55, '29'),
		(0x58, '32'),
		(0x5b, '36'),
		(0x5c, '38'),
		(0x5d, '40'),
		(0x60, '45'),
		(0x63, '51'),
		(0x64, '54'),
		(0x65, '57'),
		(0x68, '64'),
		(0x6b, '72'),
		(0x6c, '76'),
		(0x6d, '81'),
		(0x70, '91'),
]))
PropertyDescription(
	code = DevicePropCode.EXPOSURE_MODE,
	name = 'EXPOSURE_MODE',
	description = 'Indicates the exposure mode selected.',
	values = OrderedDict([
		(0x00, 'Auto'),
		(0x01, 'P'),
		(0x02, 'Tv'),
		(0x03, 'Av'),
		(0x04, 'M'),
		(0x05, 'A_DEP'),
		(0x06, 'M_DEP'),
		(0x07, 'Bulb'),
		(0x80, 'CAMERAM'),
		(0x81, 'MYCOLOR'),
		(0x82, 'PORTRAIT'),
		(0x83, 'LANDSCAPE'),
		(0x84, 'NIGHTSCENE'),
		(0x85, 'FOREST'),
		(0x86, 'SNOW'),
		(0x87, 'BEACH'),
		(0x88, 'FIREWORKS'),
		(0x89, 'PARTY'),
		(0x8A, 'NIGHTSNAP'),
		(0x8B, 'STITCH'),
		(0x8C, 'MOVIE'),
		(0x8D, 'CUSTOM'),
		(0x8E, 'INTERVAL'),
		(0x8F, 'DIGITALMACRO'),
		(0x90, 'LONGSHUTTER'),
		(0x91, 'UNDERWATER'),
		(0x92, 'KIDSANDPETS'),
		(0x93, 'FASTSHUTTER'),
		(0x94, 'SLOWSHUTTER'),
		(0x95, 'CUSTOM1'),
		(0x96, 'CUSTOM2'),
		(0x97, 'NEUTRAL'),
		(0x98, 'GRAY'),
		(0x99, 'SEPIA'),
		(0x9A, 'VIVID'),
		(0x9B, 'SPORTS'),
		(0x9C, 'MACRO'),
		(0x9D, 'SUPERMACRO'),
		(0x9E, 'PANFOCUS'),
		(0x9F, 'BW'),
		(0xA0, 'FLASHINHIBIT'),
]))
PropertyDescription(
	code = DevicePropCode.SLOW_SHUTTER_SETTING,
	name = 'SLOW_SHUTTER_SETTING',
	description = 'Sets the low-speed shutter.',
	values = OrderedDict([
		(0x00, 'Off'),
		(0x01, 'Night View'),
		(0x02, 'On'),
		(0x03, 'Low-speed shutter function not available.'),
		(0xFF, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.COMP_QUALITY,
	name = 'COMP_QUALITY',
	description = 'Indicates the image quality set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Not defined'),
		(0x01, 'Economy'),
		(0x02, 'Normal'),
		(0x03, 'Fine'),
		(0x04, 'Lossless'),
		(0x05, 'SuperFine'),
]))
PropertyDescription(
	code = DevicePropCode.ROTATION_ANGLE,
	name = 'ROTATION_ANGLE',
	description = 'Indicates the angle of rotation detected by the gravity sensor.',
	values = OrderedDict([
		(0x0000, '0 Degree'),
		(0x0001, '90 Degrees'),
		(0x0002, '180 Degrees'),
		(0x0003, '270 Degrees'),
		(0xffff, 'None'),
]))
PropertyDescription(
	code = DevicePropCode.ROTATION_SENSE,
	name = 'ROTATION_SENSE',
	description = 'Indicates the angle of rotation detected by the gravity sensor.',
	values = OrderedDict([
		(0x0000, 'Enable'),
		(0x0001, 'Disable'),
		(0xffff, 'None'),
]))
PropertyDescription(
	code = DevicePropCode.COLOR_GAIN,
	name = 'COLOR_GAIN',
	description = 'Indicates the color compensation set by a capture parameter.',
	values = OrderedDict([
		(-0x2, 'Low 2'),
		(-0x1, 'Low'),
		(0x0, 'Standard'),
		(0x1, 'High'),
		(0x2, 'High 2'),
]))
PropertyDescription(
	code = DevicePropCode.DISP_AV_MAX,
	name = 'DISP_AV_MAX',
	description = 'Indicates how to display the maximum Av value as described in &quot;Reference&quot;.',
	values = OrderedDict([
		(0x0000, '1/3 Level'),
		(0x0001, 'A value corresponding to one-tenth the value retrieved by prPTP_DEV_PROP_AV_MAX_APEX is displayed.'),
]))
PropertyDescription(
	code = DevicePropCode.SENSITIVITY,
	name = 'SENSITIVITY',
	description = 'Sets the sensitivity.',
	values = OrderedDict([
		(0x0, 'Standard'),
		(0x1, 'Upper 1'),
		(0x2, 'Upper 2'),
		(0xFF, 'Invalid or not set.'),
]))
PropertyDescription(
	code = DevicePropCode.SHARPNESS,
	name = 'SHARPNESS',
	description = 'Indicates the sharpness set by a capture parameter.',
	values = OrderedDict([
		(-0x2, 'Low 2'),
		(-0x1, 'Low'),
		(0x0, 'Standard'),
		(0x1, 'High'),
		(0x2, 'High 2'),
]))
PropertyDescription(
	code = DevicePropCode.AF_LIGHT,
	name = 'AF_LIGHT',
	description = 'Indicates the on/off of AF-assist light.',
	values = OrderedDict([
		(0x0000, 'Off'),
		(0x0001, 'On'),
]))
PropertyDescription(
	code = DevicePropCode.BEEP,
	name = 'BEEP',
	description = 'Indicates the buzzer set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Off'),
		(0x01, 'On'),
]))
PropertyDescription(
	code = DevicePropCode.AF_DISTANCE,
	name = 'AF_DISTANCE',
	description = 'Indicates information relating to the search range in the AF mode.',
	values = OrderedDict([
		(0x0, 'Manual'),
		(0x01, 'Auto'),
		(0x02, 'Unknown'),
		(0x03, 'Zone Focus (Close-up)'),
		(0x04, 'Zone Focus (Very Close )'),
		(0x05, 'Zone Focus (Close)'),
		(0x06, 'Zone Focus (Medium)'),
		(0x07, 'Zone Focus (Far)'),
		(0x08, 'Zone Focus (Reserved 1)'),
		(0x09, 'Zone Focus (Reserved 2)'),
		(0x0A, 'Zone Focus (Reserved 3)'),
		(0x0B, 'Zone Focus (Reserved 4)'),
		(0xFF, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.IMAGE_MODE,
	name = 'IMAGE_MODE',
	description = 'Indicates the image mode to be applied at capture.',
	values = OrderedDict([
		(0x00, 'Auto'),
		(0x01, 'Manual'),
		(0x02, 'Distant View'),
		(0x03, 'High-speed Shutter'),
		(0x04, 'Low-speed Shutter'),
		(0x05, 'Night View'),
		(0x06, 'Grayscale'),
		(0x07, 'Sepia'),
		(0x08, 'Portrait'),
		(0x09, 'Sports'),
		(0x0A, 'Macro'),
		(0x0B, 'Monochrome'),
		(0x0C, 'Pan Focus'),
		(0x0D, 'Neutral'),
		(0x0E, 'Soft'),
]))
PropertyDescription(
	code = DevicePropCode.CAPTURE_TRANSFER_MODE,
	name = 'CAPTURE_TRANSFER_MODE',
	description = 'Indicates the image transfer mode to be applied at capture.',
	values = OrderedDict([
		(0x0000, 'Not defined.'),
		(0x0002, 'Transfer Entire Image to PC'),
		(0x0004, 'Save Thumbnail Image to Device (A JPEG image will be saved as a normal JPEG file together with the entire image.)'),
		(0x0008, 'Save Entire Image to Device (A JPEG image will be saved as a normal JPEG file together with a thumbnail image.)'),
]))
PropertyDescription(
	code = DevicePropCode.FULLVIEW_FILE_FORMAT,
	name = 'FULLVIEW_FILE_FORMAT',
	description = 'Indicates the image type set by a capture parameter.',
	values = OrderedDict([
		(0x00, 'Not defined.'),
		(0x01, 'JPEG'),
		(0x02, 'CRW'),
]))
PropertyDescription(
	code = DevicePropCode.DRIVE_MODE,
	name = 'DRIVE_MODE',
	description = 'Sets the drive mode.',
	values = OrderedDict([
		(0x00, 'Single-frame Shooting'),
		(0x01, 'Continuous Shooting'),
		(0x02, 'Timer (Single) Shooting'),
		(0x04, 'Continuous Low-speed Shooting'),
		(0x05, 'Continuous High-speed Shooting'),
		(0xFF, 'Invalid or the setting is not changed.'),
]))
PropertyDescription(
	code = DevicePropCode.CONTRAST,
	name = 'CONTRAST',
	description = 'Indicates the contrast set by a capture parameter.',
	values = OrderedDict([
		(-0x2, 'Low 2'),
		(-0x1, 'Low'),
		(0x0, 'Standard'),
		(0x1, 'High'),
		(0x2, 'High 2'),
]))
PropertyDescription(
	code = DevicePropCode.EXPOSURE_COMP,
	name = 'EXPOSURE_COMP',
	description = 'Indicates exposure compensation.',
	values = OrderedDict([
		(0x00, '+3'),
		(0x03, '+2 (2/3)'),
		(0x04, '+2 (1/2)'),
		(0x05, '+2 (1/3)'),
		(0x08, '+2'),
		(0x0b, '+1 (2/3)'),
		(0x0c, '+1 (1/2)'),
		(0x0d, '+1 (1/3)'),
		(0x10, '+1'),
		(0x13, '+2/3'),
		(0x14, '+1/2'),
		(0x15, '+1/3'),
		(0x18, '0'),
		(0x1b, '-1/3'),
		(0x1c, '-1/2'),
		(0x1d, '-2/3'),
		(0x20, '-1'),
		(0x23, '-1 (1/3)'),
		(0x24, '-1 (1/2)'),
		(0x25, '-1 (2/3)'),
		(0x28, '-2'),
		(0x2b, '-2 (1/3)'),
		(0x2c, '-2 (1/2)'),
		(0x2d, '-2 (2/3)'),
		(0x30, '-3'),
]))
PropertyDescription(
	code = DevicePropCode.AEB_EXPOSURE_COMP,
	name = 'AEB_EXPOSURE_COMP',
	description = 'Indicates AEB exposure compensation.',
	values = OrderedDict([
		(0x00, '+3'),
		(0x03, '+2 (2/3)'),
		(0x04, '+2 (1/2)'),
		(0x05, '+2 (1/3)'),
		(0x08, '+2'),
		(0x0b, '+1 (2/3)'),
		(0x0c, '+1 (1/2)'),
		(0x0d, '+1 (1/3)'),
		(0x10, '+1'),
		(0x13, '+2/3'),
		(0x14, '+1/2'),
		(0x15, '+1/3'),
		(0x18, '0'),
		(0x1b, '-1/3'),
		(0x1c, '-1/2'),
		(0x1d, '-2/3'),
		(0x20, '-1'),
		(0x23, '-1 (1/3)'),
		(0x24, '-1 (1/2)'),
		(0x25, '-1 (2/3)'),
		(0x28, '-2'),
		(0x2b, '-2 (1/3)'),
		(0x2c, '-2 (1/2)'),
		(0x2d, '-2 (2/3)'),
		(0x30, '-3'),
]))
PropertyDescription(
	code = DevicePropCode.FLASH_COMP,
	name = 'FLASH_COMP',
	description = 'Indicates flash exposure compensation.',
	values = OrderedDict([
		(0x00, '+3'),
		(0x03, '+2 (2/3)'),
		(0x04, '+2 (1/2)'),
		(0x05, '+2 (1/3)'),
		(0x08, '+2'),
		(0x0b, '+1 (2/3)'),
		(0x0c, '+1 (1/2)'),
		(0x0d, '+1 (1/3)'),
		(0x10, '+1'),
		(0x13, '+2/3'),
		(0x14, '+1/2'),
		(0x15, '+1/3'),
		(0x18, '0'),
		(0x1b, '-1/3'),
		(0x1c, '-1/2'),
		(0x1d, '-2/3'),
		(0x20, '-1'),
		(0x23, '-1 (1/3)'),
		(0x24, '-1 (1/2)'),
		(0x25, '-1 (2/3)'),
		(0x28, '-2'),
		(0x2b, '-2 (1/3)'),
		(0x2c, '-2 (1/2)'),
		(0x2d, '-2 (2/3)'),
		(0x30, '-3'),
]))
