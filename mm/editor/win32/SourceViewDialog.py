__version__ = "$Id$"

import ViewDialog
import windowinterface, usercmd
from usercmd import *
import features

class SourceViewDialog(ViewDialog.ViewDialog):
    readonly = features.SOURCE_VIEW_EDIT not in features.feature_set

    def __init__(self):
        ViewDialog.ViewDialog.__init__(self, 'sourceview_')
        self.__textwindow = None
        self.__setCommonCommandList()

        self._findReplaceDlg = None
        self._findText = ''
        self._replaceText = None
        self._findOptions = (0,0)
        self.__selChanged = 1
        self.__replacing = 0

    def __setCommonCommandList(self):
        self._commonCommandList = [SELECTNODE_FROM_SOURCE(callback = (self.onRetrieveNode, ())),
                                   FIND(callback = (self.onFind, ())),
                                   FINDNEXT(callback = (self.onFindNext, ())),
                                   ]
        self._copyCommand = [COPY(callback = (self.onCopy, ()))]
        if self.readonly:
            self._undoCommand = []
            self._cutCommand = []
            self._pasteComamnd = []
        else:
            self._commonCommandList.append(REPLACE(callback = (self.onReplace, ())))
            self._undoCommand = [UNDO(callback = (self.onUndo, ()))]
            self._copyCommand.append(CUT(callback = (self.onCut, ())))
            self._pasteComamnd = [PASTE(callback = (self.onPaste, ()))]

    def destroy(self):
        self.__textwindow = None

    def show(self):
        self.load_geometry()
        if not self.__textwindow:
            import MenuTemplate
            self.window = self.__textwindow = \
                    self.toplevel.window.textwindow("", readonly=self.readonly, xywh=self.last_geometry, title='Source')
            self.__textwindow.set_mother(self)
            self.setpopup(MenuTemplate.POPUP_SOURCEVIEW)
        else:
            # Pop it up
            self.pop()
        self.__updateCommandList()
        self.__textwindow.setListener(self)

    def get_geometry(self):
        if self.__textwindow:
            self.last_geometry = self.__textwindow.getgeometry(windowinterface.UNIT_PXL)
            return self.last_geometry

    def pop(self):
        if self.__textwindow != None:
            self.__textwindow.pop()

    def __updateCommandList(self):
        commandList = []

        # undo
        if not self.readonly and self.__textwindow.canUndo():
            commandList.append(UNDO(callback = (self.onUndo, ())))

        # copy/paste/cut
        if self.__textwindow.isSelected():
            commandList = commandList + self._copyCommand
        if not self.readonly and not self.__textwindow.isClipboardEmpty():
            commandList = commandList + self._pasteComamnd

        # other operations all the time actived
        commandList = commandList+self._commonCommandList

        self.setcommandlist(commandList)

    def is_showing(self):
        if self.__textwindow:
            return 1
        else:
            return 0

    def hide(self):
        self.save_geometry()
        if self.__textwindow:
            self.__textwindow.removeListener()
            self.__textwindow.close()
            self.__textwindow = None

        if self._findReplaceDlg:
            self._findReplaceDlg.hide()
            self._findReplaceDlg = None

    def setcommandlist(self, commandlist):
        if self.__textwindow:
            self.__textwindow.set_commandlist(commandlist)

    def setpopup(self, template):
        if self.__textwindow:
            self.__textwindow.setpopupmenu(template)

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
        if self.readonly:
            return 0
        if self.__textwindow:
            return self.__textwindow.isChanged()

    def select_chars(self, s, e):
        if self.__textwindow:
            self.__textwindow.select_chars(s,e)

    def select_lines(self, sLine, eLine):
        if self.__textwindow:
            self.__textwindow.select_line(sLine)

    # return the current line pointed by the carret
    def getCurrentCharIndex(self):
        if self.__textwindow:
            return self.__textwindow.getCurrentCharIndex()
        return -1

    # return the line number
    def getLineNumber(self):
        if self.__textwindow:
            return self.__textwindow.getLineNumber()
        return 0

    #
    # text window listener interface
    #

    # this call back is called when the selection change
    def onSelChanged(self):
        self.__updateCommandList()
        self.__selChanged = 1
        if not self.__replacing and self._findReplaceDlg != None:
            self._findReplaceDlg.enableReplace(0)

    # this call back is called when the content of the clipboard change (or may have changed)
    def onClipboardChanged(self):
        self.__updateCommandList()

    #
    # command listener interface
    #

    # note: these copy, paste and cut operation don't use the GRiNS clipboard
    def onCopy(self):
        self.__textwindow.Copy()

    def onCut(self):
        if self.readonly:
            self.__textwindow.Copy()
        else:
            self.__textwindow.Cut()

    def onPaste(self):
        if not self.readonly:
            self.__textwindow.Paste()

    def onUndo(self):
        if not self.readonly:
            self.__textwindow.Undo()


    #
    # find/replace support
    #

    def onFind(self):
        # if another dlg was showed, we hide it
        if self._findReplaceDlg != None:
            self._findReplaceDlg.hide()
            self._findReplaceDlg = None

        import win32dialog
        self._findReplaceDlg = win32dialog.FindDialog(self.doFindNext, self._findText, self._findOptions, self.window)
        self._findReplaceDlg.show()

    def onFindNext(self):
        if self._findText != None:
            self.doFindNext(self._findText, self._findOptions)

    def onReplace(self):
        if self.readonly:
            return

        # if another dlg was shown, we hide it
        if self._findReplaceDlg != None:
            self._findReplaceDlg.hide()
            self._findReplaceDlg = None

        import win32dialog
        self._findReplaceDlg = win32dialog.ReplaceDialog(self.doFindNext, self.doReplace, self.doReplaceAll, \
                                                                                                        self._findText, self._replaceText, self._findOptions, self.window)
        self._findReplaceDlg.show()
        if not self.__selChanged:
            self._findReplaceDlg.enableReplace(1)

    def doFindNext(self, text, options):
        if not self.__textwindow:
            return

        # save the text and options for the next time
        self._findText = text
        self._findOptions = options

        found = 0
        # first search from the current position
        begin = self.getCurrentCharIndex()
        if self.__textwindow.findNext(begin, text, options) == None:
            # not found, search from the begining
            ret = self.__textwindow.findNext(0, text, options)
            if ret == None:
                windowinterface.showmessage("No more occurrences.", mtype = 'error')
            else:
                found = 1
        else:
            found = 1

        if self._findReplaceDlg != None:
            self._findReplaceDlg.enableReplace(found)
        # raz the flag whitch allows to know if a replace if directly possible.
        self.__selChanged = 0

    def doReplace(self, text, options, replaceText):
        if self.readonly or not self.__textwindow:
            return

        # save the text and options for the next time
        self._findOptions = options

        if self._findText != text:
            # the findwhat value has changed since the last find
            # in this special case, we jump to the next value without automatic replace
            self._findText = text
            self.onFindNext()
            return

        self.__replacing = 1
        # save the text and options for the next time
        self._findText = text

        # save the text for the next time
        self._replaceText = replaceText
        if self.__textwindow:
            self.__textwindow.replaceSel(replaceText)
            # seek on the next occurrence found
            self.onFindNext()

        self.__replacing = 0

    def doReplaceAll(self, text, options, replaceText):
        if self.readonly or not self.__textwindow:
            return

        self.__replacing = 1

        # save the text and options for the next time
        self._findText = text
        self._findOptions = options

        begin = 0
        nocc = 0
        lastPos = None
        pos = self.__textwindow.findNext(begin, self._findText, self._findOptions)
        while pos != None and lastPos != pos:
            lastPos = pos
            self.__textwindow.replaceSel(replaceText)
            begin = self.getCurrentCharIndex()
            nocc = nocc + 1
            pos = self.__textwindow.findNext(begin, self._findText, self._findOptions)

        self.__replacing = 0

        windowinterface.showmessage("Replaced "+`nocc`+' occurrences.')
