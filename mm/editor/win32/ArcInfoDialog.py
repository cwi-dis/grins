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

""" @win32doc|ArcInfoDialog
This class represents the interface between the ArcInfo platform independent
class and its implementation ArcInfoForm in lib/win32/ArcInfoForm.py which 
implements the actual dialog.

"""

__version__ = "$Id$"


class ArcInfoDialog:
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
		adornments = {
			'form_id':'arc_info',
			'callbacks':{
				'Cancel':(self.cancel_callback, ()),
				'Restore':(self.restore_callback, ()),
				'Apply':(self.apply_callback, ()),
				'OK':(self.ok_callback, ()),
			},
		}
		formid=adornments['form_id']

		import windowinterface 
		frame=windowinterface.getactivedocframe()
		fs=frame.getformserver()
		self._window=fs.newformobj(formid)
		self._window.do_init(title, srclist, srcinit, dstlist, dstinit, delay, adornments)
		fs.showform(self._window,formid)
		self._window.show()

	#
	# interface methods
	#

	def close(self):
		"""Close the dialog and free resources."""
		self._window.close()
		self._window=None

	def is_closed(self):
		return self._window==None

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self._window.settitle(title)

	# Interface to the source list.
	def src_setpos(self, pos):
		"""Set the current selection in the source list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(srclist) -- the requested position
		"""
		self._window.src_setpos( pos)

	def src_getpos(self):
		"""Return the current selection in the source list."""
		return self._window.src_getpos()

	# Interface to the destination list.
	def dst_setpos(self, pos):
		"""Set the current selection in the destination list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(srclist) -- the requested position
		"""
		self._window.dst_setpos(pos)

	def dst_getpos(self):
		"""Return the current selection in the destination list."""
		return self._window.dst_getpos()

	# Interface to the delay value.
	def delay_setvalue(self, delay):
		"""Set the value of the delay field.

		Arguments (no defaults):
		delay -- 0.0 <= delay <= 100.0 -- the new value of the
			delay
		"""
		self._window.delay_setvalue(delay)

	def delay_getvalue(self):
		"""Return the current value of the delay."""
		# return delay with an accuracy of 2 digits
		return self._window.delay_getvalue()

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
