__version__ = "$Id$"

""" @win32doc|win32ig
The ImageLib class defined in this module
offers to other modules image decompression
and display facilities.
To achive this it loads and uses the ig module
that exports the Accusoft Image Gear library
"""

# import module server
import win32ui,win32api


#############################

class ImageLib:
	def __init__(self):
		self.lib=win32ui.Getig()
		self._imglist = []
		self._transpdict = {}

	# Delete resources
	def deltemp(self):
		global _imglist
		for img in self._imglist:
			self.lib.image_delete(img)
		self._imglist=[]
		self._transpdict = {}

	# Load image
	# 1. use abs filenames
	# 2. use temp files for gif
	# 3. use cash for gif conversion
	def load(self,filename):
		filename=self.toabs(filename)
		img,gif_trans,trans_rgb=self.lib.load_gif(filename)
		if img>=0:
			if gif_trans>=0:
				self._transpdict[img]=trans_rgb
		else:img = self.lib.load_file(filename)
		if img>=0: self._imglist.append(img)
		return img

	# Returns image size
	def size(self,img):
		if img<0: return 10,10,8
		return self.lib.image_dimensions_get(img)

	# Render image
	def render(self,hdc,bgcolor,mask, img, 
		src_x, src_y,dest_x, dest_y, width, height,rcKeep):
		if img<0: return
		if img not in self._imglist:
			# image already deleted?
			# XXXX this is a quick hack, since the image
			# shouldn't have been deleted if it was still
			# being used.
			return
		rc=(dest_x, dest_y, dest_x+width, dest_y+height)
		self.lib.ip_crop(img,rcKeep)
		if self._transpdict.has_key(img):
			trans_rgb = self._transpdict[img]
			self.lib.display_transparent_set(img,trans_rgb,1)
		self.lib.device_rect_set(img,rc)
		self.lib.display_desktop_pattern_set(img,0)
		self.lib.display_image(img,hdc)

	# Delete image (release resources)
	def delete(self,img):
		if img<0:return
		self.lib.image_delete(img)
		if img in self._imglist: 
			self._imglist.remove(img)
		if self._transpdict.has_key(img):
			del self._transpdict[img]

	# Return the absolute filename
	def toabs(self,filename):
		import os,ntpath
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)	
		return filename


win32ig=ImageLib()

	

