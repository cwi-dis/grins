"""
Various utilities for running/importing a script
"""
import app
import sys
import win32ui
import win32api
import win32con
import __main__
from pywin.mfc import dialog
import os
import string
import traceback
import linecache

from cmdline import ParseArgs

lastScript = ''
lastArgs = ''
lastbUnderDebugger = 0
lastbPostMortemDebugger = 1

# A dialog box for the "Run Script" command.
class DlgRunScript(dialog.Dialog):
    "A class for the 'run script' dialog"
    def __init__(self):
        dialog.Dialog.__init__(self, win32ui.IDD_RUN_SCRIPT )
        self.AddDDX(win32ui.IDC_EDIT1, "script")
        self.AddDDX(win32ui.IDC_EDIT2, "args")
        self.AddDDX(win32ui.IDC_CHECK1, "bUnderDebugger")
        self.AddDDX(win32ui.IDC_CHECK2, "bPostMortemDebugger")
        self.HookCommand(self.OnBrowse, win32ui.IDC_BUTTON2)

    def OnBrowse(self, id, cmd):
        openFlags = win32con.OFN_OVERWRITEPROMPT|win32con.OFN_FILEMUSTEXIST
        dlg = win32ui.CreateFileDialog(1,None,None,openFlags, "Python Scripts (*.py)|*.py||", self)
        dlg.SetOFNTitle("Run Script")
        if dlg.DoModal()!=win32con.IDOK:
            return 0
        self['script'] = dlg.GetPathName()
        self.UpdateData(0)
        return 0

def GetDebugger():
    """Get the default Python debugger.  Returns the debugger, or None.

    It is assumed the debugger has a standard "pdb" defined interface.
    Currently always returns the 'pywin.debugger' debugger, or None
    (pdb is _not_ returned as it is not effective in this GUI environment)
    """
    try:
        import pywin.debugger
        return pywin.debugger
    except ImportError:
        return None

def IsOnPythonPath(path):
    "Given a path only, see if it is on the Pythonpath.  Assumes path is a full path spec."
    # must check that the command line arg's path is in sys.path
    for syspath in sys.path:
        try:
            # Python 1.5 and later allows an empty sys.path entry.
            if syspath and win32ui.FullPath(syspath)==path:
                return 1
        except win32ui.error, details:
            print "Warning: The sys.path entry '%s' is invalid\n%s" % (syspath, details)
    return 0

def GetPackageModuleName(fileName):
    """Given a filename, return (module name, new path).
       eg - given "c:\a\b\c\my.py", return ("b.c.my",None) if "c:\a" is on sys.path.
       If no package found, will return ("my", "c:\a\b\c")
    """
    path, fname = os.path.split(fileName)
    path=origPath=win32ui.FullPath(path)
    fname = os.path.splitext(fname)[0]
    modBits = []
    newPathReturn = None
    if not IsOnPythonPath(path):
        # Module not directly on the search path - see if under a package.
        while len(path)>3: # ie 'C:\'
            path, modBit = os.path.split(path)
            modBits.append(modBit)
            # If on path, _and_ existing package of that name loaded.
            if IsOnPythonPath(path) and sys.modules.has_key(modBit) and \
               ( os.path.exists(os.path.join(path, '__init__.py')) or \
                 os.path.exists(os.path.join(path, '__init__.pyc')) or \
                 os.path.exists(os.path.join(path, '__init__.pyo')) \
               ):
                modBits.reverse()
                return string.join(modBits, ".") + "." + fname, newPathReturn
            # Not found - look a level higher
        else:
            newPathReturn = origPath

    return fname, newPathReturn

def GetActiveFileName(bAutoSave = 1):
    """Gets the file name for the active frame, saving it if necessary.

    Returns None if it cant be found, or raises KeyboardInterrupt.
    """
    pathName = None
    try:
        active = win32ui.GetMainFrame().GetWindow(win32con.GW_CHILD).GetWindow(win32con.GW_CHILD)
        doc = active.GetActiveDocument()
        pathName = doc.GetPathName()

        if bAutoSave and \
           (len(pathName)>0 or \
            doc.GetTitle()[:8]=="Untitled" or \
            doc.GetTitle()[:6]=="Script"): # if not a special purpose window
            if doc.IsModified():
                try:
                    doc.OnSaveDocument(pathName)
                    pathName = doc.GetPathName()

                    # clear the linecache buffer
                    linecache.clearcache()

                except win32ui.error:
                    raise KeyboardInterrupt

    except (win32ui.error, AttributeError):
        pass
    if not pathName:
        return None
    return pathName

def RunScript(defName=None, defArgs=None, bShowDialog = 1, bUnderDebugger=None, bPostMortemDebugger = None):
    global lastScript, lastArgs, lastbUnderDebugger, lastbPostMortemDebugger

    # Get the debugger - may be None!
    debugger = GetDebugger()

    if defName is None:
        try:
            pathName = GetActiveFileName()
        except KeyboardInterrupt:
            return
    else:
        pathName = defName
    if defArgs is None:
        args = ''
        if pathName is None or len(pathName)==0:
            pathName = lastScript
        if pathName==lastScript:
            args = lastArgs
    else:
        args = defArgs
    if bUnderDebugger is None: bUnderDebugger = debugger is not None and lastbUnderDebugger
    if bPostMortemDebugger is None: bPostMortemDebugger = debugger is not None and lastbPostMortemDebugger

    if not pathName or bShowDialog:
        dlg = DlgRunScript()
        dlg['script'] = pathName
        dlg['args'] = args
        dlg['bUnderDebugger'] = bUnderDebugger
        dlg['bPostMortemDebugger'] = bPostMortemDebugger
        if dlg.DoModal() != win32con.IDOK:
            return
        script=dlg['script']
        args=dlg['args']
        bUnderDebugger = dlg['bUnderDebugger']
        bPostMortemDebugger = dlg['bPostMortemDebugger']
        if not script: return # User cancelled.
    else:
        script = pathName
    lastScript = script
    lastArgs = args
    lastbUnderDebugger = bUnderDebugger
    lastbPostMortemDebugger = bPostMortemDebugger
    # try and open the script.
    if len(os.path.splitext(script)[1])==0: # check if no extension supplied, and give one.
        script = script + '.py'
    # If no path specified, try and locate the file
    path, fnameonly = os.path.split(script)
    if len(path)==0:
        try:
            os.stat(fnameonly) # See if it is OK as is...
            script = fnameonly
        except os.error:
            fullScript = app.LocatePythonFile(script)
            if fullScript is None:
                win32ui.MessageBox("The file '%s' can not be located" % script )
                return
            script = fullScript
    else:
        path = win32ui.FullPath(path)
        if not IsOnPythonPath(path): sys.path.append(path)

    try:
        f = open(script)
    except IOError, (code, msg):
        win32ui.MessageBox("The file could not be opened - %s (%d)" % (msg, code))
        return

    oldArgv = sys.argv
    sys.argv = ParseArgs(args)
    sys.argv.insert(0, script)
    bWorked = 0
    win32ui.DoWaitCursor(1)
    base = os.path.split(script)[1]
    win32ui.PumpWaitingMessages()
    win32ui.SetStatusText('Running script %s...' % base,1 )
    exitCode = 0
    # We set the interactive window to write output as it occurs
    oldFlag = None
    try:
        oldFlag = sys.stdout.template.writeQueueing
        # sys.stdout may change on us!  So we remember the object
        # that we actually modified so we can reset it correctly.
        oldFlagObject = sys.stdout.template
        oldFlagObject.writeQueueing = 0
    except (NameError, AttributeError):
        # sys.stdout is not an interactive window - we dont care.
        pass
    # Check the debugger flags
    if debugger is None and (bUnderDebugger or bPostMortemDebugger):
        win32ui.MessageBox("No debugger is installed.  Debugging options have been ignored!")
        bUnderDebugger = bPostMortemDebugger = 0

    # Get a code object - ignore the debugger for this, as it is probably a syntax error
    # at this point
    try:
        codeObject = compile(f.read()+"\n", script, "exec")
    except:
        _HandlePythonFailure("run script", script)
        # Almost certainly a syntax error!
        traceback.print_exc()
        # No code object which to debug = get out now!
        return
    try:
        if bUnderDebugger:
            debugger.run(codeObject, __main__.__dict__)
        else:
            exec codeObject in __main__.__dict__
        bWorked = 1
    except SystemExit, code:
        exitCode = code
        bWorked = 1
    except KeyboardInterrupt:
        print "Interrupted!"
        # Consider this successful, as we dont want the debugger!?!?
        bWorked = 1
    except SyntaxError:
        # We dont want to break into the debugger for a syntax error!
        traceback.print_exc()
    except:
        # Reset queueing before exception for nice clean printing.
        if not oldFlag is None:
            oldFlagObject.writeQueueing = oldFlag
            oldFlag = oldFlagObject = None
        if bPostMortemDebugger:
            debugger.pm()
        traceback.print_exc()
    sys.argv = oldArgv
    f.close()
    if not oldFlag is None:
        oldFlagObject.writeQueueing = oldFlag
        oldFlag = oldFlagObject = None
    if bWorked:
        win32ui.SetStatusText("Script '%s' returned exit code %s" %(script, exitCode))
    else:
        win32ui.SetStatusText('Exception raised while running script  %s' % base)
    try:
        sys.stdout.flush()
    except:
        pass

    win32ui.DoWaitCursor(0)

def ImportFile():
    """ This code looks for the current window, and determines if it can be imported.  If not,
    it will prompt for a file name, and allow it to be imported. """
    try:
        pathName = GetActiveFileName()
    except KeyboardInterrupt:
        pathName = None

    if pathName is not None:
        if string.lower(os.path.splitext(pathName)[1]) <> ".py":
            pathName = None

    if pathName is None:
        openFlags = win32con.OFN_OVERWRITEPROMPT|win32con.OFN_FILEMUSTEXIST
        dlg = win32ui.CreateFileDialog(1,None,None,openFlags, "Python Scripts (*.py)|*.py||")
        dlg.SetOFNTitle("Import Script")
        if dlg.DoModal()!=win32con.IDOK:
            return 0

        pathName = dlg.GetPathName()

    # If already imported, dont look for package
    path, modName = os.path.split(pathName)
    modName, modExt = os.path.splitext(modName)
    newPath = None
    for key, mod in sys.modules.items():
        if hasattr(mod, '__file__'):
            fname = mod.__file__
            base, ext = os.path.splitext(fname)
            if string.lower(ext) in ['.pyo', '.pyc']:
                ext = '.py'
            fname = base + ext
            if win32ui.ComparePath(fname, pathName):
                modName = key
                break
    else: # for not broken
        modName, newPath = GetPackageModuleName(pathName)
        if newPath: sys.path.append(newPath)

    if sys.modules.has_key(modName):
        bNeedReload = 1
        what = "reload"
    else:
        what = "import"
        bNeedReload = 0

    win32ui.SetStatusText(string.capitalize(what)+'ing module...',1)
    win32ui.DoWaitCursor(1)
#       win32ui.GetMainFrame().BeginWaitCursor()
    try:
        # always do an import, as it is cheap is already loaded.  This ensures
        # it is in our name space.
        codeObj = compile('import '+modName,'<auto import>','exec')
        exec codeObj in __main__.__dict__
        if bNeedReload:
            reload(sys.modules[modName])
#                       codeObj = compile('reload('+modName+')','<auto import>','eval')
#                       exec codeObj in __main__.__dict__
        win32ui.SetStatusText('Successfully ' + what + "ed module '"+modName+"'")
    except:
        _HandlePythonFailure(what)
    win32ui.DoWaitCursor(0)

def CheckFile():
    """ This code looks for the current window, and gets Python to check it
    without actually executing any code (ie, by compiling only)
    """
    try:
        pathName = GetActiveFileName()
    except KeyboardInterrupt:
        return

    what = "check"
    win32ui.SetStatusText(string.capitalize(what)+'ing module...',1)
    win32ui.DoWaitCursor(1)
    try:
        f = open(pathName)
    except IOError, details:
        print "Cant open file '%s' - %s" % (pathName, details)
        return
    try:
        code = f.read() + "\n"
    finally:
        f.close()
    try:
        codeObj = compile(code, pathName,'exec')
        if RunTabNanny(pathName):
            win32ui.SetStatusText("Python and the TabNanny successfully checked the file '"+os.path.basename(pathName)+"'")
    except SyntaxError:
        _HandlePythonFailure(what, pathName)
    except:
        traceback.print_exc()
        _HandlePythonFailure(what)
    win32ui.DoWaitCursor(0)

def RunTabNanny(filename):
    import cStringIO
    tabnanny = FindPythonTool("tabnanny.py")
    if tabnanny is None:
        win32ui.MessageBox("The TabNanny is not around, so the children can run amok!" )
        return

    # We "import" the tab nanny, so we run faster next time:
    tabnannyhome, tabnannybase = os.path.split(tabnanny)
    tabnannybase = os.path.splitext(tabnannybase)[0]
    # Put tab nanny at the top of the path.
    sys.path.insert(0, tabnannyhome)
    try:
        tn = __import__(tabnannybase)
        # Capture the tab-nanny output
        newout = cStringIO.StringIO()
        old_out = sys.stderr, sys.stdout
        sys.stderr = sys.stdout = newout
        try:
            tn.check(filename)
        finally:
            # Restore output
            sys.stderr, sys.stdout = old_out
        data = newout.getvalue()
        if data:
            try:
                lineno = string.split(data)[1]
                lineno = int(lineno)
                _JumpToPosition(filename, lineno)
                win32ui.SetStatusText("The TabNanny found trouble at line %d" % lineno)
            except (IndexError, TypeError, ValueError):
                print "The tab nanny complained, but I cant see where!"
                print data

            return 0
        else:
            return 1

    finally:
        # remove the tab-nanny from the path
        del sys.path[0]

def _JumpToPosition(fileName, lineno, col = 1):
    view = win32ui.GetApp().OpenDocumentFile(fileName).GetFirstView()
    charNo = view.LineIndex(lineno-1)
    view.SetSel(charNo + col - 1)


def _HandlePythonFailure(what, syntaxErrorPathName = None):
    typ, details, tb = sys.exc_info()
    if typ == SyntaxError:
        try:
            msg, (fileName, line, col, text) = details
            if (not fileName or fileName =="<string>") and syntaxErrorPathName:
                fileName = syntaxErrorPathName
            _JumpToPosition(fileName, line, col)
        except (TypeError, ValueError):
            msg = str(details)
        win32ui.SetStatusText('Failed to ' + what + ' - syntax error - %s' % msg)
    else:
        traceback.print_exc()
        win32ui.SetStatusText('Failed to ' + what + ' - ' + str(details) )

# Find a Python "tool" - ie, a file in the Python Tools/Scripts directory.
def FindPythonTool(filename):
    try:
        path = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "SOFTWARE\\Python\\PythonCore\\%s\\InstallPath" % (sys.winver))
    except win32api.error:
        print "WARNING - The Python registry does not have an 'InstallPath' setting"
        print "          The file '%s' can not be located" % (filename)
        return None
    fname = os.path.join(path, "Tools\\Scripts\\%s" % filename)
    try:
        os.stat(fname)
        return fname
    except os.error:
        print "WARNING - The Python registry's 'InstallPath' setting does not appear valid"
        print "          The file '%s' can not be located in path '%s'" % (filename, path)
        return None

def LocatePythonFile( fileName, bBrowseIfDir = 1 ):
    " Given a file name, return a fully qualified file name, or None "
    # first look for the exact file as specified
    if not os.path.isfile(fileName):
        # Go looking!
        baseName = fileName
        for path in sys.path:
            fileName = os.path.join(path, baseName)
            if os.path.isdir(fileName):
                if bBrowseIfDir:
                    old=os.getcwd()
                    os.chdir(fileName)
                    d=win32ui.CreateFileDialog(1, "*.py", None, 0, "Python Files (*.py)|*.py|All files|*.*")
                    rc=d.DoModal()
                    os.chdir(old)
                    if rc==win32con.IDOK:
                        fileName = d.GetPathName()
                        break
                    else:
                        return None
            else:
                fileName = fileName + ".py"
                if os.path.isfile(fileName):
                    break # Found it!

        else:   # for not broken out of
            return None
    return win32ui.FullPath(fileName)
