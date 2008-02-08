__version__ = "$Id$"

import windowinterface, usercmd

class SourceViewDialog:
    def __init__(self):
        self.__textwindow = None

    def destroy(self):
        self.__textwindow = None
    def show(self):
        if not self.__textwindow:
            self.__textwindow = windowinterface.textwindow("", readonly=0, geometry=self.last_geometry)
            self.__textwindow.set_mother(self)
        else:
            # Pop it up
            pass

    def get_geometry(self):
        if self.__textwindow:
            return self.__textwindow.getgeometry(units=windowinterface.UNIT_PXL)

    def is_showing(self):
        if self.__textwindow:
            return 1
        else:
            return 0

    def hide(self):
        if self.__textwindow:
            self.__textwindow.close()
            self.__textwindow = None

    def get_text(self):
        if self.__textwindow:
            return self.__textwindow.gettext()
        else:
            print "ERROR (get_text): No text window."

    def set_text(self, text, colors=[]):
        if self.__textwindow:
            return self.__textwindow.settext(text, colors)
        else:
            print "ERROR (set text): No text window"

    def is_changed(self):
        if self.__textwindow:
            return self.__textwindow.is_changed()

    def select_lines(self, s, e):
        if self.__textwindow:
            self.__textwindow.select_lines(s,e)

    def select_chars(self, s, e):
        if self.__textwindow:
            self.__textwindow.select_chars(s,e)

    def getCurrentCharIndex(self):
        if self.__textwindow:
            (sl, el), (sc, ec) = self.__textwindow.get_select()
            return sc
        return -1

    # return the line number
    def getLineNumber(self):
        if self.__textwindow:
            (sl, el), (sc, ec) = self.__textwindow.get_select()
            return sl
        return 0

    def setcommandlist(self, cmdlist):
        pass

    def setpopup(self, template):
        pass
