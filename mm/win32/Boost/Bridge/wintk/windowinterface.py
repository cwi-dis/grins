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
		self._activecmds={'app':{},'document':{},'pview_':{}}
	
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
		cmd = None
		if dict: cmd = dict.get(cmdclass)
		if cmd is not None and cmd.callback:
			apply(apply, cmd.callback)
			return
		dict = self._activecmds['document']
		if dict: cmd = dict.get(cmdclass)
		if cmd is not None and cmd.callback:
			apply(apply, cmd.callback)
			return
		dict = self._activecmds['app']
		if dict: cmd = dict.get(cmdclass)
		if cmd is not None and cmd.callback:
			apply(apply, cmd.callback)
			return
				
import wingeneric
import usercmd

class MainWnd(wingeneric.Wnd, DocumentFrame):
	def __init__(self):
		wingeneric.Wnd.__init__(self)	
		DocumentFrame.__init__(self)

	def create(self):
		wingeneric.Wnd.create(self)
		self.setMenu()
		self.SetTimer(1, 100)
		self.HookMessage(self.OnTimer, win32con.WM_TIMER)
		self.HookMessage(self.OnCommand, win32con.WM_COMMAND)

	def OnTimer(self, params):
		get_toplevel().serve_events(params)
	
	def OnCommand(self, params):
		cmdid = Win32Msg(params).id()
		import usercmdui
		cmd = usercmdui.id2usercmd(cmdid)
		print cmd
		self.execute_cmd(cmd)

	def setMenu(self):
		import win32menu, MenuTemplate, usercmdui
		self._mainmenu = win32menu.Menu()
		template = MenuTemplate.MENUBAR
		self._mainmenu.create_from_menubar_spec_list(template,  usercmdui.usercmd2id)
		self.SetMenu(self._mainmenu.GetHandle())
		self.DrawMenuBar()

def mainloop():
	pass

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
			self._frame.set_commandlist(commandlist, 'app')
		return self._frame

	def getactivedocframe(self):
		return self._frame
	
	def getmainwnd(self):
		if self._frame is None:
			self._frame = MainWnd()
			self._frame.create()
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


from wintk_dialog import showmessage, showquestion
from wintk_dialog import ProgressDialog
from FileDialog import FileDialog


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


############################
# XXX: import win32mu
def loword(v):
	return v & 0xFFFF

def hiword(v):
	return (v >> 16) & 0xFFFF

class Win32Msg:
	def __init__(self,params):
		self._hwnd,self._message,self._wParam,self._lParam,self._time,self._pt=params
	def pos(self):
		return loword(self._lParam), hiword(self._lParam)
	def id(self):
		return loword(self._wParam); 
############################
