"""Dialog for the Preferences window.

"""

__version__ = "$Id$"


from components import *
import string


class PreferencesDialog(ResDialog,ControlsDict):
	def __init__(self,cbd=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_PREFERENCES,parent)

		self['system_bitrate']= Edit(self,grinsRC.IDC_EDIT1)
		self['system_language']= Edit(self,grinsRC.IDC_EDIT2)
		self['system_captions']=CheckButton(self,grinsRC.IDC_CHECK1)
		self['system_overdub_or_caption']=CheckButton(self,grinsRC.IDC_CHECK2)

		self['OK']=Button(self,win32con.IDOK)
		self['Cancel']=Button(self,win32con.IDCANCEL)
		self['Reset']=Button(self,grinsRC.IDC_RESET)
		self._cbd=cbd
	
		#mark as int edit
		self['system_bitrate']._int=1

	def OnInitDialog(self):	
		self.attach_handles_to_subwindows()	
		self.HookCommand(self.OnReset,self['Reset']._id)

	def create(self):
		self.CreateWindow()
	def close(self):
		self.DestroyWindow()


	def OnOK(self):	apply(apply,self._cbd['OK'])
	def OnCancel(self):apply(apply,self._cbd['Cancel'])
	def OnReset(self,id,code):apply(apply,self._cbd['Reset'])


	def show(self):
		self.CenterWindow(self.GetParent())
		self.ShowWindow(win32con.SW_SHOW)

	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)
	def pop(self):
		self.show()

	#
	# helper methods
	#	
	def is_string(self,k):
		return self[k].__class__==Edit and not hasattr(self[k],'_int')
	def is_int(self,k):
		return self[k].__class__==Edit and hasattr(self[k],'_int')
	def is_bool(self,k):
		return self[k].__class__==CheckButton  

	#
	# interface methods
	#
	def setstringitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		self[item].settext(value)
		
	def getstringitem(self, item):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		return self[item].gettext()
		
	def getstringnames(self):
		l=[]
		for k in self.keys():
			if self.is_string(k):l.append(k)
		return l
		
	def setintitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		if value is None:
			self[item].settext('')
		else:
			self[item].settext('%d' % value)
		
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
		
	def getintnames(self):
		l=[]
		for k in self.keys():
			if self.is_int(k):l.append(k)
		return l

	def setboolitem(self, item, value):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		self[item].setcheck(1)

	def getboolitem(self, item):
		if not self.has_key(item):
			raise 'Unknown preference item', item
		return self[item].getcheck()
		
	def getboolnames(self):
		l=[]
		for k in self.keys():
			if self.is_bool(k):l.append(k)
		return l
