__version__ = "$Id$"

import os
import windowinterface
import MMExc, MMAttrdefs, MMTree
from EditMgr import EditMgr
import Timing
from ViewDialog import ViewDialog

# an empty document
EMPTY = "(seq '1' ((channellist) (hyperlinks)))"

# List of currently open toplevel windows
opentops = []

class TopLevel(ViewDialog):
	def __init__(self, main, filename, new_file):
		self._tracing = 0
		self.waiting = 0
		ViewDialog.__init__(self, 'toplevel_')
		self.showing = 0
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.filename = filename
		self.new_file = new_file
		self.main = main
		self.dirname, self.basename = os.path.split(self.filename)
		if self.basename[-5:] == '.cmif':
			self.basename = self.basename[:-5]
		elif self.basename[-4:] == '.mml':
			self.basename = self.basename[:-4]
		self.read_it()
		self.makeviews()
		self.window = None
		opentops.append(self)

	def __repr__(self):
		return '<TopLevel instance, filename=' + `self.filename` + '>'

	def show(self):
		if self.showing:
			return
		self.load_geometry()
		self.window = windowinterface.Window(self.basename,
				deleteCallback = (self.close_callback, ()))
		self.buttons = self.window.ButtonRow(
			[('Play', (self.play_callback, ())),
			 # The numbers below correspond with the
			 # positions in the `self.views' list (see
			 # `makeviews' below).
			 ('Player', (self.view_callback, (0,)), 't'),
			 ('Hierarchy view', (self.view_callback, (1,)), 't'),
			 ('Channel view', (self.view_callback, (2,)), 't'),
##			 ('Style sheet', (self.view_callback, (4,)), 't'),
			 ('Hyperlinks', (self.view_callback, (3,)), 't'),
			 None,
			 ('Open...', (self.open_callback, ())),
			 ('Save', (self.save_callback, ())),
			 ('Save for Player', (self.save_player_callback, ())),
			 ('Save as...', (self.saveas_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Close', (self.close_callback, ())),
			 None,
			 ('Debug', (self.debug_callback, ())),
			 ('Trace', (self.trace_callback, ()), 't')],
##			 ('Help', (self.help_callback, ()))],
			top = None, bottom = None, left = None, right = None,
			vertical = 1)
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
		for i in range(len(self.views)):
			if view is self.views[i]:
				self.buttons.setbutton(i+1, showing)

	def destroy(self):
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
		if self in opentops:
			opentops.remove(self)

	def timer_callback(self):
		self._last_timer_id = None
		self.player.timer_callback()

	def set_timer(self, delay):
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

	def view_callback(self, viewno):
		self.setwaiting()
		view = self.views[viewno]
		if view.is_showing():
			view.hide()
		else:
			view.show()
		self.setready()

	def open_okcallback(self, filename):
		try:
			top = TopLevel(self.main, filename, 0)
		except (IOError, MMExc.MTypeError, MMExc.MSyntaxError), msg:
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
		prompt = 'Open CMIF file:'
		dir = self.dirname
		if dir == '':
			dir = os.curdir
		file = self.basename + '.cmif'
		pat = '*.cmif'
		windowinterface.FileDialog(prompt, dir, pat, '',
					   self.open_okcallback, None)

	def save_callback(self):
		if self.new_file:
			self.saveas_callback()
			return
		self.setwaiting()
		ok = self.save_to_file(self.filename)
		self.setready()

	def save_player_callback(self):
		self.save_callback()
		self.setwaiting()
		import MMPlayerTree
		if self.filename[-4:] == '.mml':
			filename = self.filename[:-4] + '.cmif'
		else:
			filename = self.filename
		MMPlayerTree.WriteFile(self.root, filename)
		self.setready()

	def saveas_okcallback(self, filename):
		if not filename:
			return 'no file specified'
		self.setwaiting()
		try:
			if self.save_to_file(filename):
				self.filename = filename
				self.fixtitle()
			else:
				return 1
		finally:
			self.setready()

	def saveas_callback(self):
		prompt = 'Save CMIF file:'
		dir = self.dirname
		if dir == '':
			dir = os.curdir
		file = self.basename + '.cmif'
		pat = '*.cmif'
		windowinterface.FileDialog('Save CMIF file:', dir, pat, '',
					   self.saveas_okcallback, None)

	def fixtitle(self):
		self.dirname, self.basename = os.path.split(self.filename)
		if self.basename[-5:] == '.cmif':
			self.basename = self.basename[:-5]
		self.window.settitle(self.basename)
		for v in self.views:
			v.fixtitle()

	def save_to_file(self, filename):
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
			if filename[-4:] == '.mml':
				import MMLTree
				MMLTree.WriteFile(self.root, filename)
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
		import time
		self.changed = 0
		if self.new_file:
			self.root = MMTree.ReadString(EMPTY, self.filename)
		else:
			print 'parsing', self.filename, '...'
			t0 = time.time()
			if self.filename[-4:] == '.mml':
				import MMLTree
				self.root = MMLTree.ReadFile(self.filename)
			else:
				self.root = MMTree.ReadFile(self.filename)
			t1 = time.time()
			print 'done in', round(t1-t0, 3), 'sec.'
		Timing.changedtimes(self.root)
		self.context = self.root.GetContext()
		self.editmgr = EditMgr(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)

	def close_callback(self):
		self.setwaiting()
		self.close()
		self.setready()

	def close(self):
		ok = self.close_ok()
		if ok:
			self.destroy()
			if len(opentops) == 0:
				raise SystemExit, 0

	def close_ok(self):
		if not self.changed:
			return 1
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'
		reply = windowinterface.multchoice(prompt, [b1, b2, b3], -1)
		if reply == 2:
			return 0
		if reply == 1:
			return 1
		return self.save_to_file(self.filename)

	def debug_callback(self):
		import pdb
		pdb.set_trace()

	def trace_callback(self):
		import trace
		if self._tracing:
			trace.unset_trace()
			self._tracing = 0
		else:
			self._tracing = 1
			trace.set_trace()

	def help_callback(self):
		import Help
		Help.showhelpwindow()

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
	def jumptoexternal(self, filename, aid):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		for top in opentops:
			if not os.path.isabs(filename) and self.dirname:
				filename = os.path.join(self.dirname, filename)
			if top.is_document(filename):
				break
		else:
			try:
				top = TopLevel(self.main, filename, 0)
			except (IOError, MMExc.MTypeError, MMExc.MSyntaxError), msg:
				if type(msg) is type(self):
					if hasattr(msg, 'strerror'):
						msg = msg.strerror
					else:
						msg = msg.args[0]
				windowinterface.showmessage(
					'Open operation failed.\n'+
					'File: '+filename+'\n'+
					'Error: '+`msg`)
				return 0
		top.show()
		top.player.show((top.player.playfromanchor, (top.root, aid)))
		return 1

	def is_document(self, filename):
		import posix

		try:
			fn = self.filename
			if self.dirname:
				fn = os.path.join(self.dirname, self.filename)
			ourdata = posix.stat(fn)
			hisdata = posix.stat(filename)
		except posix.error:
			return 0
		return (ourdata == hisdata)

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
		for top in opentops:
			if top is not self:
				rv = rv + top._getlocalexternalanchors()
		return rv

	#
	# Geometry support.
	#
	def get_geometry(self):
		if self.showing:
			self.last_geometry = self.window.getgeometry()
