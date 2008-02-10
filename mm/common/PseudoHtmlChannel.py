__version__ = "$Id$"

#
# XXXX This is a placeholder for the coming HTML channel. It is just
# an ordinary text channel, but it's anchors have arguments.
#
from Channel import ChannelWindow, error
import string
from TextChannel import extract_paragraphs, extract_taglist, mapfont
from StringStuff import calclines

class HtmlChannel(ChannelWindow):
    chan_attrs = ChannelWindow.chan_attrs + ['fgcolor']

    def __init__(self, name, attrdict, scheduler, ui):
        ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

    def do_arm(self, node, same=0):
        if same and self.armed_display:
            return 1
        try:
            str = self.getstring(node)
        except error, arg:
            print arg
            str = ''
        parlist = extract_paragraphs(str)
        taglist = extract_taglist(parlist)
##             if taglist: print `taglist`
        fontspec = getfont(node)
        fontname, pointsize = mapfont(fontspec)
        baseline, fontheight, pointsize = \
                  self.armed_display.setfont(\
                  fontname, pointsize)
        margin = self.armed_display.strsize('m')[0] / 2
        width = 1.0 - 2 * margin
        curlines, partoline, linetopar = calclines(parlist, \
                  self.armed_display.strsize, width)
        self.armed_display.setpos(margin, baseline)
        buttons = []
        # write the text on the window.
        # The loop is executed once for each anchor defined
        # in the text.  pline and pchar specify how far we got
        # with printing.
        pline, pchar = 0, 0
        for (par0, chr0, par1, chr1, name, type, times) in taglist:
            # first convert paragraph # and character #
            # to line and character.
            line0, char0 = map_parpos_to_linepos(par0, \
                      chr0, 0, curlines, partoline)
            line1, char1 = map_parpos_to_linepos(par1, \
                      chr1, 1, curlines, partoline)
            if (line0, char0) > (line1, char1):
                print 'Anchor without screenspace:', name
                continue
            # write everything before the anchor
            for line in range(pline, line0):
                dummy = self.armed_display.writestr(curlines[line][pchar:] + '\n')
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
        # write text after last button
        for line in range(pline, len(curlines)):
            dummy = self.armed_display.writestr(curlines[line][pchar:] + '\n')
            pchar = 0
##             print 'buttons:',`buttons`
        self.armed_display.fgcolor(self.gethicolor(node))
        for (name, box, type, times) in buttons:
            button = self.armed_display.newbutton(box, times = times)
            button.hiwidth(3)
            self.setanchor(name, type, button, times)
##             dummy = self.armed_display.writestr(string.joinfields(curlines, '\n'))
        # Draw a little square if some text did not fit.
        box = self.armed_display.writestr('')
        fits = 1
        for pos in box:
            if pos > 1:
                fits = 0
        if not fits:
            xywh = (1.0-margin, 1.0-margin, margin, margin)
            self.armed_display.drawfbox(self.gethicolor(node),
                                        xywh)
        return 1

    def defanchor(self, node, anchor, cb):
        # Anchors don't get edited in the HtmlChannel.  You
        # have to edit the text to change the anchor.  We
        # don't want a message, though, so we provide our own
        # defanchor() method.
        apply(cb, (anchor,))

PseudoHtmlChannel = HtmlChannel

# Convert an anchor to a set of boxes.
def map_parpos_to_linepos(parno, charno, last, curlines, partoline):
    # This works only if parno and charno are valid
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

def getfont(node):
    return 'Times-Roman'
