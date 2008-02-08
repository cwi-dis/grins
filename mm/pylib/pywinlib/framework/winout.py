# winout.py
#
# generic "output window"
#
# This Window will detect itself closing, and recreate next time output is
# written to it.

# This has the option of writing output at idle time (by hooking the
# idle message, and queueing output) or writing as each
# write is executed.
# Updating the window directly gives a jerky appearance as many writes
# take place between commands, and the windows scrolls, and updates etc
# Updating at idle-time may defer all output of a long process, giving the
# appearence nothing is happening.
# There is a compromise "line" mode, which will output whenever
# a complete line is available.

# behaviour depends on self.writeQueueing

# This module is thread safe - output can originate from any thread.  If any thread
# other than the main thread attempts to print, it is always queued until next idle time

import sys, string, regex
from pywinlib.mfc import docview, window
import app
import win32ui, win32api, win32con
import Queue

debug = lambda msg: None

#debug=win32ui.OutputDebugString
#import win32trace;win32trace.InitWrite() # for debugging - delete me!
#debug = win32trace.write

error = "winout error"
#import thread

class flags:
    # queueing of output.
    WQ_NONE = 0
    WQ_LINE = 1
    WQ_IDLE = 2

#WindowOutputDocumentParent=docview.RichEditDoc
WindowOutputDocumentParent=docview.Document
class WindowOutputDocument(WindowOutputDocumentParent):
    def SaveModified(self):
        return 1        # say it is OK to destroy my document

class WindowOutputFrame(window.MDIChildWnd):
    def __init__(self, wnd = None):
        window.MDIChildWnd.__init__(self, wnd)
        self.HookMessage(self.OnSizeMove, win32con.WM_SIZE)
        self.HookMessage(self.OnSizeMove, win32con.WM_MOVE)

    def LoadFrame( self, idResource, style, wndParent, context ):
        self.template = context.template
        return self._obj_.LoadFrame(idResource, style, wndParent, context)

    def PreCreateWindow(self, cc):
        cc = self._obj_.PreCreateWindow(cc)
        if self.template.defSize and self.template.defSize[0] != self.template.defSize[1]:
            rect = app.RectToCreateStructRect(self.template.defSize)
            cc = cc[0], cc[1], cc[2], cc[3], rect, cc[5], cc[6], cc[7], cc[8]
        return cc
    def AutoRestore(self):
        "If the window is minimised or maximised, restore it."
        p = self.GetWindowPlacement()
        if p[1]==win32con.SW_MINIMIZE or p[1]==win32con.SW_SHOWMINIMIZED:
            self.SetWindowPlacement(p[0], win32con.SW_RESTORE, p[2], p[3], p[4])
    def OnSizeMove(self, msg):
        # so recreate maintains position.
        # Need to map coordinates from the
        # frame windows first child.
        mdiClient = self.GetParent()
        self.template.defSize = mdiClient.ScreenToClient(self.GetWindowRect())
    def OnDestroy(self, message):
        self.template.OnFrameDestroy(self)
        return 1

WindowOutputViewParent=docview.RichEditView
class WindowOutputView(WindowOutputViewParent):
    def __init__(self,  doc):
        WindowOutputViewParent.__init__(self, doc)
        self.patErrorMessage=regex.compile('.*File "\(.*\)", line \([0-9]+\)')
        self.template = self.GetDocument().GetDocTemplate()

    def HookHandlers(self):
        # Hook for finding and locating error messages
        self.HookMessage(self.OnLDoubleClick,win32con.WM_LBUTTONDBLCLK)
        # Hook for the right-click menu.
        self.HookMessage(self.OnRClick,win32con.WM_RBUTTONDOWN)

    def OnDestroy(self, msg):
        self.template.OnViewDestroy(self)
        return WindowOutputViewParent.OnDestroy(self, msg)

    def OnInitialUpdate(self):
        if len(self.template.killBuffer):
            self.StreamIn(win32con.SF_RTF, self.StreamRTFIn)
            self.template.killBuffer = []
        self.SetSel(-2) # end of buffer
        self.HookHandlers()
    def StreamRTFIn(self, bytes):
        try:
            item = self.template.killBuffer[0]
            self.template.killBuffer.remove(item)
            if bytes < len(item):
                print "Warning - output buffer not big enough!"
            return item

        except IndexError:
            return None

    def GetRightMenuItems(self):
        ret = []
        flags=win32con.MF_STRING|win32con.MF_ENABLED
        ret.append((flags, win32ui.ID_EDIT_COPY, '&Copy'))
        ret.append((flags, win32ui.ID_EDIT_SELECT_ALL, '&Select all'))
        return ret

    #
    # Windows command handlers, virtuals, etc.
    #
    def OnRClick(self,params):
        paramsList = self.GetRightMenuItems()
        menu = win32ui.CreatePopupMenu()
        for appendParams in paramsList:
            if type(appendParams)!=type(()):
                appendParams = (appendParams,)
            apply(menu.AppendMenu, appendParams)
        menu.TrackPopupMenu(params[5]) # track at mouse position.
        return 0

    def OnLDoubleClick(self,params):
        if self.HandleSpecialLine():
            return 0        # dont pass on
        return 1        # pass it on by default.

    # as this is often used as an output window, exeptions will often
    # be printed.  Therefore, we support this functionality at this level.
    # Returns TRUE if the current line is an error message line, and will
    # jump to it.  FALSE if no error (and no action taken)
    def HandleSpecialLine(self):
        import scriptutils
        line = self.GetLine()
        matchResult = self.patErrorMessage.match(line)
        if matchResult<=0:
            # No match - try the next line
            lineNo = self.LineFromChar()
            if lineNo > 0:
                line = self.GetLine(lineNo-1)
                matchResult = self.patErrorMessage.match(line)
        if matchResult>0:
            # we have an error line.
            fileName = self.patErrorMessage.group(1)
            if fileName[0]=="<":
                win32ui.SetStatusText("Can not load this file")
                return 1        # still was an error message.
            else:
#                               if fileName[:2]=='.\\':
#                                       fileName = fileName[2:]
                lineNoString = self.patErrorMessage.group(2)
                # Attempt to locate the file (in case it is a relative spec)
                fileNameSpec = fileName
                fileName = scriptutils.LocatePythonFile(fileName)
                if fileName is None:
                    # Dont force update, so it replaces the idle prompt.
                    win32ui.SetStatusText("Cant locate the file '%s'" % (fileNameSpec), 0)
                    return 1

                win32ui.SetStatusText("Jumping to line "+lineNoString+" of file "+fileName,1)
                doc = win32ui.GetApp().OpenDocumentFile(fileName)
                if doc is None:
                    win32ui.SetStatusText("Could not open %s" % fileName)
                    return 1        # still was an error message.
                view = doc.GetFirstView()
                try:
                    view.GetParent().AutoRestore()# hopefully is an editor window
                except AttributeError:
                    pass # but may not be.
                lineNo = string.atoi(lineNoString)
                view.GetLineCount() # seems to be needed in RTF to work correctly?
                charNo = view.LineIndex(lineNo-1)
                view.SetSel(charNo)
                return 1
        if line[:11]=="com_error: ":
            # An OLE Exception - pull apart the exception
            # and try and locate a help file.
            try:
                import win32api, win32con
                det = eval(string.strip(line[string.find(line,":")+1:]))
                win32ui.SetStatusText("Opening help file on OLE error...");
                win32api.WinHelp(win32ui.GetMainFrame().GetSafeHwnd(),det[2][3],win32con.HELP_CONTEXT, det[2][4])
                return 1
            except win32api.error, details:
                try:
                    msg = details[2]
                except:
                    msg = str(details)
                win32ui.SetStatusText("The help file could not be opened - %s" % msg)
                return 1
            except:
                win32ui.SetStatusText("Line is OLE error, but no WinHelp details can be parsed");
        return 0        # not an error line
    def write(self, msg):
        return self.template.write(msg)
    def writelines(self, lines):
        for line in lines:
            self.write(line)
    def flush(self):
        return self.template.flush()

# The WindowOutput class is actually an MFC template.  This is a conventient way of
# making sure that my state can exist beyond the life of the windows themselves.
# This is primarily to support the functionality of a WindowOutput window automatically
# being recreated if necessary when written to.
class WindowOutput(docview.DocTemplate):
    """ Looks like a general Output Window - text can be written by the 'write' method.
            Will auto-create itself on first write, and also on next write after being closed """
    softspace=1
    def __init__(self, title=None, defSize=None, queueing = flags.WQ_LINE, \
                 bAutoRestore = 1, style=None,
                 makeDoc = None, makeFrame = None, makeView = None):
        """ init the output window -
        Params
        title=None -- What is the title of the window
        defSize=None -- What is the default size for the window - if this
                        is a string, the size will be loaded from the ini file.
        queueing = flags.WQ_LINE -- When should output be written
        bAutoRestore=1 -- Should a minimized window be restored.
        style -- Style for Window, or None for default.
        makeDoc, makeFrame, makeView -- Classes for frame, view and window respectively.
        """
        if makeDoc is None: makeDoc = WindowOutputDocument
        if makeFrame is None: makeFrame = WindowOutputFrame
        if makeView is None: makeView = WindowOutputView
        docview.DocTemplate.__init__(self, win32ui.IDR_PYTHONTYPE, \
            makeDoc, makeFrame, makeView)
        self.SetDocStrings("\nOutput\n\n\n\n\n\n")
        win32ui.GetApp().AddDocTemplate(self)
        self.writeQueueing = queueing
        self.errorCantRecreate = 0
        self.killBuffer=[]
        self.style = style
        self.bAutoRestore = bAutoRestore
        self.title = title
        if type(defSize)==type(''):     # is a string - maintain size pos from ini file.
            self.iniSizeSection = defSize
            self.defSize = app.LoadWindowSize(defSize)
            self.loadedSize = self.defSize
        else:
            self.iniSizeSection = None
            self.defSize=defSize
        self.currentView = None
        self.outputQueue = Queue.Queue(-1)
        self.mainThreadId = win32api.GetCurrentThreadId()
        self.idleHandlerSet = 0
        self.SetIdleHandler()

    def __del__(self):
        self.Close()

    def Create(self, title=None, style = None):
        if title: self.title = title
        if style: self.style = style
        doc=self.OpenDocumentFile()
        if doc is None: return
        self.currentView = doc.GetFirstView()
        if self.title: doc.SetTitle(self.title)

    def Close(self):
        self.RemoveIdleHandler()
        if self.currentView:
            self.currentView.GetParent().DestroyWindow()

    def SetTitle(self, title):
        self.title = title
        if self.currentView: self.currentView.GetDocument().SetTitle(self.title)

    def OnViewDestroy(self, view):
        self.currentView.StreamOut(win32con.SF_RTFNOOBJS, self.StreamRTFOut)
        self.currentView = None

    def OnFrameDestroy(self, frame):
        if self.iniSizeSection:
            # use GetWindowPlacement(), as it works even when min'd or max'd
            newSize = frame.GetWindowPlacement()[4]
            if self.loadedSize!=newSize:
                app.SaveWindowSize(self.iniSizeSection, newSize)

    def StreamRTFOut(self, data):
        self.killBuffer.append(data)
        return 1 # keep em coming!

    def SetIdleHandler(self):
        if not self.idleHandlerSet:
            debug("Idle handler set\n")
            app.AddIdleHandler(self.QueueIdleHandler)
            self.idleHandlerSet = 1

    def RemoveIdleHandler(self):
        if self.idleHandlerSet:
            debug("Idle handler reset\n")
            if (app.DeleteIdleHandler(self.QueueIdleHandler)==0):
                debug('Error deleting idle handler\n')
            self.idleHandlerSet = 0

    def RecreateWindow(self):
        if self.errorCantRecreate:
            debug("Error = not trying again")
            return 0
        try:
            # This will fail if app shutting down
            win32ui.GetMainFrame().GetSafeHwnd()
            self.Create()
            return 1
        except (win32ui.error, AttributeError):
            self.errorCantRecreate = 1
            debug("Winout can not recreate the Window!\n")
            return 0

    def _PrepareOperation(self, op = None, args = ()):
        ok = 0
        if op is None: args = (-2,)
        try:
            if self.currentView is not None:
                if op is None: op = self.currentView.SetSel
                apply(op, args)
                ok = 1
        except win32ui.error:
            ok = 0

        if not ok and self.bAutoRestore:
            if self.RecreateWindow():
                if op is None: op = self.currentView.SetSel
                apply(op, args)
                ok = 1
        return ok


    # this handles the idle message, and does the printing.
    def QueueIdleHandler(self,handler,count):
#               debug("In idle handler\n")
        if self.outputQueue.empty():
            return 0
        try:
            self.QueueFlush(10)
        except KeyboardInterrupt:
            while 1:
                try:
                    self.outputQueue.get(0)
                except Queue.Empty:
                    break
            print "Interrupted."
            return 0
        return 1 # More handling until queue empty

    def QueueFlush(self, max = sys.maxint):
        if not self._PrepareOperation():
            return # What to do with queue?
        while max > 0:
            try:
                self.currentView.ReplaceSel(self.outputQueue.get_nowait())
            except Queue.Empty:
                break
            max = max - 1

    def HandleOutput(self,message):
        debug("QueueOutput on thread %d, flags %d with '%s'..." % (win32api.GetCurrentThreadId(), self.writeQueueing, message ))
        self.outputQueue.put(message)
        if win32api.GetCurrentThreadId() != self.mainThreadId:
            debug("not my thread - ignoring queue options!\n")
        elif self.writeQueueing==flags.WQ_LINE:
            pos = string.rfind(message, '\n')
            if pos>0:
                debug("Line queueing - forcing flush\n")
                return self.QueueFlush()
        elif self.writeQueueing==flags.WQ_NONE:
            debug("WQ_NONE - flushing!\n")
            return self.QueueFlush()
        # Let our idle handler get it - wake it up
        try:
            win32ui.GetMainFrame().PostMessage(win32con.WM_USER) # Kick main thread off.
        except win32ui.error:
            # This can happen as the app is shutting down, and possibly
            # if the event queue is full - either way, we ignore!
            win32api.OutputDebugString(message)

    # delegate certain fns to my view.
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self,message):
        self.HandleOutput(message)

    def flush(self):
        self.QueueFlush()

    def HandleSpecialLine(self):
        self.currentView.HandleSpecialLine()


def thread_test(o):
    for i in range(5):
        o.write("Hi from thread %d\n" % (win32api.GetCurrentThreadId()))
        win32api.Sleep(100)

def test():
    w = WindowOutput(queueing=flags.WQ_IDLE)
    w.write("First bit of text\n")
    import thread
    for i in range(5):
        w.write("Hello from the main thread\n")
        thread.start_new(thread_test, (w,))
    for i in range(2):
        w.write("Hello from the main thread\n")
        win32api.Sleep(50)
    return w

if __name__=='__main__':
    test()

#v=winout2.test();thread.start_new(winout2.thread_test, (v,))
