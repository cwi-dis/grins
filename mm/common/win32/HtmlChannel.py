__version__ = "$Id$"

#
# WIN32 HTML channel.
#

# @win32doc|HtmlChannel
# The HtmlChannel extends the ChannelWindow

# For this channel to work the window
# must support beyond the standard interface
# the following interface:

# interface IHtmlWnd:
#       def RetrieveUrl(self,url):pass
#       def DestroyHtmlCtrl(self):pass
#       def SetBackColor(self,clr):pass
#       def SetImmHtml(self,str):pass
#       def setanchorcallback(self,cbanchor):pass

# The window or an agent of the window is supposed
# to call back the HtmlChannel's callback set by
# the setanchorcallback method when a cmif: anchor
# is fired.

# The _SubWindow defined in lib/win32/_CmifView.py
# supports this interface

# Note:
# For not local files we get the url by calling
# the channel's method getfileurl(node) and pass
# it directly through RetrieveUrl.
# For local files we follow the Internet Explorer
# convention of passing the absolute local filename
# through RetrieveUrl.

import Channel

# node attributes
import MMAttrdefs

# url parsing
import os, ntpath, urllib, MMurl, urlparse

import sys, string
#import WMEVENTS

import windowinterface
import win32ui,win32con

import parsehtml

class error(Exception):
    pass

class HtmlChannel(Channel.ChannelWindow):
    chan_attrs = Channel.ChannelWindow.chan_attrs + ['fgcolor']

    def __init__(self, name, attrdict, scheduler, ui):
        self.played_str = ()
        self.__errors=[]
        self.__armed=0
        self.__which_control = None
        # release any resources on exit
        windowinterface.addclosecallback(self.release_res,())

        Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

    def __repr__(self):
        return '<HtmlChannel instance, name=' + `self._name` + '>'

    def do_hide(self):
        if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
            self.window.DestroyHtmlCtrl()
        Channel.ChannelWindow.do_hide(self)

    def destroy(self):
        if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
            self.window.DestroyHtmlCtrl()
            self.window.setredrawfunc(None)
        Channel.ChannelWindow.destroy(self)

    def mustreshow(self):
        # Return true if control setting changed
        import settings
        if self.__which_control == settings.get('html_control'):
            return 0
        return 1

    def release_res(self):
        if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
            self.window.DestroyHtmlCtrl()

    def do_arm(self, node, same=0):
        if node.type != 'ext':
            self.armed_str = self.getstring(node)
        else:
            self.armed_str = None
        anchors = {}
        for c in node.GetSchedChildren():
            if c.GetType() != 'anchor':
                continue
            fragment = MMAttrdefs.getattr(c, 'fragment')
            if not fragment:
                continue
            if anchors.has_key(fragment):
                print 'fragment',fragment,'used in multiple anchors'
                # ignore all but first
            else:
                anchors[fragment] = c.GetUID()
        if anchors:
            if self.armed_str is None:
                self.armed_str = self.getstring(node)
            parser = parsehtml.Parser(anchors)
            parser.feed(self.armed_str)
            self.armed_str = parser.close()
        self.armed_url=self.getfileurl(node)
        # XXXX Should we check that the URL is non-empty?
        self.__armed=0
        if self.window:
            self.window.CreateOSWindow(html=1)
            if not self.window.HasHtmlCtrl():
                import settings
                self.__which_control = settings.get('html_control')
                # IE:0 or WEBSTER:1
                if not self.__which_control:
                    self.__which_control = 0
                try:
                    self.window.CreateHtmlCtrl(which = self.__which_control)
                except:
                    msg = "Could not create HTML Browser control.\nCheck that the browser control you have selected is installed."
                    self.errormsg(None, msg)
                else:
                    self.__arm(node)
        return 1

    def do_play(self, node, curtime):
        # set play state information
        # for functions related to cmif anchors
        self.played_url = self.url = self.armed_url
        self.played_str = self.armed_str
        self.play_node=node
        self.window.setanchorcallback(self.cbanchor)

        # set colors
        bg = self.played_display._bgcolor
        #self.window.SetBackColor(windowinterface.RGB(bg))

        if not self.__armed:self.__arm(node)
        if not self.window.HasHtmlCtrl():
            print 'Warning: Failed to create Html control'


    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
#               if self.window:
#                       self.window.SetImmHtml(' ')
        if self.window:
            self.window.DestroyOSWindow()
            self.window.setredrawfunc(None)
        Channel.ChannelWindow.stopplay(self, node, curtime)


    def __arm(self,node):
        if self.armed_str is not None:
            self.window.SetImmHtml(self.armed_str)
        else:
            import settings
            url = MMurl.canonURL(self.getfileurl(node))
            if not settings.get('html_control'):
                url=urllib.unquote(url)
            self.window.RetrieveUrl(url)
        self.__armed=1

#################################
    def defanchor(self, node, anchor, cb):
        # Anchors don't get edited in the HtmlChannel.  You
        # have to edit the text to change the anchor.  We
        # don't want a message, though, so we provide our own
        # defanchor() method.
        apply(cb, (anchor,))

    def cbanchor(self, href):
        if href[:5] != 'cmif:':
            self.www_jump(href, 'GET', None, None)
            return
        self.cbcmifanchor(href, None)

    def cbform(self, widget, userdata, calldata):
        if widget != self.htmlw:
            raise 'kaboo kaboo'
        href = calldata.href
        list = map(lambda a,b: (a,b),
                   calldata.attribute_names, calldata.attribute_values)
        if not href or href[:5] != 'cmif:':
            self.www_jump(href, calldata.method,
                          calldata.enctype, list)
            return
        self.cbcmifanchor(href, list)

    def cbcmifanchor(self, href, list):
        # Workaround for something that turns "cmif:xx" anchors
        # into "cmif:///xx" anchors
        if href[:8] == "cmif:///":
            uid = href[8:]
        else:
            uid = href[5:]
        try:
            node = self.play_node.GetContext().mapuid(uid)
        except:
            self.errormsg(self.play_node, 'Unknown anchor: '+uid)
            return
        # XXX we're losing the list arg here
        self.onclick(node)

    #
    # The stuff below has little to do with CMIF per se, it implements
    # a general www browser
    #
    def www_jump(self, href, method, enctype, list):
        #
        # Check that we understand what is happening
        if enctype is not None:
            print 'HtmlChannel: unknown enctype:', enctype
            return
        if method not in (None, 'GET'):
            print 'HtmlChannel: unknown method:', method
            print 'href:', href
            print 'method:', method
            print 'enctype:', enctype
            print 'list:', list
            return
        if href:
            if href[:6] == 'about:':
                return
            if href[:4] == 'res:':
                return
            if href == 'XXXX:play/node':
                self.htmlw.insert_html(self.played_str, self.played_url)
                self.url = self.played_url
                return
            href = MMurl.basejoin(self.url, href)
        else:
            href = self.url
        if list:
            href = addquery(href, list)
        utype, host, path, params, query, tag = urlparse.urlparse(href)
        self.url = urlparse.urlunparse((utype, host, path, params, query, ''))
        # XXXX do something with the tag
        u = None
        try:
            u = MMurl.urlopen(self.url)
## Old code:
##             if u.headers.maintype == 'image':
##                 newtext = '<IMG SRC="%s">\n' % self.url
##             else:
##                 newtext = u.read()
## New code:
            if __debug__: print 'DBG: u.headers.type:', u.headers.type
            if u.headers.type != 'text/html':
                import Hlinks
                anchor = self.url
                if tag:
                    anchor = anchor + '#' + tag
                self._player.toplevel.waspaused = 0
                self._player.toplevel.jumptoexternal(anchor, Hlinks.TYPE_JUMP)
                return
            newtext = u.read()
        except IOError:
            newtext = '<H1>Cannot Open</H1><P>'+ \
                      'Cannot open '+self.url+':<P>'+ \
                      `(sys.exc_type, sys.exc_value)`+ \
                      '<P>\n'
        if u is not None:
            u.close()
        footer = '<HR>[<A HREF="XXXX:play/node">BACK</A> to CMIF node]'
        self.htmlw.insert_html(newtext+footer, self.url)
##         self.htmlw.footerText = '<P>[<A HREF="'+self.armed_url+\
##               '">BACK</A> to CMIF node]<P>'


def addquery(href, list):
    if not list: return href
    if len(list) == 1 and list[0][0] == 'isindex':
        query = encodestring(list[0][1])
    else:
        list = map(encodequery, list)
        list = map(lambda x:x[0]+'='+x[1], list)
        query = string.joinfields(list, '&')
    href = href + '?' + query
    return href

def encodequery(query):
    name, value = query
    name = encodestring(name)
    value = encodestring(value)
    return (name, value)

def encodestring(s):
    return MMurl.quote(s or '')     # Catches None as well!
