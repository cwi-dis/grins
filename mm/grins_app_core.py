# grins_app_core.py  - The Pythonwin Application class for the GRINS Player and Editor.
#
import sys, os
import win32ui, win32con, win32api
from pywinlib.mfc import window, dialog, thread, afxres

import traceback
import longpath

def fix_argv():
    # Turn pathnames into their full NT version
    for i in range(1, len(sys.argv)):
        if os.path.exists(sys.argv[i]):
            sys.argv[i] = longpath.short2longpath(sys.argv[i])

def SafeCallbackCaller(fn, args):
    try:
        return apply(fn, args)
    except SystemExit, rc:
        # We trap a system exit, and translate it to the "official" way to bring down a GUI.
        try:
            rc = int(rc[0])
        except (ValueError, TypeError):
            rc = 0
        win32api.PostQuitMessage(rc)
    except:
        # We trap all other errors, ensure the main window is shown, then
        # print the traceback.
        try:
            import __main__
            if not hasattr(__main__,'embedded') or not __main__.embedded:
                win32ui.GetMainFrame().ShowWindow(win32con.SW_SHOW)
        except win32ui.error:
            print "Cant show the main frame!"
        traceback.print_exc()
        return


win32ui.InstallCallbackCaller(SafeCallbackCaller)


# GRiNS Debugging Terminal frame
class MainFrame(window.MDIFrameWnd):
    statusBarIndicators = ( afxres.ID_SEPARATOR, #// status line indicator
                            afxres.ID_INDICATOR_CAPS,
                            afxres.ID_INDICATOR_NUM,
                            afxres.ID_INDICATOR_SCRL,
                            win32ui.ID_INDICATOR_LINENUM,
                            win32ui.ID_INDICATOR_COLNUM )
    def OnCreate(self, cs):
        self._CreateStatusBar()
        return 0

    def _CreateStatusBar(self):
        self.statusBar = win32ui.CreateStatusBar(self)
        self.statusBar.SetIndicators(self.statusBarIndicators)
        self.HookCommandUpdate(self.OnUpdatePosIndicator, win32ui.ID_INDICATOR_LINENUM)
        self.HookCommandUpdate(self.OnUpdatePosIndicator, win32ui.ID_INDICATOR_COLNUM)

    def OnUpdatePosIndicator(self, cmdui):
        try:
            childFrame, bIsMaximised = self.MDIGetActive()
            childWnd = childFrame.GetWindow(win32con.GW_CHILD)
            try:
                editControl = childWnd.GetRichEditCtrl()
            except AttributeError:
                try:
                    editControl = childWnd.GetEditCtrl()
                except AttributeError:
                    if hasattr(childWnd, "hWndScintilla"):
                        editControl = childWnd
                    else:
                        editControl = None
            if editControl:
                startChar, endChar = editControl.GetSel()
                lineNo = editControl.LineFromChar(startChar)
                colNo = endChar - editControl.LineIndex(lineNo)

                if cmdui.m_nID==win32ui.ID_INDICATOR_LINENUM:
                    value = "%0*d" % (5, lineNo + 1)
                else:
                    value = "%0*d" % (3, colNo + 1)
            else:
                value = " " * 5
        except win32ui.error:
            value = " " * 5

        cmdui.SetText(value)
        cmdui.Enable()


# The application object.
class GrinsApp(thread.WinApp):
    def __init__(self):
        self.oldCallbackCaller = None
        thread.WinApp.__init__(self, win32ui.GetApp() )
        self.idleHandlers = []

    def CreateMainFrame(self):
        return MainFrame()

    def LoadMainFrame(self):
        " Create the main applications frame "
        self.frame = self.CreateMainFrame()
        self.SetMainFrame(self.frame)
        self.frame.LoadFrame(win32ui.IDR_MAINFRAME, win32con.WS_OVERLAPPEDWINDOW)
        #self.frame.DragAcceptFiles()   # we can accept these.

        if 0:
            self.frame.ShowWindow(win32ui.GetInitialStateRequest());
            self.frame.UpdateWindow();

        self.frame.SetWindowText("Ambulant Debugging Terminal")
        self.HookCommands()


    def InitInstance(self):
        afx = win32ui.GetAfx()
        afx.OleInit()
        afx.EnableControlContainer()
        self.LoadMainFrame()
        from pywinlib.framework import interact
        interact.CreateInteractiveWindow()
        interact.edit.currentView.GetParent().ShowWindow(win32con.SW_MAXIMIZE)

    def Run(self):
        self.BootGrins()
        return self.ExitInstance()

    def ExitInstance(self):
        if self.frame and hasattr(self.frame,'DestroyWindow'):
            self.frame.DestroyWindow()
        self.frame = None
        if hasattr(self,'SetMainFrame'):
            self.SetMainFrame(None)
        import __main__
        if hasattr(__main__,'resdll'):
            del __main__.resdll

        win32ui.OutputDebug("Application shutdown\n")
        # Restore the callback manager, if any.
        try:
            win32ui.InstallCallbackCaller(self.oldCallbackCaller)
        except AttributeError:
            pass
        if self.oldCallbackCaller:
            del self.oldCallbackCaller
        self.idleHandlers = []
        # Attempt cleanup if not already done!
        if self._obj_: self._obj_.AttachObject(None)
        self._obj_ = None
        return 0

    def BootGrins(self):
        raise RuntimeError, "You must subclass this object"

    #
    #  Idle processing
    #
    def HaveIdleHandler(self, handler):
        return handler in self.idleHandlers
    def AddIdleHandler(self, handler):
        self.idleHandlers.append(handler)
    def DeleteIdleHandler(self, handler):
        self.idleHandlers.remove(handler)
    def OnIdle(self, count):
        try:
            ret = 0
            handlers = self.idleHandlers[:] # copy list, as may be modified during loop
            for handler in handlers:
                try:
                    thisRet = handler(handler, count)
                except:
                    print "Idle handler %s failed" % (`handler`)
                    traceback.print_exc()
                    print "Idle handler removed from list"
                    self.DeleteIdleHandler(handler)
                    thisRet = 0
                ret = ret or thisRet
            return ret
        except KeyboardInterrupt:
            pass

    #
    #  Commands
    #
    def HookCommands(self):
        # Hook for the right-click menu.
        self.frame.GetWindow(win32con.GW_CHILD).HookMessage(self.OnRClick,win32con.WM_RBUTTONDOWN)

    def OnRClick(self,params):
        " Handle right click message "
        # put up the entire FILE menu!
        menu = win32ui.LoadMenu(win32ui.IDR_TEXTTYPE).GetSubMenu(0)
        menu.TrackPopupMenu(params[5]) # track at mouse position.
        return 0


def BootApplication(appClass):

    # Create the application itself.
    gapp = appClass()

    # If we are not hosted by Pythonwin.exe, we need to simulate an MFC startup.
    if win32ui.GetApp().IsInproc():
        #print "Not hosted by pythonwin - simulating MFC startup..."
        #win32ui.MessageBox('Not hosted by pythonwin - simulating MFC startup...')
        rc = gapp.InitInstance()
        #print "InitInstance returned", rc
        if not rc: # None or 0 mean "this is OK"
            gapp.Run()
