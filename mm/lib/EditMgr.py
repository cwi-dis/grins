__version__ = "$Id$"

# Edit Manager.
# Amazing as it may seem, this module is not dependent on window software!

# Edit manager interface -

##The edit manager is responsible for taking and recording changes made
##by different parts of the system in a fashion that allows undo's,
##redo's and safe changes to the MMNode (and other) structures.

##It works (currently) as follows:
##	* A specific view wants to make a change to the structure. em
##	is an instance of the editmanager.
##	* That view calls em.transaction() to tell everybody in
##	em.registry that it wants an exclusive lock on making changes.
##	* The view does it's stuff to the data structures through calls
##	to methods of em.
##	* the view calls em.commit(). commit will record the changes
##	and let all views know that the document has changed.

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
	def __init__(self, toplevel):
		self.reset()
		self.toplevel = toplevel

	def setRoot(self, root):
		self.root = root
		self.context = self.root.context
		
	def __repr__(self):
		return '<EditMgr instance, context=' + `self.context` + '>'

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

		# if the context is changed there are some special treatment to do during commit		
		self.__newRoot = None

	def destroy(self):
		for x in self.registry[:]:
			x.kill()
		self.reset()

	def __delete(self, list):
		# hook to delete (destroy) instances in list
		for trans in list:
			for action in trans:
				cmd = action[0]
				func = getattr(self, 'clean_'+cmd)
				apply(func, action[1:])
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
		for i in range(len(self.registry)):
			if self.registry[i] is x:
				del self.registry[i]
				break
##		self.registry.remove(x)
		if x in self.focus_registry:
			self.focus_registry.remove(x)
		if x in self.playerstate_registry:
			self.playerstate_registry.remove(x)

	def is_registered(self, x):
		return x in self.registry

	#
	# Mutator client interface -- transactions.
	# This calls the dependent clients' callbacks.
	#
	def __start_transaction(self, type, undo=0):
		done = []
		for x in self.registry[:]:
			method = x.transaction
			if not x.transaction(type):
				for x in done:
					x.rollback()
				return 0
			done.append(x)
		self.undostep = []
		if undo:
			self.future.append(self.undostep)
		else:
			self.history.append(self.undostep)
		self.busy = 1
		return 1

	def transaction(self, type=None):
		if self.busy: raise MMExc.AssertError, 'recursive transaction'
		self.__delete(self.future)
		self.future = []

		# allow transaction only the document is valid, or if the transaction come from the source view
		# note: this test can't be done from the source view which may be closed
		if type != 'source' and not self.context.isValidDocument():
			import windowinterface
			windowinterface.showmessage('The source document contains some errors\nYou have to fix them before to be able to edit',
						    mtype = 'error')
			return 0
		
		return self.__start_transaction(type)

	def commit(self, type=None):
		if not self.busy: raise MMExc.AssertError, 'invalid commit'
		import MMAttrdefs
		# test if the root node has changed
		if not self.__newRoot:
			# the root node hasn't changed (the document hasn't been reloaded)
			# normal treatment
			MMAttrdefs.flushcache(self.root)
			
			self.context.changedtimes()
			self.root.clear_infoicon()
			self.root.ResetPlayability()
			for x in self.registry[:]:
				x.commit(type)
		else:
			# the root node has changed (the document has been reloaded)
			# special treatment			
			self.toplevel.changeRoot(self.__newRoot)
			self.__newRoot = None
			
		self.busy = 0
		del self.undostep # To frustrate invalid addstep calls
			
	def rollback(self):
		if not self.busy: raise MMExc.AssertError, 'invalid rollback'
		# undo changes made in this transaction
		actions = self.undostep
		self.__do_undo(actions)
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
	def __do_undo(self, actions):
		for i in range(len(actions)-1,-1,-1):
			action = actions[i]
			cmd = action[0]
			func = getattr(self, 'undo_'+cmd)
			apply(func, action[1:])
		
	def undo(self):
		if self.busy: raise MMExc.AssertError, 'undo while busy'
		if not self.history:
			return 0
		step = self.history[-1]
		if not self.__start_transaction(None, 1):
			return 0
		del self.history[-1]
		self.__do_undo(step)
		self.commit()
		return 1

	def redo(self):
		if self.busy: raise MMExc.AssertError, 'redo while busy'
		if not self.future:
			return 0
		step = self.future[-1]
		if not self.__start_transaction(None):
			return 0
		del self.future[-1]
		self.__do_undo(step)
		self.commit()
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

	def undo_delnode(self, parent, i, node):
		self.addnode(parent, i, node)

	def clean_delnode(self, parent, i, node):
		if node.GetParent() is None:
			node.Destroy()

	def addnode(self, parent, i, node):
		self.addstep('addnode', node)
		node.AddToTree(parent, i)

	def undo_addnode(self, node):
		self.delnode(node)

	def clean_addnode(self, node):
		pass

	def setnodetype(self, node, type):
		oldtype = node.GetType()
		self.addstep('setnodetype', node, oldtype)
		node.SetType(type)

	def undo_setnodetype(self, node, oldtype):
		self.setnodetype(node, oldtype)

	def clean_setnodetype(self, node, oldtype):
		pass

	def setnodeattr(self, node, name, value):
		oldvalue = node.GetRawAttrDef(name, None)
		self.addstep('setnodeattr', node, name, oldvalue)
		if value is not None:
			node.SetAttr(name, value)
		else:
			node.DelAttr(name)

	def undo_setnodeattr(self, node, name, oldvalue):
		self.setnodeattr(node, name, oldvalue)

	def clean_setnodeattr(self, node, name, oldvalue):
		pass

	def setnodevalues(self, node, values):
		self.addstep('setnodevalues', node, node.GetValues())
		node.SetValues(values)

	def undo_setnodevalues(node, oldvalues):
		self.setnodevalues(node, oldvalues)

	def clean_setnodevalues(node, oldvalues):
		pass

	#
	# Sync arc operations
	#
	def addsyncarc(self, node, attr, arc, pos = -1):
		list = node.GetRawAttrDef(attr, [])[:]
		if arc in list:
			return
		if pos >= 0:
			list.insert(pos, arc)
		else:
			list.append(arc)
		node.SetAttr(attr, list)
		self.addstep('addsyncarc', node, attr, arc, pos)

	def undo_addsyncarc(self, node, attr, arc, pos):
		self.delsyncarc(node, attr, arc)

	def clean_addsyncarc(self, node, attr, arc, pos):
		pass

	def delsyncarc(self, node, attr, arc):
		list = node.GetRawAttrDef(attr, [])[:]
		for i in range(len(list)):
			if list[i] == arc:
				break
		else:
			raise MMExc.AssertError, 'bad delsyncarc call'
		del list[i]
		if list:
			node.SetAttr(attr, list)
		else:
			node.DelAttr(attr)
		self.addstep('delsyncarc', node, attr, arc, i)

	def undo_delsyncarc(self, node, attr, arc, i):
		self.addsyncarc(node, attr, arc, i)

	def clean_delsyncarc(self, node, attr, arc, i):
		pass

	#
	# Hyperlink operations
	#
	def addlink(self, link):
		self.addstep('addlink', link)
		self.context.hyperlinks.addlink(link)

	def undo_addlink(self, link):
		self.dellink(link)

	def clean_addlink(self, link):
		pass

	def dellink(self, link):
		self.addstep('dellink', link)
		self.context.hyperlinks.dellink(link)

	def undo_dellink(self, link):
		self.addlink(link)

	def clean_dellink(self, link):
		pass

	def addexternalanchor(self, url):
		self.addstep('addexternalanchor', url)
		self.context.externalanchors.append(url)

	def undo_addexternalanchor(self, url):
		self.delexternalanchor(url)

	def clean_addexternalanchor(self, url):
		pass

	def delexternalanchor(self, url):
		self.addstep('delexternalanchor', url)
		self.context.externalanchors.remove(url)

	def undo_delexternalanchor(self, url):
		self.addexternalanchor(url)

	def clean_delexternalanchor(self, url):
		pass

	#
	# Channel operations
	#
	def addchannel(self, name, i, type):
		c = self.context.getchannel(name)
		if c is not None:
			raise MMExc.AssertError, \
				'duplicate channel name in addchannel'
		self.addstep('addchannel', name)
		self.context.addchannel(name, i, type)

	def undo_addchannel(self, name):
		self.delchannel(name)

	def clean_addchannel(self, name):
		pass

	def copychannel(self, name, i, orig):
		c = self.context.getchannel(name)
		if c is not None:
			raise MMExc.AssertError, \
				'duplicate channel name in copychannel'
		c = self.context.getchannel(orig)
		if c is None:
			raise MMExc.AssertError, \
				'unknown orig channel name in copychannel'
		self.addstep('copychannel', name)
		self.context.copychannel(name, i, orig)

	def undo_copychannel(self, name):
		self.delchannel(name)

	def clean_copychannel(self, name):
		pass

	def movechannel(self, name, i):
		old_i = self.context.channelnames.index(name)
		self.addstep('movechannel', name, old_i)
		self.context.movechannel(name, i)

	def undo_movechannel(self, name, old_i):
		self.movechannel(name, old_i)

	def clean_movechannel(self, name, old_i):
		pass

	def delchannel(self, name):
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in delchannel'
		i = self.context.channels.index(c)
		pchan = c.GetParent()
		attrdict = c.attrdict.copy()
		if pchan is not None:
			attrdict['base_window'] = pchan.name
		self.addstep('delchannel', name, i, attrdict)
		self.context.delchannel(name)

	def undo_delchannel(self, name, i, attrdict):
		self.addchannel(name, i, attrdict['type'])
		for key, val in attrdict.items():
			if key == 'type':
				continue
			self.setchannelattr(name, key, val)

	def clean_delchannel(self, name, i, attrdict):
		pass

	def setchannelname(self, name, newname):
		if newname == name:
			return # No change
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in setchannelname'
		self.addstep('setchannelname', name, newname)
		self.context.setchannelname(name, newname)

	def undo_setchannelname(self, oldname, name):
		self.setchannelname(name, oldname)

	def clean_setchannelname(self, oldname, name):
		pass

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
		self.addstep('setchannelattr', name, attrname, oldvalue)
		if value is None:
			del c[attrname]
		else:
			c[attrname] = value

	def undo_setchannelattr(self, name, attrname, oldvalue):
		self.setchannelattr(name, attrname, oldvalue)

	def clean_setchannelattr(self, name, attrname, oldvalue):
		pass

	#
	# Layout operations
	#
	def addlayout(self, name):
		if self.context.layouts.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate layout name in addlayout'
		self.addstep('addlayout', name)
		self.context.addlayout(name)

	def undo_addlayout(self, name):
		self.dellayout(name)

	def clean_addlayout(self, name):
		pass

	def dellayout(self, name):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, 'unknown layout in dellayout'
		self.addstep('dellayout', name, layout)
		self.context.dellayout(name)

	def undo_dellayout(self, name, layout):
		self.addlayout(name)
		for channel in layout:
			self.addlayoutchannel(name, channel)

	def clean_dellayout(self, name, layout):
		pass

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

	def undo_addlayoutchannel(self, name, channel):
		self.dellayoutchannel(name, channel)

	def clean_addlayoutchannel(self, name, channel):
		pass

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

	def undo_dellayoutchannel(self, name, channel):
		self.addlayoutchannel(name, channel)

	def clean_dellayoutchannel(self, name, channel):
		pass

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

	def undo_setlayoutname(self, oldname, name):
		self.setlayoutname(name, oldname)

	def clean_setlayoutname(self, oldname, name):
		pass

	#
	# User group operations
	#
	def addusergroup(self, name, value):
		if self.context.usergroups.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate usergroup name in addusergroup'
		self.addstep('addusergroup', name)
		self.context.addusergroup(name, value)

	def undo_addusergroup(self, name):
		self.delusergroup(name)

	def clean_addusergroup(self, name):
		pass

	def delusergroup(self, name):
		usergroup = self.context.usergroups.get(name)
		if usergroup is None:
			raise MMExc.AssertError, 'unknown usergroup in delusergroup'
		self.addstep('delusergroup', name, usergroup)
		self.context.delusergroup(name)

	def undo_delusergroup(self, name, usergroup):
		self.addusergroup(name, usergroup)
		
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

	def clean_delusergroup(self, name, usergroup):
		pass

	def undo_setusergroupname(self, oldname, name):
		self.setusergroupname(name, oldname)

	def clean_setusergroupname(self, oldname, name):
		pass

	#
	# Transitions operations
	#
	def addtransition(self, name, value):
		if self.context.transitions.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate transition name in addtransition'
		self.addstep('addtransition', name)
		self.context.addtransition(name, value)

	def undo_addtransition(self, name):
		self.deltransition(name)

	def clean_addtransition(self, name):
		pass

	def deltransition(self, name):
		transition = self.context.transitions.get(name)
		if transition is None:
			raise MMExc.AssertError, 'unknown transition in deltransition'
		self.addstep('deltransition', name, transition)
		self.context.deltransition(name)

	def undo_deltransition(self, name, transition):
		self.addtransition(name)
		for key, val in transition.items():
			self.settransitionvalue(name, key, val)

	def clean_deltransition(self, name, transition):
		pass

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

	def undo_settransitionname(self, oldname, name):
		self.settransitionname(name, oldname)

	def clean_settransitionname(self, oldname, name):
		pass

	def settransitionvalue(self, name, key, value):
		if not self.context.transitions.has_key(name):
			raise MMExc.AssertError, \
			      'unknown transition name in settransitionname'
		dict = self.context.transitions[name]
		oldvalue = dict.get(key)
		if oldvalue == value:
			return
		# XXX should we delete key if value==None?
		dict[key] = value
		self.addstep('settransitionvalue', name, key, oldvalue)

	def undo_settransitionvalue(self, name, key, oldvalue):
		self.settransitionvalue(name, key, oldvalue)

	def clean_settransitionvalue(self, name, key, oldvalue):
		pass

	#
	# Document operations
	#
	def deldocument(self, root):
		self.addstep('deldocument', root)

	def adddocument(self, root):
		self.addstep('adddocument', root)
		self.__newRoot = root

	def undo_deldocument(self, root):
		self.adddocument(root)

	def undo_adddocument(self, root):
		self.deldocument(root)

	def clean_deldocument(self, root):
		pass		

	def clean_adddocument(self, root):
		pass		
				  