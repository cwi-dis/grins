__version__ = "$Id$"

# Edit Manager.
# Amazing as it may seem, this module is not dependent on window software!

# Edit manager interface -

##The edit manager is responsible for taking and recording changes made
##by different parts of the system in a fashion that allows undo's,
##redo's and safe changes to the MMNode (and other) structures.

##It works (currently) as follows:
##	* A specific view wants to make a change to the structure. ed
##	is an instance of the editmanager.
##	* That view calls em.register() to tell everybody in
##	em.registry that it wants an exclusive lock on making changes.
##	* The view does it's stuff to the data structures.
##	* the view calls ed.commit(). commit will record the changes
##	and let all other views know that the document has changed.

##A better scheme would be as follows:
##        - The edit manager solely records changes to models.
##	- When undoing, the edit manager blindly interprets the
##	transaction list to undo the changes made to objects.
##	- Each model has an interface for calls from the edit
##	manager, views and controllers.

##	When a view wants to make a change:
##        1) A controller calls a change() method on a certain Model.
##	2) The model sets a lock on itself or it's container (if multitasking)
##	3) The model records the change with the edit manager.
##	4) The model makes the change to itself or it's parent.
##	5) The model tells all of it's views that it has changed.
##	6) The model releases the lock and returns.

##	In this case, the Edit manager would be more of a transaction
##	manager, that records a list of undoable transactions to the
##	document.	


import MMExc
from HDTL import HD, TL
import features

class EditMgr:
	#
	# Initialization.
	#
	def __init__(self, root):
		self.reset()
		self.root = root
		self.context = root.GetContext()
	#
	def __repr__(self):
		return '<EditMgr instance, context=' + `self.context` + '>'
	#
	def reset(self):
		self.root = self.context = None
		self.busy = 0
		self.history = []
		self.future = []
		self.registry = []
		self.focus_registry = []
		self.focus = None, None
		self.focus_busy = 0

		self.playerstate_registry = []
		self.playerstate = None, None
		self.playerstate_busy = 0
		
	#
	def destroy(self):
		for x in self.registry[:]:
			x.kill()
		self.reset()
	#
	# Dependent client interface.
	#
	def register(self, x, want_focus=0, want_playerstate=0):
		self.registry.append(x)
		if want_focus:
			self.focus_registry.append(x)
		if want_playerstate:
			self.playerstate_registry.append(x)
			
	def registerfirst(self, x, want_focus=0, want_playerstate=0):
		self.registry.insert(0, x)
		if want_focus:
			self.focus_registry.insert(0, x)
		if want_playerstate:
			self.playerstate_registry.insert(0, x)
	
	def unregister(self, x):
		self.registry.remove(x)
		if x in self.focus_registry:
			self.focus_registry.remove(x)
		if x in self.playerstate_registry:
			self.playerstate_registry.remove(x)
	#
	def is_registered(self, x):
		return x in self.registry
	#
	# Mutator client interface -- transactions.
	# This calls the dependent clients' callbacks.
	#
	def transaction(self, type=None):
		if self.busy: raise MMExc.AssertError, 'recursive transaction'
		done = []
		for x in self.registry[:]:
			method = x.transaction
			if not x.transaction(type):
				for x in done:
					x.rollback()
				return 0
			done.append(x)
		self.undostep = []
		self.history.append(self.undostep)
		self.busy = 1
		return 1
	#
	def commit(self, type=None):
		if not self.busy: raise MMExc.AssertError, 'invalid commit'
		import MMAttrdefs
		MMAttrdefs.flushcache(self.root)
		self.context.changedtimes()
		self.root.clear_infoicon()
		self.root.ResetPlayability()
		for x in self.registry[:]:
			x.commit(type)
		self.busy = 0
		del self.undostep # To frustrate invalid addstep calls
	#
	def rollback(self):
		if not self.busy: raise MMExc.AssertError, 'invalid rollback'
		# XXX undo changes made in this transaction
		for x in self.registry[:]:
			x.rollback()
		self.busy = 0
		del self.undostep # To frustrate invalid addstep calls

	#
	# player state interface
	#
	def setplayerstate(self, state, parameters):
		if (state, parameters) == self.playerstate:
			return
		if self.playerstate_busy: raise MMExc.AssertError, 'recursive playerstate'
		self.playerstate_busy = 1
		self.playerstate = (state, parameters)
		for client in self.playerstate_registry:
			client.playerstatechanged(state, parameters)
		self.playerstate_busy = 0

	def getplayerstate(self):
		return self.playerstate
		
	#
	# Focus interface
	#
	def setglobalfocus(self, focustype, focusobject):
		# Jack: Thank you for this elaborately documented code. We have absolutely
		# no idea what type of object "focustype" is. 

		# Pas op all functions calling this: The focusobject may be None.. 
		
		# Quick return if this product does not have a shared focus
		if not features.UNIFIED_FOCUS in features.feature_set:
			return
		if (focustype, focusobject) == self.focus:
			return
		if self.focus_busy: raise MMExc.AssertError, 'recursive focus'
		self.focus_busy = 1
		self.focus = (focustype, focusobject)
		for client in self.focus_registry:
			client.globalfocuschanged(focustype, focusobject)
		self.focus_busy = 0
		
	def getglobalfocus(self):
		return self.focus
	#
	# UNDO interface -- this code isn't ready yet.
	#
	def undo(self):
		if self.busy: raise MMExc.AssertError, 'undo while busy'
		i = len(self.history) - 1
		if i < 0: return 0 # Nothing to undo
		step = self.history[i]
		XXX # Carry out items in step in reverse order
		self.future.insert(0, step)
		del self.history[i]
		return 1
	#
	def redo(self):
		if self.busy: raise MMExc.AssertError, 'undo while busy'
		if not future: return 0 # Nothing to redo
		step = self.future(0)
		XXX # Carry out items in step in forward order
		self.history.append(step)
		del self.future[0]
		return 1
	# XXX The undo/redo business is unfinished.
	# E.g., What to do if the user undoes a few steps,
	# then makes new changes, then wants to redo?
	# Also the commit/rollback stuff isn't watertight
	# (ideally rollback must be able to roll back even if
	# an arbitrary keyboard interrupt hit).
	#
	def addstep(self, *step):
		# This fails if we're not busy because self.undostep is deleted
		self.undostep.append(step)
	#
	# Mutator client interface -- tree mutations.
	#
	# Node operations
	#
	def delnode(self, node):
		parent = node.GetParent()
		i = parent.GetChildren().index(node)
		self.addstep('delnode', parent, i, node)
		node.Extract()
			
	def addnode(self, parent, i, node):
		self.addstep('addnode', parent, i, node)
		node.AddToTree(parent, i)
	#
	def setnodetype(self, node, type):
		oldtype = node.GetType()
		self.addstep('setnodetype', node, oldtype, type)
		node.SetType(type)
	#
	def setnodeattr(self, node, name, value):
		if name == 'synctolist':
			raise MMExc.AssertError, 'cannot set synctolist attr'
		oldvalue = node.GetRawAttrDef(name, None)
		self.addstep('setnodeattr', node, name, oldvalue, value)
		if value is not None:
			node.SetAttr(name, value)
		else:
			node.DelAttr(name)
	#
	def setnodevalues(self, node, values):
		self.addstep('setnodevalues', node, node.GetValues(), values)
		node.SetValues(values)
	#
	# Sync arc operations
	#
	def __isbegin(self, xnode, xside, ynode, yside):
		if yside == HD:
			if ynode.GetParent().GetType() == 'seq' and xside == TL:
				prev = None
				for n in ynode.GetParent().GetChildren():
					if n is ynode:
						break
					prev = n
				if prev is not None and xnode is prev:
					return 1
			elif xside == HD and xnode is ynode.GetParent():
				return 1
		return 0

	def addsyncarc(self, xnode, xside, delay, ynode, yside):
		skip = 0
		if self.__isbegin(xnode, xside, ynode, yside):
			skip = 1
			self.setnodeattr(ynode, 'begin', delay)
		list = ynode.GetRawAttrDef('synctolist', None)
		if list is None:
			list = []
			if not skip:
				ynode.SetAttr('synctolist', list)
		xuid = xnode.GetUID()
		for item in list:
			xn, xs, de, ys = item
			if xn==xuid and (xs,ys) == (xside,yside):
				self.addstep('delsyncarc',xnode,xs,de,ynode,ys)
				list.remove(item)
				break
		if not skip:
			self.addstep('addsyncarc', xnode, xside, delay, ynode, yside)
			list.append((xuid, xside, delay, yside))

	def delsyncarc(self, xnode, xside, delay, ynode, yside):
		if self.__isbegin(xnode, xside, ynode, yside):
			self.setnodeattr(ynode, 'begin', None)
			return
		list = ynode.GetRawAttrDef('synctolist', [])
		xuid = xnode.GetUID()
		for item in list:
			xn, xs, de, ys = item
			if xn==xuid and (xs,de,ys) == (xside,delay,yside):
				self.addstep('delsyncarc',xnode,xs,de,ynode,ys)
				list.remove(item)
				if not list:
					# no sync arcs left
					ynode.DelAttr('synctolist')
				break
		else:
			raise MMExc.AssertError, 'bad delsyncarc call'
	#
	# Hyperlink operations
	#
	def addlink(self, link):
		self.addstep('addlink', link)
		self.context.hyperlinks.addlink(link)

	def dellink(self, link):
		self.addstep('dellink', link)
		self.context.hyperlinks.dellink(link)

	def addexternalanchor(self, url):
		self.addstep('addexternalanchor', url)
		self.context.externalanchors.append(url)
	#
	# Channel operations
	#
	def addchannel(self, name, i, type):
		c = self.context.getchannel(name)
		if c is not None:
			raise MMExc.AssertError, \
				'duplicate channel name in addchannel'
		self.addstep('addchannel', name, i, type)
		self.context.addchannel(name, i, type)
	#
	def copychannel(self, name, i, orig):
		c = self.context.getchannel(name)
		if c is not None:
			raise MMExc.AssertError, \
				'duplicate channel name in copychannel'
		c = self.context.getchannel(orig)
		if c is None:
			raise MMExc.AssertError, \
				'unknown orig channel name in copychannel'
		self.addstep('copychannel', name, i, orig)
		self.context.copychannel(name, i, orig)
	#
	def movechannel(self, name, i):
		self.addstep('movechannel', name, i)
		self.context.movechannel(name, i)
	#
	def delchannel(self, name):
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in delchannel'
		i = self.context.channels.index(c)
		attrdict = c.attrdict
		self.addstep('delchannel', name, i, attrdict)
		self.context.delchannel(name)
	#
	def setchannelname(self, name, newname):
		if newname == name:
			return # No change
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in setchannelname'
		self.addstep('setchannelname', name, newname)
		self.context.setchannelname(name, newname)
	#
	def setchannelattr(self, name, attrname, value):
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in setchannelattr'
		if c.has_key(attrname):
			oldvalue = c[attrname]
		else:
			oldvalue = None
		if value == oldvalue:
			return
		self.addstep('setchannelattr', name, attrname, oldvalue, value)
		if value is None:
			del c[attrname]
		else:
			c[attrname] = value

	#
	# Layout operations
	#
	def addlayout(self, name):
		if self.context.layouts.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate layout name in addlayout'
		self.addstep('addlayout', name)
		self.context.addlayout(name)

	def dellayout(self, name):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, 'unknown layout in dellayout'
		self.addstep('dellayout', name, layout)
		self.context.dellayout(name)

	def addlayoutchannel(self, name, channel):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, \
			      'unknown layout in addlayoutchannel'
		if channel in layout:
			raise MMExc.AssertError, \
			      'channel already in layout in addlayoutchannel'
		self.addstep('addlayoutchannel', name, channel)
		self.context.addlayoutchannel(name, channel)

	def dellayoutchannel(self, name, channel):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, \
			      'unknown layout in addlayoutchannel'
		if channel not in layout:
			raise MMExc.AssertError, \
			      'channel not in layout in dellayoutchannel'
		self.addstep('dellayoutchannel', name, channel)
		self.context.dellayoutchannel(name, channel)

	def setlayoutname(self, name, newname):
		if newname == name:
			return		# no change
		if not self.context.layouts.has_key(name):
			raise MMExc.AssertError, \
			      'unknown layout name in setlayoutname'
		if self.context.layouts.has_key(newname):
			raise MMExc.AssertError, \
			      'name already in use in setlayoutname'
		self.addstep('setlayoutname', name, newname)
		self.context.setlayoutname(name, newname)

	#
	# User group operations
	#
	def addusergroup(self, name, value):
		if self.context.usergroups.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate usergroup name in addusergroup'
		self.addstep('addusergroup', name)
		self.context.addusergroup(name, value)

	def delusergroup(self, name):
		usergroup = self.context.usergroups.get(name)
		if usergroup is None:
			raise MMExc.AssertError, 'unknown usergroup in delusergroup'
		self.addstep('delusergroup', name, usergroup)
		self.context.delusergroup(name)

	def setusergroupname(self, name, newname):
		if newname == name:
			return		# no change
		if not self.context.usergroups.has_key(name):
			raise MMExc.AssertError, \
			      'unknown usergroup name in setusergroupname'
		if self.context.usergroups.has_key(newname):
			raise MMExc.AssertError, \
			      'name already in use in setusergroupname'
		self.addstep('setusergroupname', name, newname)
		self.context.setusergroupname(name, newname)

	#
	# Transitions operations
	#
	def addtransition(self, name, value):
		if self.context.transitions.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate transition name in addtransition'
		self.addstep('addtransition', name)
		self.context.addtransition(name, value)

	def deltransition(self, name):
		transition = self.context.transitions.get(name)
		if transition is None:
			raise MMExc.AssertError, 'unknown transition in deltransition'
		self.addstep('deltransition', name, transition)
		self.context.deltransition(name)

	def settransitionname(self, name, newname):
		if newname == name:
			return		# no change
		if not self.context.transitions.has_key(name):
			raise MMExc.AssertError, \
			      'unknown transition name in settransitionname'
		if self.context.transitions.has_key(newname):
			raise MMExc.AssertError, \
			      'name already in use in settransitionname'
		self.addstep('settransitionname', name, newname)
		self.context.settransitionname(name, newname)
		
	def settransitionvalue(self, name, key, value):
		if not self.context.transitions.has_key(name):
			raise MMExc.AssertError, \
			      'unknown transition name in settransitionname'
		dict = self.context.transitions[name]
		dict[key] = value
		self.addstep('settransitionvalue', name, key, value)

##	#
##	# Style operations
##	#
##	def addstyle(self, name):
##		if self.context.styledict.has_key(name):
##			raise MMExc.AssertError, \
##				'duplicate style name in addstyle'
##		self.addstep('addstyle', name)
##		self.context.styledict[name] = {}
##	#
##	def delstyle(self, name):
##		self.addstep('delstyle', name, self.context.styledict[name])
##		del self.context.styledict[name]
##	#
##	def setstylename(self, name, newname):
##		if self.context.styledict.has_key(newname):
##			raise MMExc.AssertError, \
##				'duplicate style name in setstylename'
##		attrdict = self.context.styledict[name]
##		self.addstep('setstylename', name, newname)
##		self.context.styledict[newname] = attrdict
##		del self.context.styledict[name]
##	#
##	def setstyleattr(self, name, attrname, value):
##		attrdict = self.context.styledict[name]
##		if attrdict.has_key(attrname):
##			oldvalue = attrdict[attrname]
##		else:
##			oldvalue = None
##		if value is None is oldvalue:
##			return
##		self.addstep('setstyleattr', name, attrname, oldvalue, value)
##		if value is None:
##			del attrdict[attrname]
##		else:
##			attrdict[attrname] = value
##	#

