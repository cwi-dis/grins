import mw_globals
import WMEVENTS
import usercmd
import htmlwidget

X=0.1
Y=0.1
W=0.5
H=0.7
UNITS=mw_globals.UNIT_SCREEN
TITLE="Source"

class textwindow:
	
	def __init__(self, data, html=0, url=None):
		self.data = data
		self.is_html = html
		self.url = url
		self.title = TITLE
		self.showing = 0
		self.show()
		
	def show(self):
		commandlist = [
			usercmd.CLOSE_WINDOW(callback = (self.hide, ()))
		]
##		if self.url:
##			commandlist.append(
##				usercmd.HOME(callback=(self.home_callback, ()))
##			)
		self.window = wd = mw_globals.toplevel.newwindow(X, Y, W, H, self.title, 
			units=UNITS, commandlist=commandlist)
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
		self.widget.setanchorcallback(self.cbanchor)
		self.showing = 1
		
	def hide(self):
		self.window.close()
		self.showing = 0
		
	def is_close(self):
		return not self.showing
		
	def create_widget(self):
		rect = self.window.qdrect()
		wid = self.window._wid
		self.widget = htmlwidget.HTMLWidget(wid, rect, self.title, self.window)
		
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
		
	def cbanchor(self, href):
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		windowinterface.showmessage("Cannot jump to CMIF from help")

		
