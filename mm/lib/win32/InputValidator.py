import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()

import string
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
	def onKey(self, vk, val, pos):
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
	def __init__(self,sep='',sm=None):
		InputValidator.__init__(self)
		self._sep=sep
		if not sm:
			tl=[(1,2,'d'),(2,2,'d'),(2,3,'s'),(3,2,'d')]
			self._fsm=fsm.FSM(tl,1)
		else:
			self._fsm=sm

	def inttuplefilter(self,ch):
		code=ord(ch[0])
		if code in range(ord('0'),ord('9')+1):
			return 'd'
		if ch==' ':
			return 's'
		return 'null'

	def isIntTuple(self, val):
		self._fsm.reset(1)
		for ch in val:
			if not self._fsm.advance(self.inttuplefilter(ch),ch):
				return 0
		return 1

	def onKey(self, vk, val, pos):
		charcode = Sdk.MapVirtualKey(vk,2)
		# accept control chars
		if charcode<32:return 1
		
		# accept anything if not at the end
		if pos!=len(val): return 1
		
		nval=val+chr(charcode)
		if self.isIntTuple(nval):
			return 1
		else:
			win32api.MessageBeep(win32con.MB_ICONEXCLAMATION)
			return 0

class ColorValidator(IntTupleValidator):
	def __init__(self,sep=''):
		ch=self.checkcolor
		cl=self.clearbuf
		tl=[ (1,2,'d'), (2,2,'d',ch), (2,3,'s',cl), (3,4,'d'), (4,4,'d',ch), 
			(4,5,'s',cl), (5,5,'d',ch) ]
		sm=fsm.FSM(tl,1)
		IntTupleValidator.__init__(self,sep,sm)

	def onKey(self, vk, val, pos):
		charcode = Sdk.MapVirtualKey(vk,2)
		# accept control chars
		if charcode<32:return 1
		
		# accept anything if not at the end
		if pos!=len(val): return 1
		
		nval=val+chr(charcode)
		if self.isalpha_en(val) and self.isvk_alpha_en(vk):
			return 1
		elif self.isIntTuple(nval):
			return 1
		win32api.MessageBeep(win32con.MB_ICONEXCLAMATION)
		return 0
	
	def checkcolor(self,str):
		if string.atoi(str)>255:
			return 0
		return 1

	def clearbuf(self,str):
		self._fsm._input=''
		return 1

