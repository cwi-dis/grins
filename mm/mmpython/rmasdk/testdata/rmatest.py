import sys, os, urllib
# Add our parent directory to the search path (rma may live there)
sys.path.append(os.pardir)

# An example of a RM listener class.
# An instance can be set to receive RM status notifications
# RMListener classes may have some or all of the methods
class PrintRMListener:
    def __init__(self):
        pass
    def __del__(self):
        print 'PrintRMListener dying'
    def OnPresentationOpened(self):
        print 'OnPresentationOpened'
    def OnPresentationClosed(self):
        print 'OnPresentationClosed'
    def OnStop(self):
        print 'OnStop'
    def OnPause(self,timenow):
        print 'OnPause',timenow
    def OnBegin(self,timenow):
        print 'OnBegin',timenow
    def OnPosLength(self,pos,len):
        #print 'pos:',pos,'/',len
        pass
    def OnPreSeek(self,oldtime,newtime):
        pass
    def OnPostSeek(self,oldtime,newtime):
        pass
    def OnBuffering(self,flags,percentcomplete):
        pass
    def OnContacting(self,hostname):
        print hostname

# real audio
cwd = os.getcwd()
url1="file:" + urllib.pathname2url(os.path.join(cwd, "thanks3.ra"))

# real video
url2="file:" + urllib.pathname2url(os.path.join(cwd,"test.rv"))

# real text
url3="file:" + urllib.pathname2url(os.path.join(cwd,"news.rt"))

# real pixel
url4="file:" + urllib.pathname2url(os.path.join(cwd,"fadein.rp"))

url = url1

import rma
engine = rma.CreateEngine()
player=engine.CreatePlayer()
x1 = player.SetStatusListener(PrintRMListener())
print 'SetStatusListener returned', x1
x2 = player.OpenURL(url)
print 'OpenURL(%s) returned'%url, hex(x2)
x3 = player.Begin()
print 'Begin returned', hex(x3)

if os.name == 'mac':
    import MacOS, Evt, Events

    # Disable event processing
    oldparms = MacOS.SchedParams(0, 0)
    while not player.IsDone():
        ok, evt = Evt.WaitNextEvent(-1, 0)      # No timeout, immedeate return
        if evt[0] == Events.keyDown:    # Stop on any key
            break
        engine.EventOccurred(evt)
    apply(MacOS.SchedParams, oldparms)
    print 'press return to exit-'
    sys.stdin.readline()
# for console apps, enter message loop
#import sys
#if sys.platform=='win32':
#       import win32ui
#       win32ui.GetApp().RunLoop(win32ui.GetWin32Sdk().GetDesktopWindow())
