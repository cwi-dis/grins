__version__ = "$Id$"

""" @win32doc|win32ig
The ImageLib class defined in this module
offers to other modules image decompression
and display facilities.
To achive this it loads and uses the ig module
that exports the Accusoft Image Gear 
library
"""

# import module server
import win32ui,win32api


#############################
_gifcache = {}
_imglist = []

class ImageLib:
	def __init__(self):
		self.lib=win32ui.Getig()
		self.giflib=win32ui.GetGifex()
		self._tempmap={}

	# Delete resources
	def deltemp(self):
		for img in _imglist:
			self.lib.image_delete(img)
		for f in self._tempmap.values():
			win32api.DeleteFile(f)

	# Load image
	# 1. use abs filenames
	# 2. use temp files for gif
	# 3. use cash for gif conversion
	def load(self,filename):
		import tempfile
		filename=self.toabs(filename)
		self._isgif=0
		self._isgif,gif_tras=self.giflib.IsGif(filename)
		tras=0
		ldfilename=filename
		if self._isgif:
			if filename in self._tempmap.keys():
				ldfilename=self._tempmap[filename]
			else:
				ldfilename = tempfile.mktemp('.bmp')
				self._tempmap[filename]=ldfilename
				self.giflib.Gif2Bmp(filename,ldfilename)
			tras=gif_tras
		img= self.lib.load_file(ldfilename)
		if self._isgif: _gifcache[img]=tras
		_imglist.append(img)
		return img

	# Returns image size
	def size(self,img):
		return self.lib.image_dimensions_get(img)

	# Render image
	def render(self,hdc,bgcolor,mask, img, 
		src_x, src_y,dest_x, dest_y, width, height,rcKeep):
		rc=(dest_x, dest_y, dest_x+width, dest_y+height)
		self.lib.ip_crop(img,rcKeep)
		trans=-1
		try:
			trans = _gifcache[img]
		except KeyError:
			trans=-1
		if trans>=0: 
			clr=win32ui.GetWin32Sdk().GetRGBValues(trans)
			clr=self.lib.palette_entry_get(img,trans)
			self.lib.display_transparent_set(img,clr,1)
			
		self.lib.device_rect_set(img,rc)
		self.lib.display_desktop_pattern_set(img,0)
		self.lib.display_image(img,hdc)

	# Destroy image (release resources)
	def destroy(self,img):
		self.lib.image_delete(img)

	# Return the absolute filename
	def toabs(self,filename):
		import os,ntpath
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)	
		return filename

	# Return true if the file is writable
	def assertGifMediaWriteable(self,filename):
		try:
			tfp = open(filename, 'wb')
			tfp.close()
		except IOError:
			msg='GIF format has limited (demo) support for the current version.\nIt is not supported for local read-only media.\nTry testing your application on a writable media'
			win32ui.MessageBox(msg)

win32ig=ImageLib()

	

