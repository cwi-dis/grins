# Timing arc stuff

import FL
import fl

NB = FL.NORMAL_BUTTON
XB = FL.RETURN_BUTTON
RB = FL.RADIO_BUTTON
HS = FL.HOR_SLIDER

# The Editor.
# Apart from the standard editor 'cancel', 'apply', 'reset' and 'ok' buttons,
# it has two sets of radio buttons that indicate the position of the source
# and destination of the timing arc and a slide that indicates the delay.
#
class ArcEditor:
	def init(self, arrow):
		arrow.arceditor = self
		self.arrow = arrow
		self.view, self.dst, self.arcinfo = arrow.arc
		uid, frompos, delay, topos = self.arcinfo
		self.uid = uid
		self.frompos = frompos
		self.delay = delay
		self.topos = topos
		f = fl.make_form (FL.UP_BOX,540,300)
		src = f.bgn_group()
		src_b1 = f.add_button(RB,20,180,140,40,'Source start')
		src_b1.set_call_back(self.src_b1_callback, None)
		self.src_b1 = src_b1
		src_b2 = f.add_button(RB,20,230,140,40,'Source end')
		src_b2.set_call_back(self.src_b2_callback, None)
		self.src_b2 = src_b2
		f.end_group()
		sld = f.add_valslider(HS,180,210,180,30,'Delay')
		sld.set_call_back(self.sld_callback, None)
		sld.set_slider_return(FL.FALSE)
		sld.set_slider_bounds(0.0, 100.0)
		sld.set_slider_precision(1)
		self.sld = sld
		dst = f.bgn_group()
		dst_b1 = f.add_button(RB,380,180,140,40,'Destination start')
		dst_b1.set_call_back(self.dst_b1_callback, None)
		self.dst_b1 = dst_b1
		dst_b2 = f.add_button(RB,380,230,140,40,'Destination end')
		dst_b2.set_call_back(self.dst_b2_callback, None)
		self.dst_b2 = dst_b2
		f.end_group()

		#
		# Add buttons for cancel/restore/apply/OK commands to
		# the bottom of the form, and a hint text between them.
		#
		cancel = f.add_button(NB, 2, 2, 66, 26, 'Cancel')
		cancel.set_call_back(self.cancelcallback, None)
		restore = f.add_button(NB, 72, 2, 66, 26, 'Restore')
		restore.set_call_back(self.restorecallback, None)
		apply = f.add_button(NB, 402, 2, 66, 26, 'Apply')
		apply.set_call_back(self.applycallback, None)
		ok = f.add_button(XB, 472, 2, 66, 26, 'OK')
		ok.set_call_back(self.okcallback, None)
		self.all = [src_b1, src_b2, sld, dst_b1, dst_b2, cancel, restore, apply, ok]
		self.setbuttons()
		f.show_form(FL.PLACE_MOUSE, FL.TRUE, 'Arc Editor')
		self.f = f
		return self

	def setbuttons(self):
		self.src_b1.set_button(1 - self.frompos)
		self.src_b2.set_button(self.frompos)
		self.sld.set_slider_value(self.delay)
		self.dst_b1.set_button(1 - self.topos)
		self.dst_b2.set_button(self.topos)

	def src_b1_callback(self, dummy):
		self.frompos = 0

	def src_b2_callback(self, dummy):
		self.frompos = 1

	def sld_callback(self, dummy):
		self.delay = self.sld.get_slider_value()

	def dst_b1_callback(self, dummy):
		self.topos = 0

	def dst_b2_callback(self, dummy):
		self.topos = 1

	def cancelcallback(self, dummy):
		self.close()

	def restorecallback(self, dummy):
		self.f.freeze_form()
		uid, frompos, delay, topos = self.arcinfo
		self.uid = uid
		self.frompos = frompos
		self.delay = delay
		self.topos = topos
		self.setbuttons()
		self.f.unfreeze_form()

	def applycallback(self, dummy):
		self.setvalues()

	def okcallback(self, dummy):
		self.setvalues()
		self.close()

	def setvalues(self):
		print 'arcedit', self.delay
		self.view.setarcvalues(self.arrow, (self.uid, self.frompos, self.delay, self.topos))

	def close(self):
		self.f.hide_form()
		del self.arrow.arceditor

def showarceditor(arrow):
	try:
		arceditor = arrow.arceditor
		return # Arc editor form is already active
	except NameError:
		pass # No arc editor active
	except AttributeError:
		pass # No arc editor active (new style exceptions)
	#
	arceditor = ArcEditor().init(arrow)


def hidearceditor(arrow):
	try:
		arceditor = arrow.arceditor
	except NameError:
		return # No arc editor active
	except AttributeError:
		return # No arc editor active (new style exceptions)

def hasarceditor(arrow):
	try:
		arceditor = arrow.arceditor
		return 1
	except NameError:
		return 0
	except AttributeError: # new style exceptions
		return 0

