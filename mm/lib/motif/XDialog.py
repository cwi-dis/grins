__version__ = "$Id$"

import Xt, Xm, Xmd
import os
from types import StringType
from XTopLevel import toplevel
import ToolTip
from XConstants import TRUE, FALSE, _WAITING_CURSOR, _READY_CURSOR
from XHelpers import _setcursor

class showmessage:
	_cursor = ''
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message', parent = None):
		if grab:
			dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
			if parent is None:
				parent = toplevel
			while 1:
				if hasattr(parent, '_shell'):
					parent = parent._shell
					break
				if hasattr(parent, '_main'):
					parent = parent._main
					break
				if hasattr(parent, '_parent'):
					parent = parent._parent
				else:
					parent = toplevel
		else:
			dialogStyle = Xmd.DIALOG_MODELESS
			parent = toplevel._main
		if mtype == 'error':
			func = parent.CreateErrorDialog
		elif mtype == 'warning':
			func = parent.CreateWarningDialog
		elif mtype == 'information':
			func = parent.CreateInformationDialog
		elif mtype == 'question':
			func = parent.CreateQuestionDialog
		else:
			func = parent.CreateMessageDialog
		self._grab = grab
		w = func(name, {'messageString': text,
				'title': title,
				'dialogStyle': dialogStyle,
				'resizePolicy': Xmd.RESIZE_NONE,
				'visual': toplevel._default_visual,
				'depth': toplevel._default_visual.depth,
				'colormap': toplevel._default_colormap})
		w.MessageBoxGetChild(Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		if mtype == 'question' or cancelCallback:
			w.AddCallback('cancelCallback',
				      self._callback, cancelCallback)
		else:
			w.MessageBoxGetChild(Xmd.DIALOG_CANCEL_BUTTON).UnmanageChild()
		w.AddCallback('okCallback', self._callback, callback)
		w.AddCallback('destroyCallback', self._destroy, None)
		w.ManageChild()
		self._main = w
		self.setcursor(_WAITING_CURSOR)
		toplevel._subwindows.append(self)
		if grab:
			toplevel.setready()
			while self._grab:
				Xt.DispatchEvent(Xt.NextEvent())

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			w = self._main
			self._main = None
			w.UnmanageChild()
			w.DestroyWidget()
		self._grab = 0

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		if toplevel._waiting:
			cursor = 'watch'
		_setcursor(self._main, cursor)

	def is_closed(self):
		return self._main is None

	def _callback(self, widget, callback, call_data):
		ToolTip.rmtt()
		if not self._main:
			return
		if toplevel._in_create_box and toplevel._in_create_box._rb_dialog is not self:
			return
		if callback:
			apply(apply, callback)
		if self._grab:
			self.close()
		toplevel.setready()

	def _destroy(self, widget, client_data, call_data):
		self._main = None

class FileDialog:
	_cursor = ''
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel,
		     existing = 0, parent = None):
		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth,
			 'width': 400}
		if parent is None:
			parent = toplevel
		while 1:
			if hasattr(parent, '_shell'):
				parent = parent._shell
				break
			if hasattr(parent, '_main'):
				parent = parent._main
				break
			parent = parent._parent
		if prompt:
			form = parent.CreateFormDialog('fileSelect', attrs)
			self._main = form
			label = form.CreateManagedWidget('filePrompt',
					Xm.LabelGadget,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM})
			label.labelString = prompt
			dialog = form.CreateManagedWidget('fileSelect',
					Xm.FileSelectionBox,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_WIDGET,
					 'topWidget': label,
					 'width': 400})
		else:
			dialog = parent.CreateFileSelectionDialog('fileSelect',
								  attrs)
			self._main = dialog
		self._dialog = dialog
		dialog.AddCallback('okCallback', self._ok_callback, existing)
		dialog.AddCallback('cancelCallback', self._cancel_callback,
				       None)
		self._main.Parent().AddWMProtocolCallback(
			toplevel._delete_window, self._cancel_callback, None)
		helpb = dialog.FileSelectionBoxGetChild(
						    Xmd.DIALOG_HELP_BUTTON)
		helpb.UnmanageChild()
		if not directory:
			directory = '.'
		try:
			if os.stat(directory) == os.stat('/'):
				directory = '/'
		except os.error:
			pass
		if not filter:
			filter = '*'
		self.filter = filter
		filter = os.path.join(directory, filter)
		dialog.FileSelectionDoSearch(filter)
		text = dialog.FileSelectionBoxGetChild(Xmd.DIALOG_TEXT)
		text.value = file
		self._main.ManageChild()
		self.setcursor(_WAITING_CURSOR)
		toplevel._subwindows.append(self)

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			self._main.UnmanageChild()
			self._main.DestroyWidget()
			self._dialog = None
			self._main = None

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		if toplevel._waiting:
			cursor = 'watch'
		_setcursor(self._main, cursor)

	def is_closed(self):
		return self._main is None

	def _cancel_callback(self, *rest):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		must_close = TRUE
		try:
			if self.cb_cancel:
				ret = self.cb_cancel()
				if ret:
					if type(ret) is StringType:
						showmessage(ret, parent = self)
					must_close = FALSE
					return
		finally:
			if must_close:
				self.close()
			toplevel.setready()

	def _ok_callback(self, widget, existing, call_data):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		self._do_ok_callback(widget, existing, call_data)
		toplevel.setready()

	def _do_ok_callback(self, widget, existing, call_data):
		filename = call_data.value
		dir = call_data.dir
		filter = call_data.pattern
		filename = os.path.join(dir, filename)
		if os.path.isdir(filename):
			filter = os.path.join(filename, filter)
			self._dialog.FileSelectionDoSearch(filter)
			return
		dir, file = os.path.split(filename)
		if not os.path.isdir(dir):
			showmessage("path to file `%s' does not exist or is not a directory" % filename, parent = self)
			return
		if existing:
			if not os.path.exists(filename):
				showmessage("file `%s' does not exist" % filename, parent = self)
				return
		else:
			if os.path.exists(filename):
				showmessage("file `%s' exists, use anyway?" % filename, mtype = 'question', callback = (self._confirm_callback, (filename,)), parent = self)
				return
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, parent = self)
				return
		self.close()

	def _confirm_callback(self, filename):
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, parent = self)
				return
		self.close()

class SelectionDialog:
	_cursor = ''
	def __init__(self, listprompt, selectionprompt, itemlist, default,
		     parent = None):
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth,
			 'textString': default,
			 'autoUnmanage': FALSE}
		if parent is None:
			parent = toplevel
		while 1:
			if hasattr(parent, '_shell'):
				parent = parent._shell
				break
			if hasattr(parent, '_main'):
				parent = parent._main
				break
			parent = parent._parent
		if hasattr(self, 'NomatchCallback'):
			attrs['mustMatch'] = TRUE
		if listprompt:
			attrs['listLabelString'] = listprompt
		if selectionprompt:
			attrs['selectionLabelString'] = selectionprompt
		form = parent.CreateSelectionDialog('selectDialog', attrs)
		self._main = form
		form.AddCallback('okCallback', self._ok_callback, None)
		form.AddCallback('cancelCallback', self._cancel_callback, None)
		if hasattr(self, 'NomatchCallback'):
			form.AddCallback('noMatchCallback',
					 self._nomatch_callback, None)
		for b in [Xmd.DIALOG_APPLY_BUTTON, Xmd.DIALOG_HELP_BUTTON]:
			form.SelectionBoxGetChild(b).UnmanageChild()
		list = form.SelectionBoxGetChild(Xmd.DIALOG_LIST)
		list.ListAddItems(itemlist, 1)
		form.ManageChild()
		self.setcursor(_WAITING_CURSOR)
		toplevel._subwindows.append(self)

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		if toplevel._waiting:
			cursor = 'watch'
		_setcursor(self._main, cursor)

	def is_closed(self):
		return self._main is None

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			self._main.UnmanageChild()
			self._main.DestroyWidget()
			self._main = None

	def _nomatch_callback(self, widget, client_data, call_data):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		ret = self.NomatchCallback(call_data.value)
		if ret and type(ret) is StringType:
			showmessage(ret, mtype = 'error', parent = self)
		toplevel.setready()

	def _ok_callback(self, widget, client_data, call_data):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		try:
			func = self.OkCallback
		except AttributeError:
			pass
		else:
			ret = func(call_data.value)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error',
						    parent = self)
				toplevel.setready()
				return
		self.close()
		toplevel.setready()

	def _cancel_callback(self, widget, client_data, call_data):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		try:
			func = self.CancelCallback
		except AttributeError:
			pass
		else:
			ret = func()
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error',
						    parent = self)
				toplevel.setready()
				return
		self.close()
		toplevel.setready()


class InputDialog:
	_cursor = ''
	def __init__(self, prompt, default, cb, cancelCallback = None,
		     parent = None):
		import time
		attrs = {'textString': default or '',
			 'selectionLabelString': prompt or '',
			 'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth}
		if parent is None:
			parent = toplevel._main
		else:
			while 1:
				if hasattr(parent, '_shell'):
					parent = parent._shell
					break
				elif hasattr(parent, '_main'):
					parent = parent._main
					break
				parent = parent._parent
		self._main = parent.CreatePromptDialog('inputDialog', attrs)
		self._main.AddCallback('okCallback', self._ok, cb)
		self._main.AddCallback('cancelCallback', self._cancel,
				       cancelCallback)
		self._main.Parent().AddWMProtocolCallback(
			toplevel._delete_window, self._cancel, cancelCallback)
		self._main.SelectionBoxGetChild(
			Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		self._main.ManageChild()
		if default:
			self._main.SelectionBoxGetChild(
				Xmd.DIALOG_TEXT).TextFieldSetSelection(
					0, len(default), 0)
		toplevel._subwindows.append(self)
		self.setcursor(_WAITING_CURSOR)

	def _ok(self, w, client_data, call_data):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		value = call_data.value
		self.close()
		if client_data:
			client_data(value)
			toplevel.setready()

	def _cancel(self, w, client_data, call_data):
		ToolTip.rmtt()
		if toplevel._in_create_box or self.is_closed():
			return
		self.close()
		if client_data:
			apply(apply, client_data)
			toplevel.setready()

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		if toplevel._waiting:
			cursor = 'watch'
		_setcursor(self._main, cursor)

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			self._main.UnmanageChild()
			self._main.DestroyWidget()
			self._main = None

	def is_closed(self):
		return self._main is None
