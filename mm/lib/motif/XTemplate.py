__version__ = "$Id$"

import Xt, Xm, Xmd, X
from XTopLevel import toplevel

WIDTH = 226
HEIGHT = 150

class TemplateDialog:
	def __init__(self, names, descriptions, cb, parent = None):
		self.__names = names
		self.__descriptions = descriptions
		self.__gc = None
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
		w = parent.CreateFormDialog(
			'template',
			{'visual': toplevel._visual,
			 'depth': toplevel._visual.depth,
			 'colormap': toplevel._colormap,
			 'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL})
		self.__window = w
		w.Parent().AddWMProtocolCallback(
			toplevel._delete_window,
			self.__callback, None)
		d = w.CreateDrawingArea('preview',
					{'width': WIDTH, 'height': HEIGHT,
					 'topAttachment': Xmd.ATTACH_FORM,
					 'bottomAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
		d.ManageChild()
		self.__draw = d
		d.AddCallback('exposeCallback', self.__expose, None)
		menu = w.CreatePulldownMenu('namesMenu',
					    {'visual': toplevel._visual,
					     'depth': toplevel._visual.depth,
					     'colormap': toplevel._colormap,
					     'orientation': Xmd.VERTICAL})
		o = w.CreateOptionMenu('namesOption',
				       {'subMenuId': menu,
					'visual': toplevel._visual,
					'depth': toplevel._visual.depth,
					'colormap': toplevel._colormap,
					'topAttachment': Xmd.ATTACH_FORM,
					'leftAttachment': Xmd.ATTACH_FORM,
					'rightAttachment': Xmd.ATTACH_WIDGET,
					'rightWidget': d})
		o.ManageChild()
		cancel = w.CreatePushButton('cancel',
					    {'labelString': 'Cancel',
					     'rightAttachment': Xmd.ATTACH_WIDGET,
					     'rightWidget': d,
					     'bottomAttachment': Xmd.ATTACH_FORM})
		cancel.AddCallback('activateCallback', self.__callback, None)
		cancel.ManageChild()
		ok = w.CreatePushButton('ok',
					{'labelString': 'OK',
					 'showAsDefault': 1,
##					 'rightAttachment': Xmd.ATTACH_WIDGET,
##					 'rightWidget': cancel,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'bottomAttachment': Xmd.ATTACH_FORM})
		ok.AddCallback('activateCallback', self.__callback, cb)
		ok.ManageChild()
		w.defaultButton = ok
					 
		buttons = []
		for i in range(len(names)):
			button = menu.CreatePushButton('templateOptionButton',
						       {'labelString': names[i]})
			button.ManageChild()
			button.AddCallback('activateCallback',
					   self.__namecallback, i)
			buttons.append(button)
		self.__index = 0
		o.menuHistory = buttons[self.__index]
# done through expose?
##		self.__namecallback(buttons[self.__index], self.__index, None)
		w.RealizeWidget()
		w.ManageChild()

	def __namecallback(self, widget, index, call_data):
		import img
		self.__index = index
		if self.__gc is None:
			self.__gc = self.__draw.CreateGC({})
		self.__gc.FillRectangle(0, 0, WIDTH, HEIGHT)
		filename = self.__descriptions[index][1]
		if filename:
			try:
				rdr = img.reader(toplevel._imgformat, filename)
			except:
				# don't try to display non-existing image...
				return
			xim = toplevel._visual.CreateImage(
				toplevel._visual.depth, X.ZPixmap, 0, rdr.read(),
				rdr.width, rdr.height, toplevel._imgformat.descr['align'], 0)
			xim.byte_order = toplevel._byteorder
			self.__gc.PutImage(xim, 0, 0, (WIDTH-rdr.width)/2, (HEIGHT-rdr.height)/2, rdr.width, rdr.height)

	def __expose(self, widget, client_data, call_data):
		self.__namecallback(widget, self.__index, call_data)

	def __callback(self, widget, callback, call_data):
		if callback:
			callback(self.__descriptions[self.__index])
		self.__window.DestroyWidget()
		toplevel.setready()
