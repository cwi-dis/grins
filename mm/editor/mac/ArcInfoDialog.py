"""Dialog for the ArcInfo editor.

The ArcInfoDialog consists of two option menus (lists of strings of
which exactly one item is selected): the source list and the
destination list.  The contents of these lists are dynamically
determined, but don't change during the life time of a dialog window.
There are no callbacks associated with these lists, but it must be
possible to get and set the current selection.

Furthermore, there should be an interface in which a floating point
number in the range 0 .. 100 can be specified.  (Only two digits of
precision are required, so whole numbers if >= 10, one decimal if less
than 10 but >= 1, two decimals if less than 1.)  For this interface
there is also no callback.  [ In X this is implemented as a slider,
but that is not required. ]

Lastly, there are four buttons `Cancel', `Restore', `Apply', and `OK'.
For these buttons there are callbacks.

"""

__version__ = "$Id$"

import Dlg
import Qd
import windowinterface
import WMEVENTS
import string
import MacOS

def ITEMrange(fr, to): return range(fr, to+1)

# Dialog parameters
ID_DIALOG_ARCINFO=519
ITEM_SRC_BEGIN=2
ITEM_SRC_END=3
ITEMLIST_SRC=ITEMrange(ITEM_SRC_BEGIN, ITEM_SRC_END)

ITEM_DST_BEGIN=5
ITEM_DST_END=6
ITEMLIST_DST=ITEMrange(ITEM_DST_BEGIN, ITEM_DST_END)

ITEM_DELAY=8

ITEM_CANCEL=10
ITEM_RESTORE=11
ITEM_APPLY=12
ITEM_OK=13

ITEMLIST_ALL=ITEMrange(1, ITEM_OK)

class ArcInfoDialog(windowinterface.MACDialog):
	__rangelist = ['0-1 sec', '0-10 sec', '0-100 sec']

	def __init__(self, title, srclist, srcinit, dstlist, dstinit, delay):
		"""Create the ArcInfo dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pops it up (i.e. displays it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		srclist -- list of strings
		srcinit -- 0 <= srcinit < len(srclist) -- the initial
			selction of srclist.
		dstlist -- list of strings
		dstinit -- 0 <= dstinit < len(dstlist) -- the initial
			selection of dstlist
		delay -- 0.0 <= delay <= 100.0 -- the initial value of
			the floating point value
		"""
		windowinterface.MACDialog.__init__(self, title, ID_DIALOG_ARCINFO,
				ITEMLIST_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)
		self.src_setpos(0)
		self.dst_setpos(0)
		self.delay_setvalue(0)
		self.show()

##		self.__window = windowinterface.Window(title, resizable = 1,
##					deleteCallback = (self.cancel_callback, ()))
##		self.__src_choice = self.__window.OptionMenu('From:',
##					srclist, srcinit,
##					None, top = None, left = None)
##		self.__dst_choice = self.__window.OptionMenu('To:',
##					dstlist, dstinit,
##					None, top = None,
##					left = self.__src_choice, right = None)
##		if delay > 10.0:
##			rangeinit = 2
##		elif delay > 1.0:
##			rangeinit = 1
##		else:
##			rangeinit = 0
##		range = float(10 ** rangeinit)
##		self.__delay_slider = self.__window.Slider(None, 0, delay, range,
##					None,
##					top = self.__src_choice, left = None)
##		self.__range_choice = self.__window.OptionMenu(None,
##					self.__rangelist,
##					rangeinit, (self.__range_callback, ()),
##					top = self.__dst_choice,
##					left = self.__delay_slider, right = None)
##		buttons = self.__window.ButtonRow(
##			[('Cancel', (self.cancel_callback, ())),
##			 ('Restore', (self.restore_callback, ())),
##			 ('Apply', (self.apply_callback, ())),
##			 ('OK', (self.ok_callback, ()))],
##			left = None, top = self.__delay_slider, vertical = 0)
##		self.__window.show()

	def do_itemhit(self, item, event):
		if item in ITEMLIST_SRC:
			self.src_setpos(item-ITEM_SRC_BEGIN)
		elif item in ITEMLIST_DST:
			self.dst_setpos(item-ITEM_DST_BEGIN)
		elif item == ITEM_DELAY:
			# Only test for validity
			str = self._getlabel(ITEM_DELAY)
			try:
				value = string.atof(str)
			except ValueError, arg:
				MacOS.SysBeep()
		elif item == ITEM_CANCEL:
			self.cancel_callback()
		elif item == ITEM_OK:
			self.ok_callback()
		elif item == ITEM_RESTORE:
			self.restore_callback()
		elif item == ITEM_APPLY:
			self.apply_callback()
		else:
			print 'Unknown ArcInfoDialog item', item, 'event', event

	#
	# interface methods
	#

	# Interface to the source list.
	def src_setpos(self, pos):
		"""Set the current selection in the source list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(srclist) -- the requested position
		"""
		for i in range(2):
			tp, h, rect = self._dialog.GetDialogItem(ITEMLIST_SRC[i])
			ctl = h.as_Control()
			if i == pos:
				ctl.SetControlValue(1)
			else:
				ctl.SetControlValue(0)

	def src_getpos(self):
		"""Return the current selection in the source list."""
		for i in range(2):
			tp, h, rect = self._dialog.GetDialogItem(ITEMLIST_SRC[i])
			ctl = h.as_Control()
			if ctl.GetControlValue():
				return i
		raise 'No src position set?'

	# Interface to the destination list.
	def dst_setpos(self, pos):
		"""Set the current selection in the destination list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(srclist) -- the requested position
		"""
		for i in range(2):
			tp, h, rect = self._dialog.GetDialogItem(ITEMLIST_DST[i])
			ctl = h.as_Control()
			if i == pos:
				ctl.SetControlValue(1)
			else:
				ctl.SetControlValue(0)

	def dst_getpos(self):
		"""Return the current selection in the destination list."""
		for i in range(2):
			tp, h, rect = self._dialog.GetDialogItem(ITEMLIST_DST[i])
			ctl = h.as_Control()
			if ctl.GetControlValue():
				return i
		raise 'No destination position set?'

	# Interface to the delay value.
	def delay_setvalue(self, delay):
		"""Set the value of the delay field.

		Arguments (no defaults):
		delay -- 0.0 <= delay <= 100.0 -- the new value of the
			delay
		"""
		delay = `delay`
		self._setlabel(ITEM_DELAY, delay)

	def delay_getvalue(self):
		"""Return the current value of the delay."""
		# return delay with an accuracy of 2 digits
		str = self._getlabel(ITEM_DELAY)
		try:
			value = string.atof(str)
		except ValueError, arg:
			windowinterface.showmessage('%s\r(zero delay used)'%(arg,))
			value = 0.0
		return value
			

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def cancel_callback(self):
		"""Called when `Cancel' button is pressed."""
		pass

	def restore_callback(self):
		"""Called when `Restore' button is pressed."""
		pass

	def apply_callback(self):
		"""Called when `Apply' button is pressed."""
		pass

	def ok_callback(self):
		"""Called when `OK' button is pressed."""
		pass
