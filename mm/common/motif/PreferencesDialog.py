"""Dialog for the Preferences window.

"""

__version__ = "$Id$"


PreferencesDialogError="PreferencesDialog.Error"



class PreferencesDialog:

	def __init__(self, title):
		"""Create the Preferences dialog.

		Create the dialog window, but does not display it yet

		Arguments (no defaults):
		title -- string to be displayed as window title
		"""

	#
	# interface methods
	#
	def setstringitem(self, item, value):
		pass
		
	def getstringitem(self, item):
		return None
		
	def getstringnames(self):
		return []
		
	def setintitem(self, item, value):
		pass
		
	def getintitem(self, item):
		return None
		
	def getintnames(self):
		return []
		
	def setboolitem(self, item, value):
		pass

	def getboolitem(self, item):
		return None
		
	def getboolnames(self):
		return []

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def cancel_callback(self):
		"""Called when `Cancel' button is pressed."""
		pass

	def reset_callback(self):
		"""Called when `Restore' button is pressed."""
		pass

	def ok_callback(self):
		"""Called when `OK' button is pressed."""
		pass
