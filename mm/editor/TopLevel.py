import os, sys, posixpath
import windowinterface, cmifex2, win32api, win32con, win32ui
import string
import CloseDialogRC, dialog
import MMExc, MMAttrdefs, MMTree, MMurl
from EditMgr import EditMgr
import Timing
from ViewDialog import ViewDialog
from Hlinks import TYPE_JUMP, TYPE_CALL, TYPE_FORK

# an empty document
EMPTY = "(seq '1' ((channellist ('root-layout' (type layout) (units 2) (winsize  640 480))) (hyperlinks)))"

opentops = []

class TopLevel(ViewDialog):
	def __init__(self, main, url, new_file):
		self.waiting = 0
		ViewDialog.__init__(self, 'toplevel_')
		self.showing = 0
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.new_file = new_file
		utype, url = MMurl.splittype(url)
		host, url = MMurl.splithost(url)
		dir, base = posixpath.split(url)
		if not utype and not host:
			# local file
			self.dirname = dir
		else:
			# remote file
			self.dirname = ''
		if base[-5:] == '.cmif':
			self.basename = base[:-5]
		elif base[-4:] == '.smi':
			self.basename = base[:-4]
		elif base[-5:] == '.smil':
			self.basename = base[:-5]
		else:
			self.basename = base
		if host:
			url = '//%s%s' % (host, url)
		if utype:
			url = '%s:%s' % (utype, url)
		self.filename = url
		self.main = main
		self.source = None
		self.read_it()
		self.makeviews()
		self.window = None
		opentops.append(self)

	def __repr__(self):
		return '<TopLevel instance, url=' + `self.filename` + '>'

	def show(self):
		if self.showing:
			return
		self.load_geometry()
		self.window = w = windowinterface.Window(self.basename,
				#deleteCallback = (self.close_callback, ()))
				deleteCallback = (self.close_callback, ()), havpar = 0)
		#self.buttons = self.window.ButtonRow(
		#	[('Play', (self.play_callback, ())),
		#	 # The numbers below correspond with the
		#	 # positions in the `self.views' list (see
		#	 # `makeviews' below).
		#	 ('Player', (self.view_callback, (0,)), 't'),
		#	 ('Hierarchy view', (self.view_callback, (1,)), 't'),
		#	 ('Channel view', (self.view_callback, (2,)), 't'),
##		#	 ('Style sheet', (self.view_callback, (4,)), 't'),
		#	 ('Hyperlinks', (self.view_callback, (3,)), 't'),
		#	 None,
		#	 ('Open...', (self.open_callback, ())),
		#	 ('Save', (self.save_callback, ())),
		#	 ('Save for Player', (self.save_player_callback, ())),
		#	 ('Save as...', (self.saveas_callback, ())),
		#	 ('Restore', (self.restore_callback, ())),
		#	 ('Close', (self.close_callback, ())),
		#	 None,
		#	 ('Debug', (self.debug_callback, ())),
		#	 ('Trace', (self.trace_callback, ()), 't')],
##		#	 ('Help', (self.help_callback, ()))],
		#	top = None, bottom = None, left = None, right = None,
		#	vertical = 1)


		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = constant2
		self._h = constant
		butw = 0
		max = 0

		ls = ['Play', 'Player', 'Hierarchy view', 'Channel view', 'Hyperlinks', 
			 None,  'Save', 'Save as...', 'Restore', 'Close']

		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'TextEdit'):
			ls.insert(0, 'View Source...')
		
		
		length = 0
		for item in ls:
			label = item
			if label:
				length = cmifex2.GetStringLength(w._hWnd, label)
				if length>max:
					max = length

		butw = max + 60
		self._w = self._w + butw
		#self._h = self._h + (len(ls)-1)*25
		self._h = self._h + len(ls)*25 - 8
		
		buttons = [('Play', (self.play_callback, ())),
			 # The numbers below correspond with the
			 # positions in the `self.views' list (see
			 # `makeviews' below).
			 ('Player', (self.view_callback, (0,)), 't'),
			 ('Hierarchy view', (self.view_callback, (1,)), 't'),
			 ('Channel view', (self.view_callback, (2,)), 't'),
			 ('Hyperlinks', (self.view_callback, (3,)), 't'),
			 None,
			 ('Save', (self.save_callback, ())),
##			 ('Save for Player', (self.save_player_callback, ())),
			 ('Save as...', (self.saveas_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Close', (self.close_callback, ())),
			 #None,
			 #('Help', (self.help_callback, ()))
			 ]	
		
		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'TextEdit'):
			buttons.insert(0, ('View Source...', (self.source_callback, ())))
		
		self.buttons = self.window.ButtonRow(
			buttons,
			top = 0, bottom = self._h-constant, left = 0, right = butw,
			vertical = 1)
		
		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.window._hWnd.HookKeyStroke(self.help_callback,104)
		self.window.show()
		self.showing = 1
		
	
	def hide(self):
		if not self.showing:
			return
		self.hideviews()
		self.window.close()
		self.window = None
		self.showing = 0

	def showstate(self, view, showing):
		ls = ['Player', 'Hierarchy view', 'Channel view', 'Hyperlinks']
		for i in range(len(self.views)):
			if view is self.views[i]:
				s = ls[i]
				a = 0
				for item in self.buttons._buttons:
					if item.GetWindowText()==s:
						a = self.buttons._buttons.index(item)
						break
		self.buttons.setbutton(a, showing)

	def destroy(self):
		self.editmgr.unregister(self)
		self.editmgr.destroy()
		self.destroyviews()
		if self.window:
			self.window.close()
			self.window = None
		self.showing = 0
		self.root.Destroy()
		import Clipboard
		type, data = Clipboard.getclip()
		if type == 'node' and data is not None:
			Clipboard.setclip('', None)
			data.Destroy()
		for v in self.views:
			v.toplevel = None
		self.views = []
		if self in self.main.tops:
			self.main.tops.remove(self)
			opentops.remove(self)

	def timer_callback(self):
		self._last_timer_id = None
		self.player.timer_callback()

	def set_timer(self, delay):
		#print 'Entering Editor TopLevel set_timer...'
		if self._last_timer_id is not None:
			windowinterface.canceltimer(self._last_timer_id)
			self._last_timer_id = None
		if delay:
			self._last_timer_id = windowinterface.settimer(delay,
				  (self.timer_callback, ()))

	#
	# View manipulation.
	#
	def makeviews(self):
		import HierarchyView
		self.hierarchyview = HierarchyView.HierarchyView(self)

		import ChannelView
		self.channelview = \
			ChannelView.ChannelView(self)

		import Player
		self.player = Player.Player(self)

##		import StyleSheet
##		self.styleview = StyleSheet.StyleSheet(self)

		import LinkEdit
		self.links = LinkEdit.LinkEdit(self)

		# Views that are destroyed by restore (currently all)
		self.views = [self.player, self.hierarchyview,
			      self.channelview, self.links]

	def hideviews(self):
		for v in self.views:
			v.hide()

	def destroyviews(self):
		for v in self.views:
			v.destroy()

	def checkviews(self):
		pass

	#
	# Callbacks.
	#

	def play_callback(self):
		self.setwaiting()
		self.player.show((self.player.playsubtree, (self.root,)))
		self.setready()

	def source_callback(self):
		if self.source is not None and self.source.is_closed():
			self.source.show()
			return
		elif self.source is not None:
			return
		w = windowinterface.Window('Source', resizable = 1, deleteCallback = 'hide', havpar = 0)

		import string
		tm = string.splitfields(self.root.source, '\n')
		tm2 = []
		for s in tm:
			s = s+'\015'
			tm2.append(s)
		
		t = w.TextEdit(tm2, None, editable = 0, top = 35, left = 0, right = 80*7, bottom = 300, rows = 30, columns = 80)

		b = w.ButtonRow([('Close', (w.hide, ()))], top = 5, left = 5, right = 150, bottom = 30, vertical = 0)

		cmifex2.ResizeWindow(w._hWnd, 80*7+20, 380)
		w.show()
		self.source = w
	
	

	def view_callback(self, viewno):
		self.setwaiting()
		view = self.views[viewno]
		if view.is_showing():
			view.hide()
		else:
			view.show()
		self.setready()

	def open_okcallback(self, filename):
		if os.path.isabs(filename):
			cwd = os.getcwd()
			if os.path.isdir(filename):
				dir, file = filename, os.curdir
			else:
				dir, file = os.path.split(filename)
			# XXXX maybe should check that dir gets shorter!
			while len(dir) > len(cwd):
				dir, f = os.path.split(dir)
				file = os.path.join(f, file)
			if dir == cwd:
				filename = file
		try:
			top = TopLevel(self.main, MMurl.pathname2url(filename), 0)
		except:
			msg = sys.exc_value
			if type(msg) is type(self):
				if hasattr(msg, 'strerror'):
					msg = msg.strerror
				else:
					msg = msg.args[0]
			windowinterface.showmessage('Open operation failed.\n'+
						    'File: '+filename+'\n'+
						    'Error: '+`msg`)
			return
		top.show()
		top.setready()
	
	
	def open_callback(self):
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		#Now that we have smil files change the prompt
		#pat = 'smil files (*.smi;*.smil)|*.smi;*.smil|cmif files (*.cmif)|*.cmif||'
		#file = Htmlex.FDlg('Open CMIF or SMIL file:', " ", pat) #registryex.init()
		#pat = 'cmif files (*.cmif)|*.cmif|smil files (*.smi;*.smil)|*.smi;*.smil||'
		windowinterface.FileDialog('Open CMIF or SMIL file:', cwd, '*.smil *.cmif', ' ',
					   self.open_okcallback, None, existing = 1)

	def save_callback(self):
		if self.new_file:
			self.saveas_callback()
			return
		utype, url = MMurl.splittype(self.filename)
		host, url = MMurl.splithost(url)
		if (utype and utype != 'file') or host:
			windowinterface.showmessage('Cannot save to remote URL',
						    mtype = 'warning')
			return
		file = MMurl.url2pathname(url)
		self.setwaiting()
		ok = self.save_to_file(file)
		self.setready()

	def save_player_callback(self):
		self.save_callback()
		utype, url = MMurl.splittype(self.filename)
		host, url = MMurl.splithost(url)
		if utype or host:
			# already warned
			return
		filename = MMurl.url2pathname(url)
		self.setwaiting()
		import MMPlayerTree
		if filename[-4:] == '.smi':
			filename = filename[:-4] + '.cmif'
		elif filename[-5:] == '.smil':
			filename = filename[:-5] + '.cmif'
		MMPlayerTree.WriteFile(self.root, filename)
		self.setready()


	def saveas_okcallback(self, filename):
		if not filename:
			return 'no file specified'
		self.setwaiting()
		try:
			if self.save_to_file(filename):
				self.filename = MMurl.pathname2url(filename)
				self.fixtitle()
			else:
				return 1
		finally:
			self.setready()

	def saveas_callback(self):
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		#pat = 'cmif files (*.cmif)|*.cmif|smil files (*.smi;*.smil)|*.smi;*.smil||'
		windowinterface.FileDialog('Save CMIF or SMIL file:', cwd, '*.smil *.cmif', '',
					   self.saveas_okcallback, None)

	def fixtitle(self):
		#self.dirname, self.basename = os.path.split(self.filename)
		utype, url = MMurl.splittype(self.filename)
		host, url = MMurl.splithost(url)
		dir, base = os.path.split(url)
		if not utype and not host:
			# local file
			self.dirname = dir
		else:
			# remote file
			self.dirname = ''
		if base[-5:] == '.cmif':
			self.basename = base[:-5]
		elif base[-4:] == '.smi':
			self.basename = base[:-4]
		elif base[-5:] == '.smil':
			self.basename = base[:-5]
		else:
			self.basename = base
		self.window.settitle(self.basename)
		for v in self.views:
			v.fixtitle()

	def save_to_file(self, filename):
## 		if os.path.isabs(filename):
## 			cwd = self.dirname
## 			if not cwd:
## 				cwd = os.getcwd()
## 			elif not os.path.isabs(cwd):
## 				cwd = os.path.join(os.getcwd(), cwd)
## 			if os.path.isdir(filename):
## 				windowinterface.showmessage('%s is a directory; please select a file' % filename, mtype = 'error')
## 				return
## 			# XXXX maybe should check that dir gets shorter!
## 			dir, file = os.path.split(filename)
## 			while len(dir) > len(cwd):
## 				dir, f = os.path.split(dir)
## 				file = os.path.join(f, file)
## 			if dir == cwd:
## 				filename = file
		# Get rid of hyperlinks outside the current tree and clipboard
		# (XXX We shouldn't *save* the links to/from the clipboard,
		# but we don't want to throw them away either...)
		roots = [self.root]
		import Clipboard
		type, data = Clipboard.getclip()
		if type == 'node' and data is not None:
			roots.append(data)
		self.context.sanitize_hyperlinks(roots)
		# Get all windows to save their current geometry.
		self.get_geometry()
		self.save_geometry()
		for v in self.views:
			v.get_geometry()
			v.save_geometry()
		# Make a back-up of the original file...
		try:
			os.rename(filename, filename + '~')
		except os.error:
			pass
		print 'saving to', filename, '...'
		try:
			if filename[-4:] == '.smi' or filename[-5:] == '.smil':
				import SMILTree
				SMILTree.WriteFile(self.root, filename)
			else:
				MMTree.WriteFile(self.root, filename)
		except IOError, msg:
			windowinterface.showmessage('Save operation failed.\n'+
						    'File: '+filename+'\n'+
						    'Error: '+msg[1])
			return 0
		print 'done saving.'
		self.changed = 0
		self.new_file = 0
		return 1

	def restore_callback(self):
		if self.changed:
			l1 = 'Are you sure you want to re-read the file?\n'
			l2 = '(This will destroy the changes you have made)\n'
			l3 = 'Click OK to restore, Cancel to keep your changes'
			windowinterface.showmessage(
				l1+l2+l3, mtype = 'question',
				callback = (self.do_restore, ()),
				title = 'Destroy?')
			return
		self.do_restore()

	def do_restore(self):
		if not self.editmgr.transaction():
			return
		self.setwaiting()
		self.editmgr.rollback()
		self.editmgr.unregister(self)
		self.editmgr.destroy() # kills subscribed views
		self.context.seteditmgr(None)
		self.root.Destroy()
		self.read_it()
		#
		# Move the menu window to where it's supposed to be
		#
		self.get_geometry() # From window
		old_geometry = self.last_geometry
		self.load_geometry() # From document
		new_geometry = self.last_geometry
		if new_geometry[:2]<>(-1,-1) and new_geometry <> old_geometry:
			self.hide()
			# Undo unwanted save_geometry()
			self.last_geometry = new_geometry
			self.save_geometry()
			self.show()
		#
		self.makeviews()
		self.setready()

	def read_it(self):
		import time,MMTree
		self.changed = 0
		if self.new_file:
			self.root = MMTree.ReadString(EMPTY, self.filename)
		else:
			import mimetypes
			print 'parsing', self.filename, '...'
			t0 = time.time()
			mtype = mimetypes.guess_type(self.filename)[0]
			if mtype == 'application/smil':
				import SMILTree
				self.root = SMILTree.ReadFile(self.filename)
			elif mtype == 'application/x-cmif':
				import MMTree
				self.root = MMTree.ReadFile(self.filename)
			else:
				import SMILTree
				self.root = SMILTree.ReadString('''\
<smil>
  <body>
    <ref dur="indefinite" src="%s"/>
  </body>
</smil>
''' % self.filename, self.filename)
			t1 = time.time()
			print 'done in', round(t1-t0, 3), 'sec.'
		Timing.changedtimes(self.root)
		self.context = self.root.GetContext()
		self.editmgr = EditMgr(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)

	def close_callback(self):
		self.setwaiting()
		if self.source and not self.source.is_closed():
			self.source.close()
		self.source = None
		self.close()
		self.setready()

	def close(self):
		ok = self.close_ok()
		if ok:
			CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
			dir = CMIFDIR+"\\Help\\Cmifed.hlp"
			win32api.WinHelp(self.window._hWnd.GetSafeHwnd(),dir,win32con.HELP_QUIT,0)
			self.destroy()
		#	if len(opentops) == 0:
		#		## there seems to be a bug when raising SystemExit exception
		#		## temporarily repolaced with Destroying Main Window
		#		#raise SystemExit, 0
		#		import win32ui
		#		h1 = win32ui.GetMainFrame()
		#		h1.DestroyWindow()


	def close_ok(self):
		if not self.changed:
			return 1
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'
		print 'Loading Library.............'
		#PydPath = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Python\\PythonCore\\1.4.0\\PythonPath\\PyDLLs")
		PydPath = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\PyDLLs")
		cmifexPath = PydPath + "\\cmifex.pyd"

		try:
			dll=win32ui.LoadLibrary(cmifexPath)
		except win32ui:
			print "Could not Locate CmifEx.Pyd"	

		#self.d = dialog.Dialog(CloseDialogRC.IDD_CLOSING_DIALOG, dll)
		##destroying the dialog means 'cancel'
		#self.reply = 2           
		#self.d.HookCommand(self.button_callback, CloseDialogRC.IDC_SAVE_BUTTON)
		#self.d.HookCommand(self.button_callback, CloseDialogRC.IDC_DONTSAVE_BUTTON)
		#self.d.HookCommand(self.button_callback, CloseDialogRC.IDC_CANCEL_BUTTON)
		#self.d.DoModal()
		##reply = windowinterface.multchoice(prompt, [b1, b2, b3], -1)
		#reply = self.reply
		#if reply == 2:
		#	return 0
		#if reply == 1:
		#	return 1

		reply = cmifex2.MesBox(prompt,"Warning !"," qc")
		
		if reply == win32con.IDCANCEL:
			cmifex2.SetFlag(1)
			return 0
		
		if reply == win32con.IDNO:
			self.reply = 1
			return 1

		utype, url = MMurl.splittype(self.filename)
		host, url = MMurl.splithost(url)
		#if utype or host:
		if (utype and utype != 'file') or host:
			windowinterface.showmessage('Cannot save to URL',
						    mtype = 'warning')
			return 0
		file = MMurl.url2pathname(url)
		return self.save_to_file(file)

	def button_callback(self, par1, par2):
		if (par1 == CloseDialogRC.IDC_SAVE_BUTTON):
			self.reply = 0
		if (par1 == CloseDialogRC.IDC_DONTSAVE_BUTTON):
			self.reply = 1
		if (par1 == CloseDialogRC.IDC_CANCEL_BUTTON):
			self.reply = 2
		self.d.EndDialog(0)

			
	
	def debug_callback(self):
		import pdb
		pdb.set_trace()

	def trace_callback(self):
		import trace
		for item in self.buttons._buttons:
			if item.GetWindowText()=='Trace':
				a = self.buttons._buttons.index(item)
				break
		if self._tracing:
			trace.unset_trace()
			self._tracing = 0
			self.buttons.setbutton(a, self._tracing)
		else:
			self._tracing = 1
			self.buttons.setbutton(a, self._tracing)
			trace.set_trace()

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow(self.window._hWnd)
		#CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
		#dir = CMIFDIR+"\\Help\\Cmifed.hlp"
		#win32api.WinHelp(self.window._hWnd.GetSafeHwnd(),dir,win32con.HELP_CONTENTS,0)

	def setwaiting(self):
		if self.waiting: return
		self.waiting = 1
		windowinterface.setcursor('watch')
		for v in self.views:
			v.setwaiting()

	def setready(self):
		if not self.waiting: return
		self.waiting = 0
		for v in self.views:
			v.setready()
		windowinterface.setcursor('')

	#
	# EditMgr interface (as dependent client).
	# This is the first registered client; hence its commit routine
	# will be called first, so it can fix the timing for the others.
	# It also flushes the attribute cache maintained by MMAttrdefs.
	#
	def transaction(self):
		# Always allow transactions
		return 1

	def commit(self):
		# Fix the timing -- views may depend on this.
		self.changed = 1
		MMAttrdefs.flushcache(self.root)
		Timing.changedtimes(self.root)

	def rollback(self):
		# Nothing has happened.
		pass

	def kill(self):
		print 'TopLevel.kill() should not be called!'

	#
	# Global hyperjump interface
	#
	def jumptoexternal(self, uid, aid, atype):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		import MMurl
		if '/' not in uid:
			url = self.filename
		elif uid[-2:] == '/1':
			url = uid[:-2]
		else:
			url = uid
		url = MMurl.basejoin(self.filename, url)
		for top in self.main.tops:
			if top is not self and top.is_document(url):
				break
		else:
			try:
				top = TopLevel(self.main, url, 0)
			except:
				msg = sys.exc_value
				if type(msg) is type(self):
					if hasattr(msg, 'strerror'):
						msg = msg.strerror
					else:
						msg = msg.args[0]
				windowinterface.showmessage(
					'Open operation failed.\n'+
					'File: '+url+'\n'+
					'Error: '+`msg`)
				return 0
		top.show()
		node = top.root
		if '/' not in uid:
			try:
				node = top.root.context.mapuid(uid)
			except NoSuchUIDError:
				print 'uid not found in document'
		top.player.show((top.player.playfromanchor, (node, aid)))
		if atype == TYPE_CALL:
			self.player.pause(1)
		elif atype == TYPE_JUMP:
			self.close()
		return 1

	def is_document(self, url):
		return self.filename == url
## 		import os

## 		try:
## 			fn = self.filename
## 			if self.dirname:
## 				fn = os.path.join(self.dirname, self.filename)
## 			ourdata = os.stat(fn)
## 			hisdata = os.stat(filename)
## 		except os.error:
## 			return 0
## 		return (ourdata == hisdata)

	def _getlocalexternalanchors(self):
		fn = self.filename
		if not '/' in fn:
			fn = './' + fn
		rv = []
		alist = MMAttrdefs.getattr(self.root, 'anchorlist')
		for i, t, v in alist:
			rv.append((fn, i))
		return rv

	def getallexternalanchors(self):
		rv = []
		for top in self.main.tops:
			if top is not self:
				rv = rv + top._getlocalexternalanchors()
		return rv

	#
	# Geometry support.
	#
	def get_geometry(self):
		if self.showing:
			self.last_geometry = self.window.getgeometry()
