# Top level control.
# Reads the file and creates a control panel that access the other functions.

from MMExc import *
import MMAttrdefs
import MMTree

import fl
from FL import *
import glwindow

WIDTH, HEIGHT = 100, 250
BHEIGHT = 30

class TopLevel():
	#
	def init(self, filename):
		self.filename = filename
		print 'parsing', self.filename, '...'
		self.root = MMTree.ReadFile(self.filename)
		print 'done.'
		self.makeviews()
		self.makecpanel()
		return self
	#
	def show(self):
		self.showcpanel()
	#
	def hide(self):
		self.hideviews()
		self.hidecpanel()
	#
	def destroy(self):
		self.destroyviews()
		self.destroycpanel()
	#
	#
	#
	def run(self):
		glwindow.mainloop()
	#
	#
	#
	def makecpanel(self):
		self.cpanel = cp = fl.make_form(FLAT_BOX, WIDTH, HEIGHT)
		self.cpshown = 0
		#
		x, y, w, h = 0, HEIGHT, WIDTH, BHEIGHT
		#
		y = y - h
		self.bvbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Block view')
		self.bvbutton.set_call_back(self.bv_callback, None)
		#
		y = y - h
		self.cvbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Channel view')
		self.cvbutton.set_call_back(self.cv_callback, None)
		#
		y = y - h
		self.pvbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Pres. view')
		self.pvbutton.set_call_back(self.pv_callback, None)
		#
		y = y - h
		self.svbutton = \
			cp.add_button(PUSH_BUTTON,x,y,w,h, 'Style view')
		self.svbutton.set_call_back(self.sv_callback, None)
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
		self.cpanel.show_form(PLACE_SIZE, TRUE, 'MM ed')
		self.cpshown = 1
	#
	def hidecpanel(self):
		if not self.cpshown: return
		self.cpanel.hide_form()
		self.cpshown = 0
	#
	def destroycpanel(self):
		self.hidecpanel()
	#
	#
	#
	def makeviews(self):
		import BlockView
		self.blockview = BlockView.BlockView().init(self.root)
		import ChannelView
		self.channelview = ChannelView.ChannelView().init(self.root)
		import Player
		self.presview = Player.Player().init(self.root)
		setcurrenttime = self.channelview.setcurrenttime
		self.presview.set_setcurrenttime_callback(setcurrenttime)
		import StyleEdit
		self.styleview = StyleEdit.StyleEditor().init(self.root)
		self.views = [self.blockview, self.channelview, \
				self.presview, self.styleview]
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
	#
	#
	def bv_callback(self, (obj, arg)):
		if obj.get_button():
			self.blockview.show()
		else:
			self.blockview.hide()
	#
	def cv_callback(self, (obj, arg)):
		if obj.get_button():
			self.channelview.show()
		else:
			self.channelview.hide()
	#
	def pv_callback(self, (obj, arg)):
		if obj.get_button():
			self.presview.show()
		else:
			self.presview.hide()
	#
	def sv_callback(self, (obj, arg)):
		if obj.get_button():
			self.styleview.show()
		else:
			self.styleview.hide()
	#
	def save_callback(self, (obj, arg)):
		if not obj.get_button(): return
		fl.show_message('You don\'t want to save this mess!','',':-)')
		obj.set_button(0)
	#
	def restore_callback(self, (obj, arg)):
		if not obj.get_button(): return
		self.destroyviews()
		self.root.Destroy()
		print 'parsing', self.filename, '...'
		self.root = MMTree.ReadFile(self.filename)
		print 'done.'
		self.makeviews()
	#
	def quit_callback(self, (obj, arg)):
		self.destroy()
		raise ExitException, 0
	#

