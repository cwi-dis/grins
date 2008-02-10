__version__ = "$Id$"

from RealWindowChannel import RealWindowChannel
import os

class RealPixChannel(RealWindowChannel):
    node_attrs = RealWindowChannel.node_attrs + \
                 ['size', 'aspect', 'bitrate', 'maxfps', 'preroll', 'href', 'captionchannel']
    node_attrs.remove('project_convert')

    tmpfiles = []
    __callback_added = 0

    def getfileurl(self, node):
        # This method has all sorts of magic to write a
        # RealPix file "just in time".  If the node has
        # changed there is a tmpfile attribute.  Since the
        # node has changed internally, we must write a copy
        # and we'll use the tmpfile attribute for a file name.
        # If the node has no URL, there is no existing file
        # that we can use, so we invent a name and write the
        # file.
        if hasattr(node, 'tmpfile'):
            import MMurl, realsupport
            if hasattr(node, 'rptmpfile'):
                f = MMurl.url2pathname(node.rptmpfile)
                try:
                    os.unlink(f)
                except:
                    pass
                node.rptmpfile = None
                del node.rptmpfile
            realsupport.writeRP(node.tmpfile, node.slideshow.rp, node, baseurl = node.tmpfile)
            return MMurl.pathname2url(node.tmpfile)
        url = RealWindowChannel.getfileurl(self, node)
        if not url or url[:5] == 'data:':
            if hasattr(node, 'rptmpfile'):
                url = node.rptmpfile
            else:
                import tempfile, realsupport, MMurl
                f = tempfile.mktemp('.rp')
                url = MMurl.pathname2url(f)
                node.rptmpfile = url
                realsupport.writeRP(f, node.slideshow.rp, node, baseurl = url)
                if not self.__callback_added:
                    import windowinterface
                    windowinterface.addclosecallback(
                            _deltmpfiles, ())
                    RealPixChannel.__callback_added = 1
                self.tmpfiles.append(f)
        return url

    def getduration(self, node):
        # use duration attribute if different from what's in the file
        duration = RealWindowChannel.getduration(self, node)
        if hasattr(node, 'slideshow') and \
           node.slideshow.rp.duration == duration:
            return 0
        return duration

def _deltmpfiles():
    for f in RealPixChannel.tmpfiles:
        try:
            os.unlink(f)
        except:
            pass
    RealPixChannel.tmpfiles = []
