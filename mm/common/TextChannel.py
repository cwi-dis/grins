__version__ = "$Id$"

from Channel import ChannelWindow, error
import string
import StringStuff
import MMAttrdefs
import os
import re

class TextChannel(ChannelWindow):
    chan_attrs = ChannelWindow.chan_attrs + ['fgcolor']

    def do_arm(self, node, same=0):
        if same and self.armed_display:
            return 1
        fgcolor = self.getfgcolor(node)
        try:
            str = self.getstring(node)
        except error, arg:
            self.errormsg(node, arg)
            str = ''
        parlist = extract_paragraphs(str)
        taglist = extract_taglist(parlist)
        fontspec = getfont(node)
        fontname, pointsize = mapfont(fontspec)
        baseline, fontheight, pointsize = \
                  self.armed_display.setfont(fontname, pointsize)
        margin = self.armed_display.strsize('m')[0] / 2
        width = 1.0 - 2 * margin
        curlines, partoline, linetopar = StringStuff.calclines(
                parlist, self.armed_display.strsize, width)
        self.armed_display.setpos(margin, baseline)
        buttons = []
        # write the text on the window.
        # The loop is executed once for each anchor defined
        # in the text.  pline and pchar specify how far we got
        # with printing.
        # If there is only one anchor and this anchor contains
        # all text, then draw a button the size of the whole
        # channel.
        if len(taglist) == 1:
            par0, chr0, par1, chr1, name, type, times, access = taglist[0]
            if par0 == 0 and chr0 == 0 and \
               par1 == len(parlist)-1 and chr1 == len(parlist[-1]):
                taglist = []
                buttons.append((name, (0.0,0.0,1.0,1.0), type, times))
        pline, pchar = 0, 0
        for (par0, chr0, par1, chr1, name, type, times, access) in taglist:
            # first convert paragraph # and character #
            # to line and character.
            line0, char0 = map_parpos_to_linepos(par0, \
                      chr0, 0, curlines, partoline)
            line1, char1 = map_parpos_to_linepos(par1, \
                      chr1, 1, curlines, partoline)
            if (line0, char0) >= (line1, char1):
                print 'Anchor without screenspace:', name
                continue
            # write everything before the anchor
            for line in range(pline, line0):
                self.armed_display.writestr(curlines[line][pchar:] + '\n')
                pchar = 0
            dummy = self.armed_display.writestr(curlines[line0][pchar:char0])
            pline, pchar = line0, char0
            # write the anchor text and remember its
            # position (note: the anchor may span several
            # lines)
            for line in range(pline, line1):
                box = self.armed_display.writestr(curlines[line][pchar:])
                buttons.append((name, box, type, times))
                dummy = self.armed_display.writestr('\n')
                pchar = 0
            box = self.armed_display.writestr(curlines[line1][pchar:char1])
            buttons.append((name, box, type, times))
            # update loop invariants
            pline, pchar = line1, char1
            self.armed_display.fgcolor(fgcolor)
        # write text after last button
        for line in range(pline, len(curlines)):
            dummy = self.armed_display.writestr(curlines[line][pchar:] + '\n')
            pchar = 0
##             print 'buttons:',`buttons`
        self.armed_display.fgcolor(self.getbgcolor(node))
        for (name, box, type, times) in buttons:
            button = self.armed_display.newbutton(box, times = times)
            self.setanchor(name, type, button, times)
##             dummy = self.armed_display.writestr(string.joinfields(curlines, '\n'))
        # Draw a little square if some text did not fit.
        box = self.armed_display.writestr('')
        fits = 1
        for pos in box:
            if pos > 1:
                fits = 0
        if not fits:
            import sys
            if sys.platform == 'win32':
                self.window.setcontentcanvas(1.0,box[1]+box[3])
            else:
                xywh = (1.0-margin, 1.0-margin, margin, margin)
                self.armed_display.drawfbox(self.gethicolor(node),
                                    xywh)
        return 1

    def defanchor(self, node, anchor, cb):
        # Anchors don't get edited in the TextChannel.  You
        # have to edit the text to change the anchor.  We
        # don't want a message, though, so we provide our own
        # defanchor() method.
        apply(cb, (anchor,))

# Convert an anchor to a set of boxes.
def map_parpos_to_linepos(parno, charno, last, curlines, partoline):
    # This works only if parno and charno are valid
    while parno < len(partoline):
        sublist = partoline[parno]
        for lineno, char0, char1 in sublist:
            if charno <= char1:
                i = max(0, charno-char0)
                if last:
                    return lineno, i
                curline = curlines[lineno]
                n = len(curline)
                while i < n and curline[i] == ' ': i = i+1
                if i < n:
                    return lineno, charno-char0
                charno = char1
        charno = 0
        parno = parno + 1
    if partoline:
        sublist = partoline[-1]
        lineno, char0, char1 = sublist[-1]
        return lineno, char1
    return 0, 0

def getfont(node):
    return 'Times-Roman'

# Turn a text string into a list of strings, each representing a paragraph.
# Tabs are expanded to spaces (since the font mgr doesn't handle tabs),
# but this only works well at the start of a line or in a monospaced font.
# \n characters separate paragraphs.

def extract_paragraphs(text):
    lines = string.splitfields(text, '\n')
    parlist = []
    for line in lines:
        if '\t' in line: line = string.expandtabs(line, 8)
        parlist.append(line)
    return parlist


# Extract anchor tags from a list of paragraphs.
#
# An anchor starts with "<A NAME=...>" and ends with "</A>".
# Alternatively, for compatability with the HTML channel, anchors can
# be formatted as <A HREF="cmif:...">.
# These tags are case independent; whitespace is significant.
# Anchors may span paragraphs but an anchor tag must be contained in
# one paragraph.  Other occurrences of < are left in the text.
#
# The list of paragraps is modified in place (the tags are removed).
# The return value is a list giving the start and end position
# of each anchor and its name.  Start and end positions are given as
# paragraph_number, character_offset.

pat = re.compile('<a +name=([a-z0-9_]+)>|'
                 '<a +href="cmif:([a-z0-9_]+)">|</a>',
                 re.I)
def extract_taglist(parlist):
    # (1) Extract the raw tags, removing them from the text
    rawtaglist = []
    for i in range(len(parlist)):
        par = parlist[i]
        j = 0
        res = pat.search(par, j)
        while res is not None:
            a, b = res.span(0)
            par = par[:a] + par[b:]
            j = a
            name = res.group(1) or res.group(2) # None if endtag
            rawtaglist.append((i, j, name))
            res = pat.search(par, j)
        parlist[i] = par
    # (2) Parse the raw taglist, picking up the valid patterns
    # (a begin tag immediately followed by an end tag)
    taglist = []
    last = None
    for item in rawtaglist:
        if item[2] is not None:
            last = item
        elif last:
            taglist.append(last[:2] + item[:2] + last[2:3])
            last = None
    return taglist

# Map a possibly symbolic font name to a real font name and default point size

fontmap = {
        '':             ('Times-Roman', 12),
        'default':      ('Times-Roman', 12),
        'plain':        ('Times-Roman', 12),
        'italic':       ('Times-Italic', 12),
        'bold':         ('Times-Bold', 12),
        'courier':      ('Courier', 12),
        'bigbold':      ('Times-Bold', 14),
        'title':        ('Times-Bold', 24),
        'greek':        ('Greek', 14),
        'biggreek':     ('Greek', 17),
        }

def mapfont(fontname):
    if fontmap.has_key(fontname):
        return fontmap[fontname]
    else:
        return fontname, 12
