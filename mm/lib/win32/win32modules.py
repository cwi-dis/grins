__version__ = "$Id$"

# import module server
import win32ui

####################################
# get the Win32 SDK module wrapper object
# from win32ui server 

win32sdk=win32ui.GetWin32Sdk()

####################################
# get the app module wrapper objects
# from win32ui server 

cmifex=win32ui.GetCmifex()
cmifex2=win32ui.GetCmifex2()
soundex=win32ui.GetSoundex()
gifex=win32ui.GetGifex()
Htmlex=win32ui.GetHtmlex()
imageex=win32ui.GetImageex()
midiex=win32ui.GetMidiex()
mpegex=win32ui.GetMpegex()
timerex=win32ui.GetTimerex()
timerex2=win32ui.GetTimerex2()

# alias for text functionality (temporal)
textex=cmifex
	
