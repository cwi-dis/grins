__version__ = "$Id$"

import Xt
from WMEVENTS import *

from XConstants import *

from XTopLevel import *			# toplevel and various functions

from XFont import *
from XDialog import *
from XFormWindow import Window

def beep():
	dpy = toplevel._main.Display()
	dpy.Bell(100)
	dpy.Flush()

def lopristarting():
	pass

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
	   parent = None):
	w = Window(title, grab = grab, parent = parent)
	options = {'top': None, 'left': None, 'right': None}
	if prompt:
		l = apply(w.Label, (prompt,), options)
		options['top'] = l
	options['vertical'] = vertical
	if grab:
		options['callback'] = (lambda w: w.close(), (w,))
	b = apply(w.ButtonRow, (list,), options)
	w.buttons = b
	w.show()
	return w

class _Question:
	def __init__(self, text, parent = None):
		self.looping = FALSE
		self.answer = None
		showmessage(text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)),
			    parent = parent)

	def run(self):
# Not needed anymore, now that showmessage() is truly modal.
# 		self.looping = TRUE
# 		toplevel.setready()
# 		while self.looping:
# 			Xt.DispatchEvent(Xt.NextEvent())
		return self.answer

	def callback(self, answer):
		if toplevel._in_create_box:
			return
		self.answer = answer
		self.looping = FALSE

def showquestion(text, parent = None):
	return _Question(text, parent = parent).run()

class _MultChoice:
	def __init__(self, prompt, msg_list, defindex, parent = None):
		self.looping = FALSE
		self.answer = None
		self.msg_list = msg_list
		list = []
		for msg in msg_list:
			list.append(msg, (self.callback, (msg,)))
		self.dialog = Dialog(list, title = None, prompt = prompt,
				     grab = TRUE, vertical = FALSE,
				     parent = parent)

	def run(self):
		self.looping = TRUE
		toplevel.setready()
		while self.looping:
			Xt.DispatchEvent(Xt.NextEvent())
		return self.answer

	def callback(self, msg):
		if toplevel._in_create_box:
			return
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				self.looping = FALSE
				return

def multchoice(prompt, list, defindex, parent = None):
	return _MultChoice(prompt, list, defindex, parent = parent).run()

def textwindow(text):
	w = Window('Source', resizable = 1, deleteCallback = 'hide')
	b = w.ButtonRow([('Close', (w.hide, ()))],
			top = None, left = None, right = None,
			vertical = 0)
	t = w.TextEdit(text, None, editable = 0,
		       top = b, left = None, right = None,
		       bottom = None, rows = 30, columns = 80)
	w.show()
	return w
