
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
			if len(t)==3:
				s1,s2,input=t
				cond=None
			elif len(t)==4:
				s1,s2,input,cond=t
			else:
				continue
			if graph.has_key(s1):
				if graph.has_key(s2):
					graph[s1]._transition[input]=(graph[s2],cond)
				else:
					graph[s2]=State(s2)
					graph[s1]._transition[input]=(graph[s2],cond)	
			else:
				graph[s1]=State(s1)
				if graph.has_key(s2):
					graph[s1]._transition[input]=(graph[s2],cond)
				else:
					graph[s2]=State(s2)
					graph[s1]._transition[input]=(graph[s2],cond)	
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
		if not ainput: ainput=input
		if self._current:
			if self._current._transition.has_key(input):
				state,cond = self._current._transition[input]
				if cond:
					if apply(cond,(self._input+ainput,)):
						self._current=state
						self._input=self._input+ainput
					else:
						self._current=None
				else:
					self._current=state
					self._input=self._input+ainput	
			else:
				self._current=None
		return self._current

	def getstate(self):
		return self._current
	
