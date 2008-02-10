__version__ = "$Id$"

# Clipboard module.
#
# There is one *global* clipboard object, but it is implemented as a class,
# so you can create multiple instances if you wish.
#
# Unfortunately, there is no link with the X clipboard facility (yet).
#
# The clipboard node typed: you always specify a list of objects.
# the type of object is known with the 'getClassName' method
# Standard type we currently support
#
# type
#
# 'MMNode'                                      MM subtree (must not have a parent)
# 'Region'                                      MMChannel instance
# 'Viewport'                            MMChannel instance representing a topLayout
# 'RegionAssociation'           MMRegionAssociation instance (LayoutView only)
# 'Properties'                          MMAttrContainer instance
#
# To implement Cut/Copy/Paste (example with single selection)
#
# 'Cut':        use x.Extract() to remove the node from its tree,
#               then call setclip([x])
# 'Copy':       use y = x.DeepCopy() to make a copy of the tree,
#               then call setclip([y])
# 'Paste':      insert the actual contents from the clipboard in the tree,
#               then *copy* it back to the clipboard:
#               list = getclip(); x=[list]; setclip(type, [x.DeepCopy()])

from Owner import *

class Clipboard:

    def __init__(self):
        self.__data = []

    def __repr__(self):
        return '<Clipboard instance, type=' + `self.type` + '>'

    def setclip(self, data):
        if not type(data) in (type(()), type([])):
            print 'Clipboard.setclip : data is not a list ',data
            return
        for node in self.__data:
            node.removeOwner(OWNER_CLIPBOARD)
        for node in data:
            node.addOwner(OWNER_CLIPBOARD)

        self.__data = data

    def getclip(self):
        return self.__data

    def getclipcopy(self):
        data = self.getclip()
        new_data = []
        for node in data:
            if hasattr(node, 'getClassName'):
                if hasattr(node, 'DeepCopy'):
                    # We return the old one and put the new one on the clipboard
                    new_data.append(node.DeepCopy())
                else:
                    # Don't have DeepCopy method. So we guess we don't need to copy
                    # the object in this case
                    new_data.append(node)
        self.restoreclip(new_data)
        return data

    def clearclip(self):
        Clipboard.setclip(self, [])
