__version__ = "$Id$"

# import module server
import win32ui



####################################
# get the app module wrapper objects
# from win32ui server 
midiex=win32ui.GetMidiex()
mpegex=win32ui.GetMpegex()

# NOTE: the following namespaces
# will be removed (they are already only partialy used)
cmifex2=win32ui.GetCmifex2()

# REMOVED
# cmifex=win32ui.GetCmifex()
# Htmlex=win32ui.GetHtmlex()
# timerex=win32ui.GetTimerex()
# imageex=win32ui.GetImageex()
# soundex=win32ui.GetSoundex()
	
# resources
import grinsRC

#############################
_gifcache = {}
_imglist = []

class ImageLib:
	def __init__(self):
		self.lib=win32ui.Getig()
		self.giflib=win32ui.GetGifex()

	def __del__(self):
		for img in _imglist:
			self.lib.image_delete(img)

	def load(self,filename):
		self._isgif=0
		self._isgif,gif_tras=self.giflib.IsGif(filename)
		tras=0
		ldfilename=filename
		if self._isgif:
			ldfilename = filename + ".bmp"
			self.giflib.Gif2Bmp(filename,ldfilename)
			tras=gif_tras
		img= self.lib.load_file(ldfilename)
		if self._isgif: _gifcache[img]=tras
		_imglist.append(img)
		return img

	def size(self,img):
		return self.lib.image_dimensions_get(img)

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

		#self.lib.display_transparent_set(img,bgcolor,1)
		self.lib.device_rect_set(img,rc)
		self.lib.display_desktop_pattern_set(img,0)
		self.lib.display_image(img,hdc)

	def destroy(self,img):
		self.lib.image_delete(img)

imageex=ImageLib()

	

#############################
class Word:
	def __init__(self):
		pass
	def Word(self,i,prog):
		pass

wordC=Word()

