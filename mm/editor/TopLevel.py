# Top level menu.
# Read the file and create a menu that accesses the basic functions.

import os

import gl, DEVICE
import fl
from FL import *

import glwindow
from Dialog import BasicDialog
from ViewDialog import ViewDialog

import MMExc
import MMAttrdefs
import MMTree

from EditMgr import EditMgr

import Timing


# Parametrizations
BHEIGHT = 30				# Button height

# List of currently open toplevel windows
opentops = []

class TopLevel(ViewDialog, BasicDialog):
	#
	# Initialization.
	#
	def init(self, filename):
		self = ViewDialog.init(self, 'toplevel_')
		self.filename = filename
		self.dirname, self.basename = os.path.split(self.filename)
		if self.basename[-5:] == '.cmif':
			self.basename = self.basename[:-5]
		self.read_it()
		width, height = \
			MMAttrdefs.getattr(self.root, 'toplevel_winsize')
		self = BasicDialog.init(self, width, height, self.basename)
		self.makeviews()	# References the form just made
		opentops.append(self)
		return self
	#
	def __repr__(self):
		return '<TopLevel instance, filename=' + `self.filename` + '>'
	#
	# Interface to prefix relative filenames with the CMIF file's
	# directory, if the resulting filename exists.
	#
	def findfile(self, filename):
		return self.context.findfile(filename)
	#
	# Interface to MMAttrdefs.getattr() which applies findfile to
	# the result if the attribute name is 'file'
	#
	def getattr(self, node, attrname):
		value = MMAttrdefs.getattr(node, attrname)
		if attrname == 'file':
			value = self.context.findfile(value)
		return value
	#
	# Extend inherited show/hide/destroy interface.
	#
	def show(self):
		if self.showing: return
		BasicDialog.show(self)
		fl.qdevice(DEVICE.WINQUIT)
	#
	def hide(self):
		BasicDialog.hide(self)
		self.hideviews()
	#
	def destroy(self):
		self.hide()
		self.destroyviews()
		self.root.Destroy()
		import Clipboard
		type, data = Clipboard.getclip()
		if type == 'node' and data <> None:
			Clipboard.setclip('', None)
			data.Destroy()
		for v in self.views: v.toplevel = None
		self.views = []
		BasicDialog.destroy(self)
		if self in opentops:
			opentops.remove(self)
	#
	# Main interface.
	#
	def run(self):
		return fl.do_forms()
	#
	# EditMgr interface (as dependent client).
	# This is the first registered client; hence its commit routine
	# will be called first, so it can fix the timing for the others.
	# It also flushes the attribute cache maintained by MMAttrdefs.
	#
	def transaction(self):
		# Always allow transactions
		return 1
	#
	def commit(self):
		# Fix the timing -- views may depend on this.
		self.changed = 1
		MMAttrdefs.flushcache(self.root)
		Timing.changedtimes(self.root)
	#
	def rollback(self):
		# Nothing has happened.
		pass
	#
	def kill(self):
		print 'TopLevel.kill() should not be called!'
	#
	# Make the menu form (called from BasicDialog.init).
	#
	def make_form(self):
		width, height = glwindow.mm2pixels(self.width, self.height)
		bheight = height/12.5
		self.form = form = fl.make_form(FLAT_BOX, width, height)
		#
		# The topmost button is a shortcut to start playing.
		#
		# The next four buttons in the menu open/close views.
		# They show a light which indicates whether the view
		# is open or closed.
		#
		# Their callbacks are set later, in makeviews.
		#
		x, y, w, h = 0, height, width, bheight
		#
		y = y - h
		self.playbutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Play')
		#
		y = y - h
		self.pvbutton = \
			form.add_lightbutton(PUSH_BUTTON,x,y,w,h, 'Player')
		#
		y = y - h
		self.bvbutton = \
			form.add_lightbutton(PUSH_BUTTON,x,y,w,h, \
			'Hierarchy view')
		#
		y = y - h
		self.cvbutton = \
			form.add_lightbutton(PUSH_BUTTON,x,y,w,h, \
			'Channel view')
		#
		y = y - h
		self.svbutton = \
		    form.add_lightbutton(PUSH_BUTTON,x,y,w,h, 'Style sheet')
		#
		y = y - h
		self.lvbutton = \
		    form.add_lightbutton(PUSH_BUTTON,x,y,w,h, 'Hyperlinks')
		#
		# The bottom three buttons are document-related commands.
		# They remain pressed while the command is executing.
		#
		y = 6.25*bheight
		#
		y = y - h
		self.openbutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Open...')
		self.openbutton.set_call_back(self.open_callback, None)
		#
		y = y - h
		self.savebutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Save')
		self.savebutton.set_call_back(self.save_callback, None)
		#
		y = y - h
		self.saveasbutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Save as...')
		self.saveasbutton.set_call_back(self.saveas_callback, None)
		#
		y = y - h
		self.restorebutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Restore')
		self.restorebutton.set_call_back(self.restore_callback, None)
		#
		y = y - h
		self.closebutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Close')
		self.closebutton.set_call_back(self.close_callback, None)
		#
		# The help button is at the very bottom
		#
		y = bheight
		#
		y = y - h
		self.helpbutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'Help')
		self.helpbutton.set_call_back(self.help_callback, None)
		#
	#
	# View manipulation.
	#
	def makeviews(self):
		import HierarchyView
		self.hierarchyview = HierarchyView.HierarchyView().init(self)
		#
		import ChannelView
		self.channelview = \
			ChannelView.ChannelView().init(self)
		#
		import Player
		self.player = Player.Player().init(self)
		#
		import StyleSheet
		self.styleview = StyleSheet.StyleSheet().init(self)
		#
		import LinkEdit
		self.links = LinkEdit.LinkEdit().init(self)
		#
		# Views that are destroyed by restore (currently all)
		self.views = [self.hierarchyview, self.channelview, \
			  self.player, self.styleview, self.links]
		#
		self.bvbutton.set_call_back(self.view_callback, \
			  			self.hierarchyview)
		self.cvbutton.set_call_back(self.view_callback, \
						self.channelview)
		self.pvbutton.set_call_back(self.view_callback, self.player)
		self.playbutton.set_call_back(self.play_callback, None)
		self.svbutton.set_call_back(self.view_callback, self.styleview)
		self.lvbutton.set_call_back(self.view_callback, self.links)
	#
	def hideviews(self):
		for v in self.views: v.hide()
	#
	def checkviews(self):
		# Check that the button states are still correct
		self.bvbutton.set_button(self.hierarchyview.is_showing())
		self.cvbutton.set_button(self.channelview.is_showing())
		self.pvbutton.set_button(self.player.is_showing())
		self.svbutton.set_button(self.styleview.is_showing())
		self.lvbutton.set_button(self.links.is_showing())
	#
	def destroyviews(self):
		self.hideviews()
		for v in self.views: v.destroy()
	#
	# Callbacks.
	#
	def play_callback(self, obj, arg):
		if obj.get_button():
			self.setwaiting()
			self.player.show()
			self.player.playsubtree(self.root)
			self.setready()
	#
	def view_callback(self, obj, view):
		if obj.get_button():
			self.setwaiting()
			view.show()
			self.setready()
		else:
			view.hide()
	#
	def open_callback(self, obj, arg):
		if not obj.pushed: return
		prompt = 'Open CMIF file:'
		dir = self.dirname
		if dir == '': dir = '.'
		file = self.basename + '.cmif'
		pat = '*.cmif'
		filename = fl.show_file_selector(prompt, dir, pat, file)
		if not filename:
			obj.set_button(0)
			return
		try:
			top = TopLevel().init(filename)
		except (IOError, MMExc.TypeError, MMExc.SyntaxError), msg:
			fl.show_message('Open operation failed.  File:', \
				filename, \
				'Error: ' + `msg`)
			obj.set_button(0)
			return
		top.show()
		obj.set_button(0)
	#
	def save_callback(self, obj, arg):
		if not obj.pushed: return
		ok = self.save_to_file(self.filename)
		obj.set_button(0)
	#
	def saveas_callback(self, obj, arg):
		if not obj.pushed: return
		prompt = 'Save CMIF file:'
		dir = self.dirname
		if dir == '': dir = '.'
		file = self.basename + '.cmif'
		pat = '*.cmif'
		filename = fl.show_file_selector(prompt, dir, pat, file)
		if not filename:
			obj.set_button(0)
			return
		if self.save_to_file(filename):
			self.filename = filename
			self.fixtitle()
		obj.set_button(0)
	#
	def fixtitle(self):
		self.dirname, self.basename = os.path.split(self.filename)
		if self.basename[-5:] == '.cmif':
			self.basename = self.basename[:-5]
		self.settitle(self.basename)
		for v in self.views:
			v.fixtitle()
	#
	def save_to_file(self, filename):
		# Get rid of hyperlinks outside the current tree and clipboard
		# (XXX We shouldn't *save* the links to/from the clipboard,
		# but we don't want to throw them away either...)
		roots = [self.root]
		import Clipboard
		type, data = Clipboard.getclip()
		if type == 'node' and data != None:
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
			MMTree.WriteFile(self.root, filename)
		except IOError, msg:
			fl.show_message('Save operation failed.  File:', \
				filename, \
				'Error: ' + `msg`)
			return 0
		print 'done saving.'
		self.changed = 0
		return 1
	#
	def restore_callback(self, obj, arg):
		if not obj.pushed:
			return
		if self.changed:
			l1 = 'Are you sure you want to re-read the file?'
			l2 = '(This will destroy the changes you have made)'
			l3 = 'Click Yes to restore, No to keep your changes'
			reply = fl.show_question(l1, l2, l3)
			if not reply:
				obj.set_button(0)
				return
		if not self.editmgr.transaction():
			obj.set_button(0)
			return
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
		obj.set_button(0)
	#
	def read_it(self):
		import time
		self.changed = 0
		print 'parsing', self.filename, '...'
		t0 = time.millitimer()
		self.root = MMTree.ReadFile(self.filename)
		t1 = time.millitimer()
		print 'done in', (t1-t0) * 0.001, 'sec.'
		Timing.changedtimes(self.root)
		self.context = self.root.GetContext()
		self.editmgr = EditMgr().init(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
	#
	def close_callback(self, obj, arg):
		if not obj.pushed:
			return
		self.close()
	#
	def close(self):
		ok = self.close_ok()
		if ok:
			self.destroy()
			if len(opentops) == 0:
				raise SystemExit, 0
		else:
			self.closebutton.set_button(0)
	#
	def close_ok(self):
		if not self.changed:
			return 1
		l1 = 'You haven\'t saved your changes yet;'
		l2 = 'do you want to save them before closing?'
		l3 = ''
		b1 = 'Save'
		b2 = 'Don\'t save'
		b3 = 'Cancel'
		reply = fl.show_choice(l1, l2, l3, b1, b2, b3)
		if reply == 3:
			return 0
		if reply == 2:
			return 1
		return self.save_to_file(self.filename)
	#
	def help_callback(self, obj, arg):
		import Help
		Help.showhelpwindow()
	#
	# GL event callback for WINSHUT and WINQUIT (called from glwindow)
	#
	def winshut(self):
		self.closebutton.set_button(1)
		self.close()
	#
	# watch cursor management
	#
	def setwaiting(self):
		BasicDialog.setwaiting(self)
		for v in self.views:
			v.setwaiting()
	#
	def setready(self):
		BasicDialog.setready(self)
		for v in self.views:
			v.setready()
