__version__ = "$Id$"

#
#       SVGChannel
#

import Channel
import MMurl

import svgdom

import windowinterface

import MMAttrdefs

class SVGChannel(Channel.ChannelWindow):
    def __init__(self, name, attrdict, scheduler, ui):
        Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
        self.svgdstrect = None
        self.svgsrcrect = None
        self.svgorgsize = None
        self.svgdds = None
        self.svgrenderer = None
        self.svgplayer = None
        self.svgddcolor = 0

    def __repr__(self):
        return '<SVGChannel instance, name=' + `self._name` + '>'

    def do_hide(self):
        Channel.ChannelWindow.do_hide(self)

    def destroy(self):
        del self.svgdds
        Channel.ChannelWindow.destroy(self)

    def do_arm(self, node, same=0):
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1

        url = self.getfileurl(node)
        if not url:
            self.errormsg(node, 'No URL set on node.')
            return 1

        from winversion import osversion
        if osversion.isWin9x():
            self.errormsg(node, 'SVG preview is not supported on Windows 9x versions.')
            return 1

        if svgdom.doccache.hasdoc(url):
            svgdoc = svgdom.doccache.getDoc(url)
        else:
            try:
                u = MMurl.urlopen(url)
            except IOError, arg:
                if type(arg) is type(self):
                    arg = arg.strerror
                self.errormsg(node, 'Cannot open: %s\n\n%s.' % (url, arg))
                return 1

            source = u.read()
            u.close()
            svgdoc = svgdom.SvgDocument(source)
            svgdom.doccache.cache(url, svgdoc)

        # default to white
        bgcolor = self.getbgcolor(node) or (255,255,255)
        r, g, b = bgcolor
        if r+g+b == 0: bgcolor = 255, 255, 255

        if self.window and svgdoc:
            coordinates = 0, 0, 1.0, 1.0 # self.getmediageom(node)
            self.svgdstrect = left, top, width, height = self.window._convert_coordinates(coordinates)
            self.svgorgsize = svgdoc.getSize()
            self.svgsrcrect = 0, 0, width, height # promise for svg scaling
            self.svgdds = self.window.createDDS(width, height)
            self.svgddcolor = self.svgdds.GetColorMatch(bgcolor)
            self.renderOn(self.svgdds, svgdoc, update=0)
            if svgdoc.hasTiming():
                rendercb = (self.renderOn, (self.svgdds, svgdoc))
                self.svgplayer = svgdom.SVGPlayer(svgdoc, windowinterface.toplevel, rendercb)
            fit = MMAttrdefs.getattr(node, 'fit')
            self.window.setmediadisplayrect(self.svgdstrect)
            self.window.setmediafit(fit)
        return 1

    def do_play(self, node, curtime):
        if self.window and self.svgdds:
            self.registerEvents(self.window, 1)
            self.window.setredrawdds(self.svgdds, self.svgdstrect, self.svgsrcrect)
            self.window.update(self.window.getwindowpos())
            if self.svgplayer:
                self.svgplayer.play()

    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        if self.window:
            self.window.setredrawdds(None)
            if self.svgplayer:
                self.svgplayer.stop()
                self.svgplayer = None
            self.svgdds = None
            self.svgrenderer = None
            self.registerEvents(self.window, 0)
        Channel.ChannelWindow.stopplay(self, node, curtime)

    def setpaused(self, paused, timestamp):
        Channel.ChannelWindow.setpaused(self, paused, timestamp)
        if self.svgplayer:
            if paused:
                self.svgplayer.pause()
            else:
                self.svgplayer.resume()

    def renderOn(self, dds, svgdoc, update = 1):
        import svgrender, svgwin
        svggraphics = svgwin.SVGWinGraphics()
        sw, sh = self.svgorgsize
        if sw and sh:
            dw, dh = self.svgdstrect[2:]
            sx, sy = dw/float(sw), dh/float(sh)
            sx = sy = min(sx, sy)
            svggraphics.applyTfList( [('scale',[sx, sy]),])
        self.svgdds.BltFill(self.svgsrcrect, self.svgddcolor)
        ddshdc = dds.GetDC()
        svggraphics.tkStartup(ddshdc)
        if self.svgrenderer is None:
            self.svgrenderer = svgrender.SVGRenderer(svgdoc, svggraphics)
        else:
            self.svgrenderer.reset(svgdoc, svggraphics)
        self.svgrenderer.render()
        svggraphics.tkShutdown()
        dds.ReleaseDC(ddshdc)
        if update:
            self.window.update(self.window.getwindowpos())

    def registerEvents(self, window, f):
        import WMEVENTS
        if f:
            window.register(WMEVENTS.Mouse0Press, self._mousepress, 'foreignObject')
            window.register(WMEVENTS.MouseMove, self._mousemove, 'foreignObject')
        else:
            window.unregister(WMEVENTS.Mouse0Press)
            window.unregister(WMEVENTS.MouseMove)

    def _mousepress(self, arg, window, event, value):
        if self.svgrenderer:
            pt = value[:2]
            node = self.svgrenderer.getElementAt(pt)
            if node and node.isMouseSensitive():
                node.onClick()

    def _mousemove(self, arg, window, event, value):
        if self.svgrenderer:
            pt = value[:2]
            node = self.svgrenderer.getElementAt(pt)
            if node and node.isMouseSensitive():
                window.setdefaultcursor('hand')
                return
        window.setdefaultcursor('arrow')



## #################################
# SVG channel alt using an OS window and Adobe's SVG viewer

# flag indicating SVG support
import windowinterface

class SVGOsChannel(Channel.ChannelWindow):
    HAS_SVG_SUPPORT = windowinterface.HasSvgSupport()
    def __init__(self, name, attrdict, scheduler, ui):
        Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

    def __repr__(self):
        return '<SVGChannel instance, name=' + `self._name` + '>'

    def do_hide(self):
        if self.window and hasattr(self.window,'DestroySvgCtrl'):
            self.window.DestroySvgCtrl()
        Channel.ChannelWindow.do_hide(self)

    def destroy(self):
        if self.window and hasattr(self.window,'DestroySvgCtrl'):
            self.window.DestroySvgCtrl()
        Channel.ChannelWindow.destroy(self)

    def do_arm(self, node, same=0):
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1
        f = self.getfileurl(node)
        if not f:
            self.errormsg(node, 'No URL set on node.')
            return 1
        try:
            f = MMurl.urlretrieve(f)[0]
        except IOError, arg:
            if type(arg) is type(self):
                arg = arg.strerror
            self.errormsg(node, 'Cannot open: %s\n\n%s.' % (f, arg))
            return 1

        if self.HAS_SVG_SUPPORT:
            if self.window:
                self.window.CreateOSWindow(svg=1)
                if not self.window.HasSvgCtrl():
                    try:
                        self.window.CreateSvgCtrl()
                    except:
                        self.errormsg(node, 'Failed to create SVG control.\nCheck that the control has been installed properly.')
                    else:
                        self.window.SetSvgSrc(f)
        else:
            self.errormsg(node, 'No SVG support on this system.')
        return 1

    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        if self.window and hasattr(self.window,'DestroySvgCtrl'):
            self.window.DestroySvgCtrl()
        Channel.ChannelWindow.stopplay(self, node, curtime)
