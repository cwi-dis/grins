# Channel list editor

# This is not the channel view, but lets you edit the collection of
# channels and their attributes.

import gl
import fl
from FL import *
import glwindow
from MMExc import *
import AttrEdit

BWIDTH = 70
BHEIGHT = 50

class ChannelEditor:
	#
	def init(self, context):
		self.context = context
		self.makeform()
		return self
	#
	def makeform(self):
		nchannels = len(self.context.channelnames)
		if nchannels == 0:
			print 'No channels!'
			raise ExitException, 1
		#
		form = fl.make_form(FLAT_BOX, nchannels*BWIDTH, BHEIGHT)
		#
		self.buttons = []
		x, y, w, h = 0, 0, BWIDTH, BHEIGHT
		for name in self.context.channelnames:
			b = form.add_button(NORMAL_BUTTON,x,y,w,h, name)
			b.set_call_back(self.callback, name)
			x = x + BWIDTH
			self.buttons.append(b)
		#
		self.editors = {}
		#
		form.show_form(PLACE_SIZE, TRUE, 'Channel List Editor')
		self.form = form
	#
	def callback(self, (obj, name)):
		if AttrEdit.haschannelattreditor(self.context, name):
			gl.ringbell()
		else:
			AttrEdit.showchannelattreditor(self.context, name)
