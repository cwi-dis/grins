__version__ = "$Id$"

# constants
from appcon import *


# Registration function for close callbacks
def addclosecallback(func, args):
	pass

def removeclosecallback(func, args):
	pass

def register_event(ev, cb, arg):
	pass

# Embedding Support	
__onOpenEvent = None
def register_embedded(event, func, arg):
	print 'register_embedded', event, func, arg
	if event == 'OnOpen':
		global __onOpenEvent
		__onOpenEvent = func, arg

def unregister_embedded(event):
	pass

def close():
	import win32ui
	(win32ui.GetAfx()).PostQuitMessage(0)

class __MainDialog:
	def __init__(self):
		pass
	def set_dynamiclist(self, command, list):
		print '__MainDialog.set_dynamiclist', command, list

__main_dialog = __MainDialog()

def createmainwnd(title = None, adornments = None, commandlist = None):
	return __main_dialog

def getactivedocframe():
	return __main_dialog
	
def getmainwnd():
	return __main_dialog

def getscreensize():
	return 800, 600

class DocumentFrame:
	def __init__(self):
		self._activecmds={'frame':{},'document':{},'pview_':{}}
	def set_commandlist(self,commandlist, context):
		if not self._activecmds.has_key(context):
			self._activecmds[context] = {}
		for cmd in 	commandlist:
			self._activecmds[context][cmd.__class__] = cmd
		print 'DocumentFrame.set_commandlist', commandlist, context
	def setcoords(self,coords, units=UNIT_MM):
		print 'DocumentFrame.setcoords', coords, units
	def set_dynamiclist(self, command, list):
		print 'DocumentFrame.set_dynamiclist', command, list
	def set_toggle(self, cmdcl, onoff):
		print 'DocumentFrame.set_toggle',  cmdcl, onoff
	def setplayerstate(self, state):
		print 'DocumentFrame.setplayerstate', state
	def execute_cmd(self, cmdclass):
		dict = self._activecmds['pview_']
		cmd = dict.get(cmdclass)
		if cmd is not None and cmd.callback:
			apply(apply, cmd.callback)

__docframe = DocumentFrame()

def newdocument(cmifdoc, adornments=None, commandlist=None):
	return __docframe

def FileDialog(prompt, directory, filter, file, cb_ok, cb_cancel, existing = 0, parent = None):
	pass
			
def __open():
	filename = r'D:\ufs\Demo_xhtml_smil\Commute\Commute.grins'
	global __onOpenEvent
	event = 'OnOpen'
	if __onOpenEvent is not None:
		func, arg = __onOpenEvent
		print 'call open', filename
		func(arg, __main_dialog, event, filename)


__tick = 0
def _on_timer(params):
	global __tick
	__tick = __tick + 1
	if __tick == 10:
		__open()
	if __tick == 30:
		import usercmd
		__docframe.execute_cmd(usercmd.PLAY)
	global toplevel
	toplevel.serve_events(params)

def __on_play():
	pass
	
from GenWnd import GenWnd
pipe_wnd = None

class PipeWnd(GenWnd):
	def __init__(self, wi_module):
		GenWnd.__init__(self)
		self.__wi_module = wi_module
	
	def set_timer(self):
		import win32con
		self.HookMessage(self.OnTimer, win32con.WM_TIMER)
		self.SetTimer(1,10)

	def OnTimer(self, params):
		self.__wi_module._on_timer(params)

def mainloop():
	print 'entering main loop'
	import win32ui, win32con, win32api
	win32ui.HookWindowsMessages()
	global pipe_wnd

	import windowinterface
	pipe_wnd = PipeWnd(windowinterface)
	pipe_wnd.create()
	pipe_wnd.set_timer()

	#main = win32ui.GetAfx().GetMainWnd()
	#main.HookMessage(__on_timer, win32con.WM_TIMER)
	#main.SetTimer(1,100)
	#win32ui.GetApp().RunLoop()
	#import winuser
	#winuser.RedrawWindow(0, None, 0, win32con.RDW_INVALIDATE | win32con.RDW_ERASE | win32con.RDW_ALLCHILDREN)

def showquestion(text, parent = None):
	print text
	return 1

class ProgressDialog:
	def __init__(self, *args):
		print 'ProgressDialog', args

	def set(self, *args):
		print 'ProgressDialog', args

def settimer(sec, cb):
	global toplevel
	return toplevel.settimer(sec, cb)

def canceltimer(id):
	global toplevel
	toplevel.canceltimer(id)

def setwaiting():
	pass

def setidleproc(cb):
	global toplevel
	return toplevel.setidleproc(cb)

def cancelidleproc(id):
	global toplevel
	return toplevel.cancelidleproc(id)

import win32ui
Sdk = win32ui.GetWin32Sdk()

class Application:
	def __init__(self):
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._idles = {}
		self.__idleid = 0
		self._time = float(Sdk.GetTickCount())/TICKS_PER_SECOND

	def serve_events(self,params=None):	
		while self._timers:
			t = float(Sdk.GetTickCount())/TICKS_PER_SECOND
			sec, cb, tid = self._timers[0]
			sec = sec - (t - self._time)
			self._time = t
			if sec <= 0.002:
				del self._timers[0]
				apply(apply, cb)
			else:
				self._timers[0] = sec, cb, tid
				break
		self._time=float(Sdk.GetTickCount())/TICKS_PER_SECOND
		self.serve_timeslices()

	# Register a timer even
	def settimer(self, sec, cb):
		self._timer_id = self._timer_id + 1
		t0 = float(Sdk.GetTickCount())/TICKS_PER_SECOND
		if self._timers:
			t, a, i = self._timers[0]
			t = t - (t0 - self._time) # can become negative
			self._timers[0] = t, a, i
		self._time = t0
		t = 0
		for i in range(len(self._timers)):
			time0, dummy, tid = self._timers[i]
			if t + time0 > sec:
				self._timers[i] = (time0 - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, cb, self._timer_id))
				return self._timer_id
			t = t + time0
		self._timers.append((sec - t, cb, self._timer_id))
		return self._timer_id

	# Unregister a timer even
	def canceltimer(self, id):
		if id == None: return
		for i in range(len(self._timers)):
			t, cb, tid = self._timers[i]
			if tid == id:
				del self._timers[i]
				if i < len(self._timers):
					tt, cb, tid = self._timers[i]
					self._timers[i] = (tt + t, cb, tid)
				return
		raise 'unknown timer', id

	# Register for receiving timeslices
	def setidleproc(self, cb):
		self.__idleid = self.__idleid + 1
		self._idles[self.__idleid] = cb
		return self.__idleid

	# Register for receiving timeslices
	def cancelidleproc(self, id):
		del self._idles[id]

	# Dispatch timeslices
	def serve_timeslices(self):
		for onIdle in self._idles.values():
			onIdle()

	def _image_size(self, filename, grinsdoc):
		from win32ig import win32ig
		img = win32ig.load(filename) 
		return win32ig.size(img)[:2]

	def _image_handle(self, filename, grinsdoc):
		from win32ig import win32ig
		return win32ig.load(filename) 


toplevel = Application()
import __main__
__main__.toplevel = toplevel

class showmessage:
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'GRiNS', parent = None, identity = None):
		# XXXX If identity != None the user should have the option of not
		# showing this message again
		self._wnd=None
		if grab==0:
			self._wnd=ModelessMessageBox(text,title,parent)
			return
		if cancelCallback:
			style = win32con.MB_OKCANCEL
		else:
			style = win32con.MB_OK

		if mtype == 'error':
			style = style |win32con.MB_ICONERROR
				
		elif mtype == 'warning':
			style = style |win32con.MB_ICONWARNING
			
		elif mtype == 'information':
			style = style |win32con.MB_ICONINFORMATION
	
		elif mtype == 'message':
			style = style|win32con.MB_ICONINFORMATION
			
		elif mtype == 'question':
			style = win32con.MB_OKCANCEL|win32con.MB_ICONQUESTION
		
		if not parent or not hasattr(parent,'MessageBox'):	
			self._res = win32ui.MessageBox(text,title,style)
		else:
			self._res = parent.MessageBox(text,title,style)
		if callback and self._res==win32con.IDOK:
			apply(apply,callback)
		elif cancelCallback and self._res==win32con.IDCANCEL:
			apply(apply,cancelCallback)

	# Returns user response
	def getresult(self):
		return self._res

context = None

def newwindow(x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
	import win32window
	global context
	if context is None:
		context = win32window.ViewportContext(0, w, h, units, bgcolor or (0,0,0))
	return context._viewport

def GetImageSize(filename):
	from win32ig import win32ig
	img = win32ig.load(filename) 
	return win32ig.size(img)[:2]
