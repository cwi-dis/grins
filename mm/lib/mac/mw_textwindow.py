import mw_globals
import WMEVENTS
import usercmd
import htmlwidget
import MMurl
import sys

X=0.1
Y=0.1
W=0.5
H=0.7
UNITS=mw_globals.UNIT_SCREEN
TITLE="Source"

class _common_window:
	# The subclasses provide X,Y,W,H,TITLE and __init__
	def __init__(self):
		self.window = None
		
	def _do_show(self):
		self.window = wd = mw_globals.toplevel.newwindow(
			self.X, self.Y, self.W, self.H, self.TITLE, 
			units=UNITS, commandlist=self.commandlist)
		self.create_widget()
		if self.is_html:
			self.widget.insert_html(self.data, self.url)
		else:
			self.widget.insert_plaintext(self.data)
		wd.setredrawfunc(self.redraw)
		wd.setclickfunc(self.click)
		wd.register(WMEVENTS.WindowActivate, self.activate, 0)
		wd.register(WMEVENTS.WindowDeactivate, self.deactivate, 0)
		wd.register(WMEVENTS.ResizeWindow, self.resize, 0)
		self.widget.setanchorcallback(self.goto_url)
		
	def show(self):
		if self.window:
			self.window.pop()
		else:
			self._do_show()
		
	def hide(self):
		self.window.close()
		self.widget.close()
		self.widget = None
		self.window = None
		
	def close(self):
		self.hide()
		
	def is_closed(self):
		return not self.window
		
	def create_widget(self):
		rect = self.window.qdrect()
		wid = self.window._wid
		self.widget = htmlwidget.HTMLWidget(wid, rect, self.TITLE, self.window)
		
	def redraw(self):
		if self.widget:
			self.widget.do_update()
		
	def click(self, down, where, event):
		if self.widget:
			self.widget.do_click(down, where, event)
	
	def activate(self, *args):
		if self.widget:
			self.widget.do_activate()
			
	def deactivate(self, *args):
		if self.widget:
			self.widget.do_deactivate()
			
	def resize(self, arg, window, event, value):
		wd = self.window
		self.widget.do_moveresize(wd.qdrect())
		
	def goto_url(self, href):
		print "Anchor callback from non-html window?"

class textwindow(_common_window):
	X=0
	Y=0
	W=0.5
	H=0.7
	UNITS=mw_globals.UNIT_SCREEN
	TITLE="Source"

	def __init__(self, data):
		_common_window.__init__(self)
		self.data = data
		self.is_html = 0
		self.url = None
		self.commandlist = [
			usercmd.CLOSE_WINDOW(callback = (self.hide, ()))
		]
		self.adornments = None
		self.show()

	def settext(self, data):
		self.data = data
		self.widget.insert_plaintext(data)
	
class htmlwindow(_common_window):
	X=0
	Y=0
	W=0.5
	H=0.7
	UNITS=mw_globals.UNIT_SCREEN
	TITLE="GRiNS Help"
	
	def __init__(self, url):
		_common_window.__init__(self)
		self.url = None
		self.load(url)
		self.is_html = 1
		self.commandlist = [
			usercmd.CLOSE_WINDOW(callback = (self.hide, ())),
##			usercmd.HOME(callback=(self.home_callback, ()))
		]
		self.adornments = None
		self.show()

	def goto_url(self, href):
		self.load(href)
		self.widget.insert_html(self.data, self.url)

	def load(self, href):
		if href:
			if self.url:
				href = MMurl.basejoin(self.url, href)
		else:
			href = self.url
		self.url, tag = MMurl.splittag(href)
		try:
			u = MMurl.urlopen(self.url)
			if u.headers.maintype == 'image':
				newtext = '<IMG SRC="%s">\n' % self.url
			else:
				newtext = u.read()
		except IOError:
			newtext = '<H1>Cannot Open</H1><P>'+ \
				  'Cannot open '+self.url+':<P>'+ \
				  `(sys.exc_type, sys.exc_value)`+ \
				  '<P>\n'
		self.data = newtext
