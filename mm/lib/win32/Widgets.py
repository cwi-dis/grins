__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2

import string
from types import *

from appcon import *
import win32mu

_def_useGadget = 1

class _MenuSupport:
	'''Support methods for a pop up menu.'''
	def __init__(self):
		self._menu = None

	def close(self):
		'''Close the menu.'''
		self.destroy_menu()

	def create_menu(self, list, title = None):
		'''Create a popup menu.

		TITLE is the title of the menu.  If None or '', the
		menu will not have a title.  LIST is a list with menu
		entries.  Each entry is either None to get a
		separator, a string to get a label, or a tuple of two
		elements.  The first element is the label in the menu,
		the second argument is either a callback which is
		called when the menu entry is selected or a list which
		defines a cascading submenu.  A callback is either a
		callable object or a tuple consisting of a callable
		object and a tuple.  If the callback is just a
		callable object, it is called without arguments; if
		the callback is a tuple consisting of a callable
		object and a tuple, the object is called using apply
		with the tuple as argument.'''

		self.destroy_menu()
		if title:
			list = [title, list]
		menu = cmifex2.CreateMenu()
		win32mu._create_menu(menu, list)
		self._menu = menu

	def destroy_menu(self):
		'''Destroy the pop up menu.

		This function is called automatically when a new menu
		is created using create_menu, or when the window
		object is closed.'''

		menu = self._menu
		self._menu = None

	# support methods, only used by derived classes
	def _post_menu(self, w, client_data, call_data):
		if not self._menu:
			return

	def _destroy(self):
		self._menu = None

##################################################################
class _Widget(_MenuSupport):
	'''Support methods for all window objects.'''
	def __init__(self, parent, widget):
		self._parent = parent
		parent._children.append(self)
		self._showing = TRUE
		self._form = widget
		#widget.ManageChild()
		_MenuSupport.__init__(self)
		#self._form.AddCallback('destroyCallback', self._destroy, None)
		#if widget:
		#	widget.HookMessage(self._destroy, win32con.WM_DESTROY)

	def __repr__(self):
		return '<_Widget instance at %x>' % id(self)

	def close(self):
		'''Close the window object.'''
		try:
			form = self._form
		except AttributeError:
			pass
		else:
			#del self._form
			_MenuSupport.close(self)
			#cmifex2.DestroyWindow(form)
			#form.DestroyWindow()
			#form.DestroyWidget()
		if self._parent:
			#cmifex2.DestroyMenu(self._parent._hWnd)
			self._parent._children.remove(self)
		self._parent = None
		return

	def is_closed(self):
		'''Returns true if the window is already closed.'''
		return not hasattr(self, '_form')

	def _showme(self, w):
		self._parent._showme(w)

	def _hideme(self, w):
		self._parent._hideme(w)

	def show(self):
		'''Make the window visible.'''
		self._parent._showme(self)
		self._showing = TRUE

	def hide(self):
		'''Make the window invisible.'''
		self._parent._hideme(self)
		self._showing = FALSE

	def is_showing(self):
		'''Returns true if the window is visible.'''
		return self._showing

	# support methods, only used by derived classes
	def _attachments(self, attrs, options):
		'''Calculate the attachments for this window.'''
		for pos in ['left', 'top', 'right', 'bottom']:
			#attachment = pos + 'Attachment'
			#try:
			#	widget = options[pos]
			#except:
			#	pass
			#else:
			#	if type(widget) in (FloatType, IntType):
			#		attrs[attachment] = \
			#			Xmd.ATTACH_POSITION
			#		attrs[pos + 'Position'] = \
			#			int(widget * 100 + .5)
			#	elif widget:
			#		attrs[pos + 'Attachment'] = \
			#			  Xmd.ATTACH_WIDGET
			#		attrs[pos + 'Widget'] = widget._form
			#	else:
			#		attrs[pos + 'Attachment'] = \
			#			  Xmd.ATTACH_FORM
			if options.has_key(pos):
				attrs[pos] = options[pos]


	def _destroy(self, params):
		'''Destroy callback.'''
		#try:
		#	form = self._form
		#except AttributeError:
		#	return
		if hasattr(self, '_form'):
			form = self._form
			del self._form
			#cmifex2.DestroyWindow(form)
			if form:
				form.DestroyWindow()
			if self._parent:
				#if self._menu:
				#	 cmifex2.DestroyMenu(self._parent._hWnd)
				self._parent._children.remove(self)
			self._parent = None
			_MenuSupport._destroy(self)

##################################################################
class Label(_Widget):
	'''Label window object.'''
	def __init__(self, parent, text, justify = 'center', useGadget = _def_useGadget,
		     name = 'windowLabel', **options):
		'''Create a Label subwindow.

		PARENT is the parent window, TEXT is the text for the
		label.  OPTIONS is an optional dictionary with
		options.  The only options recognized are the
		attachment options.'''
		print "Label control", parent, text, options
		attrs = {}
		self._attachments(attrs, options)
		#if useGadget:
		#	label = Xm.LabelGadget
		#else:
		#	label = Xm.Label
		#label = parent._form.CreateManagedWidget(name, label, attrs)
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
	
		label = cmifex2.CreateStatic(text,parent._hWnd,left,top,width,height,justify)	
		#self._form = label
		#label.labelString = text
		self._text = text
		_Widget.__init__(self, parent, label)

	def __repr__(self):
		return '<Label instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		'''Set the text of the label to TEXT.'''
		#self._form.labelString = text
		self._text = text
		cmifex2.SetCaption(self._form, text)


##################################################################
class Button(_Widget):
	'''Button window object.'''
	def __init__(self, parent, label, callback, useGadget = _def_useGadget,
		     name = 'windowButton', **options):
		'''Create a Button subwindow.

		PARENT is the parent window, LABEL is the label on the
		button, CALLBACK is the callback function that is
		called when the button is activated.  The callback is
		a tuple consiting of a callable object and an argument
		tuple.'''
		self._text = label
		attrs = {'labelString': label}
		self._attachments(attrs, options)
		#if useGadget:
		#	button = Xm.PushButtonGadget
		#else:
		#	button = Xm.PushButton
		#button = parent._form.CreateManagedWidget(name, button, attrs)
		self._cb = callback
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
		
		#button = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)
		
		button = cmifex2.CreateButton(label,parent._hWnd,left,top,width,height,('b',' '))
		if callback:
			#button.AddCallback('activateCallback',
			#		   self._callback, callback)
			#button.HookMessage(self._callback, win32con.WM_LBUTTONDOWN)
			pass
		#button.HookMessage(self._callback, win32con.WM_COMMAND)
		button.HookMessage(self._callback, win32con.WM_LBUTTONUP)
		_Widget.__init__(self, parent, button)

	def __repr__(self):
		return '<Button instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		#self._form.labelString = text
		self._text = text
		cmifex2.SetCaption(self._form, text)

	def setsensitive(self, sensitive):
		#self._form.sensitive = sensitive
		self._form.EnableWindow(sensitive)
		return

	def _callback(self, params):
		#global _in_create_box
		#if _in_create_box == None or self._parent==_in_create_box:
			#print "level 1"
			if self.is_closed():
				return
			#print "level 2"
			#val = win32api.HIWORD(params[2])

			#if val == win32con.BN_CLICKED:
			#	print "level 3"
			#	if self._cb:
			#		apply(self._cb[0], self._cb[1])
			if self._cb:
				apply(self._cb[0], self._cb[1])
			self._form.ReleaseCapture()
			
			
##################################################################		
class OptionMenu(_Widget):
	'''Option menu window object.'''
	def __init__(self, parent, label, optionlist, startpos, cb,
		     useGadget = _def_useGadget, name = 'windowOptionMenu',
		     **options):
		'''Create an option menu window object.

		PARENT is the parent window, LABEL is a label for the
		option menu, OPTIONLIST is a list of options, STARTPOS
		gives the initial selected option, CB is the callback
		that is to be called when the option is changed,
		OPTIONS is an optional dictionary with options.
		If label is None, the label is not shown, otherwise it
		is shown to the left of the option menu.
		The optionlist is a list of strings.  Startpos is the
		index in the optionlist of the initially selected
		option.  The callback is either None, or a tuple of
		two elements.  If None, no callback is called when the
		option is changed, otherwise the the first element of
		the tuple is a callable object, and the second element
		is a tuple giving the arguments to the callable
		object.'''

		attrs = {}
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		self._useGadget = useGadget
		#initbut = self._do_setoptions(parent, optionlist,
		#			      startpos)
		#attrs = {'menuHistory': initbut,
		#	 'subMenuId': self._omenu,
		#	 'colormap': toplevel._default_colormap,
		#	 'visual': toplevel._default_visual,
		#	 'depth': toplevel._default_visual.depth}
		self._attachments(attrs, options)
		#option = parent._form.CreateOptionMenu(name, attrs)
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
		
		option = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,25)
		
		if label is None:
			#option.OptionLabelGadget().UnmanageChild()
			
			self._combo = cmifex2.CreateCombobox(" ",option,0,0,width,height,(0,'dr',1))
			self._text = '<None>'
		else:
			#option.labelString = label
			#print parent._hWnd
			cmifex2.CreateStatic(label,option,0,0,cmifex2.GetStringLength(parent._hWnd,label),25,'left')
			l1 = cmifex2.GetStringLength(parent._hWnd,label)
			self._combo = cmifex2.CreateCombobox(" ",option,cmifex2.GetStringLength(parent._hWnd,label),0,width-cmifex2.GetStringLength(parent._hWnd,label),height,(0,'dr',1))
			self._text = label
		initbut = self._do_setoptions(parent, optionlist,
					      startpos)
		self._callback = cb
		option.HookMessage(self._cb, win32con.WM_COMMAND)
		_Widget.__init__(self, parent, option)

	def __repr__(self):
		return '<OptionMenu instance at %x, label=%s>' % (id(self), self._text)

	def close(self):
		_Widget.close(self)
		self._callback = self._value = self._optionlist = \
				 self._buttons = None

	def getpos(self):
		'''Get the index of the currently selected option.'''
		return self._value

	def getvalue(self):
		'''Get the value of the currently selected option.'''
		return self._optionlist[self._value]

	def setpos(self, pos):
		'''Set the currently selected option to the index given by POS.'''
		if pos == self._value:
			return
		#self._form.menuHistory = self._buttons[pos]
		if pos in self._buttons:
			cmifex2.Set(self._combo,self._buttons.index(pos))
			self._value = pos

	def setsensitive(self, pos, sensitive):
		if sensitive==0:
			if pos in self._buttons:
				cmifex2.DeleteToPos(self._combo,self._buttons.index(pos))
				self._buttons.remove(pos)
		else:
			if not pos in self._buttons:
				if 0 <= pos < len(self._optionlist):
					self._buttons.append(pos)
					self._buttons.sort()
					p = self._buttons.index(pos)
					cmifex2.InsertToPos(self._combo,p,self._optionlist[pos])
		#if 0 <= pos < len(self._buttons):
		#	#self._buttons[pos].sensitive = sensitive
		#	pass
		#else:
		#	raise error, 'pos out of range'

	def setvalue(self, value):
		'''Set the currently selected option to VALUE.'''
		self.setpos(self._optionlist.index(value))

	def setoptions(self, optionlist, startpos):
		'''Set new options.

		OPTIONLIST and STARTPOS are as in the __init__ method.'''

		if optionlist != self._optionlist:
			#if self._useGadget:
			#	createfunc = self._omenu.CreatePushButtonGadget
			#else:
			#	createfunc = self._omenu.CreatePushButton
			# reuse old menu entries or create new ones
			cmifex2.Reset(self._combo)
			self._buttons = []
			for i in range(len(optionlist)):
				item = optionlist[i]
				#if i == len(self._buttons):
				#	button = createfunc(
				#		'windowOptionButton',
				#		{'labelString': item})
				#	button.AddCallback('activateCallback',
				#			   self._cb, i)
				#	button.ManageChild()
				#	self._buttons.append(button)
				#else:
				#	button = self._buttons[i]
				#	button.labelString = item
				self._buttons.append(i)
				cmifex2.Add(self._combo,item)
			# delete superfluous menu entries
			#n = len(optionlist)
			#while len(self._buttons) > n:
			#	self._buttons[n].DestroyWidget()
			#	del self._buttons[n]
			tmp = []
			for item in optionlist:
				tmp.append(item)
			#self._optionlist = optionlist
			self._optionlist = tmp
		# set the start position
		self.setpos(startpos)

	def _do_setoptions(self, form, optionlist, startpos):
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		#menu = form.CreatePulldownMenu('windowOption',
		#		{'colormap': toplevel._default_colormap,
		#		 'visual': toplevel._default_visual,
		#		 'depth': toplevel._default_visual.depth})
		#self._omenu = menu
		tmp = []
		for item in optionlist:
			tmp.append(item)
		#self._optionlist = optionlist
		self._optionlist = tmp
		self._value = startpos
		self._buttons = []
		#if self._useGadget:
		#	createfunc = menu.CreatePushButtonGadget
		#else:
		#	createfunc = menu.CreatePushButton
		for i in range(len(optionlist)):
			item = optionlist[i]
		#	button = createfunc('windowOptionButton',
		#			    {'labelString': item})
		#	button.AddCallback('activateCallback', self._cb, i)
		#	button.ManageChild()
		#	if startpos == i:
		#		initbut = button
		#	self._buttons.append(button)
			self._buttons.append(i)
			cmifex2.Add(self._combo,item)
		#return initbut
		cmifex2.Set(self._combo,startpos)
		return startpos

	def _cb(self, params):
		if self.is_closed():
			return
		val = win32api.HIWORD(params[2])
		if val == win32con.LBN_SELCHANGE or val == win32con.CBN_SELCHANGE:
			#self._value = value
			self._value = self._buttons[cmifex2.GetPos(self._combo)]
			if self._callback:
				f, a = self._callback
				apply(f, a)
		else:
			return

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		#del self._omenu
		del self._optionlist
		del self._buttons
		del self._callback

##################################################################
class PulldownMenu(_Widget):
	'''Menu bar window object.'''
	def __init__(self, parent, menulist, useGadget = _def_useGadget,
		     name = 'menuBar', **options):
		'''Create a menu bar window object.

		PARENT is the parent window, MENULIST is a list giving
		the definition of the menubar, OPTIONS is an optional
		dictionary of options.
		The menulist is a list of tuples.  The first elements
		of the tuples is the name of the pulldown menu, the
		second element is a list with the definition of the
		pulldown menu.'''

		attrs = {}
		self._callback_dict = {}
		menuid = 0
		menubar = cmifex2.CreateMenu()
		buttons = []
		for item, list in menulist:
			menu = cmifex2.CreateMenu()
			temp = win32mu._create_menu(menu, list, menuid,self._callback_dict)
			if temp:
				menuid = temp[0]
				dict2 = temp[1]
				dkeys = dict2.keys()
				for k in dkeys:
					if not self._callback_dict.has_key(k):
						self._callback_dict[k] = dict2[k]
			cmifex2.PopupAppendMenu(menubar, menu, item)
		_Widget.__init__(self, parent, None)
		self._buttons = buttons
		self._menu = menubar
		#cmifex2.SetMenu(parent._hWnd,menubar)
		parent._hWnd.HookMessage(self._menu_callback, win32con.WM_COMMAND)


	def __repr__(self):
		return '<PulldownMenu instance at %x>' % id(self)

	def _menu_callback(self, params):
		if params[3] != 0:
			return
		#print "menu-->", params
		item = params[2]
		if self._callback_dict.has_key(item):
			try:
				f, a = self._callback_dict[item]
			except AttributeError:
				pass
			else:
				apply(f, a)

	
	def close(self):
		_Widget.close(self)
		self._buttons = None

	def setmenu(self, pos, list):
		if not 0 <= pos < len(self._buttons):
			raise error, 'position out of range'
		button = self._buttons[pos]

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons


##################################################################
# super class for Selection and List
class _List:
	def __init__(self, list, itemlist, initial, sel_cb):
		self._list = list
		#list.ListAddItems(itemlist, 1)
		for item in itemlist:
			cmifex2.Add(list,item)
		self._itemlist = itemlist
		self._cb = None
		if type(sel_cb) is ListType:
			if len(sel_cb) >= 1 and sel_cb[0]:
				#list.AddCallback('singleSelectionCallback',
				#		 self._callback, sel_cb[0])
				self._cb = sel_cb[0]
			if len(sel_cb) >= 2 and sel_cb[1]:
				#list.AddCallback('defaultActionCallback',
				#		 self._callback, sel_cb[1])
				self._cb = sel_cb[1]
		elif sel_cb:
			#list.AddCallback('singleSelectionCallback',
			#		 self._callback, sel_cb)
			self._cb = sel_cb
		
		if itemlist:
			self.selectitem(initial)
		


	def close(self):
		self._itemlist = None
		self._list = None

	def getselected(self):
		#pos = self._list.ListGetSelectedPos()
		pos = cmifex2.GetPos(self._list)
		if pos>=0:
			#return pos[0] - 1
			return pos #- 1
		else:
			return None

	def getlistitem(self, pos):
		return self._itemlist[pos]

	def getlist(self):
		return self._itemlist

	def addlistitem(self, item, pos):
		if pos < 0:
			pos = len(self._itemlist)
		#self._list.ListAddItem(item, pos + 1)
		self._itemlist.insert(pos, item)
		cmifex2.InsertToPos(self._list,pos,item)

	def addlistitems(self, items, pos):
		if pos < 0:
			pos = len(self._itemlist)
		#self._list.ListAddItems(items, pos + 1)
		for item in items:
			cmifex2.InsertToPos(self._list,pos,item)
			pos = pos +1
		self._itemlist[pos:pos] = items

	def dellistitem(self, pos):
		del self._itemlist[pos]
		#self._list.ListDeletePos(pos + 1)
		cmifex2.DeleteToPos(self._list,pos)
	

	def dellistitems(self, poslist):
		#self._list.ListDeletePositions(map(lambda x: x+1, poslist))
		list = poslist[:]
		list.sort()
		list.reverse()
		for pos in list:
			del self._itemlist[pos]
			cmifex2.DeleteToPos(self._list,pos)

	def replacelistitem(self, pos, newitem):
		self.replacelistitems(pos, [newitem])

	def replacelistitems(self, pos, newitems):
		self._itemlist[pos:pos+len(newitems)] = newitems
		#self._list.ListReplaceItemsPos(newitems, pos + 1)
		for item in newitems:
			cmifex2.ReplaceToPos(self._list,pos,item)
			pos = pos +1

	def delalllistitems(self):
		self._itemlist = []
		#self._list.ListDeleteAllItems()
		cmifex2.Reset(self._list)

	def selectitem(self, pos):
		if pos is None:
			#self._list.ListDeselectAllItems()
			cmifex2.Set(self._list,-1)
			self._list.SendMessage(win32con.WM_LBUTTONDBLCLK,0,0)
			return
		if pos < 0:
			pos = len(self._itemlist) - 1
		#self._list.ListSelectPos(pos + 1, TRUE)
		cmifex2.Set(self._list,pos)
		self._list.SendMessage(win32con.WM_LBUTTONDBLCLK,0,0)

	def is_visible(self, pos):
		#print "pos -->>>", pos
	#	if pos < 0:
	#		pos = len(self._itemlist) - 1
	#	top = self._list.topItemPosition - 1
	#	vis = self._list.visibleItemCount
	#	return top <= pos < top + vis
		return 1

	def scrolllist(self, pos, where):
		#if pos < 0:
		#	pos = len(self._itemlist) - 1
		#if where == TOP:
		#	self._list.ListSetPos(pos + 1)
		#elif where == BOTTOM:
		#	self._list.ListSetBottomPos(pos + 1)
		#elif where == CENTER:
		#	vis = self._list.visibleItemCount
		#	toppos = pos - vis / 2 + 1
		#	if toppos + vis > len(self._itemlist):
		#		toppos = len(self._itemlist) - vis + 1
		#	if toppos <= 0:
		#		toppos = 1
		#	self._list.ListSetPos(toppos)
		#else:
		#	raise error, 'bad argument for scrolllist'
		pass
			

	def _callback(self, params):
		if self.is_closed():
			return
		if self._cb:
			f, a = self._cb
			apply(f, a)
		else:
			return
		


	def _destroy(self):
		del self._itemlist
		del self._list

##################################################################
class Selection(_Widget, _List):
	def __init__(self, parent, listprompt, itemprompt, itemlist, initial, sel_cb,
		     name = 'windowSelection', **options):
		attrs = {}
		self._attachments(attrs, options)
		#selection = parent._form.CreateSelectionBox(name, attrs)
		#for widget in Xmd.DIALOG_APPLY_BUTTON, \
		#    Xmd.DIALOG_CANCEL_BUTTON, Xmd.DIALOG_DEFAULT_BUTTON, \
		#   Xmd.DIALOG_HELP_BUTTON, Xmd.DIALOG_OK_BUTTON, \
		#    Xmd.DIALOG_SEPARATOR:
		#	selection.SelectionBoxGetChild(widget).UnmanageChild()
		#w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		self._list = None
		self._listlabel = None
		self._editlabel = None
		self._edit = None
		self._sel_cb = None
		selection = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)
		if listprompt is None:
			#w.UnmanageChild()
			top = 0
			self._text = '<None>'
		else:
			#w.labelString = listprompt
			self._listlabel = cmifex2.CreateStatic(listprompt,selection,0,0,width,25,'left')
			top = 25
			height = height - 25
			self._text = listprompt
		#w = selection.SelectionBoxGetChild(Xmd.DIALOG_SELECTION_LABEL)
		
		if itemprompt is None:
			#w.UnmanageChild()
			list = cmifex2.CreateListbox(" ",selection,0,top,width,height-25,0)
			top = top + height - 25
			print "No item label"
		else:
			#w.labelString = itemprompt
			list = cmifex2.CreateListbox(" ",selection,0,top,width,height-50,0)
			top = top + height - 50
			self._editlabel = cmifex2.CreateStatic(itemprompt,selection,0,top,width,25,'left')
			top = top + 25
		#list = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST)
		#list.selectionPolicy = Xmd.SINGLE_SELECT
		#list.listSizePolicy = Xmd.CONSTANT
		self._edit = cmifex2.CreateEdit(" ",selection,0,top,width,25,TRUE)
		try:
			cb = options['enterCallback']
		except KeyError:
			pass
		else:
			#txt = selection.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
			#txt.AddCallback('activateCallback', self._callback, cb)
			self._sel_cb = cb
			self._edit.HookMessage(self.sel_callback, win32con.WM_KEYUP)
		_List.__init__(self, list, itemlist, initial, sel_cb)
		_Widget.__init__(self, parent, selection)
		str = cmifex2.Get(self._list)
		if str!='':
			cmifex2.SetCaption(self._edit,str)
		#self._list.HookMessage(self._callback, win32con.WM_LBUTTONDBLCLK)
		#self._list.HookMessage(self._callback, win32con.WM_KEYUP)
		self._list.HookMessage(self._callback, win32con.WM_LBUTTONUP)
		
		

	def __repr__(self):
		return '<Selection instance at %x; label=%s>' % (id(self), self._text)

	
	def _callback(self, params):
		if self.is_closed():
			return
		val = params[1]
		if val == win32con.WM_LBUTTONDBLCLK or (val == win32con.WM_KEYUP and params[2] == 13):
			#print "selection _callback"
			str = cmifex2.Get(self._list)
			#print str
			if str!='':
				cmifex2.SetCaption(self._edit,str)
			else:
				cmifex2.SetCaption(self._edit,'')
				return
			_List._callback(self,params)
		elif val == win32con.WM_LBUTTONUP:
				val = win32api.LOWORD(params[2])
				
				str = cmifex2.Get(self._list)
				#print str
				_List._callback(self,params)
				if str:
					cmifex2.SetCaption(self._edit,str)
				else:
					return
				self._list.ReleaseCapture()
				return


	
	def sel_callback(self, params):
		if self.is_closed():
			return
		val = params[1]
		if val == win32con.WM_KEYUP and params[2] == 13:
			if self._sel_cb:
				f, a = self._sel_cb
				apply(f, a)
			else:
				return
		else:
			return


	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		#w = self._form.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		#w.labelString = label
		if self._listlabel:
			cmifex2.SetCaption(self._listlabel, label)
			self._text = label

	def getselection(self):
		#text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		#if hasattr(text, 'TextFieldGetString'):
		#	return text.TextFieldGetString()
		#else:
		#	return text.TextGetString()
		text = cmifex2.GetText(self._edit)
		print "--------->", text
		return text

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

	def seteditable(self, editable):
		#text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		#text.editable = editable
		self._edit.EnableWindow(editable)

##################################################################
class List(_Widget, _List):
	def __init__(self, parent, listprompt, itemlist, sel_cb,
		     rows = 10, useGadget = _def_useGadget,
		     name = 'windowList', **options):
		#attrs = {'resizePolicy': parent.resizePolicy}
		attrs = {}
		self._attachments(attrs, options)
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		self._list = None
		self._listlabel = None
		form = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)
		
		if listprompt is not None:
		#	if useGadget:
		#		labelwidget = Xm.LabelGadget
		#	else:
		#		labelwidget = Xm.Label
		#	form = parent._form.CreateManagedWidget(
		#		'windowListForm', Xm.Form, attrs)
		#	label = form.CreateManagedWidget(name + 'Label',
		#			labelwidget,
		#			{'topAttachment': Xmd.ATTACH_FORM,
		#			 'leftAttachment': Xmd.ATTACH_FORM,
		#			 'rightAttachment': Xmd.ATTACH_FORM})
		#	self._label = label
		#	label.labelString = listprompt
		#	attrs = {'topAttachment': Xmd.ATTACH_WIDGET,
		#		 'topWidget': label,
		#		 'leftAttachment': Xmd.ATTACH_FORM,
		#		 'rightAttachment': Xmd.ATTACH_FORM,
		#		 'bottomAttachment': Xmd.ATTACH_FORM,
		#		 'visibleItemCount': rows,
		#		 'selectionPolicy': Xmd.SINGLE_SELECT}
		#	try:
		#		attrs['width'] = options['width']
		#	except KeyError:
		#		pass
		#	if parent.resizePolicy == Xmd.RESIZE_ANY:
		#		attrs['listSizePolicy'] = \
		#					Xmd.RESIZE_IF_POSSIBLE
		#	else:
		#		attrs['listSizePolicy'] = Xmd.CONSTANT
		#	list = form.CreateScrolledList(name, attrs)
		#	list.ManageChild()
			self._listlabel = cmifex2.CreateStatic(listprompt,form,0,0,width,25,'center')
			list = cmifex2.CreateListbox(" ",form,0,25,width,height-25,0)
		#	widget = form
			self._text = listprompt
		else:
			attrs['visibleItemCount'] = rows
		#	attrs['selectionPolicy'] = Xmd.SINGLE_SELECT
		#	if parent.resizePolicy == Xmd.RESIZE_ANY:
		#		attrs['listSizePolicy'] = \
		#					Xmd.RESIZE_IF_POSSIBLE
		#	else:
		#		attrs['listSizePolicy'] = Xmd.CONSTANT
		#	try:
		#		attrs['width'] = options['width']
		#	except KeyError:
		#		pass
		#	list = parent._form.CreateScrolledList(name, attrs)
		#	widget = list
			list = cmifex2.CreateListbox(" ",form,0,0,width,height,0)
			self._text = '<None>'
		widget = form
		_List.__init__(self, list, itemlist, None, sel_cb)
		_Widget.__init__(self, parent, widget)
		#self._list.HookMessage(self._callback, win32con.WM_LBUTTONDBLCLK)
		#self._list.HookMessage(self._callback, win32con.WM_KEYUP)
		self._list.HookMessage(self._callback, win32con.WM_LBUTTONUP)

	

	def __repr__(self):
		return '<List instance at %x; label=%s>' % (id(self), self._text)

	
	def _callback(self, params):
		self._list.ReleaseCapture()
		if self.is_closed():
			return
		val = params[1]
		if val == win32con.WM_LBUTTONUP or (val == win32con.WM_KEYUP and params[2] == 13):
			str = cmifex2.Get(self._list)
			if not str:
				return
			_List._callback(self,params)
		else:
			return

	
	
	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		#try:
		#	self._label.labelString = label
		#except AttributeError:
		#	raise error, 'List created without label'
		#else:
		#	self._text = label
		if self._listlabel:
			cmifex2.SetCaption(self._listlabel,label)
			self._text = label
		else:
			return

	def _destroy(self, widget, value, call_data):
		#try:
		#	del self._label
		#except AttributeError:
		#	pass
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

##################################################################
class TextInput(_Widget):
	def __init__(self, parent, prompt, inittext, chcb, accb,
		     useGadget = _def_useGadget, name = 'windowTextfield',
		     **options):
		attrs = {}
		self._attachments(attrs, options)
		#if prompt is not None:
		#	if useGadget:
		#		labelwidget = Xm.LabelGadget
		#	else:
		#		labelwidget = Xm.Label
		#	form = parent._form.CreateManagedWidget(
		#		name + 'Form', Xm.Form, attrs)
		#	label = form.CreateManagedWidget(
		#		name + 'Label', labelwidget,
		#		{'topAttachment': Xmd.ATTACH_FORM,
		#		 'leftAttachment': Xmd.ATTACH_FORM,
		#		 'bottomAttachment': Xmd.ATTACH_FORM})
		#	self._label = label
		#	label.labelString = prompt
		#	attrs = {'topAttachment': Xmd.ATTACH_FORM,
		#		 'leftAttachment': Xmd.ATTACH_WIDGET,
		#		 'leftWidget': label,
		#		 'bottomAttachment': Xmd.ATTACH_FORM,
		#		 'rightAttachment': Xmd.ATTACH_FORM}
		#	widget = form
		#else:
		#	form = parent._form
		#	widget = None
		#try:
		#	attrs['columns'] = options['columns']
		#except KeyError:
		#	pass
		#attrs['value'] = inittext
		try:
			attrs['editable'] = options['editable']
		except KeyError:
			pass
		#text = form.CreateTextField(name, attrs)
		#text.ManageChild()
		#if not widget:
		#	widget = text
		if attrs.has_key('editable'):
			editable = attrs['editable']
		else:
			editable = TRUE
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		text = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		if prompt is None:
			if (inittext==None or inittext==''):
				inittext= ' '
			self._edit = cmifex2.CreateEdit(inittext,text,0,0,width,height,editable)
			self._label = None
		else:
			print cmifex2.GetStringLength(text, prompt)
			self._label = cmifex2.CreateStatic(prompt,text,0,0,cmifex2.GetStringLength(text, prompt),25,'left')
			self._edit = cmifex2.CreateEdit(inittext,text,cmifex2.GetStringLength(text, prompt),0,width-cmifex2.GetStringLength(text, prompt),height,editable)
		
		widget = text

		if chcb:
			#text.AddCallback('valueChangedCallback',
			#		 self._callback, chcb)
			self._ch_cb = chcb
		else:
			self._ch_cb = None
		if accb:
			#text.AddCallback('activateCallback',
			#		 self._callback, accb)
			self._ac_cb = accb
		else:
			self._ac_cb = None

		self._text = text
		_Widget.__init__(self, parent, widget)
		#print '-----------------------------', self._edit
		#print '-----------------------------', self._callback
		#self._edit.HookMessage(self._callback, win32con.WM_SETFOCUS)
		self._edit.HookMessage(self._callback, win32con.WM_KILLFOCUS)


	def __repr__(self):
		return '<TextInput instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._text = None

	def setlabel(self, label):
		if not hasattr(self, '_label'):
			raise error, 'TextInput create without label'
		#self._label.labelString = label
		cmifex2.SetCaption(self._label,label)

	def gettext(self):
		#return self._text.TextFieldGetString()
		if self._form:
			return cmifex2.GetText(self._edit)
		else:
			return ''

	def settext(self, text):
		#self._text.value = text
		if self._form:
			cmifex2.SetCaption(self._edit,text)

	def _callback(self, params):
		if self.is_closed():
			return
		if params[1] == win32con.WM_KILLFOCUS:
			if self._ch_cb:
				func, arg = self._ch_cb
			else:
				return
		else:
			res = cmifex2.Changed(self._form)
			if res !=0:
				if self._ac_cb:
					func, arg = self._ac_cb
				else:
					return
			else:
				return
		apply(func, arg)

	def seteditable(self, editable):
		self._form.EnableWindow(editable)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		try:
			del self._label
		except AttributeError:
			pass
		del self._text


##################################################################
class TextEdit(_Widget):
	def __init__(self, parent, inittext, cb, name = 'windowText',
		     **options):
		#attrs = {'editMode': Xmd.MULTI_LINE_EDIT,
		attrs = {'editable': TRUE,
				 'rows': 10}
		for option in ['editable', 'rows', 'columns']:
			try:
				attrs[option] = options[option]
			except KeyError:
				pass
		if not attrs['editable']:
			attrs['cursorPositionVisible'] = FALSE
		self._attachments(attrs, options)
		#text = parent._form.CreateScrolledText(name, attrs)
		
		editable = attrs['editable']

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
		#print  parent._hWnd,left,top,width,height,editable
		str1 = 'klh'
		text = cmifex2.CreateMultiEdit(str1,parent._hWnd,left,top,width,height,editable)
		self._cb = None
		
		if cb:
			#text.AddCallback('activateCallback', self._callback,
			#		 cb)
			self._cb = cb
		_Widget.__init__(self, parent, text)
		self.settext(inittext)
		text.HookMessage(self._callback, win32con.WM_SETFOCUS)


	def __repr__(self):
		return '<TextEdit instance at %x>' % id(self)


	def settext(self, text):
		if type(text) is ListType:
			text = string.joinfields(text, '\n')
		#self._form.TextSetString(text)
		cmifex2.SetCaption(self._form,text)
		self._linecache = None

	def gettext(self):
		#return self._form.TextGetString()
		if self._form:
			return cmifex2.GetText(self._form)
		else:
			return ''


	def getlines(self):
		text = self.gettext()
		text = string.splitfields(text, '\n')
		if len(text) > 0 and text[-1] == '':
			del text[-1]
		return text

	def _mklinecache(self):
		text = self.getlines()
		self._linecache = c = []
		pos = 0
		for line in text:
			c.append(pos)
			pos = pos + len(line) + 1

	def getline(self, line):
		lines = self.getlines()
		if line < 0 or line >= len(lines):
			line = len(lines) - 1
		return lines[line]

	def scrolltext(self, line, where):
		if not self._linecache:
			self._mklinecache()
		if line < 0 or line >= len(self._linecache):
			line = len(self._linecache) - 1
		if where == TOP:
			pass
		else:
			rows = self._form.rows
			if where == BOTTOM:
				line = line - rows + 1
			elif where == CENTER:
				line = line - rows/2 + 1
			else:
				raise error, 'bad argument for scrolltext'
			if line < 0:
				line = 0
		#self._form.TextSetTopCharacter(self._linecache[line])

	def selectchars(self, line, start, end):
		if not self._linecache:
			self._mklinecache()
		if line < 0 or line >= len(self._linecache):
			line = len(self._linecache) - 1
		pos = self._linecache[line]
		#self._form.TextSetSelection(pos + start, pos + end, 0)
		cmifex2.Select(self._form, pos + start, pos + end)

	def _callback(self, params):
		if self.is_closed():
			return
		if self._cb:
			func, arg = self._cb
			apply(func, arg)
		res = cmifex2.Changed(self._form)

	def seteditable(self, editable):
		self._form.EnableWindow(editable)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._linecache


##################################################################
class Separator(_Widget):
	def __init__(self, parent, useGadget = _def_useGadget,
		     name = 'windowSeparator', **options):
		attrs = {}
		self._attachments(attrs, options)
		#if useGadget:
		#	separator = Xm.SeparatorGadget
		#else:
		#	separator = Xm.Separator
		#separator = parent._form.CreateManagedWidget(name, separator,
		#					     attrs)
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		separator = cmifex2.CreateSeparator(parent._hWnd,left,top,width,height,0)
		_Widget.__init__(self, parent, separator)

	def __repr__(self):
		return '<Separator instance at %x>' % id(self)


##################################################################
class ButtonRow(_Widget):
	def __init__(self, parent, buttonlist,
		     vertical = 1, callback = None,
		     buttontype = 'pushbutton', useGadget = _def_useGadget,
		     name = 'windowRowcolumn', **options):
		#attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
		#	 'traversalOn': FALSE}
		#if not vertical:
		#	attrs['orientation'] = Xmd.HORIZONTAL
##		#	attrs['packing'] = Xmd.PACK_COLUMN
		self._cb = callback
		#if useGadget:
		#	separator = Xm.SeparatorGadget
		#	cascadebutton = Xm.CascadeButtonGadget
		#	pushbutton = Xm.PushButtonGadget
		#	togglebutton = Xm.ToggleButtonGadget
		#else:
		#	separator = Xm.Separator
		#	cascadebutton = Xm.CascadeButton
		#	pushbutton = Xm.PushButton
		#	togglebutton = Xm.ToggleButton
		attrs = {}
		self._attachments(attrs, options)
		#rowcolumn = parent._form.CreateManagedWidget(name, Xm.RowColumn, attrs)
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		rowcolumn = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)
		
		if vertical:
			#max = 0
			#length = 0
			#for entry in buttonlist:
			#	if type(entry) is TupleType:
			#		label = entry[0]
			#	else:
			#		label = entry
			#	length = cmifex2.GetStringLength(rowcolumn,label)
			#	if length>max:
			#		max = length
			#width = max+5
			width = width - 10
		
		left = top = 0
		self._buttons = []
		self._callbks = {}
		for entry in buttonlist:
			if entry is None:
				#if vertical:
				#	attrs = {'orientation': Xmd.HORIZONTAL}
				#else:
				#	attrs = {'orientation': Xmd.VERTICAL}
				#dummy = rowcolumn.CreateManagedWidget(
				#	'buttonSeparator', separator, attrs)
				if vertical:
					cmifex2.CreateSeparator(rowcolumn,left+5,top+5,width,height,0)
					top = top + 10
				else:
					cmifex2.CreateSeparator(rowcolumn,left+5,top+5,width,height,1)
					left = left + 10
				continue
			btype = buttontype
			if type(entry) is TupleType:
				label, callback = entry[:2]
				if len(entry) > 2:
					btype = entry[2]
			else:
				label, callback = entry, None
			if type(callback) is ListType:
				continue
			if callback and type(callback) is not TupleType:
				callback = (callback, (label,))
			if btype[0] in ('b', 'p'): # push button
				#gadget = pushbutton
				battrs = {}
				callbackname = 'activateCallback'
			elif btype[0] == 't': # toggle button
				callbackname = 'valueChangedCallback'
			elif btype[0] == 'r': # radio button
				callbackname = 'valueChangedCallback'
			else:
				raise error, 'bad button type'
			if not vertical:
				if label:
					width = cmifex2.GetStringLength(rowcolumn,label)+10
				else:
					width = 10
			
			button = cmifex2.CreateButton(label,rowcolumn,left+5,top+5,width,20,(btype[0],'right'))
			if callback or self._cb:
				pass
				
			self._buttons.append(button)
			if callback:
				self._callbks[button.GetSafeHwnd()] = (callback,btype[0])
			else:
				self._callbks[button.GetSafeHwnd()] = (None,None)

			if vertical:
				top = top + 25
			else:
				left = left + width+5

		rowcolumn.HookMessage(self._callback, win32con.WM_COMMAND)
		_Widget.__init__(self, parent, rowcolumn)


	def __repr__(self):
		return '<ButtonRow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._buttons = None
		self._cb = None

	def hide(self, button = None):
		if button is None:
			_Widget.hide(self)
			return
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#self._buttons[button].UnmanageChild()
		self._buttons[button].ShowWindow(win32con.SW_HIDE)


	def show(self, button = None):
		if button is None:
			_Widget.show(self)
			return
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#self._buttons[button].ManageChild()
		self._buttons[button].ShowWindow(win32con.SW_SHOW)

	def getbutton(self, button):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#return self._buttons[button].set
		return self._buttons[button]

	def setbutton(self, button, onoff = 1):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		button = self._buttons[button]
		#button.set = onoff
		cmifex2.CheckButton(button,onoff)

	def setsensitive(self, button, sensitive):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#self._buttons[button].sensitive = sensitive
		self._buttons[button].EnableWindow(sensitive)

	def _callback(self, params):
		#global _in_create_box
		#if _in_create_box == None or self._parent==_in_create_box:
			if self.is_closed():
				return

			val = win32api.HIWORD(params[2])
			if val == win32con.BN_CLICKED:
				if self._cb:
					apply(self._cb[0], self._cb[1])
				
				val = params[3]
				callback, type = self._callbks[val]
				if type == 'r':
					for bt in self._buttons:
						cb, tp = self._callbks[bt.GetSafeHwnd()]
						if tp == 'r' and bt.GetSafeHwnd() != val:
							self.setbutton(self._buttons.index(bt),0)
						elif bt.GetSafeHwnd() == val:
							self.setbutton(self._buttons.index(bt),1)

				if callback:
					apply(callback[0], callback[1])

	def _popup(self, widget, submenu, call_data):
		submenu.ManageChild()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons
		del self._cb


##################################################################
class Slider(_Widget):
	def __init__(self, parent, prompt, minimum, initial, maximum, cb,
		     vertical = 0, showvalue = 1, name = 'windowScale',
		     **options):
		#if vertical:
		#	orientation = Xmd.VERTICAL
		#else:
		#	orientation = Xmd.HORIZONTAL
		#self._orientation = orientation
		orientation = self._orientation = vertical
		range = maximum - minimum
		if range < 0:
			range = -range
			minimum, maximum = maximum, minimum
		self._factor = range/100
		direction, min, init, max, decimal, factor = \
			   self._calcrange(minimum, initial, maximum)
		attrs = {'minimum': min,
			 'maximum': max,
			 'processingDirection': direction,
			 'decimalPoints': decimal,
			 'orientation': orientation,
			 'showValue': showvalue,
			 'value': init}
		self._attachments(attrs, options)
		
		if not vertical:
			vertical = 0
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
		self._slider = None
		self._sliderlabel = None

		#scale = parent._form.CreateScale(name, attrs)
		scale = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)
		
		
		if prompt is None:
			#for w in scale.GetChildren():
			#	if w.Name() == 'Title':
			#		w.UnmanageChild()
			#		break
			self._slider = cmifex2.CreateSlider(" ",scale,0,0,width-50,height,vertical) 
			self._edit = cmifex2.CreateEdit(" ",scale,width-45,0,40,25,0)
		else:
			#scale.titleString = prompt
			self._sliderlabel = cmifex2.CreateStatic(prompt,scale,0,0,width,25,'left')
			self._slider = cmifex2.CreateSlider(prompt,scale,0,25,width-50,height-25,vertical)
			self._edit = cmifex2.CreateEdit(" ",scale,width-45,25,40,25,0) 
		
		self._cb = None

		if cb:
			#scale.AddCallback('valueChangedCallback',
			#		  self._callback, cb)
			self._cb = cb
		self._slider.HookMessage(self._callback, win32con.WM_LBUTTONUP)
		
		self.setrange(minimum, maximum)
		self.setvalue(initial)
		
		_Widget.__init__(self, parent, scale)
		

	def __repr__(self):
		return '<Slider instance at %x>' % id(self)

	def getvalue(self):
		#return self._form.ScaleGetValue() / self._factor
		return cmifex2.GetPosition(self._slider) * self._factor

	def setvalue(self, value):
		value = int(value / self._factor + .5)
		#self._form.ScaleSetValue(value)
		cmifex2.SetPosition(self._slider, value)
		if self._factor<1:
			value2 = value * self._factor
			cmifex2.SetCaption(self._edit, `value2`)
		else:
			cmifex2.SetCaption(self._edit, `value`)

	def setrange(self, minimum, maximum):
		direction, minimum, initial, maximum, decimal, factor = \
			   self._calcrange(minimum, self.getvalue(), maximum)
		#self._form.SetValues({'minimum': minimum,
		#		      'maximum': maximum,
		#		      'processingDirection': direction,
		#		      'decimalPoints': decimal,
		#		      'value': initial})
		cmifex2.SetRange(self._slider,minimum,maximum)

	def getrange(self):
		return self._minimum, self._maximum
		#return cmifex2.GetRange(self._slider)*int(self._factor)

	def _callback(self, params):
		self.setvalue(self.getvalue())
		if self.is_closed():
			return
		if self._cb:
			apply(self._cb[0], self._cb[1])
		self._slider.ReleaseCapture()

	def _calcrange(self, minimum, initial, maximum):
		self._minimum, self._maximum = minimum, maximum
		range = maximum - minimum
		direction = 1
		if range < 0:
			#f self._orientation == Xmd.VERTICAL:
			#	direction = Xmd.MAX_ON_BOTTOM
			#else:
			#	direction = Xmd.MAX_ON_LEFT
			range = -range
			minimum, maximum = maximum, minimum
		#else:
		#	if self._orientation == Xmd.VERTICAL:
		#		direction = Xmd.MAX_ON_TOP
		#	else:
		#		direction = Xmd.MAX_ON_RIGHT
		decimal = 0
		factor = 1.0
		if FloatType in [type(minimum), type(maximum)]:
			factor = 1.0
		#while 0 < range <= 10:
		#	range = range * 10
		#	decimal = decimal + 1
		#	factor = factor * 10
		factor = range/100
		self._factor = factor
		return direction, int(minimum / factor + .5), \
		       int(initial / factor + .5), \
		       int(maximum / factor + .5), decimal, factor

####################################################
