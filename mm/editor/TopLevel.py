# Top level control window.
# Read the file and create a control panel that accesses the other functions.

import MMExc
import MMAttrdefs
import MMTree
from EditMgr import EditMgr

import Timing
import AttrEdit

import gl, GL, DEVICE
import fl
from FL import *
import glwindow

WIDTH, HEIGHT = 120, 250
BHEIGHT = 30

class TopLevel() = (glwindow.glwindow)():
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
		Timing.calctimes(self.root)
		self.makecpanel()
		self.makeviews()	# Must be called after makecpanel!
		return self
	#
	# Show/hide interface.
	#
	def show(self):
		self.showcpanel()
	#
	def hide(self):
		self.hideviews()
		self.hidecpanel()
	#
	def destroy(self):
		AttrEdit.closeall(self.root)
		self.destroyviews()
		self.destroycpanel()
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
	# Control panel handling.
	#
	def makecpanel(self):
		self.cpanel = cp = fl.make_form(FLAT_BOX, WIDTH, HEIGHT)
		self.cpshown = 0
		#
		x, y, w, h = 0, HEIGHT, WIDTH, BHEIGHT
		#
		y = y - h
		self.bvbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Hierarchy')
		#
		y = y - h
		self.cvbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Time chart')
		#
		y = y - h
		self.pvbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Presentation')
		#
		y = y - h
		self.svbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Styles')
		#
		y = 90
		#
		y = y - h
		self.savebutton = \
			cp.add_button(INOUT_BUTTON,x,y,w,h, 'Save')
		self.savebutton.set_call_back(self.save_callback, None)
		#
		y = y - h
		self.restorebutton = \
			cp.add_button(INOUT_BUTTON,x,y,w,h, 'Restore')
		self.restorebutton.set_call_back(self.restore_callback, None)
		#
		y = y - h
		self.quitbutton = \
			cp.add_button(INOUT_BUTTON,x,y,w,h, 'Quit')
		self.quitbutton.set_call_back(self.quit_callback, None)
		#
	#
	def showcpanel(self):
		if self.cpshown: return
		#
		# Use the winpos attribute of the root to place the panel
		#
		h, v = MMAttrdefs.getattr(self.root, 'toplevel_winpos')
		width, height = WIDTH, HEIGHT
		glwindow.setgeometry(h, v, width, height)
		#
		self.cpanel.show_form(PLACE_SIZE, TRUE, 'CMIF')
		gl.winset(self.cpanel.window)
		gl.winconstraints() # Allow resize
		fl.qdevice(DEVICE.WINSHUT)
		fl.qdevice(DEVICE.WINQUIT)
		glwindow.register(self, self.cpanel.window)
		self.cpshown = 1
	#
	def hidecpanel(self):
		if not self.cpshown: return
		glwindow.unregister(self)
		self.cpanel.hide_form()
		self.cpshown = 0
	#
	def destroycpanel(self):
		self.hidecpanel()
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
	# GL event callback for WINSHUT (called from glwindow)
	#
	def winshut(self):
		self.quitbutton.set_button(1)
		self.destroy()
		raise MMExc.ExitException, 0
	#
