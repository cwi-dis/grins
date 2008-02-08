__version__ = "$Id$"

import xmllib, string, re, os
import MMurl
import urlcache

error = 'realsupport.error'

import colors
# see SMILTreeRead for a more elaborate version
color = re.compile('#(?P<hex>[0-9a-fA-F]{3}|'           # #f00
                   '[0-9a-fA-F]{6})$')                  # #ff0000

class RTParser(xmllib.XMLParser):
    topelement = 'window'
    attributes = {
            'window': {'type':'generic',
                       'duration':None,
                       'endtime': None, # obsolete name for duration
                       'width':None,
                       'height':None,
                       'bgcolor':None,
                       'scrollrate':None,
                       'crawlrate':None,
                       'link':'blue',
                       'underline_hyperlinks':'true',
                       'wordwrap':'true',
                       'loop':'true',
                       'extraspaces':'use',},
            'time': {'begin':None,
                     'end':None,},
            'clear': {},
            'pos': {'x':'0',
                    'y':'0',},
            'tu': {'color':None,},
            'tl': {'color':None,},
            'p': {},
            'br': {},
            'ol': {},
            'ul': {},
            'li': {},
            'hr': {},
            'center': {},
            'pre': {},
            'b': {},
            'i': {},
            's': {},
            'u': {},
            'font': {'charset':'us-ascii',
                     'color':None,
                     'bgcolor':None, # obsolete name for color
                     'face':'Times New Roman',
                     'size':'+0',},
            'a': {'href':None,
                  'target':None,},
            'required': {},
            }
    __empty = []
    __all = ['time', 'clear', 'pos', 'tu', 'tl', 'p', 'br', 'ol', 'ul',
             'li', 'hr', 'center', 'pre', 'b', 'i', 's', 'u', 'font',
             'a', 'required', ]
    entities = {
            topelement: __all,
            'a': __all,
            'b': __all,
            'br': __empty,
            'center': __all,
            'clear': __empty,
            'font': __all,
            'hr': __empty,
            'i': __all,
            'li': __all,
            'ol': __all,
            'p': __all,
            'pos': __empty,
            'required': __all,
            's': __all,
            'time': __empty,
            'tl': __all,
            'tu': __all,
            'u': __all,
            'ul': __all,
            }

    def __init__(self, file = None, printfunc = None):
        self.elements = {
                'window': (self.start_window, None),
                }
        self.__file = file or '<unknown file>'
        self.__printdata = []
        self.__printfunc = printfunc
        xmllib.XMLParser.__init__(self, accept_unquoted_attributes = 1,
                                  accept_utf8 = 1, map_case = 1)

    def start_window(self, attributes):
        duration = attributes.get('duration') or attributes.get('endtime')
        if duration is None:
            duration = 60
        else:
            try:
                duration = decode_time(duration)
            except ValueError:
                self.syntax_error('badly formatted duration attribute')
                duration = 60
        type = string.lower(attributes.get('type'))
        if type in ('tickertape', 'marquee'):
            defwidth = 500
            defheight = 30
        else:
            defwidth = 320
            defheight = 180
        width = attributes.get('width')
        if width is None:
            width = defwidth
        else:
            try:
                width = string.atoi(string.strip(width))
            except string.atoi_error:
                self.syntax_error('badly formatted width attribute')
                width = defwidth
        height = attributes.get('height')
        if height is None:
            height = defheight
        else:
            try:
                height = string.atoi(string.strip(height))
            except string.atoi_error:
                self.syntax_error('badly formatted height attribute')
                height = defheight
        self.duration = duration
        self.width = width
        self.height = height

    def syntax_error(self, msg):
        if self.__printfunc is None:
            print 'Warning: syntax error in file %s, line %d: %s' % (self.__file, self.lineno, msg)
        else:
            self.__printdata.append('Warning: syntax error on line %d: %s' % (self.lineno, msg))

    def unknown_entityref(self, name):
        pass

    def close(self):
        xmllib.XMLParser.close(self)
        if self.__printfunc is not None and self.__printdata:
            data = string.join(self.__printdata, '\n')
            # first 30 lines should be enough
            data = string.split(data, '\n')
            if len(data) > 30:
                data = data[:30]
                data.append('. . .')
            self.__printfunc(string.join(data, '\n'))
            self.__printdata = []
        self.elements = None
        self.__printdata = None
        self.__printfunc = None

    # the rest is to check that the nesting of elements is done
    # properly
    def finish_starttag(self, tagname, attrdict, method):
        if len(self.stack) > 1:
            ptag = self.stack[-2][2]
            if tagname not in self.entities.get(ptag, ()):
                if not self.entities.get(ptag):
                    # missing close tag of empty element, just remove the entry from the stack
                    del self.stack[-2]
                else:
                    self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
        elif tagname != self.topelement:
            self.syntax_error('outermost element must be "%s"' % self.topelement)
        xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

    # special version that doesn't complain about missing end tags
    def finish_endtag(self, tag):
        self.literal = 0
        if not tag:
            xmllib.XMLParser.finish_endtag(self, tag)
            return
        else:
            found = -1
            for i in range(len(self.stack)):
                if tag == self.stack[i][0]:
                    found = i
            if found == -1:
                xmllib.XMLParser.finish_endtag(self, tag)
                return
        while len(self.stack) > found+1:
            nstag = self.stack[-1][2]
            method = self.elements.get(nstag, (None, None))[1]
            if method is not None:
                self.handle_endtag(nstag, method)
            else:
                self.unknown_endtag(nstag)
            del self.stack[-1]
        xmllib.XMLParser.finish_endtag(self, tag)

class RPParser(xmllib.XMLParser):
    topelement = 'imfl'
    attributes = {
            'head': {'aspect':'true',
                     'author':'',
                     'bitrate':None,
                     'copyright':'',
                     'duration':None,
                     'height':None,
                     'maxfps':None,
                     'preroll':None,
                     'timeformat':'milliseconds',
                     'title':'',
                     'url':None,
                     'width':None,},
            'image': {'handle':None,
                      'name':None,},
            'fill': {'color':None,
                     'grins_image_caption':'',
                     'dsth':'0',
                     'dstw':'0',
                     'dstx':'0',
                     'dsty':'0',
                     'start':None,},
            'fadein': {'aspect':None,
                       'grins_image_caption':'',
                       'dsth':'0',
                       'dstw':'0',
                       'dstx':'0',
                       'dsty':'0',
                       'duration':None,
                       'maxfps':None,
                       'srch':'0',
                       'srcw':'0',
                       'srcx':'0',
                       'srcy':'0',
                       'start':None,
                       'target':None,
                       'url':None,
                       'fadeout':None,
                       'fadeouttime':'0',
                       'fadeoutduration':'0',
                       'fadeoutcolor':'black',
                       'project_convert':'1',
                       },
            'fadeout': {'color':None,
                        'grins_image_caption':'',
                        'dsth':'0',
                        'dstw':'0',
                        'dstx':'0',
                        'dsty':'0',
                        'duration':None,
                        'maxfps':None,
                        'start':None,},
            'crossfade': {'aspect':None,
                          'grins_image_caption':'',
                          'dsth':'0',
                          'dstw':'0',
                          'dstx':'0',
                          'dsty':'0',
                          'duration':None,
                          'maxfps':None,
                          'srch':'0',
                          'srcw':'0',
                          'srcx':'0',
                          'srcy':'0',
                          'start':None,
                          'target':None,
                          'url':None,
                          'project_convert':'1',},
            'wipe': {'aspect':None,
                     'grins_image_caption':'',
                     'direction':None,
                     'dsth':'0',
                     'dstw':'0',
                     'dstx':'0',
                     'dsty':'0',
                     'duration':None,
                     'maxfps':None,
                     'srch':'0',
                     'srcw':'0',
                     'srcx':'0',
                     'srcy':'0',
                     'start':None,
                     'target':None,
                     'type':None,
                     'url':None,
                     'project_convert':'1',},
            'viewchange': {'dsth':'0',
                               'grins_image_caption':'',
                           'dstw':'0',
                           'dstx':'0',
                           'dsty':'0',
                           'duration':None,
                           'maxfps':None,
                           'srch':'0',
                           'srcw':'0',
                           'srcx':'0',
                           'srcy':'0',
                           'start':None,},
            }
    __empty = []
    entities = {
            topelement: ['head', 'image', 'fill', 'fadein', 'fadeout',
                         'crossfade', 'wipe', 'viewchange',],
            'head': __empty,
            'image': __empty,
            'fill': __empty,
            'fadein': __empty,
            'fadeout': __empty,
            'crossfade': __empty,
            'wipe': __empty,
            'viewchange': __empty,
            }

    def __init__(self, file = None, baseurl = '', printfunc = None):
        self.elements = {
                'head': (self.start_head, None),
                'image': (self.start_image, None),
                'fill': (self.start_fill, None),
                'fadein': (self.start_fadein, None),
                'fadeout': (self.start_fadeout, None),
                'crossfade': (self.start_crossfade, None),
                'wipe': (self.start_wipe, None),
                'viewchange': (self.start_viewchange, None),
                }
        self.tags = []
        self.__images = {}
        self.__file = file or '<unknown file>'
        self.__baseurl = baseurl
        self.__printdata = []
        self.__printfunc = printfunc
        self.__headseen = 0
        xmllib.XMLParser.__init__(self, accept_utf8 = 1)

    def close(self):
        xmllib.XMLParser.close(self)
        if not self.__headseen:
            raise error, 'Not a .rp file, no <head> tag'
        if self.__printfunc is not None and self.__printdata:
            data = string.join(self.__printdata, '\n')
            # first 30 lines should be enough
            data = string.split(data, '\n')
            if len(data) > 30:
                data = data[:30]
                data.append('. . .')
            self.__printfunc(string.join(data, '\n'))
            self.__printdata = []
        self.tags.sort(self.__tagsort)
        prevstart = 0
        for tag in self.tags:
            start = tag['start']
            tag['start'] = start - prevstart
            prevstart = start
        self.elements = None
        self.__images = None
        self.__printdata = None
        self.__printfunc = None

    def goahead(self, end):
        try:
            xmllib.XMLParser.goahead(self, end)
        except:
            import sys
            type, value, traceback = sys.exc_info()
            if self.__printfunc is not None:
                msg = 'Fatal error while parsing at line %d: %s' % (self.lineno, str(value))
                if self.__printdata:
                    data = string.join(self.__printdata, '\n')
                    # first 30 lines should be enough
                    data = string.split(data, '\n')
                    if len(data) > 30:
                        data = data[:30]
                        data.append('. . .')
                else:
                    data = []
                data.insert(0, msg)
                self.__printfunc(string.join(data, '\n'))
                self.__printdata = []
            raise           # re-raise

    def __tagsort(self, tag1, tag2):
        return cmp(tag1['start'], tag2['start'])

    def start_head(self, attributes):
        self.__headseen = 1
        self.timeformat = attributes['timeformat']
        duration = attributes.get('duration')
        if duration is None:
            self.syntax_error('required attribute duration missing in head element')
            duration = 0
        else:
            try:
                duration = decode_time(duration, self.timeformat)
            except ValueError:
                self.syntax_error('badly formatted duration attribute')
                duration = 0
        width = attributes.get('width')
        if width is None:
            self.syntax_error('required attribute width missing in head element')
            width = 256
        else:
            try:
                width = string.atoi(string.strip(width))
            except string.atoi_error:
                self.syntax_error('badly formatted width attribute')
                width = 256
        height = attributes.get('height')
        if height is None:
            self.syntax_error('required attribute height missing in head element')
            height = 256
        else:
            try:
                height = string.atoi(string.strip(height))
            except string.atoi_error:
                self.syntax_error('badly formatted height attribute')
                height = 256
        bitrate = attributes.get('bitrate')
        if bitrate is None:
            self.syntax_error('required attribute bitrate missing in head element')
            bitrate = 14400
        else:
            try:
                bitrate = string.atoi(string.strip(bitrate))
            except string.atoi_error:
                self.syntax_error('badly formatted bitrate attribute')
                bitrate = 14400
        self.duration = duration
        self.width = width
        self.height = height
        self.bitrate = bitrate
        self.aspect = string.lower(attributes['aspect'])
        self.author = attributes.get('author')
        self.copyright = attributes.get('copyright')
        self.maxfps = self.__maxfps(attributes)
        preroll = attributes.get('preroll')
        if preroll is not None:
            try:
                preroll = decode_time(preroll, self.timeformat)
            except ValueError:
                self.syntax_error('badly formatted preroll attribute')
                preroll = 0
        self.preroll = preroll
        self.title = attributes.get('title')
        self.url = attributes.get('url')

    def start_image(self, attributes):
        handle = attributes.get('handle')
        name = attributes.get('name')
        if handle is None or name is None:
            self.syntax_error("required attribute `name' and/or `handle' missing")
            return
        if self.__images.has_key(handle):
            self.syntax_error("image `handle' not unique")
            return
        self.__images[handle] = MMurl.basejoin(self.__baseurl, name)

    def start_fill(self, attributes):
        destrect = self.__rect('dst', attributes)
        color = self.__color('color', attributes)
        start = self.__time('start', attributes)
        self.tags.append({'tag': 'fill',
                          'caption': attributes.get('grins_image_caption', ''),
                          'color': color,
                          'subregionxy': destrect[:2],
                          'subregionwh': destrect[2:],
                          'subregionanchor': 'top-left',
                          'start': start,
                          'displayfull': destrect == (0,0,0,0)})

    def start_fadein(self, attributes):
        self.__fadein_or_crossfade_or_wipe('fadein', attributes)

    def start_fadeout(self, attributes):
        destrect = self.__rect('dst', attributes)
        color = self.__color('color', attributes)
        start = self.__time('start', attributes)
        duration = self.__time('duration', attributes)
        maxfps = self.__maxfps(attributes)
        self.tags.append({'tag': 'fadeout',
                          'caption': attributes.get('grins_image_caption', ''),
                          'color': color,
                          'subregionxy': destrect[:2],
                          'subregionwh': destrect[2:],
                          'subregionanchor': 'top-left',
                          'start': start,
                          'tduration': duration,
                          'maxfps': maxfps,
                          'displayfull': destrect == (0,0,0,0)})

    def start_crossfade(self, attributes):
        self.__fadein_or_crossfade_or_wipe('crossfade', attributes)

    def start_wipe(self, attributes):
        self.__fadein_or_crossfade_or_wipe('wipe', attributes)

    def start_viewchange(self, attributes):
        duration = self.__time('duration', attributes)
        maxfps = self.__maxfps(attributes)
        dstrect = self.__rect('dst', attributes)
        srcrect = self.__rect('src', attributes)
        start = self.__time('start', attributes)
        self.tags.append({'tag': 'viewchange',
                          'caption': attributes.get('grins_image_caption', ''),
                          'imgcropxy': srcrect[:2],
                          'imgcropwh': srcrect[2:],
                          'imgcropanchor': 'top-left',
                          'fullimage': srcrect == (0,0,0,0),
                          'subregionxy': dstrect[:2],
                          'subregionwh': dstrect[2:],
                          'subregionanchor': 'top-left',
                          'start': start,
                          'tduration': duration,
                          'maxfps': maxfps,
                          'displayfull': dstrect == (0,0,0,0)})

    def __fadein_or_crossfade_or_wipe(self, tag, attributes):
        aspect = (attributes.get('aspect', self.aspect) == 'true')
        dstrect = self.__rect('dst', attributes)
        duration = self.__time('duration', attributes)
        maxfps = self.__maxfps(attributes)
        srcrect = self.__rect('src', attributes)
        start = self.__time('start', attributes)
        target = attributes.get('target')
        if target is None:
            # allow missing target for data: URLs
            if self.__file[:5] != 'data:':
                self.syntax_error("required attribute `target' missing")
        elif not self.__images.has_key(target):
            self.syntax_error("unknown `target' attribute")
        url = attributes.get('url')
        try:
            convert = string.atoi(attributes.get('grins_convert', '1'))
        except string.atoi_error:
            self.syntax_error("attribute `grins_convert' is not an integer" % str)
            convert = 1
        attrs = {'tag': tag,
                 'caption': attributes.get('grins_image_caption', ''),
                 'project_convert': convert,
                 'file': self.__images.get(target),
                 'imgcropxy': srcrect[:2],
                 'imgcropwh': srcrect[2:],
                 'imgcropanchor': 'top-left',
                 'fullimage': srcrect == (0,0,0,0),
                 'subregionxy': dstrect[:2],
                 'subregionwh': dstrect[2:],
                 'subregionanchor': 'top-left',
                 'aspect': aspect,
                 'start': start,
                 'tduration': duration,
                 'maxfps': maxfps,
                 'href': url,
                 'displayfull': dstrect == (0,0,0,0)}
        if tag == 'wipe':
            type = attributes.get('type')
            if type is None:
                self.syntax_error("required attributes `type' missing")
            elif type not in ('push', 'normal'):
                self.syntax_error("unknown `type' attribute")
                type = None
            if type is None: # provide default
                type = 'normal'
            attrs['wipetype'] = type
            direction = attributes.get('direction')
            if direction is None:
                self.syntax_error("required attributes `direction' missing")
            elif direction not in ('left', 'right', 'down', 'up'):
                self.syntax_error("unknown `direction' attribute")
                direction = None
            if direction is None: # provide default
                direction = 'left'
            attrs['direction'] = direction
        elif tag == 'fadein' and attributes.get('fadeout', 'false') == 'true':
            attrs['fadeout'] = 1
            attrs['fadeouttime'] = self.__time('fadeouttime', attributes)
            attrs['fadeoutduration'] = self.__time('fadeoutduration', attributes)
            attrs['fadeoutcolor'] = self.__color('fadeoutcolor', attributes)
        self.tags.append(attrs)

    def __rect(self, str, attributes):
        x = attributes.get(str+'x', '0')
        y = attributes.get(str+'y', '0')
        h = attributes.get(str+'h', '0')
        w = attributes.get(str+'w', '0')
        try:
            x = string.atoi(x)
        except string.atoi_error:
            self.syntax_error("attribute `%sx' is not an integer" % str)
            x = 0
        try:
            y = string.atoi(y)
        except string.atoi_error:
            self.syntax_error("attribute `%sy' is not an integer" % str)
            y = 0
        try:
            w = string.atoi(w)
        except string.atoi_error:
            self.syntax_error("attribute `%sw' is not an integer" % str)
            w = 0
        try:
            h = string.atoi(h)
        except string.atoi_error:
            self.syntax_error("attribute `%sh' is not an integer" % str)
            h = 0
        return x, y, w, h

    # see SMILTreeRead.SMILParser.__convert_color for a more
    # elaborate version
    def __color(self, attr, attributes):
        val = attributes.get(attr)
        if val is None:
            return
        val = string.lower(val)
        if colors.colors.has_key(val):
            return colors.colors[val]
        res = color.match(val)
        if res is None:
            self.syntax_error('bad color specification')
            return
        else:
            hex = res.group('hex')
            if len(hex) == 3:
                r = string.atoi(hex[0]*2, 16)
                g = string.atoi(hex[1]*2, 16)
                b = string.atoi(hex[2]*2, 16)
            else:
                r = string.atoi(hex[0:2], 16)
                g = string.atoi(hex[2:4], 16)
                b = string.atoi(hex[4:6], 16)
        return r, g, b

    def __time(self, attr, attributes):
        time = attributes.get(attr)
        if time is None:
            self.syntax_error("required attributes `%s' missing" % attr)
            return 0
        try:
            time = decode_time(time, self.timeformat)
        except ValueError, msg:
            self.syntax_error(msg)
            return 0
        return time

    def __maxfps(self, attributes):
        maxfps = attributes.get('maxfps')
        if maxfps is not None:
            try:
                maxfps = string.atoi(maxfps)
            except string.atoi_error:
                self.syntax_error('badly formatted maxfps attribute')
                maxfps = None
        return maxfps

    def syntax_error(self, msg):
        if self.__printfunc is None:
            print 'Warning: syntax error in file %s, line %d: %s' % (self.__file, self.lineno, msg)
        else:
            self.__printdata.append('Warning: syntax error on line %d: %s' % (self.lineno, msg))

    def unknown_entityref(self, name):
        pass

    # the rest is to check that the nesting of elements is done
    # properly (i.e. according to the SMIL DTD)
    def finish_starttag(self, tagname, attrdict, method):
        if len(self.stack) > 1:
            ptag = self.stack[-2][2]
            if tagname not in self.entities.get(ptag, ()):
                self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
        elif tagname != self.topelement:
            self.syntax_error('outermost element must be "%s"' % self.topelement)
        xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

coordnames = 'x','y','w','h'
def writecoords(f, str, full, xy, wh, anchor):
    if full:
        coords = (0,0,0,0)
    else:
        if anchor == 'top-left':
            pass
        elif anchor == 'center-left':
            xy = xy[0], xy[1]-wh[1]/2
        elif anchor == 'bottom-left':
            xy = xy[0], xy[1]-wh[1]
        elif anchor == 'top-center':
            xy = xy[0]-wh[0]/2, wh[1]
        elif anchor == 'center':
            xy = xy[0]-wh[0]/2, xy[1]-wh[1]/2
        elif anchor == 'bottom-center':
            xy = xy[0]-wh[0]/2, xy[1]-wh[1]
        elif anchor == 'top-right':
            xy = xy[0]-wh[0], wh[1]
        elif anchor == 'center-right':
            xy = xy[0]-wh[0], xy[1]-wh[1]/2
        elif anchor == 'bottom-right':
            xy = xy[0]-wh[0], xy[1]-wh[1]
        coords = xy + wh

    for i in range(4):
        c = coords[i]
        if c != 0:
            f.write(' %s%s="%d"' % (str, coordnames[i], c))


def _writeFadeout(f, start, attrs, bgcolor):
    color = attrs.get('fadeoutcolor', bgcolor)
    if colors.rcolors.has_key(color):
        color = colors.rcolors[color]
    else:
        color = '#%02x%02x%02x' % color
    duration = attrs.get('fadeoutduration',0)
    f.write('  <fadeout start="%g" duration="%g" color="%s"' %
            (start, duration, color))
    writecoords(f, 'dst', attrs.get('displayfull', 1),
                attrs.get('subregionxy', (0,0)),
                attrs.get('subregionwh', (0,0)),
                attrs.get('subregionanchor', 'top-left'))
    maxfps = attrs.get('maxfps')
    if maxfps is not None:
        f.write(' maxfps="%d"' % maxfps)
    f.write('/>\n')

def _calcdur(tags):
    start = 0
    duration = 0
    endtime = 0
    for attrs in tags:
        start = start + attrs.get('start', 0)
        tag = attrs.get('tag', 'fill')
        if tag != 'fill':
            duration = attrs.get('tduration', 0)
        else:
            duration = 0
        if tag == 'fadein' and attrs.get('fadeout', 0):
            t = start + duration + attrs.get('fadeouttime', 0)
            d = attrs.get('fadeoutduration', 0)
            if t + d > endtime:
                endtime = t + d
        if start + duration > endtime:
            endtime = start + duration
    return endtime

def writeRP(rpfile, rp, node, savecaptions=0, tostring = 0, baseurl = None, silent = 0):
    from nameencode import nameencode
    import MMAttrdefs

    bgcolor = MMAttrdefs.getattr(node, 'bgcolor')
    ctx = node.GetContext()
    if baseurl is None:
        baseurl = MMurl.canonURL(ctx.findurl(MMAttrdefs.getattr(node, 'file')))
    i = string.rfind(baseurl, '/')
    if i >= 0:
        baseurl = baseurl[:i+1] # everything up to and including last /
    else:
        baseurl = ''            # no slashes

    if tostring:
        from StringIO import StringIO
        f = StringIO()
    else:
        f = open(rpfile, 'w')
    f.write('<imfl>\n')
    f.write('  <head')
    sep = ' '
    if rp.title:
        f.write(sep+'title=%s' % nameencode(rp.title))
        sep = '\n        '
    if rp.author:
        f.write(sep+'author=%s' % nameencode(rp.author))
        sep = '\n        '
    if rp.copyright:
        f.write(sep+'copyright=%s' % nameencode(rp.copyright))
        sep = '\n        '
    f.write(sep+'timeformat="dd:hh:mm:ss.xyz"')
    sep = '\n        '
    endtime = _calcdur(rp.tags)
    if rp.duration and rp.duration < endtime and not silent:
        import windowinterface
        windowinterface.showmessage('Duration for RealPix node %s on channel %s too short to accomodate all transitions\n(duration = %g, required: %g)' % (MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName(), rp.duration, endtime), mtype = 'warning')
        node.set_infoicon('error', 'Duration too short to accomodate all transitions\n(duration = %g, required: %g)' % (rp.duration, endtime))
    elif not rp.duration and not endtime and not silent:
        import windowinterface
        windowinterface.showmessage('No durations set for RealPix node %s on channel %s\nDocument may not play' % (MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName()))
        node.set_infoicon('error', 'No durations set.')
    f.write(sep+'duration="%g"' % (rp.duration or endtime))
    f.write(sep+'bitrate="%d"' % rp.bitrate)
    f.write(sep+'width="%d"' % rp.width)
    f.write(sep+'height="%d"' % rp.height)
    defaspect = (rp.aspect == 'true')
    if not defaspect:
        f.write(sep+'aspect="false"')
    if rp.preroll is not None:
        f.write(sep+'preroll="%g"' % rp.preroll)
    if rp.url:
        f.write(sep+'url=%s' % nameencode(rp.url))
    if rp.maxfps is not None:
        f.write(sep+'maxfps="%d"' % rp.maxfps)
    f.write('/>\n')
    images = {}
    handle = 0
    for attrs in rp.tags:
        if attrs.get('tag', 'fill') in ('fadein', 'crossfade', 'wipe'):
            file = attrs.get('file')
            if not file or images.has_key(file):
                continue
            url = MMurl.canonURL(ctx.findurl(file))
            if url[:len(baseurl)] == baseurl:
                url = url[len(baseurl):]
            # This is a bit of a hack. G2 appears to want its URLs
            # without %-style quoting.
            url = MMurl.unquote(url)
            handle = handle + 1
            images[file] = handle, url
    for handle, name in images.values():
        f.write('  <image handle="%d" name=%s/>\n' % (handle, nameencode(name)))
    if not tostring and bgcolor is not None and bgcolor != (0,0,0):
        if rp.tags:
            # only write extra fill if first tag is not a fill starting at 0 which
            # fills the whole region
            attrs = rp.tags[0]
            extrafill = attrs.get('tag', 'fill') != 'fill' or attrs.get('start', 0) != 0 or attrs.get('subregionxy', (0,0)) != (0,0) or attrs.get('subregionwh', (0,0)) != (0,0)
        else:
            extrafill = 1
        if extrafill:
            if colors.rcolors.has_key(bgcolor):
                color = colors.rcolors[bgcolor]
            else:
                color = '#%02x%02x%02x' % bgcolor
            f.write('  <fill start="0" color="%s"/>\n' % color)
    start = 0
    duration = 0
    fadeouts = []
    for attrs in rp.tags:
        start = start + attrs.get('start', 0)
        while fadeouts:
            t, a = fadeouts[0]
            if t > start:
                break
            del fadeouts[0]
            _writeFadeout(f, t, a, bgcolor)
        tag = attrs.get('tag', 'fill')
        f.write('  <%s' % tag)
        f.write(' start="%g"' % start)
        if tag != 'fill':
            duration = attrs.get('tduration', 0)
            f.write(' duration="%g"' % duration)
        else:
            duration = 0
        if tag in ('fill', 'fadeout'):
            color = attrs.get('color', bgcolor)
            if colors.rcolors.has_key(color):
                color = colors.rcolors[color]
            else:
                color = '#%02x%02x%02x' % color
            f.write(' color="%s"' % color)
        else:
            if tag != 'viewchange':
                file = attrs.get('file')
                if file:
                    f.write(' target="%d"' % images[file][0])
##                 else:
##                     # file attribute missing
                aspect = attrs.get('aspect', defaspect)
                if aspect != defaspect:
                    f.write(' aspect="%s"' % ['false','true'][aspect])
                url = attrs.get('href')
                if url:
                    f.write(' url=%s' % nameencode(url))
            writecoords(f, 'src', attrs.get('fullimage', 1),
                        attrs.get('imgcropxy', (0,0)),
                        attrs.get('imgcropwh', (0,0)),
                        attrs.get('imgcropanchor', 'top-left'))
        if tag == 'wipe':
            direction = attrs.get('direction', 'left')
            f.write(' direction="%s"' % direction)
            wipetype = attrs.get('wipetype', 'normal')
            f.write(' type="%s"' % wipetype)
        writecoords(f, 'dst', attrs.get('displayfull', 1),
                    attrs.get('subregionxy', (0,0)),
                    attrs.get('subregionwh', (0,0)),
                    attrs.get('subregionanchor', 'top-left'))
        if tag != 'fill':
            maxfps = attrs.get('maxfps')
            if maxfps is not None:
                f.write(' maxfps="%d"' % maxfps)
        if savecaptions:
            caption = attrs.get('caption', '')
            if caption:
                f.write(' grins_image_caption=%s'%nameencode(caption))
        if tostring and tag == 'fadein' and attrs.get('fadeout',0):
            f.write(' fadeout="true"')
            f.write(' fadeouttime="%g"' % attrs.get('fadeouttime',0))
            f.write(' fadeoutduration="%g"' % attrs.get('fadeoutduration',0))
            color = attrs.get('fadeoutcolor', bgcolor)
            if colors.rcolors.has_key(color):
                color = colors.rcolors[color]
            else:
                color = '#%02x%02x%02x' % color
            f.write(' fadeoutcolor="%s"' % color)
        f.write('/>\n')
        if not tostring and tag == 'fadein' and attrs.get('fadeout',0):
            t = start+duration+attrs.get('fadeouttime',0)
            for i in range(len(fadeouts)):
                if t < fadeouts[i][0]:
                    fadeouts.insert(i, (t, attrs))
                    break
            else:
                fadeouts.append((t, attrs))
    for start, a in fadeouts:
        _writeFadeout(f, start, a, bgcolor)
    f.write('</imfl>\n')
    if tostring:
        # must call getvalue *before* closing the StringIO instance
        data = f.getvalue()
        f.close()
        return data
    f.close()
    if os.name == 'mac':
        import macfs
        import macostools
        fss = macfs.FSSpec(rpfile)
        fss.SetCreatorType('PNst', 'PNRA')
        macostools.touched(fss)

def writeRT(file, rp, node):
    # no size specified, initialize with channel size
    # XXXX Note: incorrect if units are something else than pixels
    ch = node.GetChannel(attrname='captionchannel')
    width, height = ch.get('base_winoff',(0,0,320,180))[2:4]

    color = node.GetAttrDef('bgcolor', ch.get('bgcolor', (0,0,0)))
    f = open(file, 'w')
    f.write('<window width="%d" height="%d"' % (int(width), int(height)))
    dur = rp.duration or _calcdur(rp.tags)
    f.write(' duration="%g"' % dur)
    if color != (255,255,255):
        if colors.rcolors.has_key(color):
            color = colors.rcolors[color]
        else:
            color = '#%02x%02x%02x' % color
        f.write(' bgcolor="%s"' % color)
    f.write('>\n')
    curtime = 0
    for rpslide in rp.tags:
        curtime = curtime + rpslide.get('start', 0)
        caption = rpslide.get('caption', '')
        if caption:
            f.write('<time begin="%d">\n'%curtime)
            f.write(caption)
            if caption[-1] != '\n':
                f.write('\n')
    f.write('</window>\n')
    f.close()
    if os.name == 'mac':
        import macfs
        import macostools
        fss = macfs.FSSpec(file)
        fss.SetCreatorType('PNst', 'PNRA')
        macostools.touched(fss)


durre = re.compile(r'\s*(?:(?P<days>\d+):(?:(?P<hours>\d+):(?:(?P<minutes>\d+):)?)?)?(?P<seconds>\d+(\.\d+)?)\s*')

def decode_time(str, fmt = 'dd:hh:mm:ss.xyz'):
    if fmt == 'milliseconds':
        try:
            ms = string.atoi(str)
        except string.atoi_error:
            raise ValueError('badly formatted duration string')
        return ms / 1000.0      # convert milliseconds to seconds
    res = durre.match(str)
    if res is None:
        raise ValueError('badly formatted duration string')
    days, hours, minutes, seconds = res.group('days', 'hours', 'minutes', 'seconds')
    if days is None:
        days = 0
    else:
        days = string.atoi(days, 10)
    if hours is None:
        hours = 0
    else:
        hours = string.atoi(hours, 10)
    hours = hours + 24 * days
    if minutes is None:
        minutes = 0
    else:
        minutes = string.atoi(minutes, 10)
    minutes = minutes + 60 * hours
    seconds = string.atof(seconds)
    return seconds + 60 * minutes

def rmff(url, fp):
    from chunk import Chunk
    import struct
    info = {}
    size, object_version = struct.unpack('>lh', fp.read(6))
    if object_version != 0 and object_version != 1:
        print '%s: unknown .RMF version' % url
        return info
    else:
        file_version, num_headers = struct.unpack('>ll', fp.read(8))
    for i in range(num_headers):
        chunk = Chunk(fp, align = 0, inclheader = 1)
        name = chunk.getname()
        if name == 'PROP':
            object_version = struct.unpack('>h', chunk.read(2))[0]
            if object_version != 0:
                print '%s: unknown PROP version' % url
            else:
                max_bit_rate, avg_bit_rate, max_packet_size, avg_packet_size, num_packets, duration, preroll, index_offset, data_offset, num_streams, flags = struct.unpack('>lllllllllhh', chunk.read(40))
                info['duration'] = float(duration)/1000
                info['bitrate'] = avg_bit_rate
                info['max_bit_rate'] = max_bit_rate
                info['avg_bit_rate'] = avg_bit_rate
        elif name == 'MDPR':
            object_version = struct.unpack('>h', chunk.read(2))[0]
            if object_version != 0:
                print '%s: unknown MDPR version' % url
            else:
                stream_number, max_bit_rate, avg_bit_rate, max_packet_size, avg_packet_size, start_time, preroll, duration, stream_name_size = struct.unpack('>hlllllllb', chunk.read(31))
                if stream_name_size > 0:
                    stream_name = chunk.read(stream_name_size)
                else:
                    stream_name = ''
                mime_type_size = struct.unpack('>b', chunk.read(1))[0]
                if mime_type_size > 0:
                    mime_type = chunk.read(mime_type_size)
                else:
                    mime_type = ''
                type_specific_len = struct.unpack('>l', chunk.read(4))[0]
                if type_specific_len > 0:
                    type_specific_data = chunk.read(type_specific_len)
                else:
                    type_specific_data = ''
                if mime_type == 'video/x-pn-realvideo' and \
                   type_specific_len >= 34:
                    width, height = struct.unpack('>hh', type_specific_data[12:16])
                    info['width'] = width
                    info['height'] = height
        elif name == 'CONT':
            object_version = struct.unpack('>h', chunk.read(2))[0]
            if object_version != 0:
                print '%s: unknown CONT version' % url
            else:
                title_len = struct.unpack('>h', chunk.read(2))[0]
                title = chunk.read(title_len)
                author_len = struct.unpack('>h', chunk.read(2))[0]
                if author_len > 0:
                    author = chunk.read(author_len)
                else:
                    author = ''
                copyright_len = struct.unpack('>h', chunk.read(2))[0]
                if copyright_len > 0:
                    copyright = chunk.read(copyright_len)
                else:
                    copyright = ''
                comment_len = struct.unpack('>h', chunk.read(2))[0]
                if comment_len > 0:
                    comment = chunk.read(comment_len)
                else:
                    comment = ''
        elif name == 'DATA':
            break           # we've seen enough
##             object_version = struct.unpack('>h', chunk.read(2))[0]
##             if object_version != 0:
##                 print '%s: unknown DATA version' % url
##             else:
##                 num_packets, next_data_header = struct.unpack('>ll', chunk.read(8))
        elif name == 'INDX':
            object_version = struct.unpack('>h', chunk.read(2))[0]
            if object_version != 0:
                print '%s: unknown INDX version' % url
            else:
                num_indices, stream_number, next_index_header = struct.unpack('>lhl', chunk.read(10))
        chunk.close()
    return info

def getinfo(url, fp = None, printfunc = None):
    cache = urlcache.urlcache[url]
    if cache.has_key('RMinfo'):
        return cache['RMinfo']
    if fp is None:
        try:
            fp = MMurl.urlopen(url)
        except:
            cache['RMinfo'] = info = {}
            return info
    head = fp.read(4)
    if head == '<imf':
        # RealPix
        rp = RPParser(url, printfunc = printfunc)
        rp.feed(head)
        rp.feed(fp.read())
        rp.close()
        info = {'width': rp.width,
                'height': rp.height,
                'duration': rp.duration or _calcdur(rp.tags),
                'bitrate': rp.bitrate,}
    elif string.lower(head) == '<win':
        # RealText
        rp = RTParser(url, printfunc = printfunc)
        rp.feed(head)
        rp.feed(fp.read())
        rp.close()
        info = {'width': rp.width,
                'height': rp.height,
                'duration': rp.duration,}
    elif head == '.RMF':
        # RealMedia
        info = rmff(url, fp)
    elif head == '.ra\375':
        # RealAudio
        import struct
        info = {}
        data = fp.read(32)
        if data[:2] == '\000\004':
            # version 4 RealAudio
            # number of encoded bytes, bytes per minute
            nbytes, bpm = struct.unpack('>ii', data[8:8+8])
            info['duration'] = nbytes * 60. / bpm
            info['bitrate'] = int(bpm / 60. * 8 + .5)
    elif head[:3] == 'FWS':
        import swfparser
        info = swfparser.swfparser(url, fp)
    else:
        # unknown format
        info = {}
    fp.close()
    cache['RMinfo'] = info
    return info
