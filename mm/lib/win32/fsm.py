
class State:
	def __init__(self,sig):
		self._sig=sig
		self._transition={}
	def getsig(self):
		return self._sig

# This is simple table driven FSM
# triplelist is a list of tuples (fromState,toState,onInput)
# inistate is the sig of the initial state
# input is assumed to be string		
class FSM:
	def __init__(self,triplelist,inistate=None):
		# create graph of states from triplelist
		graph={}
		for t in triplelist:
			s1,s2,input=t
			if graph.has_key(s1):
				if graph.has_key(s2):
					graph[s1]._transition[input]=graph[s2]
				else:
					graph[s2]=State(s2)
					graph[s1]._transition[input]=graph[s2]	
			else:
				graph[s1]=State(s1)
				if graph.has_key(s2):
					graph[s1]._transition[input]=graph[s2]
				else:
					graph[s2]=State(s2)
					graph[s1]._transition[input]=graph[s2]	
		self._graph=graph
		self._current=None
		if inistate:
			self._current=graph[inistate]
		self._input=''

	def reset(self,inistatesig=None):
		self._input=''
		self._current=None
		if inistatesig:
			self._current=self._graph[inistatesig]

	# input is the string that causes the transitions and usualy describes a set
	# ainput is the actual input
	def advance(self,input,ainput=None):
		if self._current:
			if self._current._transition.has_key(input):
				self._current = self._current._transition[input]
				if ainput:
					self._input=self._input+ainput	
				else:
					self._input=self._input+input
			else:
				self._current=None	
		return self._current

	def getstate(self):
		return self._current
	
