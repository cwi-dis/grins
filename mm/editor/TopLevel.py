# Top level menu.
# Read the file and create a menu that accesses the basic functions.

import posix

import MMExc
import MMAttrdefs
import MMTree

from EditMgr import EditMgr

import glwindow
from Dialog import BasicDialog
from ViewDialog import ViewDialog

import AttrEdit
import NodeInfo

import Timing

import gl, DEVICE
import fl
from FL import *


# Parametrizations
BHEIGHT = 30				# Button height
HELPDIR = '/ufs/guido/mm/demo/help'	# Where to find the help files


class TopLevel() = ViewDialog(), BasicDialog():
	#
	# Initialization.
	#
	def init(self, filename):
		self = ViewDialog.init(self, 'toplevel_')
		self.help = None
		self.filename = filename
		self.read_it()
		width, height = \
			MMAttrdefs.getattr(self.root, 'toplevel_winsize')
		self = BasicDialog.init(self, (width, height, 'CMIF'))
		Timing.calctimes(self.root)
		self.makeviews()	# References the form just made
		return self
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
		BasicDialog.destroy(self)
		self.destroyviews()
		AttrEdit.closeall(self.root)
		NodeInfo.closeall(self.root)
	#
	# Main interface.
	#
	def run(self):
		return fl.do_forms()
	#
	# EditMgr interface (as dependent client).
	# This is the first registered client; hence its commit routine
	# will be called first, so it can fix the timing for the others.
	#
	def transaction(self):
		# Always allow transactions
		return 1
	#
	def commit(self):
		# Fix the timing -- views may depend on this.
		Timing.calctimes(self.root)
	#
	def rollback(self):
		# Nothing has happened.
		pass
	#
	# Make the menu form (called from BasicDialog.init).
	#
	def make_form(self):
		width, height = self.width, self.height
		bheight = height/9
		self.form = form = fl.make_form(FLAT_BOX, width, height)
		#
		x, y, w, h = 0, height, width, bheight
		#
		y = y - h
		self.bvbutton = \
			form.add_button(PUSH_BUTTON,x,y,w,h, 'Hierarchy')
		#
		y = y - h
		self.cvbutton = \
			form.add_button(PUSH_BUTTON,x,y,w,h, 'Time chart')
		#
		y = y - h
		self.pvbutton = \
			form.add_button(PUSH_BUTTON,x,y,w,h, 'Presentation')
		#
		y = y - h
		self.svbutton = \
			form.add_button(PUSH_BUTTON,x,y,w,h, 'Styles')
		#
		y = 4*bheight
		#
		y = y - h
		self.savebutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Save')
		self.savebutton.set_call_back(self.save_callback, None)
		#
		y = y - h
		self.restorebutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Restore')
		self.restorebutton.set_call_back(self.restore_callback, None)
		#
		y = y - h
		self.helpbutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'Help')
		self.helpbutton.set_call_back(self.help_callback, None)
		#
		y = y - h
		self.quitbutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Quit')
		self.quitbutton.set_call_back(self.quit_callback, None)
		#
	#
	# View manipulation.
	#
	def makeviews(self):
		import BlockView
		self.blockview = BlockView.BlockView().init(self.root)
		import ChannelView
		self.channelview = \
			ChannelView.ChannelView().init(self.root)
		import Player
		self.presview = Player.Player().init(self.root)
		setcurrenttime = self.channelview.setcurrenttime
		self.presview.set_setcurrenttime_callback(setcurrenttime)
		import StyleEdit
		self.styleview = StyleEdit.StyleEditor().init(self.root)
		self.views = [self.blockview, self.channelview, \
				self.presview, self.styleview]
		self.bvbutton.set_call_back(self.view_callback, self.blockview)
		self.cvbutton.set_call_back(self.view_callback, \
						self.channelview)
		self.pvbutton.set_call_back(self.view_callback, self.presview)
		self.svbutton.set_call_back(self.view_callback, self.styleview)
	#
	def hideviews(self):
		self.bvbutton.set_button(0)
		self.cvbutton.set_button(0)
		self.pvbutton.set_button(0)
		self.svbutton.set_button(0)
		for v in self.views: v.hide()
	#
	def destroyviews(self):
		self.hideviews()
		for v in self.views: v.destroy()
	#
	# Callbacks.
	#
	def view_callback(self, (obj, view)):
		if obj.get_button():
			view.show()
		else:
			view.hide()
	#
	def save_callback(self, (obj, arg)):
		if not obj.pushed: return
		# Get all windows to save their current geometry.
		self.get_geometry()
		self.save_geometry()
		for v in self.views:
			v.get_geometry()
			v.save_geometry()
		# The help window too!
		if self.help <> None:
			self.help.get_geometry()
			self.help.save_geometry()
		# Make a back-up of the original file...
		try:
			posix.rename(self.filename, self.filename + '~')
		except posix.error:
			pass
		print 'saving to', self.filename, '...'
		MMTree.WriteFile(self.root, self.filename)
		print 'done saving.'
		obj.set_button(0)
	#
	def restore_callback(self, (obj, arg)):
		if not obj.pushed: return
		AttrEdit.closeall(self.root)
		if not self.editmgr.transaction():
			obj.set_button(0)
			return
		self.editmgr.rollback()
		self.destroyviews()
		self.editmgr.unregister(self)
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
		Timing.calctimes(self.root)
		self.makeviews()
		obj.set_button(0)
	#
	def read_it(self):
		print 'parsing', self.filename, '...'
		self.root = MMTree.ReadFile(self.filename)
		print 'done.'
		self.context = self.root.GetContext()
		self.editmgr = EditMgr().init(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
	#
	def quit_callback(self, (obj, arg)):
		self.destroy()
		raise MMExc.ExitException, 0
	#
	def help_callback(self, (obj, arg)):
		if self.help = None:
			import help
			self.help = help.HelpWindow().init(HELPDIR, self.root)
		self.help.show()
	#
	# GL event callback for WINSHUT and WINQUIT (called from glwindow)
	#
	def winshut(self):
		if fl.show_question('Do you really want to quit?', '', ''):
			self.quitbutton.set_button(1)
			self.destroy()
			raise MMExc.ExitException, 0
	#
