__version__ = "$Id$"

# app constants
from appcon import *

class DocumentFrame:
	def __init__(self):
		self._activecmds={'app':{},'document':{},'pview_':{}}
	
	def set_commandlist(self, commandlist, context):
		if not self._activecmds.has_key(context):
			self._activecmds[context] = {}
		if commandlist:
			for cmd in 	commandlist:
				self._activecmds[context][cmd.__class__] = cmd
		print 'DocumentFrame.set_commandlist', commandlist, context

	def setcoords(self,coords, units=UNIT_MM):
		print 'DocumentFrame.setcoords', coords, units

	def set_dynamiclist(self, command, list):
		pass #print 'DocumentFrame.set_dynamiclist', command, list

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

#########################				
import wingeneric

import usercmd

import winstruct

import win32con

class MainWnd(wingeneric.Wnd, DocumentFrame):
	def __init__(self):
		wingeneric.Wnd.__init__(self)	
		DocumentFrame.__init__(self)
		self._title = 'GRiNS Player'

	def create(self):
		wingeneric.Wnd.create(self)
		self.setMenu()
		self.SetTimer(1, 100)
		self.HookMessage(self.OnTimer, win32con.WM_TIMER)
		self.HookMessage(self.OnCommand, win32con.WM_COMMAND)

	def OnTimer(self, params):
		self.get_toplevel().serve_events(params)
	
	def OnCommand(self, params):
		cmdid = winstruct.Win32Msg(params).id()
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
	
	def get_toplevel(self):
		import __main__
		return __main__.toplevel

	