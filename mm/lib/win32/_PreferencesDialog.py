# @win32doc|_PreferencesDialog
# This module contains the ui implementation of the PreferencesDialog
# The _LayoutView is created using the resource dialog template 
# with identifier IDD_PREFERENCES.

__version__ = "$Id$"


from components import *
import win32dialog
import string


class PreferencesDialog(win32dialog.ResDialog,ControlsDict):

	# Class constructor. Calls base class constructors and associates ids to controls
	def __init__(self,cbd=None,parent=None):
		win32dialog.ResDialog.__init__(self,grinsRC.IDD_PREFERENCES,parent)
		ControlsDict.__init__(self)

		self['system_bitrate']= Edit(self,grinsRC.IDC_EDIT1)
		self['system_language']= Edit(self,grinsRC.IDC_EDIT2)
		self['time_scale_factor'] = Edit(self,grinsRC.IDC_EDIT3)
		self['system_captions']=CheckButton(self,grinsRC.IDC_CHECK1)
		self['system_overdub_or_caption']=CheckButton(self,grinsRC.IDC_CHECK2)
		self['cmif']=CheckButton(self, grinsRC.IDC_CHECK3)
		self['html_control']=CheckButton(self, grinsRC.IDC_CHECK4)

		self['OK']=Button(self,win32con.IDOK)
		self['Cancel']=Button(self,win32con.IDCANCEL)
		self['Reset']=Button(self,grinsRC.IDC_RESET)
		self._cbd=cbd
	
		#mark as int edit
		self['system_bitrate']._int=1
		self['time_scale_factor']._int = 0

	# Called by the OS after the OS window has been created
	def OnInitDialog(self):	
		self.attach_handles_to_subwindows()	
		self.HookCommand(self.OnReset,self['Reset']._id)

	# Create the actual OS window
	def create(self):
		self.CreateWindow()
	# Called by the core system to close the Dialog
	def close(self):
		self.DestroyWindow()

	# Response to the button OK
	def OnOK(self):
		self.win32special()	
		apply(apply,self._cbd['OK'])
	# Response to the button Cancel
	def OnCancel(self):apply(apply,self._cbd['Cancel'])
	# Response to the button Reset
	def OnReset(self,id,code):
		apply(apply,self._cbd['Reset'])


	# Called by the core syatem to show the Dialog
	def show(self):
		self.CenterWindow(self.GetParent())
		self.ShowWindow(win32con.SW_SHOW)

	# Called by the core syatem to hide the Dialog
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)
	# Called by the core system to bring the Dialog in front
	def pop(self):
		self.show()

	#
	# helper methods
	#	
	def is_string(self,k):
		return self[k].__class__==Edit and not hasattr(self[k],'_int')
	def is_int(self,k):
		return self[k].__class__==Edit and hasattr(self[k],'_int') and self[k]._int
	def is_bool(self,k):
		return self[k].__class__==CheckButton  

	#
	# interface methods
	#
	# set the attribute of the string item to the value
	def setstringitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		self[item].settext(value)
		
	# get the attribute of the string item
	def getstringitem(self, item):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		return self[item].gettext()
	
	# Get all string attributes	
	def getstringnames(self):
		l=[]
		for k in self.keys():
			if self.is_string(k):l.append(k)
		return l
		
	# set the attribute of the int item to the value
	def setintitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		if value is None:
			self[item].settext('')
		else:
			self[item].settext('%d' % value)
		
	# get the attribute of the int item
	def getintitem(self, item):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		value = self[item].gettext()
		if value == '':
			return None
		try:
			value = string.atoi(value)
		except ValueError:
			raise PreferencesDialogError, '%s value should be integer'%item
		return value
		
	# Get all int attributes	
	def getintnames(self):
		l=[]
		for k in self.keys():
			if self.is_int(k):l.append(k)
		return l

	# set the attribute of the float item to the value
	def setfloatitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		if value is None:
			self[item].settext('')
		else:
			self[item].settext('%g' % value)
		
	# get the attribute of the float item
	def getfloatitem(self, item):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		value = self[item].gettext()
		if value == '':
			return None
		try:
			value = string.atof(value)
		except ValueError:
			raise PreferencesDialogError, '%s value should be float'%item
		return value

	# Get all int attributes	
	def getfloatnames(self):
		return ['time_scale_factor']

	# set the attribute of the bool item to the value
	def setboolitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		self[item].setcheck(value)

	# get the attribute of the bool item
	def getboolitem(self, item):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		return self[item].getcheck()
		
	# Get all bool attributes	
	def getboolnames(self):
		l=[]
		for k in self.keys():
			if self.is_bool(k):l.append(k)
		return l

	def win32special(self):
		lang=self['system_language'].gettext()
		import Font
		if lang=='el' or lang=='EL':
			cb=(Font.set_win32_charset, ('GREEK',))
		else:
			cb=(Font.set_win32_charset, ('DEFAULT',))			
		apply(apply,cb)
