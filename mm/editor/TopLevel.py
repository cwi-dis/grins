# Top level menu.
# Read the file and create a menu that accesses the basic functions.

import MMExc
import MMAttrdefs
import MMTree
from EditMgr import EditMgr
from Dialog import BasicDialog
import AttrEdit
import Timing

import gl, GL, DEVICE
import fl
from FL import *


# Parametrizations
WIDTH, HEIGHT = 120, 280		# Menu dimensions
BHEIGHT = 30				# Button height
HELPDIR = '/ufs/guido/mm/demo/help'	# Where to find the help files


class TopLevel() = BasicDialog():
	#
	# Initialization.
	#
	def init(self, filename):
		self.filename = filename
		print 'parsing', self.filename, '...'
		self.root = MMTree.ReadFile(self.filename)
		print 'done.'
		self.context = self.root.GetContext()
		self.editmgr = EditMgr().init(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
		self.help = None
		Timing.calctimes(self.root)
		BasicDialog.init(self, (WIDTH, HEIGHT, 'CMIF'))
		self.makeviews()	# References the form just made
		return self
	#
	# Extend inherited show/hide/destroy interface.
	#
	def show(self):
		if self.showing: return
		BasicDialog.show(self)
		fl.qdevice(DIALOG.WINQUIT)
	#
	def hide(self):
		self.hideviews()
		BasicDialog.hide(self)
	#
	def destroy(self):
		AttrEdit.closeall(self.root)
		self.destroyviews()
		BasicDialog.destroy(self)
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
		self.form = form = fl.make_form(FLAT_BOX, WIDTH, HEIGHT)
		#
		x, y, w, h = 0, HEIGHT, WIDTH, BHEIGHT
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
		y = 120
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
		if not self.editmgr.transaction():
			obj.set_button(0)
			return
		fl.show_message('You don\'t want to save this mess!','',':-)')
		obj.set_button(0)
		self.editmgr.rollback()
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
		print 'parsing', self.filename, '...'
		self.root = MMTree.ReadFile(self.filename)
		print 'done.'
		self.context = self.root.GetContext()
		self.editmgr = EditMgr().init(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
		self.makeviews()
		obj.set_button(0)
	#
	def quit_callback(self, (obj, arg)):
		self.destroy()
		raise MMExc.ExitException, 0
	#
	def help_callback(self, (obj, arg)):
		if self.help = None:
			import help
			self.help = help.HelpWindow().init(HELPDIR)
		self.help.show()
	#
	# GL event callback for WINSHUT and WINQUIT (called from glwindow)
	#
	def winshut(self):
		self.quitbutton.set_button(1)
		self.destroy()
		raise MMExc.ExitException, 0
	#
