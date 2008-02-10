__version__ = "$Id$"

# A minimal text editor.
#
# To be done:
# - Functionality: find, etc.

from Carbon import Win
from Carbon import Qd
from Carbon import QuickDraw
from Carbon import Res
from Carbon import Fm
from Carbon import Ctl
from Carbon import Controls
import waste
import WASTEconst
import os
import string
import htmllib
import MMurl
import img
import imgformat
import mac_image
import formatter

## PIXELFORMAT=imgformat.macrgb16
PIXELFORMAT=imgformat.macrgb

LEFTMARGIN=4
TOPMARGIN=4
RIGHTMARGIN=2
BOTTOMMARGIN=0
SCROLLBARWIDTH=16
IMAGEBORDER=2

# Sizes for HTML tag types
HTML_SIZE={
        'h1': 4,
        'h2': 2
}

# Parts of the scrollbar we track:
TRACKED_PARTS=(Controls.inUpButton, Controls.inDownButton,
                Controls.inPageUp, Controls.inPageDown)

class HTMLWidget:
    def __init__(self, window, rect, name, controlhandler=None):
        init_waste()
        self.last_mouse_was_down = 0
        self.url = ''
        self.current_data_loaded = None
        self.tag_positions = {}
        self.bary = None
        self.anchor_offsets = []
        self.anchor_hrefs = []
        self.must_clear = 0
        self.bg_color = (0xffff, 0xffff, 0xffff)
        self.fg_color = (0, 0, 0)
        self.an_color = (0xffff, 0, 0)
        self.font_normal = Fm.GetFNum('Times')
        self.font_tt = Fm.GetFNum('Courier')
        self.font_size = 12
        self.name = name
        self.wid = window
        self.controlhandler = controlhandler
        l, t, r, b = rect
        self.rect = rect
        vr = l+LEFTMARGIN, t+TOPMARGIN, r-RIGHTMARGIN, b-BOTTOMMARGIN
        dr = (0, 0, vr[2]-vr[0], 0)
        Qd.SetPort(window)
        Qd.TextFont(4)
        Qd.TextSize(9)
        flags = WASTEconst.weDoAutoScroll | WASTEconst.weDoOutlineHilite
        self.ted = waste.WENew(dr, vr, flags)
        self._createscrollbars()
        self.do_activate()

    def close(self):
        Qd.SetPort(self.wid) # XXXX Needed?
        if self.bary:
            self.bary.DisposeControl()
        del self.bary
        del self.ted
        del self.wid

    def setcolors(self, bg, fg, an, recalc=0):
        any = 0
        if not bg is None:
            self.bg_color = bg
            any = 1
        if not fg is None:
            self.fg_color = fg
            self.html_color = fg
            any = 1
        if not an is None:
            self.an_color = an
            any = 1
        if any and recalc:
            self.new_font(self.html_font)

    def setfonts(self, normal, tt, defsize, recalc=0):
        any = 0
        if normal != None:
            self.font_normal = normal
            any = 1
        if tt != None:
            self.font_tt = tt
            any = 1
        if defsize != None:
            self.font_size = defsize
            any = 1
        if any and recalc:
            self.new_font(self.html_font)

    def _createscrollbars(self, reset=0):
        #
        # See if we need them.
        #
        if self.bary:
            self.bary.DisposeControl()
            if self.controlhandler:
                self.controlhandler._del_control(self.bary)
        self.bary = None
        l, t, r, b = self.rect
        if reset:
            self.ted.WECalText()
            self.ted.WESelView()
        vr = self.ted.WEGetViewRect()
        dr = self.ted.WEGetDestRect()
        need_bary = ((dr[3]-dr[1]) >= (vr[3]-vr[1]))
        if need_bary:
            vr = l+LEFTMARGIN, t+TOPMARGIN, r-(RIGHTMARGIN+SCROLLBARWIDTH-1), b-BOTTOMMARGIN
            dr = dr[0], dr[1], dr[0]+vr[2]-vr[0], dr[3]
            self.ted.WESetViewRect(vr)
            self.ted.WESetDestRect(dr)
            self.ted.WECalText()
            vr = self.ted.WEGetViewRect()
            dr = self.ted.WEGetDestRect()
            rect = r-(SCROLLBARWIDTH-1), t-1, r+1, b+1
            vy = self._getybarvalue()
            self.bary = Ctl.NewControl(self.wid, rect, "", 1, vy, 0, dr[3]-dr[1]-(vr[3]-vr[1]), 16, 0)
            if not self.activated: self.bary.DeactivateControl()
            self._updatedocview()
            if self.controlhandler:
                self.controlhandler._add_control(self.bary,
                                self._scrollbarcallback, self._scrollbarcallback)
        else:
            vr = l+LEFTMARGIN, t+TOPMARGIN, r-RIGHTMARGIN, b-BOTTOMMARGIN
            dr = dr[0], dr[1], dr[0]+vr[2]-vr[0], dr[3]
            self.ted.WESetViewRect(vr)
            self.ted.WESetDestRect(dr)
            self.ted.WECalText()
            self.ted.WEScroll(vr[0]-dr[0], vr[1]-dr[1]) # Test....

    def _getybarvalue(self):
        vr = self.ted.WEGetViewRect()
        dr = self.ted.WEGetDestRect()
        return vr[1]-dr[1]

    def _updatescrollbars(self):
        """Update scrollbars to reflect current state of document"""
        if not self.bary or not self.activated:
            return 0
        vy = self._getybarvalue()
        self.bary.SetControlValue(vy)
        max = self.bary.GetControlMaximum()
        if vy > max:
            self._updatedocview()

    def _updatedocview(self):
        """Update document view to reflect state of scrollbars"""
        vr = self.ted.WEGetViewRect()
        dr = self.ted.WEGetDestRect()
        value = self.bary.GetControlValue()
        self.ted.WEScroll(vr[0]-dr[0], vr[1]-dr[1]-value)

    def _scrollbarcallback(self, which, where):
        if which != self.bary:
            print 'funny control', which, 'not', self.bary
            return 0
        #
        # Get current position
        #
        l, t, r, b = self.ted.WEGetViewRect()
        #
        # "line" size is minimum of top and bottom line size
        #
        topline_off,dummy = self.ted.WEGetOffset((l+1,t+1))
        topline_num = self.ted.WEOffsetToLine(topline_off)
        toplineheight = self.ted.WEGetHeight(topline_num, topline_num+1)

        botline_off, dummy = self.ted.WEGetOffset((l+1, b-1))
        botline_num = self.ted.WEOffsetToLine(botline_off)
        botlineheight = self.ted.WEGetHeight(botline_num, botline_num+1)

        if botlineheight == 0:
            botlineheight = self.ted.WEGetHeight(botline_num-1, botline_num)
        if botlineheight < toplineheight:
            lineheight = botlineheight
        else:
            lineheight = toplineheight
        if lineheight <= 0:
            lineheight = 1
        pageheight = (b-t)-lineheight
        if pageheight <= 0:
            pageheight = lineheight
        #
        # Now do the command.
        #
        value = self.bary.GetControlValue()
        if where == Controls.inUpButton:
            value = value - lineheight
        elif where == Controls.inPageUp:
            value = value - pageheight
        elif where == Controls.inDownButton:
            value = value + lineheight
        elif where == Controls.inPageDown:
            value = value + pageheight
        self.bary.SetControlValue(value)
        self._updatedocview()
        return 1

    def do_activate(self):
        Qd.SetPort(self.wid)
        self.ted.WEActivate()
        if self.bary:
            self.bary.ActivateControl()
        self.activated = 1

    def do_deactivate(self):
        Qd.SetPort(self.wid)
        self.ted.WEDeactivate()
        if self.bary:
            self.bary.DeactivateControl()
        self.activated = 0

    def do_update(self):
        if self.must_clear:
            self._clear_html()
        visregion = self.wid.GetWindowPort().visRgn
        myregion = Qd.NewRgn()
        Qd.RectRgn(myregion, self.rect) # or is it self.ted.WEGetViewRect() ?
        Qd.SectRgn(myregion, visregion, myregion)
        # Waste doesn't honour the clipping region, do it ourselves
        clipregion = Qd.NewRgn()
        Qd.GetClip(clipregion)
        Qd.SectRgn(myregion, clipregion, myregion)
        if Qd.EmptyRgn(myregion):
            return
        Qd.RGBBackColor(self.bg_color)
        Qd.RGBForeColor((0, 0xffff, 0)) # DBG
        Qd.EraseRgn(visregion)
        self.ted.WEUpdate(myregion)
##         self._updatescrollbars()

    def do_moveresize(self, rect):
        l, t, r, b = rect
        self.rect = rect
        Qd.SetPort(self.wid)
        Qd.RGBBackColor(self.bg_color)
        vr = l+LEFTMARGIN, t+TOPMARGIN, r-RIGHTMARGIN, b-BOTTOMMARGIN
        self.ted.WESetViewRect(vr)
        self.wid.InvalWindowRect(self.rect)
        self._createscrollbars()

    def do_click(self, down, local, evt):
        (what, message, when, where, modifiers) = evt
        Qd.SetPort(self.wid)
        Qd.RGBBackColor(self.bg_color)
        if down:
            # Check for control
            ptype, ctl = Ctl.FindControl(local, self.wid)
            if ptype and ctl:
                if ptype in TRACKED_PARTS:
                    dummy = ctl.TrackControl(local, self._scrollbarcallback)
                else:
                    part = ctl.TrackControl(local)
                    if part:
                        self._scrollbarcallback(ctl, part)
                return
            # Remember, so we react to mouse-up next time
            self.last_mouse_was_down = 1
        else:
            if not self.last_mouse_was_down:
                # Two ups in a row,
                # probably due to window-raise or something
                return
            self.last_mouse_was_down = 0

            # Check for anchor
            if not self._cbanchor:
                return
            off, edge = self.ted.WEGetOffset(local)
            for i in range(len(self.anchor_offsets)):
                p0, p1 = self.anchor_offsets[i]
                if p0 <= off < p1:
                    href = self.anchor_hrefs[i]
                    self._cbanchor(href)
                    return

    def do_char(self, ch, event):
        pass # Do nothing.

    def _clear_html(self):
        Qd.SetPort(self.wid)
        Qd.RGBBackColor(self.bg_color)
        self.ted.WEFeatureFlag(WASTEconst.weFInhibitRecal, 1)
        self.ted.WESetSelection(0, 0x3fffffff)
        self.ted.WEDelete()
        self.ted.WEFeatureFlag(WASTEconst.weFInhibitRecal, 0)
        self.wid.InvalWindowRect(self.rect)
        self._createscrollbars(reset=1)
        self.anchor_offsets = []
        self.current_data_loaded = None
        self.must_clear = 0

    def insert_html(self, data, url, tag=None):
        if data == '':
            self.must_clear = 1
            self.wid.InvalWindowRect(self.rect)
            return

        self.must_clear = 0
        Qd.SetPort(self.wid)
        Qd.RGBBackColor(self.bg_color)
        if data == self.current_data_loaded:
            self._position_html(tag)
            return
        self.current_data_loaded = data
        f = MyFormatter(self)

        # Remember where we are, and don't update
        Qd.SetPort(self.wid)
        self.ted.WESetSelection(0, 0x3fffffff)
        self.ted.WEDelete()
        self.ted.WEFeatureFlag(WASTEconst.weFInhibitRecal, 1)

        self.html_init()
        self.tag_positions = {}
        p = MyHTMLParser(f)
        p.url = url  # Tell it the URL, for relative images
        p.feed(data)

        self.anchor_hrefs = p.anchorlist[:]

        # Restore updating, recalc, set focus
        if tag and self.tag_positions.has_key(tag):
            pos = self.tag_positions[tag]
##             print 'DBG: start', tag, pos
        else:
            if tag:
                print 'Warning: no tag named', tag
            pos = 0
        self.ted.WESetSelection(pos, pos)
##         self.ted.WESetSelection(0, 0)
        self.ted.WEFeatureFlag(WASTEconst.weFInhibitRecal, 0)
        self.wid.InvalWindowRect(self.rect)

        self._createscrollbars(reset=1)

    def insert_plaintext(self, data):
        if data == '':
            self.must_clear = 1
            self.wid.InvalWindowRect(self.rect)
            return

        self.must_clear = 0
        Qd.SetPort(self.wid)
        Qd.RGBBackColor(self.bg_color)
        self.current_data_loaded = None

        # Remember where we are, and don't update
        Qd.SetPort(self.wid)
        self.ted.WESetSelection(0, 0x3fffffff)
        self.ted.WEDelete()
        self.ted.WEFeatureFlag(WASTEconst.weFInhibitRecal, 1)

        self.html_init()
        self.new_font([0, 0, 0, 1])             # Set typewriter font
        self.send_literal_data(data)    # And insert the data.

        self.anchor_hrefs = []

        pos = 0
        self.ted.WESetSelection(pos, pos)
##         self.ted.WESetSelection(0, 0)
        self.ted.WEFeatureFlag(WASTEconst.weFInhibitRecal, 0)
        self.wid.InvalWindowRect(self.rect)

        self._createscrollbars(reset=1)

    def _position_html(self, tag=None):
        Qd.SetPort(self.wid)
        # Restore updating, recalc, set focus
        if tag and self.tag_positions.has_key(tag):
            pos = self.tag_positions[tag]
##             print 'DBG: goto', tag, pos
        else:
            if tag:
                print 'Warning: no tag named', tag
            pos = 0
        # We first scroll to the end, in an attempt to put the anchor at
        # the top of the widget.
        self.ted.WESetSelection(pos+32000, pos+32000)
        self.ted.WESelView()
        self.ted.WESetSelection(pos, pos)
##         self.ted.WESetSelection(pos, pos+32000)
##         self.ted.WESetSelection(pos+32000, pos)
        self.ted.WESelView()
        self._updatescrollbars()

    #
    # Methods for getting at the anchors
    #
    def GetHRefs(self):
        return self.anchor_hrefs[:]

    def setanchorcallback(self, cb):
        self._cbanchor = cb


    #
    # Methods for writer class for html formatter
    #

    def html_init(self):
        self.para_count = 0
        self.delayed_tag_positions = []
        self.html_font = [0, 0, 0, 0]
        self.html_style = 0
        self.html_color = self.fg_color
        self.new_font(self.html_font)
        self.last_anchor_begin_pos = -1
        self.anchor_offsets = []

    def new_font(self, font):
        self.delayed_para_send()
        if font == None:
            font = (0, 0, 0, 0)
        font = map(lambda x:x, font)
        for i in range(len(font)):
            if font[i] == None:
                font[i] = self.html_font[i]
        [size, italic, bold, tt] = font
        self.html_font = font[:]
        if tt:
            font = self.font_tt
        else:
            font = self.font_normal
        if HTML_SIZE.has_key(size):
            size = HTML_SIZE[size]
        else:
            size = 0
        size = size + self.font_size
        face = 0
        if bold: face = face | 1
        if italic: face = face | 2
        face = face | self.html_style
        self.ted.WESetStyle(WASTEconst.weDoFont | WASTEconst.weDoFace |
                        WASTEconst.weDoReplaceFace | WASTEconst.weDoSize | WASTEconst.weDoColor,
                        (font, face, size, self.html_color))

    def new_margin(self, margin, level):
        self.delayed_para_send()
        ##self.ted.WEInsert('[Margin %s %s]'%(margin, level), None, None)

    def new_spacing(self, spacing):
        self.delayed_para_send()
        ##self.ted.WEInsert('[spacing %s]'%spacing, None, None)

    def new_styles(self, styles):
        self.delayed_para_send()
        self.html_style = 0
        self.html_color = self.fg_color
        if 'anchor' in styles:
            self.html_style = self.html_style | 4
            self.html_color = self.an_color
            dummy, self.anchor_begin_pos = self.ted.WEGetSelection()
        elif self.anchor_begin_pos >= 0:
            dummy, endpos = self.ted.WEGetSelection()
            self.anchor_offsets.append((self.anchor_begin_pos, endpos))
            self.anchor_begin_pos = -1
        self.new_font(self.html_font)

    def send_paragraph(self, blankline):
        self.para_count = self.para_count + blankline + 1

    def delayed_para_send(self):
        if not self.para_count: return
        self.ted.WEInsert('\r'*self.para_count, None, None)
        self.para_count = 0

    def delayed_name_send(self):
        if not self.delayed_tag_positions: return
        for name in self.delayed_tag_positions:
            dummy, self.tag_positions[name] = self.ted.WEGetSelection()
        self.delayed_tag_positions = []

    def send_line_break(self):
        self.delayed_para_send()
        self.ted.WEInsert('\r', None, None)

    def send_hor_rule(self, *args, **kw):
        # Ignore ruler options, for now
        self.delayed_para_send()
        self.delayed_name_send()
        dummydata = Res.Resource('')
        self.ted.WEInsertObject('rulr', dummydata, (0,0))

    def send_label_data(self, data):
        self.delayed_para_send()
        self.delayed_name_send()
        self.ted.WEInsert(data, None, None)

    def send_flowing_data(self, data):
        self.delayed_para_send()
        self.delayed_name_send()
        self.ted.WEInsert(data, None, None)

    def send_literal_data(self, data):
        self.delayed_para_send()
        self.delayed_name_send()
        data = string.join(string.split(data, '\n'), '\r')
        data = string.expandtabs(data)
        self.ted.WEInsert(data, None, None)

    def send_image(self, data):
        self.delayed_para_send()
        self.delayed_name_send()
        self.ted.WEInsertObject('GIF ', data, (0, 0))

    def send_name(self, name):
        self.delayed_tag_positions.append(name)


class MyFormatter(formatter.AbstractFormatter):

    def __init__(self, writer):
        formatter.AbstractFormatter.__init__(self, writer)
        self.parskip = 1

    def my_add_image(self, image):
        self.writer.send_image(image)

    def my_send_name(self, name):
        self.writer.send_name(name)

    def my_body_colors(self, bg, fg, an):
        self.writer.setcolors(bg, fg, an, recalc=1)

class MyHTMLParser(htmllib.HTMLParser):

    from machtmlentitydefs import entitydefs

    def anchor_bgn(self, href, name, type):
        self.anchor = href
        if self.anchor:
            self.anchorlist.append(href)
            self.formatter.push_style('anchor')
        if name:
            self.formatter.my_send_name(name)

    def anchor_end(self):
        if self.anchor:
            self.anchor = None
            self.formatter.pop_style()

    def end_p(self):
        # It seems most browsers treat </p> as <p>...
        self.do_p(())

    def start_p(self, attrs):
        # It seems most browsers treat </p> as <p>...
        self.do_p(attrs)
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)

    def start_h1(self, attrs):
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)
        htmllib.HTMLParser.start_h1(self, attrs)

    def start_h2(self, attrs):
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)
        htmllib.HTMLParser.start_h2(self, attrs)

    def start_h3(self, attrs):
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)
        htmllib.HTMLParser.start_h3(self, attrs)

    def start_h4(self, attrs):
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)
        htmllib.HTMLParser.start_h4(self, attrs)

    def start_h5(self, attrs):
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)
        htmllib.HTMLParser.start_h5(self, attrs)

    def start_h6(self, attrs):
        for aname, avalue in attrs:
            if aname == 'id':
                self.formatter.my_send_name(avalue)
        htmllib.HTMLParser.start_h6(self, attrs)

    def handle_image(self, src, alt, ismap, align, width, height):
        url = MMurl.basejoin(self.url, src)
        try:
            handle = _gifkeeper.new(url)
        except (IOError, img.error), arg: # XXXX Work out which ones should really be catched
            print 'Html: failed to get image', url, arg
            self.formatter.add_flowing_data(alt)
            return
        self.formatter.my_add_image(handle)

    def start_body(self, attrs):
        bg = None
        fg = None
        an = None
        for aname, avalue in attrs:
            if aname == 'bgcolor':
                bg = self.parsecolor(avalue)
            if aname == 'text':
                fg = self.parsecolor(avalue)
            if aname == 'link':
                an = self.parsecolor(avalue)
        self.formatter.my_body_colors(bg, fg, an)

    def parsecolor(self, color):
        if color[0] == '#':
            try:
                value = string.atoi(color[1:], 16)
            except ValueError:
                return None
            r = (value>>16) & 0xff
            g = (value>>8) & 0xff
            b = value & 0xff
            return r*0x101, g*0x101, b*0x101
        return None


waste_inited = 0

def init_waste():
    global waste_inited
    if waste_inited:
        return
    waste_inited = 1
    # Ruler handlers
    waste.WEInstallObjectHandler('rulr', 'new ', newRuler)
    waste.WEInstallObjectHandler('rulr', 'draw', drawRuler)
    waste.WEInstallObjectHandler('rulr', 'free', freeRuler)
    # GIF handlers
    waste.WEInstallObjectHandler('GIF ', 'new ', newGIF)
    waste.WEInstallObjectHandler('GIF ', 'draw', drawGIF)
    waste.WEInstallObjectHandler('GIF ', 'free', freeGIF)

def newRuler(obj):
    """Insert a new ruler. Make it as wide as the window minus 2 pixels"""
    ted = obj.WEGetObjectOwner()
    l, t, r, b = ted.WEGetDestRect()
    return r-l, 4

def drawRuler((l, t, r, b), obj):
    y = (t+b)/2
    Qd.MoveTo(l+2, y)
    Qd.LineTo(r-2, y)
    return 0

def freeRuler(*args):
    return 0

def newGIF(obj):
    handle = obj.WEGetObjectDataHandle()
    width, height, pixmap = _gifkeeper.get(handle.data)
    return width+2*IMAGEBORDER, height+2*IMAGEBORDER

def drawGIF((l,t,r,b),obj):
    handle = obj.WEGetObjectDataHandle()
    width, height, pixmap = _gifkeeper.get(handle.data)
    srcrect = 0, 0, width, height
    dstrect = l+IMAGEBORDER, t+IMAGEBORDER, r-IMAGEBORDER, b-IMAGEBORDER
    port = Qd.GetPort()
    bg = port.rgbBkColor
    fg = port.rgbFgColor
    Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
    Qd.RGBForeColor((0,0,0))
##     Qd.CopyBits(pixmap, port.GetPortBitMapForCopyBits(), srcrect, dstrect,
##         QuickDraw.srcCopy+QuickDraw.ditherCopy, None)
    Qd.CopyBits(pixmap, port.GetPortBitMapForCopyBits(), srcrect, dstrect,
            QuickDraw.srcCopy, None)
    Qd.RGBBackColor(bg)
    Qd.RGBForeColor(fg)
    # XXXX paste pixmap on screen
    return 0

def freeGIF(obj):
    handle = obj.WEGetObjectDataHandle()
    _gifkeeper.delete(handle.data)
    return 0

class _Gifkeeper:
    def __init__(self):
        self.dict = {}

    def new(self, url):
        if self.dict.has_key(url):
            self.dict[url][0] = self.dict[url][0] + 1
            return self.dict[url][1]
        fname = MMurl.urlretrieve(url)[0]
        image = img.reader(PIXELFORMAT, fname)
        data = image.read()
        pixmap = mac_image.mkpixmap(image.width, image.height, PIXELFORMAT, data)
        handle = Res.Resource(url)
        self.dict[url] = [1, handle, pixmap, data, image.width, image.height]
        return handle

    def get(self, name):
        [cnt, handle, pixmap, data, width, height] = self.dict[name]
        return width, height, pixmap

    def delete(self, name):
        self.dict[name][0] = self.dict[name][0] - 1
## Should do this optionally, i.e. on used memory
##         if self.dict[name][0] == 0:
##             del self.dict[name]

_gifkeeper = _Gifkeeper()
