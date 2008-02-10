import rma

engine = rma.CreateEngine()


class RealPlayer:
    # This class is for use with the new rma pyd.
    # The new rma pyd has not a preconfigured player.
    # An object of this class exposes to its clients
    # the same interface as the previous rma buildin player
    def __init__(self, rmengine):
        p=rmengine.CreatePlayer()
        self.__dict__['_obj_'] = p

        # create client context objects
        # player is an optional arg
        # passing a player as arg we implicitly request
        # part of the config to happen automatically (see source)
        adviseSink = rma.CreateClientAdviseSink(p)
        errorSink = rma.CreateErrorSink(p)
        authManager = rma.CreateAuthenticationManager(p)
        siteSupplier = rma.CreateSiteSupplier(p)

        # create player's client context with what interfaces
        # we would like to support
        clientContext = rma.CreateClientContext()
        clientContext.AddInterface(adviseSink.QueryIUnknown())
        clientContext.AddInterface(errorSink.QueryIUnknown())
        clientContext.AddInterface(authManager.QueryIUnknown())
        clientContext.AddInterface(siteSupplier.QueryIUnknown())

        # and give it to player
        # the player will use this context to request
        # available client interfaces (through QueryInterface)
        p.SetClientContext(clientContext)
        del clientContext # now belongs to player

        # keep refs to our client context objects
        # so that we can configure them later
        self._adviseSink = adviseSink
        self._errorSink = errorSink
        self._authManager = authManager
        self._siteSupplier = siteSupplier

    def __del__(self):
        self._obj_.Stop()
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

    def SetStatusListener(self, listener):
        self._adviseSink.SetPyListener(listener)
        self._errorSink.SetPyListener(listener)

    def SetPyAdviceSink(self, listener):
        self._adviseSink.SetPyListener(listener)

    def SetPyErrorSink(self, listener):
        self._errorSink.SetPyListener(listener)

    def SetOsWindow(self, window):
        self._siteSupplier.SetOsWindow(window)

    def SetPositionAndSize(self, pos, size):
        self._siteSupplier.SetPositionAndSize(pos, size)



# An example of a RMA listener class.
# An instance can be set to receive RMA status notifications
# RMA listener classes may have some or all of the methods
class PrintListener:
    def __init__(self):
        pass
    def __del__(self):
        print 'PrintListener dying'
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

    # plus error sink interface
    def ErrorOccurred(self, msg):
        print msg


player = RealPlayer(engine)

# configure client context objects

# set our python status listener
# set our python error listener
player.SetStatusListener(PrintListener())

# set os window to site supplier
# ...


# use player

# real audio
url1="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/thanks3.ra"

# real video
url2="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/test.rv"

# real text
url3="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/news.rt"

# real pixel
url4="file:///D|/ufs/mm/cmif/mmpython/rmasdk/testdata/fadein.rp"

# test error report
url5="file:///D|/ufs/mm/cmif/mmpython/rmasdk/testdata/fadeinErr.rp"

player.OpenURL(url4)

player.Begin()

print engine.GetPlayerCount(),'players'
