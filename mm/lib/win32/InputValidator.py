import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()

import fsm

###############################
# Base class for input validators 

class InputValidator:
	def __init__(self):
		pass

	# Return 1 to allow the char to be appended to the edit box 
	# Return 0 to refuse it
	# vk: the new input char as a virual key
	# val: the string already in the edit box
	def onKey(self, vk, val):
		return 1

	def isdigit(self,str,sep=''):
		for ch in str:
			code=ord(ch)
			if code not in range(ord('0'),ord('9')+1) and \
				(not sep or string.find(sep, ch)<0):
				return 0
		return 1
		
	def isalpha_en(self,str,sep=''):
		for ch in str:
			code=ord(ch)
			if code not in range(ord('a'),ord('z')+1) and \
				code not in range(ord('A'),ord('Z')+1) and \
				(not sep or string.find(sep, ch)<0):
				return 0
		return 1

	def isvk_alpha_en(self,vk):
		code = Sdk.MapVirtualKey(vk,2)
		if code in range(ord('a'),ord('z')+1):
			return 1
		elif code in range(ord('A'),ord('Z')+1):
			return 1
		return 0

class IntTupleValidator(InputValidator):
	def __init__(self,sep=''):
		InputValidator.__init__(self)
		self._sep=sep
		tl=[(1,2,'d'),(2,2,'d'),(2,3,'s'),(3,2,'d')]
		self._fsm=fsm.FSM(tl,1)

	def inttuplefilter(self,ch):
		code=ord(ch[0])
		if code in range(ord('0'),ord('9')+1):
			return 'd'
		if ch==' ':
			return 's'
		return 'null'

	def isIntTuple(self, vk, val):
		charcode = Sdk.MapVirtualKey(vk,2)
		if charcode<32:return 1
		nval=val+chr(charcode)
		self._fsm.reset(1)
		for ch in nval:
			if not self._fsm.advance(self.inttuplefilter(ch),ch):
				return 0
		return 1

	def onKey(self, vk, val):
		if self.isIntTuple(vk, val):
			return 1
		else:
			win32api.MessageBeep(win32con.MB_ICONEXCLAMATION)
			return 0

# not very usefull yet since it is just a tuple validator
# but accepts also strings
class ColorValidator(IntTupleValidator):
	def __init__(self,sep=''):
		IntTupleValidator.__init__(self,sep)
		
	def onKey(self, vk, val):
		if self.isalpha_en(val) and self.isvk_alpha_en(vk):
			return 1
		elif self.isIntTuple(vk, val):
			return 1
		win32api.MessageBeep(win32con.MB_ICONEXCLAMATION)
		return 0
