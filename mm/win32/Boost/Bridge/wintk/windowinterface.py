__version__ = "$Id$"

#
import winkernel, winuser, win32con

# constants
from appcon import *

def get_toplevel():
	import __main__
	return __main__.toplevel

# Registration function for close callbacks
def addclosecallback(func, args):
	pass

def removeclosecallback(func, args):
	pass

def register_event(ev, cb, arg):
	pass

# Embedding Support	
def register_embedded(event, func, arg):
	get_toplevel().register_embedded(event, func, arg)

def unregister_embedded(event):
	get_toplevel().unregister_embedded(event)

def close():
	pass

# return main dialog
# main dialog should support 
# def set_dynamiclist(self, command, list): pass
def createmainwnd(title = None, adornments = None, commandlist = None):
	return get_toplevel().createmainwnd(title, adornments, commandlist)

# return new document frame for doc
def newdocument(cmifdoc, adornments=None, commandlist=None):
	return get_toplevel().newdocument(cmifdoc, adornments, commandlist)

def getactivedocframe():
	return get_toplevel().getactivedocframe()
	
def getmainwnd():
	return get_toplevel().getmainwnd()

def getscreensize():
	return 800, 600

class DocumentFrame:
	def __init__(self):
		self._activecmds={'frame':{},'document':{},'pview_':{}}
	
	def set_commandlist(self, commandlist, context):
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

def FileDialog(prompt, directory, filter, file, cb_ok, cb_cancel, existing = 0, parent = None):
	pass
			
	
import wingeneric
import usercmd

class MainWnd(wingeneric.Wnd, DocumentFrame):
	def __init__(self):
		wingeneric.Wnd.__init__(self)	
		DocumentFrame.__init__(self)
		self.__state = 0

	def create(self):
		wingeneric.Wnd.create(self)
		self.SetTimer(1, 100)
		self.HookMessage(self.OnTimer, win32con.WM_TIMER)
		self.HookMessage(self.OnLButtonDblClk, win32con.WM_LBUTTONDBLCLK)

	def OnTimer(self, params):
		get_toplevel().serve_events(params)
	
	def OnLButtonDblClk(self, params):
		if self.__state == 0:
			self.__open()
			self.__state = 1
		elif self.__state == 1:
			self.execute_cmd(usercmd.PLAY)
			self.__state = 2
		elif self.__state == 2:
			self.execute_cmd(usercmd.STOP)
			self.__state = 1

	def __open(self):
		filename = r'D:\ufs\Demo_xhtml_smil\Commute\Commute.grins'
		__onOpenEvent = get_toplevel().getOpenEvent()
		event = 'OnOpen'
		if __onOpenEvent is not None:
			func, arg = __onOpenEvent
			print 'call open', filename
			func(arg, self, event, filename)

def mainloop():
	pass

def showquestion(text, parent = None):
	print text
	return 1

class ProgressDialog:
	def __init__(self, *args):
		print 'ProgressDialog', args

	def set(self, *args):
		print 'ProgressDialog', args

def settimer(sec, cb):
	return get_toplevel().settimer(sec, cb)

def canceltimer(id):
	get_toplevel().canceltimer(id)

def setwaiting():
	pass

def setidleproc(cb):
	return get_toplevel().setidleproc(cb)

def cancelidleproc(id):
	return get_toplevel().cancelidleproc(id)

class Application:
	def __init__(self):
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._idles = {}
		self.__idleid = 0
		self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND

		self._frame = None

	def newdocument(self, cmifdoc, adornments=None, commandlist=None):
		if self._frame is None:
			self._frame = MainWnd()
			self._frame.create()
		return self._frame

	def createmainwnd(self, title = None, adornments = None, commandlist = None):
		if self._frame is None:
			self._frame = MainWnd()
			self._frame.create()
		return self._frame

	def getactivedocframe(self):
		return self._frame
	
	def getmainwnd(self):
		return self._frame

	def serve_events(self,params=None):	
		while self._timers:
			t = float(winkernel.GetTickCount())/TICKS_PER_SECOND
			sec, cb, tid = self._timers[0]
			sec = sec - (t - self._time)
			self._time = t
			if sec <= 0.002:
				del self._timers[0]
				apply(apply, cb)
			else:
				self._timers[0] = sec, cb, tid
				break
		self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND
		self.serve_timeslices()

	# Register a timer even
	def settimer(self, sec, cb):
		self._timer_id = self._timer_id + 1
		t0 = float(winkernel.GetTickCount())/TICKS_PER_SECOND
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

	#
	def register_embedded(self, event, func, arg):
		if event == 'OnOpen':
			self.__onOpenEvent = func, arg

	def unregister_embedded(event):
		self.__onOpenEvent = None

	def getOpenEvent(self):
		return self.__onOpenEvent

import __main__
__main__.toplevel = Application()

class showmessage:
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'GRiNS', parent = None, identity = None):
		# XXXX If identity != None the user should have the option of not
		# showing this message again
		self._wnd = None
		if grab == 0:
			#self._wnd = ModelessMessageBox(text,title,parent)
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
			style = style | win32con.MB_ICONINFORMATION
			
		elif mtype == 'question':
			style = win32con.MB_OKCANCEL|win32con.MB_ICONQUESTION
		
		if not parent or not hasattr(parent,'MessageBox'):	
			self._res = winuser.MessageBox(text, title, style)
		else:
			self._res = parent.MessageBox(text, title, style)
		if callback and self._res == win32con.IDOK:
			apply(apply,callback)
		elif cancelCallback and self._res == win32con.IDCANCEL:
			apply(apply,cancelCallback)

	# Returns user response
	def getresult(self):
		return self._res

def newwindow(x, y, w, h, title,
		      pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
	import wintk_window
	context = wintk_window.ViewportContext(0, w, h, units, bgcolor or (0,0,0))
	return context._viewport

newcmwindow = newwindow

def GetImageSize(filename):
	from win32ig import win32ig
	img = win32ig.load(filename) 
	return win32ig.size(img)[:2]
