import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()

import string
import fsm

###############################
# Base class for input validators 

class InputValidator:
	def __init__(self):
		self._silent=0

	# Return 1 to allow the char to be appended to the edit box 
	# Return 0 to refuse it
	# vk: the new input char as a virual key
	# val: the string already in the edit box
	# pos: the position where the char will be inserted
	def onKey(self, vk, val, pos):
		return 1

	def beep(self):
		if not self._silent:
			win32api.MessageBeep(win32con.MB_ICONEXCLAMATION)
		
class IntTupleValidator(InputValidator):
	def __init__(self, limit=0, sep='' , sm=None):
		InputValidator.__init__(self)
		self._sep=sep
		self._limit=limit
		if not sm:
			tl=[(1,2,'d'),(2,2,'d'),(2,3,'s',self.checklimit),(3,2,'d')]
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
		self._count=0
		for ch in val:
			if not self._fsm.advance(self.inttuplefilter(ch),ch):
				return 0
		return 1

	def checklimit(self,str):
		if self._limit==0: # no limit
			return 1 
		self._count=self._count+1
		if self._count<self._limit:
			return 1
		return 0

	def onKey(self, vk, val, pos):
		charcode = Sdk.MapVirtualKey(vk,2)
		# accept control chars
		if charcode<32:return 1
		
		# accept anything if not at the end for now
		if pos!=len(val): return 1
		
		nval=val+chr(charcode)
		if self.isIntTuple(nval):
			return 1
		else:
			self.beep()
			return 0

class FloatTupleValidator(InputValidator):
	def __init__(self, limit=0, sep='', sm=None):
		InputValidator.__init__(self)
		self._sep=sep
		self._limit=limit
		if not sm:
			tl=[(1,2,'d'),(2,2,'d'),(2,3,'.'),(2,4,'s',self.checklimit),
			(3,3,'d'),(3,4,'s',self.checklimit),(4,2,'d')]
			self._fsm=fsm.FSM(tl,1)
		else:
			self._fsm=sm

	def floattuplefilter(self,ch):
		code=ord(ch[0])
		if code in range(ord('0'),ord('9')+1):
			return 'd'
		elif ch==' ':
			return 's'
		elif ch=='.':
			return '.'
		return 'null'

	def isFloatTuple(self, val):
		self._fsm.reset(1)
		self._count=0
		for ch in val:
			if not self._fsm.advance(self.floattuplefilter(ch),ch):
				return 0
		return 1

	def checklimit(self,str):
		if self._limit==0: # no limit
			return 1 
		self._count=self._count+1
		if self._count<self._limit:
			return 1
		return 0

	def onKey(self, vk, val, pos):
		charcode = Sdk.MapVirtualKey(vk,2)
		# accept control chars
		if charcode<32:return 1
		
		# accept anything if not at the end for now
		if pos!=len(val): return 1
		
		nval=val+chr(charcode)
		if self.isFloatTuple(nval):
			return 1
		else:
			self.beep()
			return 0

class ColorValidator(IntTupleValidator):
	def __init__(self,sep=''):
		ch=self.checkcolor
		cl=self.clearbuf
		tl=[ (1,2,'d'), (2,2,'d',ch), (2,3,'s',cl), (3,4,'d'), (4,4,'d',ch), 
			(4,5,'s',cl), (5,5,'d',ch) ]
		sm=fsm.FSM(tl,1)
		IntTupleValidator.__init__(self,3,sep,sm)

		from colors import colors
		self._dv=DictValidator(colors.keys())
		self._dv._silent=1

	def onKey(self, vk, val, pos):
		charcode = Sdk.MapVirtualKey(vk,2)
		# accept control chars
		if charcode<32:return 1
		
		# accept anything if not at the end for now
		if pos!=len(val): return 1
		
		nval=val+chr(charcode)
		if self._dv.onKey(vk, val, pos):
			return 1
		elif self.isIntTuple(nval):
			return 1
		self.beep()
		return 0
	
	def checkcolor(self,str):
		if string.atoi(str)>255:
			return 0
		return 1

	def clearbuf(self,str):
		self._fsm._input=''
		return 1


class DictValidator(InputValidator):
	def __init__(self, names):
		InputValidator.__init__(self)
		# names should be lower
		self._names=names

	# brute force search
	# should be a tree of letters or something like that
	def isdictprefix(self,str):
		str=string.lower(str)
		for n in self._names:
			if string.find(n,str)==0:
				return 1
		return 0
	# brute force again...
	def autofill(self,str):
		l=[]
		str=string.lower(str)
		for n in self._names:
			if string.find(n,str)==0:
				l.append(n)
		if len(l)==1:
			return l[0]

	def onKey(self, vk, val, pos):
		charcode = Sdk.MapVirtualKey(vk,2)
		# accept control chars
		if charcode<32:return 1
		
		# accept anything if not at the end for now
		if pos!=len(val): return 1
		
		nval=val+chr(charcode)
		if self.isdictprefix(nval):
			return 1
		self.beep()
		return 0
	