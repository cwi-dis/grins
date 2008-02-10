__version__ = "$Id$"

import windowinterface

class SourceViewDialog:
    def __init__(self):
        self.__textwindow = None

    def destroy(self):
        self.__textwindow = None

    def show(self):
        if self.__textwindow is None:
            self.__textwindow = windowinterface.textwindow("", readonly=0, closeCallback = (self.close_callback, ()))
        else:
            # Pop it up
            self.__textwindow.pop()

    def is_showing(self):
        return self.__textwindow is not None

    def hide(self):
        if self.__textwindow is not None:
            self.__textwindow.close()
            self.__textwindow = None

    def get_text(self):
        if self.__textwindow:
            return self.__textwindow.gettext()

    def set_text(self, text, colors=[]):
        if self.__textwindow:
            return self.__textwindow.settext(text, colors)

    def is_changed(self):
        if self.__textwindow:
            return self.__textwindow.is_changed()

    def select_chars(self, s, e):
        if self.__textwindow is not None:
            self.__textwindow.select_chars(s,e)

    def getLineNumber(self):
        if self.__textwindow is None:
            return 0
        return self.__textwindow.getLineNumber()

    def getCurrentCharIndex(self):
        if self.__textwindow is None:
            return -1
        return self.__textwindow.getCurrentCharIndex()
