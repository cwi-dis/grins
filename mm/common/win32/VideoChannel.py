__version__ = "$Id$"

#
# WIN32 Video channel
#

# the core
import Channel

# common component
import MediaChannel
import RealChannel

# node attributes
import MMAttrdefs

# channel types and message
import windowinterface

debug = 0

import rma

# ddraw.error
import ddraw

class VideoChannel(Channel.ChannelWindowAsync):
    _our_attrs = ['fit']
    node_attrs = Channel.ChannelWindow.node_attrs + [
            'clipbegin', 'clipend',
            'project_audiotype', 'project_videotype', 'project_targets',
            'project_perfect', 'project_mobile']
    chan_attrs = Channel.ChannelWindow.chan_attrs + _our_attrs

    def __init__(self, name, attrdict, scheduler, ui):
        self.__mc = None
        self.__rc = None
        self.__qc = None
        self.__type = None
        self.__subtype = None
        self.need_armdone = 0
        self.__playing = None
        self.__rcMediaWnd = None
        self.__windowless_real_rendering = 1
        self.__windowless_wm_rendering = 1
        Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

    def __repr__(self):
        return '<VideoChannel instance, name=' + `self._name` + '>'

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
        url = Channel.ChannelWindowAsync.getfileurl(self, node)
        if not url or url[:5] == 'data:':
            if hasattr(node, 'rptmpfile') and node.rptmpfile[1] == url:
                url = node.rptmpfile[0]
            else:
                import tempfile, realsupport, MMurl
                f = MMurl.urlopen(url)
                head = f.read(4)
                if head != '<imf':
                    f.close()
                    # delete rptmpfile attr if it exists
                    node.rptmpfile = None
                    del node.rptmpfile
                    return url
                rp = realsupport.RPParser(url)
                rp.feed(head)
                rp.feed(f.read())
                f.close()
                rp.close()
                f = tempfile.mktemp('.rp')
                nurl = MMurl.pathname2url(f)
                node.rptmpfile = nurl, url
                realsupport.writeRP(f, rp, node, baseurl = url)
                if not self.__callback_added:
                    import windowinterface
                    windowinterface.addclosecallback(
                            _deltmpfiles, ())
                    VideoChannel.__callback_added = 1
                self.tmpfiles.append(f)
        return url

    def do_show(self, pchan):
        if not Channel.ChannelWindowAsync.do_show(self, pchan):
            return 0
        return 1

    def do_hide(self):
        self.__playing = None
        if self.__mc:
            self.__mc.stopit()
            self.__mc.destroy()
            self.__mc = None
        elif self.__rc:
            self.__rc.stopit()
            self.__rc.destroy()
            self.__rc = None
        elif self.__qc:
            self.__qc.stopit()
            self.__qc.destroy()
            self.__qc = None
        if self.window:
            self.window.DestroyOSWindow()
        Channel.ChannelWindowAsync.do_hide(self)

    def do_arm(self, node, same=0):
        self.__ready = 0
        if same and self.armed_display:
            self.__ready = 1
            return 1
        node.__type = ''
        node.__subtype = ''
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1
        url = self.getfileurl(node)
        if not url:
            self.errormsg(node, 'No URL set on node.')
            return 1
        mtype = node.GetAttrDef('type', None)
        if not mtype:
            import urlcache
            mtype = urlcache.mimetype(url)
        if mtype and (mtype.find('real') >= 0 or mtype.find('flash') >= 0 or mtype.find('image') >= 0):
            node.__type = 'real'
            if mtype not in ('image/vnd.rn-realpix', 'text/vnd.rn-realtext'):
                self.__windowless_real_rendering = 0
            if mtype.find('flash') >= 0:
                node.__subtype = 'flash'
        elif mtype and mtype.find('quicktime') >= 0:
            node.__type = 'qt'
        else:
            node.__type = 'wm'
            if mtype and mtype.find('x-ms-asf') >= 0:
                node.__subtype = 'asf'
                if not self._exporter:
                    self.__windowless_wm_rendering = 0

        if node.__type == 'real':
            if self.__rc is None:
                try:
                    self.__rc = RealChannel.RealChannel(self)
                except RealChannel.error, msg:
                    # can't do RealAudio
##                     self.__rc = 0 # don't try again
                    self.errormsg(node, msg)
            if self.__rc:
                if self.__rc.prepare_player(node):
                    self.__ready = 1
        elif node.__type == 'qt' and MediaChannel.HasQtSupport():
            if self.__qc is None:
                self.__qc = MediaChannel.QtChannel(self)
                try:
                    self.__qc.prepare_player(node, self.window)
                    self.__ready = 1
                except MediaChannel.error, msg:
                    self.errormsg(node, msg)
        else:
            if self.__mc is None:
                if not self.__windowless_wm_rendering:
                    self.__mc = MediaChannel.MediaChannel(self)
                    try:
                        self.__mc.prepare_player(node, self.window)
                        self.__ready = 1
                    except MediaChannel.error, msg:
                        self.errormsg(node, msg)
                else:
                    self.__mc = MediaChannel.VideoStream(self)
                    try:
                        self.__mc.prepare_player(node, self.window)
                        self.__ready = 1
                    except MediaChannel.error, msg:
                        self.errormsg(node, msg)

#                                               self.__windowless_wm_rendering = 0
#                                               self.__mc = MediaChannel.MediaChannel(self)
#                                               try:
#                                                       self.__mc.prepare_player(node, self.window)
#                                                       self.__ready = 1
#                                               except MediaChannel.error, msg:
#                                                       self.errormsg(node, msg)
        self.prepare_armed_display(node)
        return 1

    def do_play(self, node, curtime):
        self.__playing = node
        self.__type = node.__type
        self.__subtype = node.__subtype
        start_time = node.get_start_time()

        if not self.__ready:
            # arming failed, so don't even try playing
            self.playdone(0, curtime)
            return
        if self.__type == 'real':
            bpp = self.window._topwindow.getRGBBitCount()
            if bpp not in (8, 16, 24, 32) and self.__windowless_real_rendering:
                self.__windowless_real_rendering = 0
            if self.__subtype=='flash':
                self.__windowless_real_rendering = 0

            if not self.__windowless_real_rendering:
                self.window.CreateOSWindow(rect=self.getMediaWndRect())
            if not self.__rc:
                self.playdone(0, curtime)
                return
            try:
                if self.__windowless_real_rendering:
                    res =self.__rc.playit(node,windowless=1,start_time=start_time)
                else:
                    res = self.__rc.playit(node, self._getoswindow(), self._getoswinpos(), start_time = start_time)
            except RealChannel.error:
                ## Don't forward the error
                ## The ErrorOccurred callback is called which produces the error message.
                self.playdone(0, curtime)
                return
            if not res:
                self.errormsg(node, 'No playback support for %s on this system.\n'
                                                 % chtype)
                self.playdone(0, curtime)

        elif self.__type == 'qt' and MediaChannel.HasQtSupport():
            if not self.__qc:
                self.playdone(0, curtime)
            else:
                if not self.__qc.playit(node, curtime, self.window, start_time):
                    self.errormsg(node, 'Could not play QuickTime movie.')
                    self.playdone(0, curtime)

        else:
            if not self.__mc:
                self.playdone(0, curtime)
            else:
                if not self.__windowless_wm_rendering:
                    self.window.CreateOSWindow(rect=self.getMediaWndRect())
                if not self.__mc.playit(node, curtime, self.window, start_time):
                    self.errormsg(node, 'Could not play Windows Media file.')
                    self.playdone(0, curtime)

    # toggles between pause and run
    def setpaused(self, paused, timestamp):
        Channel.ChannelWindowAsync.setpaused(self, paused, timestamp)
        if self.__mc is not None:
            self.__mc.pauseit(paused)
        elif self.__rc:
            self.__rc.pauseit(paused)
        elif self.__qc is not None:
            self.__qc.pauseit(paused)

    def playstop(self, curtime):
        # freeze video
        self.__freezeplayer()
        self.playdone(1, curtime)

    def __stopplayer(self):
        if self.__playing:
            if self.__type == 'real':
                if self.__rc:
                    self.__rc.stopit()
                    if self.__windowless_real_rendering:
                        self.cleanVideoRenderer()
            elif self.__type == 'qt':
                if self.__qc:
                    self.__qc.stopit()
            else:
                self.__mc.stopit()
        self.__playing = None

    def __freezeplayer(self):
        if self.__playing:
            if self.__type == 'real':
                if self.__rc:
                    self.__rc.freezeit()
            elif self.__type == 'qt':
                if self.__qc:
                    self.__qc.freezeit()
            else:
                self.__mc.freezeit()

    def endoftime(self):
        self.__stopplayer()
        self.playdone(0)

    # interface for anchor creation
    def defanchor(self, node, anchor, cb):
        windowinterface.showmessage('The whole media item will be sensitive.')
        cb((anchor[0], anchor[1], ['rect',0.0,0.0,1.0,1.0], anchor[3]))

    def prepare_armed_display(self,node):
        self.armed_display._bgcolor=self.getbgcolor(node)
        self.armed_display.fgcolor(self.getbgcolor(node))
        armbox = self.prepare_anchors(node, self.window, self.getmediageom(node))
        self.setArmBox(armbox)
        self.armed_display.setMediaBox(armbox)

    def _getoswindow(self):
        return self.window.GetSafeHwnd()

    def _getoswinpos(self):
        x, y, w, h = self.window._rect
        return (x, y), (w, h)

    def play(self, node, curtime):
        if node.GetType() == 'anchor':
            self.play_anchor(node, curtime)
            return
        self.need_armdone = 1
        self.play_0(node, curtime)
        if not self._armcontext:
            return
        if self._is_shown and node.ShouldPlay() \
           and self.window and not self.syncplay:
            self.check_popup()
            self.schedule_transitions(node, curtime)
            if self.armed_display.is_closed():
                # assume that we are going to get a
                # resize event
                pass
            else:
                self.armed_display.render()
            if self.played_display:
                self.played_display.close()
            self.played_display = self.armed_display
            self.armed_display = None
            self.do_play(node, curtime)
            if self.need_armdone and node.__type != 'real':
                self.need_armdone = 0
                self.armdone()
        else:
            self.need_armdone = 0 # play_1 calls armdone()
            self.play_1(curtime)

    def playdone(self, outside_induced, curtime):
        if self.need_armdone:
            self.need_armdone = 0
            self.armdone()
        Channel.ChannelWindowAsync.playdone(self, outside_induced, curtime)
        if not outside_induced:
            self.__playing = None

    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        if node and self._played_node is not node:
##             print 'node was not the playing node '+`self,node,self._played_node`
            return
        self.__stopplayer()
        Channel.ChannelWindowAsync.stopplay(self, node, curtime)

    # Define the anchor area for visible medias
    def prepare_anchors(self, node, window, coordinates):
        if not window: return

        # GetClientRect by def returns always: 0, 0, w, h
        w_left,w_top,w_width,w_height = window.GetClientRect()

        left,top,width,height = window._convert_coordinates(coordinates, units = windowinterface.UNIT_PXL)
        if width==0 or height==0:
            print 'warning: zero size media rect'
            width, height = w_width, w_height
        self.__rcMediaWnd = left, top, width, height

        # preset for animation
        window.setmediadisplayrect(self.__rcMediaWnd)
        window.setmediafit(MMAttrdefs.getattr(node, 'fit'))

        return (left/float(w_width), top/float(w_height), width/float(w_width), height/float(w_height))

    def getMediaWndRect(self):
        return self.__rcMediaWnd


    #############################
    def getRealVideoRenderer(self):
        self.initVideoRenderer()
        return self

    #
    # Implement interface of real video renderer
    #
    videofmts = { rma.RMA_RGB: 'RGB', # windows RGB
            rma.RMA_RLE8: 'RLE8',
            rma.RMA_RLE4: 'RLE4',
            rma.RMA_BITFIELDS: 'BITFIELDS',
            rma.RMA_I420: 'I420', # planar YCrCb
            rma.RMA_YV12: 'YV12', # planar YVU420
            rma.RMA_YUY2: 'YUY2', # packed YUV422
            rma.RMA_UYVY: 'UYVY', # packed YUV422
            rma.RMA_YVU9: 'YVU9', # Intel YVU9

            rma.RMA_YUV420: 'YUV420',
            rma.RMA_RGB555: 'RGB555',
            rma.RMA_RGB565: 'RGB565',
            }

    def toStringFmt(self, fmt):
        if VideoChannel.videofmts.has_key(fmt):
            return VideoChannel.videofmts[fmt]
        else:
            return 'FOURCC(%d)' % fmt

    def initVideoRenderer(self):
        self.__rmdds = None
        self.__rmrender = None
        self.__blttimerid = 0

    def cleanVideoRenderer(self):
        if self.window:
            self.window.removevideo()
        self.__rmdds = None
        self.__rmrender = None

    def OnFormatBitFields(self, rmask, gmask, bmask):
        self.__bitFieldsMask = rmask, gmask, bmask

    def OnFormatChange(self, w, h, bpp, fmt):
        if not self.window: return
        viewport = self.window._topwindow
        screenBPP = viewport.getRGBBitCount()

        bltCode = ''
        if fmt==rma.RMA_RGB:
            bltCode = 'Blt_RGB%d_On_RGB%d' % (bpp, screenBPP)
        elif fmt==rma.RMA_YUV420:
            bltCode = 'Blt_YUV420_On_RGB%d' % screenBPP

        if debug:
            print 'Rendering real video: %s bpp=%d (%d x %d) on RGB%d' % (self.toStringFmt(fmt), bpp, w, h, screenBPP)

        if not bltCode:
            self.cleanVideoRenderer()
            return

        try:
            dymmy = getattr(viewport.getDrawBuffer(), bltCode)
        except AttributeError:
            self.cleanVideoRenderer()
        else:
            self.__rmdds = viewport.CreateSurface(w, h)
            self.__rmrender = getattr(self.__rmdds, bltCode), w, h
            self.window.setvideo(self.__rmdds, self.getMediaWndRect(), (0,0,w,h) )

    def Blt(self, data):
        if self.__rmdds and self.__rmrender:
            blt, w, h = self.__rmrender
            try:
                blt(data, w, h)
            except ddraw.error, arg:
                print arg
                return
            if not self.__blttimerid:
                self.__blttimerid = windowinterface.settimer(0.01,(self.bltUpdate,()))

    def bltUpdate(self):
        self.__blttimerid = 0
        if self.window:
            self.window.update(self.window.getwindowpos())

    def EndBlt(self):
        # do not remove video yet
        # it may be frozen
        self.__rmdds = None
        self.__rmrender = None

def _deltmpfiles():
    import os
    for f in VideoChannel.tmpfiles:
        try:
            os.unlink(f)
        except:
            pass
    VideoChannel.tmpfiles = []
