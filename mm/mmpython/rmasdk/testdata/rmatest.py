

# An example of a RM listener class.
# An instance can be set to receive RM status notifications
# RMListener classes may have some or all of the methods
class PrintRMListener:
	def __init__(self):
		pass
	def __del__(self):
		print 'PrintRMListener dying'
	def OnPresentationOpened(self):
		print 'OnPresentationOpened'
	def OnPresentationClosed(self):
		print 'OnPresentationClosed'
	def OnStop(self):
		print 'OnStop'
	def OnPause(self,timenow):
		print 'OnPause',timenow
	def OnBegin(self,timenow):
		print 'OnBegin',timenow
	def OnPosLength(self,pos,len):
		#print 'pos:',pos,'/',len
		pass
	def OnPreSeek(self,oldtime,newtime):
		pass
	def OnPostSeek(self,oldtime,newtime):
		pass
	def OnBuffering(self,flags,percentcomplete):
		pass
	def OnContacting(self,hostname):
		print hostname

# This class is responsible to draw the video 
# (including real pixel and real text streams)
# The Blt method is called by the RMEngine with the image info
class VideoSurface:
	def __init__(self):
		pass
	def __del__(self):
		print 'VideoSurface dying'
	def Blt(self,w,h,depth,compSheme,imageBitsOsPtr):
		print 'Blt:',w,h,depth,compSheme

# real audio
url1="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/thanks3.ra"

# real video
url2="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/test.ram"

# real text
url3="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/news.rt"

# real pixel
url4="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/fadein.rp"

import rma
player=rma.CreatePlayer()
player.SetStatusListener(PrintRMListener())
player.SetVideoSurface(VideoSurface())
player.OpenURL(url3)
player.Begin()

# for console apps, enter message loop
#import sys
#if sys.platform=='win32':
#	import win32ui
#	win32ui.GetApp().RunLoop(win32ui.GetWin32Sdk().GetDesktopWindow())

