# Qt module test

# QuickTime module
import Qt

# QuickTime constants
# placeholder -> replace with Mac equivalent
import QuickTime

# std windows/MFC stuff
import win32ui, win32api, win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

from pywin.mfc import window

class MfcOsWnd(window.Wnd):
	"""Generic MfcOsWnd class"""
	def __init__ (self):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._clstyle=0
		self._style=0
		self._exstyle=0
		self._icon=0
		self._cursor=0
		self._brush=0

	def setClstyle(self,clstyle):
		self._clstyle=clstyle

	def setStyle(self,style):
		self._style=style

	def setExstyle(self,exstyle):
		self._exstyle=exstyle

	def setIcon(self,icon):
		self._icon=icon

	def setIconApplication(self):
		self._icon=Afx.GetApp().LoadIcon(win32con.IDI_APPLICATION)

	def setStandardCursor(self,cursor):
		self._cursor = Afx.GetApp().LoadStandardCursor(cursor)

	def setStockBrush(self,idbrush):
		self._brush=Sdk.GetStockObject(idbrush)
	def setBrush(self,brush):
		self._brush=brush

	def create(self,title='untitled',x=0,y=0,width=200,height=150,parent=None,id=0):
		# register
		strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		# create
		self.CreateWindowEx(self._exstyle,strclass,title,self._style,
			(x, y, width, height),parent,id)

class ToplevelWnd(MfcOsWnd):
	"""Generic ToplevelWnd class"""
	def __init__ (self):
		MfcOsWnd.__init__(self)
		self._clstyle=win32con.CS_DBLCLKS
		self._style=win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
		self._exstyle=win32con.WS_EX_CLIENTEDGE

	def setClientRect(self, w, h):
		l1, t1, r1, b1 = self.GetWindowRect()
		l2, t2, r2, b2 = self.GetClientRect()
		dxe = dye = 0
		if (self._exstyle & win32con.WS_EX_CLIENTEDGE):
			dxe = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
			dye = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		wi = (r1-l1) - (r2-l2)
		wp = w + wi + dxe
		hi = (b1-t1) - (b2-t2)
		hp = h + hi + dye
		flags=win32con.SWP_NOMOVE | win32con.SWP_NOZORDER 		
		self.SetWindowPos(0, (0,0,wp,hp), flags)


class QTWnd(MfcOsWnd):
	def __init__ (self):
		MfcOsWnd.__init__(self)
		self._clstyle=win32con.CS_DBLCLKS | win32con.CS_HREDRAW | win32con.CS_VREDRAW
		self._style = win32con.WS_CHILD |win32con.WS_CLIPSIBLINGS
		self.port = 0
		self.movie = None
		self.ctrl = None

	def OnCreate(self, params):
		Qt.InitializeQTML()
		Qt.EnterMovies()
		#self.port = Qt.CreatePortAssociation(self.GetSafeHwnd())
		#Qt.SetGWorld(self.GetSafeHwnd())

		fn = 'D:\\ufs\\mm\\cmif\\win32\\Qt\\media\\fashion.mov'
		try:
			movieResRef = Qt.OpenMovieFileWin(fn, 1)
		except Exception, arg:
			print arg
			return

		try:
			self.movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0, 0)
		except Exception, arg:
			print arg
		Qt.CloseMovieFile(movieResRef)

		print 'dur =', 0.001*self.movie.GetMovieDuration(), 'sec'
		print 'box =',  self.movie.GetMovieBox()

		l, t, r, b = self.movie.GetMovieBox()
		self.ctrl = self.movie.NewMovieController((40,40, r+40, b+40), QuickTime.mcTopLeftMovie | QuickTime.mcWithFrame) 

		#self.movie.SetMovieGWorld((self.port,), None)
		self.movie.SetMovieBox((40,40, r+40, b+40))
		self.movie.SetMovieActive(1)
		self.movie.StartMovie()

		self.HookMessage(self.OnTimer,win32con.WM_TIMER)
		self.__timer_id = self.SetTimer(1,20)
	
	def PreTranslateMessage(self, params):
		if params[1] == win32con.WM_DESTROY:
			self.ctrl = None
		elif self.ctrl:
			self.ctrl.MCIsPlayerEventWin(params)
		return 1
	
	def OnTimer(self, params):
		if self.ctrl and self.port:
			self.ctrl.MCDrawWin(self.port)
	
	def OnDestroy(self):
		if self.__timer_id:
			self.KillTimer(self.__timer_id)
		self.releaseQt()
				
	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		if self.ctrl:
			self.ctrl.MCDrawWin(self.port)
		self.EndPaint(paintStruct)
			
	def releaseQt(self):
		self.movie = None
		self.ctrl = None
		if self.port:
			Qt.DestroyPortAssociation(self.port)
		self.port = 0
		Qt.ExitMovies()
		Qt.TerminateQTML()
			
def __test():
	wnd = ToplevelWnd()
	wnd.setStockBrush(win32con.WHITE_BRUSH)
	wnd.setStandardCursor(win32con.IDC_ARROW)
	wnd.create('GRiNS Lab',win32con.CW_USEDEFAULT,win32con.CW_USEDEFAULT,400,300)

	w = 400
	h = 300
	wnd.setClientRect(w, h)

	childwnd = QTWnd()
	childwnd.setStockBrush(win32con.WHITE_BRUSH)
	childwnd.setStandardCursor(win32con.IDC_ARROW)
	childwnd.create('qtchannel',0,0,w,h, wnd)

	wnd.ShowWindow(win32con.SW_SHOW)
	childwnd.ShowWindow(win32con.SW_SHOW)
	wnd.UpdateWindow()

if __name__ == '__main__':
	__test()


