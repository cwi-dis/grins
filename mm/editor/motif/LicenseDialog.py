__version__ = "$Id$"

# License dialog
import windowinterface
import Xm, Xmd, X

class LicenseDialog:
	def __init__(self):
		import splash, splashimg, imgconvert
		fg = windowinterface.toplevel._convert_color((0,0,0), 0)
		bg = windowinterface.toplevel._convert_color((0x99,0x99,0x99), 0)
		w = windowinterface.toplevel._main.CreateTemplateDialog('license', {'autoUnmanage': 0, 'foreground': fg, 'background': bg})
		tryb = w.CreatePushButton('try', {'labelString': 'Try', 'foreground': fg, 'background': bg})
		tryb.ManageChild()
		tryb.AddCallback('activateCallback', self.__callback, (self.cb_try, ()))
		self.__try = tryb
		eval = w.CreatePushButton('eval', {'labelString': 'Evaluate...', 'foreground': fg, 'background': bg})
		eval.ManageChild()
		eval.AddCallback('activateCallback', self.__callback, (self.cb_eval, ()))
		self.__eval = eval
		buy = w.CreatePushButton('buy', {'labelString': 'Buy now...', 'foreground': fg, 'background': bg})
		buy.ManageChild()
		buy.AddCallback('activateCallback', self.__callback, (self.cb_buy, ()))
		key = w.CreatePushButton('key', {'labelString': 'Enter key...', 'foreground': fg, 'background': bg})
		key.ManageChild()
		key.AddCallback('activateCallback', self.__callback, (self.cb_enterkey, ()))
		self.__key = key
		quit = w.CreatePushButton('quit', {'labelString': 'Quit', 'foreground': fg, 'background': bg})
		quit.ManageChild()
		quit.AddCallback('activateCallback', self.__callback, (self.cb_quit, ()))
		visual = windowinterface.toplevel._visual
		fmt = windowinterface.toplevel._imgformat
		rdr = imgconvert.stackreader(fmt, splashimg.reader())
		self.__imgsize = rdr.width, rdr.height
		data = rdr.read()
		depth = fmt.descr['align'] / 8
		xim = visual.CreateImage(visual.depth, X.ZPixmap, 0, data,
					 rdr.width, rdr.height, depth * 8,
					 rdr.width * depth)
		img = w.CreateDrawingArea('splash', {'width': rdr.width,
						     'height': rdr.height, 'foreground': fg, 'background': bg})
		self.__gc = None
		img.AddCallback('exposeCallback', self.__expose,
				(xim, rdr.width, rdr.height))
		img.ManageChild()
		self.__img = img
		self.__msg = None
		self.__window = w

	def __expose(self, widget, (xim, width, height), call_data):
		if self.__gc is None:
			self.__gc = widget.CreateGC({})
		self.__gc.PutImage(xim, 0, 0, 0, 0, width, height)

	def show(self):
		self.__window.ManageChild()
		
	def close(self):
		self.__window.DestroyWidget()
		self.__window = None
		del self.__window
		del self.__try
		del self.__key
		del self.__eval
		del self.__img
		del self.__msg
			
	def setdialoginfo(self):
		if self.can_try:
			self.__try.ManageChild()
			self.__window.defaultButton = self.__try
		else:
			self.__try.UnmanageChild()
			self.__window.defaultButton = self.__key
		if self.can_eval:
			self.__eval.ManageChild()
		else:
			self.__eval.UnmanageChild()
##		self.__try.SetSensitive(self.can_try)
##		self.__eval.SetSensitive(self.can_eval)
		width, height = self.__imgsize
		if self.__msg is not None:
			self.__msg.DestroyWidget
		attrs = {'labelString': self.msg,
			 'alignment': Xmd.ALIGNMENT_CENTER,
			 'x': 10,
			 'y': height - 26,
			 'width': width - 20,
			 'background': windowinterface.toplevel._convert_color((255,255,255), 0),
			 'foreground': windowinterface.toplevel._convert_color((0x06,0x14,0x40), 0)}
		try:
			import splash
			self.__img.LoadQueryFont(splash.splashfont)
		except:
			pass
		else:
			attrs['fontList'] = splash.splashfont
		self.__msg = self.__img.CreateManagedWidget('message',
							    Xm.Label, attrs)

	def __callback(self, w, callback, call_data):
		apply(apply, callback)
