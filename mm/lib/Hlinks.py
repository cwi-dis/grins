__version__ = "$Id$"

# Hyperlink management module

# An 'Hlinks' instance maintains a list of hyperlinks.
# Normally there is one such instance per context.

# An anchor is an MMNode instance or a string.  If a string, the
# anchor is a URL and refers to an external document.  It can then
# only be a destination of a hyperlink.

# The collection of hyperlinks is stored as a list of 6-tuples
# (anchor1, anchor2, direction, type, src_type, dest_type), where:
# anchor1 and anchor2 are anchors (see above);
# direction  is ->, <- or <->, using the DIR_* constants;
# type is jump, call(deprecated) or fork, using the TYPE_* constants.
# src_type control the source behavior when link is activated, using the A_SRC_* constants.
# dest_type control the destination behavior when link is activated, using the A_DEST_* constants.

# XXX It might be better to store ANCHOR1 and ANCHOR2 in a canonical order,
# this would make the search routines a lot easier (and we're doing more
# searching than changing, probably).  [I doubt it --Guido]

# Tuple indices (to avoid dependencies on the tuple definition in the code)
ANCHOR1 = 0
ANCHOR2 = 1
DIR     = 2

# Link directions
DIR_1TO2 = 0
DIR_2TO1 = 1
DIR_2WAY = 2

# Types
TYPE_JUMP = 0           # Jump to the destination and close the source context
TYPE_CALL = 1           # This value is deprecated in favor of TYPE_FORK with A_SRC_PAUSE
TYPE_FORK = 2           # Jump to the destination and keep the source context

# State of source document when the link is activated
A_SRC_PLAY = 0          # The source continues to play
A_SRC_PAUSE = 1         # The source pauses
A_SRC_STOP = 2          # The source stop

# State of destination document when the link is activated
A_DEST_PLAY = 0         # The destination target start to play when the link is activated
A_DEST_PAUSE = 1        # The destination target is paused when the link is activated

# The class
class Hlinks:

    # Initialize this instance
    def __init__(self):
        self.links = []

    # Return a string representation of this instance
    def __repr__(self):
        return '<Hlinks instance, links=' + `self.links` + '>'

    # Return the entire list of links (read-only)
    def getall(self):
        return self.links

    # Add a link
    def addlink(self, link):
        self.links.append(link)

    # Delete a link.
    # If the link does not exists, delete the reverse link
    def dellink(self, link):
        try:
            self.links.remove(link)
        except ValueError:
##             print 'dellink: try reverse link'
            self.links.remove(self.revlink(link))

    # Add a list of links
    def addlinks(self, linklist):
        self.links = self.links + linklist

    # Find the hyperlinks with the specified anchor as source.
    # Returns a list of all such links
    def findsrclinks(self, anchor):
        rv = []
        for l in self.links:
            if l[ANCHOR1]==anchor and \
                      l[DIR] in (DIR_1TO2, DIR_2WAY):
                rv.append(l)
            elif l[ANCHOR2]==anchor and \
                      l[DIR] in (DIR_2TO1, DIR_2WAY):
                rv.append(self.revlink(l))
        return rv

    # Find the hyperlinks with the specified anchor as destination.
    # Returns a list of all such links
    def finddstlinks(self, anchor):
        # anchor is an anchor tuple of (src, dest, ...)
        rv = []
        for l in self.links:
            if l[ANCHOR2]==anchor and \
               l[DIR] in (DIR_1TO2, DIR_2WAY):
                rv.append(l)
            elif l[ANCHOR1]==anchor and \
                 l[DIR] in (DIR_2TO1, DIR_2WAY):
                rv.append(self.revlink(l))
        return rv

    # Find all links related to one or two anchors.
    def findalllinks(self, a1, a2):
        rv = []
        for l in self.links:
            if a1 is l[ANCHOR1] and (a2 is None or a2 is l[ANCHOR2]):
                rv.append(l)
            elif a1 is l[ANCHOR2] and (a2 is None or a2 is l[ANCHOR1]):
                rv.append(self.revlink(l))
        return rv

    # Find links selected by a predicate
    def selectlinks(self, pred):
        rv = []
        for l in self.links:
            if pred(l):
                rv.append(l)
        return rv

    # Reverse representation of a link
    def revlink(self, link):
        a1, a2, dir = link
        if dir == DIR_1TO2:
            dir = DIR_2TO1
        elif dir == DIR_2TO1:
            dir = DIR_1TO2
        return (a2, a1, dir)

    def findnondanglinganchordict(self):
        dict = {}
        for a1, a2, dir in self.links:
            dict[a1] = 1
            dict[a2] = 1
        return dict
