__version__ = "$Id$"

import gear32sd

class ImageLib:

	# Load image from filename
	def load(self, filename):
		filename = self.toabs(filename)
		if self.islibexcept(filename):
			from windowinterface import error
			raise error, 'Not an image'

		## BEGIN_INCLUDE_GIF
		try:
			img = gear32sd.load_gif(filename)
		except gear32sd.error, arg:
			try:
				img = gear32sd.load_file(filename)
			except gear32sd.error, arg:
				img = None

		## BEGIN_NOT_INCLUDE_GIF
		##	img = gear32sd.load_file(filename)
		## END_INCLUDE_GIF

		if img is None:
			errcodes = []
			for i in range(gear32sd.error_check()):
				errcodes.append(`gear32sd.error_get(i)`)
			from windowinterface import error
			raise error, 'failed to load image, errcode(s) = %s' % ', '.join(errcodes)
		return img

	# Returns image size
	def size(self, img):
		if img is None: 
			return 10, 10, 8
		return img.image_dimensions_get()

	# Get transparent color else None
	def gettransp(self, img):
		if img is not None and img.is_transparent():
			return img.get_transparent_color()
		return None

	# Read image data
	def read(self, img, crop = None):
		if img is None: 
			return None
		if crop is None:
			data = img.area_get()
		else:
			data = img.area_get(crop)
		return data

	def color_promote(self, img, flag):
		if img is not None: 
			img.color_promote(flag)

	# Render image
	def render(self, hdc, bgcolor, mask, img, src_x, src_y,dest_x, dest_y, width, height,
			   rcKeep, aspect = 'default'):
		if img is None: 
			return
		
		if aspect == 'none':
				aspect = gear32sd.IG_ASPECT_NONE
		else:
				aspect = gear32sd.IG_ASPECT_DEFAULT
		
		rc = dest_x, dest_y, dest_x+width, dest_y+height
		try:
			img.ip_crop(rcKeep)
		except:
			errcodes = []
			for i in range(gear32sd.error_check()):
				errcodes.append(`gear32sd.error_get(i)`)
			from windowinterface import error
			raise error, 'failed to load image, errcode(s) = %s' % ', '.join(errcodes)
		if img.is_transparent():
			trans_rgb = img.get_transparent_color()
			img.display_transparent_set(trans_rgb, 1)
		rc = img.display_adjust_aspect(rc, aspect)
		img.device_rect_set(rc)
		img.display_desktop_pattern_set(0)
		img.display_image(hdc)

	# Delete image (release resources)
	def delete(self,img):
		# let Python's reference counting do the work
		pass

	# Create a DDB
	def createDDB(self,img, w = 0, h = 0):
		if img is None:
			return None
		if w==0 or h==0:
			w, h, d = img.image_dimensions_get()
		hbmp, hpal = img.image_create_ddb(w, h)
		import win32ui
		bmp = win32ui.CreateBitmapFromHandle(hbmp)
		win32ui.GetWin32Sdk().DeleteObject(hpal)
		return bmp

	# Return the absolute filename
	def toabs(self, filename):
		import os,ntpath
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)
		return filename

	# Accusoft dll gets grazy when it sees the following sig(s)
	# (enters an infinite loop consuming all available sys memory)
	def islibexcept(self,filename):
		lfn = filename
		lfn.lower()
		if lfn.find('.mpeg')>=0 or lfn.find('.mpg')>=0:
			return 1
		try:
			file = open(filename, 'rb')
			formdata = file.read(4)
			file.close()
		except:
			formdata = ''
		if formdata == '.RMF':
			return 1
		return 0

win32ig = ImageLib()

	

