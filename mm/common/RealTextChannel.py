__version__ = "$Id$"

from RealWindowChannel import RealWindowChannel

class RealTextChannel(RealWindowChannel):
    tmpfiles = []
    __callback_added = 0

    def getfileurl(self, node):
        # This method has all sorts of magic to write a
        # RealText caption file if this node is the caption-aspect
        # of a realpix slideshow. Otherwise we simply call the normal
        # getfileurl method.
        if hasattr(node, 'helpertype') and node.helpertype == 'caption':
            import tempfile, realsupport, MMurl
            f = tempfile.mktemp('.rt')
            url = MMurl.pathname2url(f)
            realsupport.writeRT(f, node.slideshow.rp, node)
            if not self.__callback_added:
                import windowinterface
                windowinterface.addclosecallback(
                        _deltmpfiles, ())
                RealTextChannel.__callback_added = 1
            self.tmpfiles.append(f)
            return url
        else:
            return RealWindowChannel.getfileurl(self, node)

def _deltmpfiles():
    import os
    for f in RealTextChannel.tmpfiles:
        try:
            os.unlink(f)
        except:
            pass
    RealTextChannel.tmpfiles = []
