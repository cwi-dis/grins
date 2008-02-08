
# RMPlayer template for extending the build in PyRMPlayer
class RMPlayer:
    def __init__(self,rmengine=None):
        if rmengine:
            p=rmengine.CreatePlayer()
        else:
            import rma
            p=rma.CreatePlayer()
        self.__dict__['_obj_'] = p

    def __del__(self):
        del self._obj_

    def __getattr__(self, attr):
        try:
            if attr != '__dict__':
                o = self.__dict__['_obj_']
                if o:
                    return getattr(o, attr)
        except KeyError:
            pass
        raise AttributeError, attr


# An example of a RMListener class.
# An instance can be set to receive RM status notifications
# RMListener classes may have some or all of the methods
class PrintRMListener:
    def __init__(self):
        pass
    def __del__(self):
        print 'PrinterAdviceSink dying'
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
