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
		#
		print 'parsing', filename, '...'
		self.root = MMTree.ReadFile(self.filename)
		print 'done.'
		#
		self.makecpanel()
		self.makeviews()
		#
		return self
	#
	def show(self):
		self.showcpanel()
	#
	def hide(self):
		self.hidecpanel()
		self.hideviews()
	#
	def destroy(self):
		self.destroycpanel()
		self.destroyviews()
	#
	#
	#
	def run(self):
		self.presview.run()
	#
	#
	#
	def makecpanel(self):
		self.cpanel = cp = fl.make_form(FLAT_BOX, WIDTH, HEIGHT)
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
			cp.add_button(NORMAL_BUTTON,x,y,w,h, 'Save')
		self.savebutton.set_call_back(self.save_callback, None)
		#
		y = y - h
		self.restorebutton = \
			cp.add_button(NORMAL_BUTTON,x,y,w,h, 'Restore')
		self.restorebutton.set_call_back(self.restore_callback, None)
		#
		y = y - h
		self.quitbutton = \
			cp.add_button(NORMAL_BUTTON,x,y,w,h, 'Quit')
		self.quitbutton.set_call_back(self.quit_callback, None)
		#
	#
	def showcpanel(self):
		#
		# Use the winpos attribute of the root to place the panel
		#
		h, v = MMAttrdefs.getattr(self.root, 'toplevel_winpos')
		width, height = 100, 200
		glwindow.setgeometry(h, v, width, height)
		#
		self.cpanel.show_form(PLACE_SIZE, TRUE, 'MM ed')
	#
	def hidecpanel(self):
		self.cpanel.hide_form()
	#
	def destroycpanel(self):
		self.cpanel.hide_form()
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
		import StyleEdit
		self.styleview = StyleEdit.StyleEditor().init(self.root)
	#
	def hideviews(self):
		self.blockview.hide()
		self.presview.hide()
	#
	def destroyviews(self):
		self.blockview.destroy()
		self.presview.destroy()
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
		print 'save not yet implemented'
	#
	def restore_callback(self, (obj, arg)):
		print 'restore not yet implemented'
	#
	def quit_callback(self, (obj, arg)):
		self.destroy()
		raise ExitException, 0
	#
