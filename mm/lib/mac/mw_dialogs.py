import Qd
import Dlg
import Controls
import MacOS
import string
import sys
from types import *
import MMurl
import macfs
import os

#
# Stuff used from other mw_ modules
#
import WMEVENTS
import mw_globals
from mw_globals import FALSE, TRUE
from mw_resources import *
from mw_windows import DialogWindow
import mw_widgets

def _string2dialog(text):
	"""Prepare a Python string for use in a dialog"""
	if '\n' in text:
		text = string.split(text, '\n')
		text = string.join(text, '\r')
	if len(text) > 253:
		text = text[:253] + '\311'
	return text

#
# XXXX Maybe the previous class should be combined with this one, or does that
# give too many stuff in one object (window, dialogwindow, per-dialog info, editor
# info)?
class MACDialog:
	def __init__(self, title, resid, allitems=[], default=None, cancel=None,
				cmdbuttons=None):
		self._itemlist_shown = allitems[:]
		self._window = DialogWindow(resid, title=title, default=default, 
			cancel=cancel, cmdbuttons=cmdbuttons)
		self._dialog = self._window._wid
		# Override event handler:
		self._window.set_itemhandler(self.do_itemhit)
		
	def do_itemhit(self, item, event):
		return 0

	def _showitemlist(self, itemlist):
		"""Make sure the items in itemlist are visible and active"""
		for item in itemlist:
			if item in self._itemlist_shown:
				continue
			self._dialog.ShowDialogItem(item)
			tp, h, rect = self._dialog.GetDialogItem(item)
			if tp == 7:		# User control
				h.as_Control().ShowControl()
			self._itemlist_shown.append(item)
		
	def _hideitemlist(self, itemlist):
		"""Make items in itemlist inactive and invisible"""
		for item in itemlist:
			if item not in self._itemlist_shown:
				continue
			self._dialog.HideDialogItem(item)
			tp, h, rect = self._dialog.GetDialogItem(item)
			if tp == 7:		# User control
				h.as_Control().HideControl()
			self._itemlist_shown.remove(item)
			
	def _setsensitive(self, itemlist, sensitive):
		"""Set or reset item sensitivity to user input"""
		for item in itemlist:
			tp, h, rect = self._dialog.GetDialogItem(item)
			ctl = h.as_Control()
			if sensitive:
				ctl.HiliteControl(0)
			else:
				ctl.HiliteControl(255)
		if sensitive:
			self._showitemlist(itemlist)

	def _setctlvisible(self, itemlist, visible):
		"""Set or reset item visibility"""
		for item in itemlist:
			tp, h, rect = self._dialog.GetDialogItem(item)
			ctl = h.as_Control()
			if visible:
				ctl.ShowControl()
			else:
				ctl.HideControl()

	def _settextsensitive(self, itemlist, sensitive):
		"""Set or reset item sensitivity to user input"""
		for item in itemlist:
			tp, h, rect = self._dialog.GetDialogItem(item)
			if sensitive:
				tp = tp & ~128
			else:
				tp = tp | 128
			self._dialog.SetDialogItem(item, tp, h, rect)
		if sensitive:
			self._showitemlist(itemlist)
			
	def _setlabel(self, item, text):
		"""Set the text of a static text or edit text"""
		text = _string2dialog(text)
		tp, h, rect = self._dialog.GetDialogItem(item)
		Dlg.SetDialogItemText(h, text)

	def _getlabel(self, item):
		"""Return the text of a static text or edit text"""
		tp, h, rect = self._dialog.GetDialogItem(item)
		text = Dlg.GetDialogItemText(h)
		if '\r' in text:
			text = string.split(text, '\r')
			text = string.join(text, '\n')
		return text

	def _selectinputfield(self, item):
		"""Select all text in an input field"""
		self._dialog.SelectDialogItemText(item, 0, 32767)
		
	def _setbutton(self, item, value):
		tp, h, rect = self._dialog.GetDialogItem(item)
		ctl = h.as_Control()
		ctl.SetControlValue(value)
	
	def _getbutton(self, item):
		tp, h, rect = self._dialog.GetDialogItem(item)
		ctl = h.as_Control()
		return ctl.GetControlValue()
	
	def _togglebutton(self, item):
		tp, h, rect = self._dialog.GetDialogItem(item)
		ctl = h.as_Control()
		value = ctl.GetControlValue()
		ctl.SetControlValue(not value)

	def close(self):
		"""Close the dialog and free resources."""
		self._window.close()
		self._dialog = None

	def show(self):
		"""Show the dialog."""
		self._window.show()
		self._window.pop()
		self._window.register(WMEVENTS.WindowExit, self.goaway, ())
		
	def pop(self):
		"""Pop window to front"""
		self._window.pop()
		
	def goaway(self, *args):
		"""Callback used when user presses go-away box of window"""
		self.hide()

	def hide(self):
		"""Hide the dialog."""
		self._window.hide()
		
	def rungrabbed(self):
		self._window.rungrabbed()
			
	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self._window.settitle(title)

	def is_showing(self):
		"""Return whether dialog is showing."""
		return self._window.is_showing()

	def setcursor(self, cursor):
		"""Set the cursor to a named shape.

		Arguments (no defaults):
		cursor -- string giving the name of the desired cursor shape
		"""
		self._window.setcursor(cursor)
		
			
class _ModelessDialog(MACDialog):
	def __init__(self, title, dialogid, text, okcallback, cancelcallback=None):
		MACDialog.__init__(self, title, dialogid, [], ITEM_QUESTION_OK, ITEM_QUESTION_CANCEL)
		self.okcallback = okcallback
		self.cancelcallback = cancelcallback
		self._setlabel(ITEM_QUESTION_TEXT, text)
		self.show()
		
	def do_itemhit(self, item, event):
		if item == ITEM_QUESTION_OK:
##			self.close()
			if self.okcallback:
				func, arglist = self.okcallback
				apply(func, arglist)
		elif item == ITEM_QUESTION_CANCEL:
			self.close()
			if self.cancelcallback:
				func, arglist = self.cancelcallback
				apply(func, arglist)
		else:
			print 'Unknown modeless dialog event', item, event
		return 1
			
def _ModalDialog(title, dialogid, text, okcallback, cancelcallback=None):
	d = Dlg.GetNewDialog(dialogid, -1)
	d.SetDialogDefaultItem(ITEM_QUESTION_OK)
	if cancelcallback:
		d.SetDialogCancelItem(ITEM_QUESTION_CANCEL)
	tp, h, rect = d.GetDialogItem(ITEM_QUESTION_TEXT)
	text = _string2dialog(text)
	Dlg.SetDialogItemText(h, text)
	w = d.GetDialogWindow()
	w.ShowWindow()
	while 1:
		n = Dlg.ModalDialog(None)
		if n == ITEM_QUESTION_OK:
			del d
			del w
			if okcallback:
				func, arglist = okcallback
				apply(func, arglist)
			return
		elif n == ITEM_QUESTION_CANCEL:
			del d
			del w
			if cancelcallback:
				func, arglist = cancelcallback
				apply(func, arglist)
			return
		else:
			print 'Unknown modal dialog item', n
			
def showmessage(text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message', parent = None):
	if '\n' in text:
		text = string.join(string.split(text, '\n'), '\r')
	if mtype == 'question' or cancelCallback:
		dlgid = ID_QUESTION_DIALOG
	else:
		dlgid = ID_MESSAGE_DIALOG
	if grab:
		_ModalDialog(title, dlgid, text, callback, cancelCallback)
	else:
		return _ModelessDialog(title, dlgid, text, callback, cancelCallback)

# XXXX Do we need a control-window too?

class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel,
		     existing=0):
		# We implement this modally for the mac.
		if directory:
			macfs.SetFolder(os.path.join(directory + ':placeholder'))
		if existing:
			fss, ok = macfs.PromptGetFile(prompt)
		else:
			fss, ok = macfs.StandardPutFile(prompt, file)
		if ok:
			filename = fss.as_pathname()
			try:
				if cb_ok:
					ret = cb_ok(filename)
			except 'xxx':
				showmessage("Internal error:\nexception %s"%`sys.exc_info()`)
				ret = None
			if ret:
				if type(ret) is StringType:
					showmessage(ret)
		else:
			try:
				if cb_cancel:
					ret = cb_cancel()
				else:
					ret = None
			except:
				showmessage("Internal error:\nexception %s"%`sys.exc_info()`)
				ret = None
			if ret:
				if type(ret) is StringType:
					showmessage(ret)

	def close(self):
		pass

	def setcursor(self, cursor):
		pass

	def is_closed(self):
		return 1
		
class ProgressDialog:
	# Placeholder
	
	def __init__(self, title, cancelcallback=None):
		import EasyDialogs
		self.cancelcallback = cancelcallback
		self.progressbar = EasyDialogs.ProgressBar(title)
		self.oldlabel = ""
		self.oldvalues = (0, 0)
		
	def set(self, label, cur1=None, max1=None, cur2=None, max2=None):
		try:
			if cur1 != None:
				label = label + " (%d of %d)"%(cur1, max1)
			if label != self.oldlabel:
				self.progressbar.label(label)
				self.oldlabel = label
			if (cur2, max2) != self.oldvalues:
				if cur2 == None:
					cur2 = 0
				if max2 == None:
					max2 = 0
				self.progressbar.set(cur2, max2)
				self.oldvalues = (cur2, max2)
		except KeyboardInterrupt:
			if self.cancelcallback:
				self.cancelcallback()
		
class SelectionDialog(DialogWindow):
	def __init__(self, listprompt, selectionprompt, itemlist, default, fixed=0, hascancel=1):
		# First create dialogwindow and set static items
		if hascancel:
			DialogWindow.__init__(self, ID_SELECT_DIALOG, 
					default=ITEM_SELECT_OK, cancel=ITEM_SELECT_CANCEL)
		else:
			DialogWindow.__init__(self, ID_SELECT_DIALOG, default=ITEM_SELECT_OK)
		if fixed:
			# The user cannot modify the items, nor cancel
			self._wid.HideDialogItem(ITEM_SELECT_SELECTPROMPT)
			self._wid.HideDialogItem(ITEM_SELECT_ITEM)
		if not hascancel:
			self._wid.HideDialogItem(ITEM_SELECT_CANCEL)
		tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_LISTPROMPT)
		Dlg.SetDialogItemText(h, _string2dialog(listprompt))
		tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_SELECTPROMPT)
		Dlg.SetDialogItemText(h, _string2dialog(selectionprompt))
		
		# Now setup the scrolled list
		self._itemlist = itemlist
		self._listwidget = self.ListWidget(ITEM_SELECT_ITEMLIST, itemlist)
		if default in itemlist:
			num = itemlist.index(default)
			self._listwidget.select(num)
			
		# and the default item
		tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_ITEM)
		Dlg.SetDialogItemText(h, _string2dialog(default))
		
		# And show it
		self.show()
	
	def do_itemhit(self, item, event):
		is_ok = 0
		if item == ITEM_SELECT_CANCEL:
			self.CancelCallback()
			self.close()
		elif item == ITEM_SELECT_OK:
			is_ok = 1
		elif item == ITEM_SELECT_ITEMLIST:
			(what, message, when, where, modifiers) = event
			Qd.SetPort(self._wid)
			where = Qd.GlobalToLocal(where)
			item, isdouble = self._listwidget.click(where, modifiers)
			if item is None:
				return 1
			tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_ITEM)
			Dlg.SetDialogItemText(h, _string2dialog(self._itemlist[item]))
			is_ok = isdouble
		elif item == ITEM_SELECT_ITEM:
			pass
		else:
			print 'Unknown item', self, item, event
		# Done a bit funny, because of double-clicking
		if is_ok:
			tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_ITEM)
			rv = Dlg.GetDialogItemText(h)
			self.OkCallback(rv)
			self.close()
		return 1
		
class SingleSelectionDialog(SelectionDialog):
	def __init__(self, list, title, prompt):
		# XXXX ignore title for now
		self.__dict = {}
		hascancel = 0
		keylist = []
		for item in list:
			if item == None:
				continue
			if item == 'Cancel':
				hascancel = 1
			else:
				k, v = item
				self.__dict[k] = v
				keylist.append(k)
		SelectionDialog.__init__(self, prompt, '', keylist, keylist[0], 
				fixed=1, hascancel=hascancel)

	def OkCallback(self, key):
		if not self.__dict.has_key(key):
			print 'You made an impossible selection??'
			return
		else:
			rtn, args = self.__dict[key]
			apply(rtn, args)
			self.grabdone()
			
	def CancelCallback(self):
		self.grabdone()
			
class InputDialog(DialogWindow):
	DIALOG_ID= ID_INPUT_DIALOG
	
	def __init__(self, prompt, default, cb, cancelCallback = None,
			passwd=0):
		# XXXX passwd parameter to be implemted
		self._is_passwd_dialog = passwd
		# First create dialogwindow and set static items
		DialogWindow.__init__(self, self.DIALOG_ID, title=prompt,
				default=ITEM_INPUT_OK, cancel=ITEM_INPUT_CANCEL)
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
		Dlg.SetDialogItemText(h, _string2dialog(default))
		self._wid.SelectDialogItemText(ITEM_INPUT_TEXT, 0, 32767)
		self._cb = cb
		self._cancel = cancelCallback
		
		self.show()

	def do_itemhit(self, item, event):
		if item == ITEM_INPUT_CANCEL:
			if self._cancel:
				apply(apply, self._cancel)
			self.close()
		elif item == ITEM_INPUT_OK:
			self.done()
		elif item == ITEM_INPUT_TEXT:
			pass
		else:
			print 'Unknown item', self, item, event
		return 1
			
	def done(self):
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
		rv = Dlg.GetDialogItemText(h)
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_OK)
		ctl = h.as_Control()
		if self._is_passwd_dialog:
			# For password dialogs make it disappear quickly
			ctl.HiliteControl(10)
			ctl.HiliteControl(0)
			self.close()
			self._cb(rv)
		else:
			ctl.HiliteControl(10)
			self._cb(rv)
			ctl.HiliteControl(0)
			self.close()
		
class InputURLDialog(InputDialog):
	DIALOG_ID=ID_INPUTURL_DIALOG

	def do_itemhit(self, item, event):
		if item == ITEM_INPUTURL_BROWSE:
			# XXXX This is an error in Python:
			##fss, ok = macfs.StandardGetFile('TEXT')
			fss, ok = macfs.StandardGetFile()
			if ok:
				pathname = fss.as_pathname()
				url = MMurl.pathname2url(pathname)
				tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
				Dlg.SetDialogItemText(h, _string2dialog(url))
				self._wid.SelectDialogItemText(ITEM_INPUT_TEXT, 0, 32767)
			return 1
		return InputDialog.do_itemhit(self, item, event)

class NewChannelDialog(DialogWindow):
	DIALOG_ID= ID_NEWCHANNEL_DIALOG
	
	def __init__(self, prompt, default, types, cb, cancelCallback = None):
		# First create dialogwindow and set static items
		DialogWindow.__init__(self, self.DIALOG_ID, title=prompt,
				default=ITEM_INPUT_OK, cancel=ITEM_INPUT_CANCEL)
##		# XXXX Use title here?
##		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_PROMPT)
##		Dlg.SetDialogItemText(h, prompt)
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
		Dlg.SetDialogItemText(h, _string2dialog(default))
		self._wid.SelectDialogItemText(ITEM_INPUT_TEXT, 0, 32767)
		self.type_select=mw_widgets.SelectWidget(self._wid, ITEM_NEWCHANNEL_TYPE, types)
		self._cb = cb
		self._cancel = cancelCallback
		
	def close(self):
		self.grabdone()
		self.type_select.delete()
		del self.type_select
		DialogWindow.close(self)
		
	def do_itemhit(self, item, event):
		if item == ITEM_INPUT_CANCEL:
			if self._cancel:
				self._cancel()
			self.close()
		elif item == ITEM_INPUT_OK:
			self.done()
		elif item == ITEM_INPUT_TEXT:
			pass
		elif item == ITEM_NEWCHANNEL_TYPE:
			pass
		else:
			print 'Unknown item', self, item, event
		return 1
			
	def done(self):
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
		name = Dlg.GetDialogItemText(h)
		type = self.type_select.getselect()
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_OK)
		ctl = h.as_Control()
		ctl.HiliteControl(10)
		self._cb(name, type)
		ctl.HiliteControl(0)
		self.close()
		
class TemplateDialog(DialogWindow):
	DIALOG_ID= ID_TEMPLATE_DIALOG
	
	def __init__(self, names, descriptions, cb, cancelCallback = None):
		# names: list of template names
		# descriptions: list of (text, image, ...) parallel to names
		#
		# First create dialogwindow and set static items
		DialogWindow.__init__(self, self.DIALOG_ID, title="New Document",
				default=ITEM_TEMPLATE_OK, cancel=ITEM_TEMPLATE_CANCEL)

		self.type_select=mw_widgets.SelectWidget(self._wid, ITEM_TEMPLATE_POPUP, names)
		self.snapshot = self.ImageWidget(ITEM_TEMPLATE_IMAGE)
		self._cb = cb
		self._cancel = cancelCallback
		self.descriptions = descriptions
		
		self.type_select.select(0)
		self._setdialoginfo(0)
		self.settarget(ITEM_TEMPLATE_PLAYER)
		
		self.show()
		
	def close(self):
		self.grabdone()
		self.type_select.delete()
		del self.type_select
		DialogWindow.close(self)
		
	def do_itemhit(self, item, event):
		if item == ITEM_INPUT_CANCEL:
			if self._cancel:
				self._cancel()
			self.close()
		elif item == ITEM_INPUT_OK:
			self.done()
		elif item == ITEM_TEMPLATE_POPUP:
			self._setdialoginfo(self.type_select.getselectindex())
		elif item in (ITEM_TEMPLATE_PLAYER, ITEM_TEMPLATE_PLUGIN):
			self.settarget(item)
		else:
			print 'Unknown item', self, item, event
		return 1
	
	def settarget(self, item):
		self._setbutton(ITEM_TEMPLATE_PLAYER, (item==ITEM_TEMPLATE_PLAYER))
		self._setbutton(ITEM_TEMPLATE_PLUGIN, (item==ITEM_TEMPLATE_PLUGIN))
		
	def _setbutton(self, item, value):
		# Silly: this duplicates a method in MACDialog
		tp, h, rect = self._wid.GetDialogItem(item)
		ctl = h.as_Control()
		ctl.SetControlValue(value)
	
	def _getbutton(self, item):
		tp, h, rect = self._wid.GetDialogItem(item)
		ctl = h.as_Control()
		return ctl.GetControlValue()
		
	def done(self):
		which = self.type_select.getselectindex()
		if 0 <= which < len(self.descriptions):
			cbarg = self.descriptions[which]
			if self._getbutton(ITEM_TEMPLATE_PLAYER):
				cbarg = cbarg + ('external_player.html',)
			else:
				cbarg = cbarg + ('embedded_player.html',)
			tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_OK)
			ctl = h.as_Control()
			ctl.HiliteControl(10)
			self._cb(cbarg)
			ctl.HiliteControl(0)
		self.close()
		
	def _setdialoginfo(self, idx):
		tp, htext, rect = self._wid.GetDialogItem(ITEM_TEMPLATE_DESCRIPTION)
		if 0 <= idx < len(self.descriptions):
			text = self.descriptions[idx][0]
			image = self.descriptions[idx][1]
		else:
			text = ''
			image = None
		Dlg.SetDialogItemText(htext, text)
		self.snapshot.setfromfile(image)

[TOP, CENTER, BOTTOM] = range(3)


def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
	   parent = None):
	w = SingleSelectionDialog(list, title, prompt)
	if grab:
		w.rungrabbed()
	return w

_end_loop = '_end_loop'			# exception for ending a loop

class _Question:
	def __init__(self, text):
		self.looping = FALSE
		self.answer = None
		self.text = text

	def run(self):
		try:
			showmessage(self.text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)))
		except _end_loop:
			pass
		return self.answer

	def callback(self, answer):
		self.answer = answer
		if self.looping:
			raise _end_loop

def showquestion(text, parent = None):
	return _Question(text).run()

def multchoice(prompt, list, defindex, parent = None):
	if len(list) == 2:
		list.append('')		# An empty cancel will remove it
	elif len(list) != 3:
		raise "MultChoice must have 3 args"
	if defindex < 0:
		defindex = 3-defindex
	import EasyDialogs
	rv = EasyDialogs.AskYesNoCancel(prompt, defindex, list[0], list[1], list[2])
	if rv < 0: return 2
	if rv > 0: return 0
	return 1
