__version__ = "$Id$"

# Placeholder.

import SourceViewDialog
import windowinterface
import SMILTreeRead, SMILTreeWrite
from ViewDialog import ViewDialog
import features
import settings

class SourceView(SourceViewDialog.SourceViewDialog, ViewDialog):
    def __init__(self, toplevel):
        self.last_geometry = None
        self.toplevel = toplevel
        self.editmgr = self.toplevel.editmgr
        self.setRoot(self.toplevel.root)
        self.myCommit = 0
        SourceViewDialog.SourceViewDialog.__init__(self)

        self.errorsview = None

        # keep the original line number before any modification
        # it's still useful to determinate if the selection is still valid
        self.__originalLineNumber = 0

    def fixtitle(self):
        pass

    def destroy(self):
        self.hide()
        SourceViewDialog.SourceViewDialog.destroy(self)

    def show(self):
        if self.is_showing():
            SourceViewDialog.SourceViewDialog.show(self)
        else:
            SourceViewDialog.SourceViewDialog.show(self) # creates the text widget
            self.read_text()
            self.editmgr.register(self, want_focus = 1)

        self.errorsview = self.toplevel.errorsview
        if self.errorsview != None:
            self.errorsview.setListener(self)

        parseErrors = self.context.getParseErrors()
        if parseErrors != None:
            self.updateError()
        else:
            # the normal focus is set only if there is no parsing error
            self.updateFocus()

    def hide(self):
        if self.errorsview != None:
            self.errorsview.removeListener(self)

        if not self.is_showing():
            return
        self.editmgr.unregister(self)
        SourceViewDialog.SourceViewDialog.hide(self)

    def updateFocus(self):
        focusobject = self.editmgr.getglobalfocus()
        self.__setFocus(focusobject)

    def __setFocus(self, focuslist):
        # the normal focus is set only if there is no parsing error
        parseErrors = self.context.getParseErrors()
        if parseErrors is not None:
            return

        # for now, make selection working only when the source is unmodified
        # to avoid some position re-computations adter each modification
        if self.is_changed():
            return

        for focusobject in focuslist:
            if hasattr(focusobject, 'char_positions') and focusobject.char_positions:
                apply(self.select_chars, focusobject.char_positions)

    def globalfocuschanged(self, focusobject):
        self.__setFocus(focusobject)

    def updateError(self):
        # if an error is occured, we set the focus on one specified error
        # it no specified error (no error view, or no selected error),
        # we put the focus on the first error
        selectedError = 0
        if self.errorsview != None:
            selectedError = self.errorsview.getSelectedError()

        if selectedError != None:
            self.showError(selectedError)

    def showError(self, errorNumber):
        parseErrors = self.context.getParseErrors()
        if parseErrors != None:
            errorList = parseErrors.getErrorList()
            if len(errorList) <= errorNumber: return
            # get error line
            errorDesc = parseErrors.getErrorList()[errorNumber]
            msg, line = errorDesc
            if line != None:
                # for now, make selection working only when the source is unmodified
                # or the line number hasn't changed.
                # to avoid some position re-computations after each modification
                if not self.is_changed() or self.__originalLineNumber == self.getLineNumber():
                    self.select_lines(line, line+1)

    def setRoot(self, root):
        self.root = root
        self.context = root.context

    #
    # edit manager interface
    #

    def transaction(self, type):
        if self.myCommit:
            return 1
        if self.is_changed():
            q = windowinterface.GetOKCancel("You have unsaved changes in the source view.\nIs it OK to discard these?", self.toplevel.window)
            return not q
        return 1

    def rollback(self):
        pass

    def commit(self, type=None):
        # update root
        self.setRoot(self.toplevel.root)
        self.read_text()
        self.updateFocus()

    #
    #
    #

    def read_text(self):
        parseErrors = self.context.getParseErrors()
        if parseErrors == None:
            # Converts the MMNode structure into SMIL and puts it in the window.
            text = SMILTreeWrite.WriteString(self.root, grinsExt = features.SOURCE_VIEW_EDIT in features.feature_set, set_char_pos = 1)
            colors = self._getcolorpositions(self.root)
            self.set_text(text, colors)
        else:
            self.set_text(parseErrors.getSource())

        # keep the line number before any modification
        self.__originalLineNumber = self.getLineNumber()

    _TYPE2COLOR = {
            # Colors are structure_xxxcolor with 60,60,60 subtracted.
            # Except for media, which have been darkened.
            'par': (19, 96, 70), # settings.get('structure_parcolor'),
            'seq': (56, 94, 129), # settings.get('structure_seqcolor'),
            'excl': (84, 57, 106), # settings.get('structure_exclcolor'),
            'switch': (124, 35, 35), # settings.get('structure_altcolor'),
            'prio': (106, 1, 66), # settings.get('structure_priocolor'),
            'imm': (95, 95, 62), #settings.get('structure_leafcolor'),
            'ext': (95, 95, 62), #settings.get('structure_leafcolor'),
    }


    def _getcolorpositions(self, node):
        # Return (begin, end, color) list for this node and children
        rv = []
        if hasattr(node, 'tag_positions') and node.tag_positions:
            for beginpos, endpos in node.tag_positions:
                type = node.GetType()
                color = self._TYPE2COLOR.get(type, (0, 0, 0))
                rv.append((beginpos, endpos, color))
        for ch in node.GetChildren():
            rv = rv + self._getcolorpositions(ch)
        return rv

    def write_text(self):
        # Writes the text back to the MMNode structure.
        self.toplevel.save_source_callback(self.get_text())

    def __applySource(self, wantToHide, autoFixErrors=0):
        self.myCommit = 1
        if self.editmgr.transaction('source'):
            text = self.get_text()

            root = self.toplevel.load_source(text)
            root = self.toplevel.checkParseErrors(root)
            context = root.GetContext()
            parseErrors = context.getParseErrors()
            if parseErrors != None:
                # XXX note: the choices may be different for 'fatal error'
                if not autoFixErrors:
                    message = "The source document contains "+`parseErrors.getErrorNumber()`+" errors : \n\n" + \
                                      parseErrors.getFormatedErrorsMessage(5) + \
                                      "\nShall I try to fix these for you?"
                    ret = windowinterface.GetYesNoCancel(message, self.toplevel.window)
                else:
                    ret = 0
                if ret == 0: # yes
                    # accept the errors automaticly fixed by GRiNS
                    context.setParseErrors(None)
                    # update edit manager
                    self.editmgr.deldocument(self.root) # old root
                    self.editmgr.adddocument(root) # new root
                elif ret == 1: # no
                    # update edit manager
                    # in this case, update juste the source file with the parse errors
                    self.editmgr.delparsestatus(self.context.getParseErrors()) # old errors
                    self.editmgr.addparsestatus(context.getParseErrors()) # new errors
                    # default treatement: accept errors and don't allow to edit another view
                else: # cancel
                    self.editmgr.rollback()
                    # destroy the new root
                    self.toplevel.destroyRoot(root)
                    self.myCommit= 0
                    return
            else:
                # no error
                if wantToHide:
                    # allow to hide only if no error
                    self.hide()
                # update edit manager
                self.editmgr.deldocument(self.root) # old root
                self.editmgr.adddocument(root) # new root

            self.editmgr.commit()

        self.myCommit= 0

    def apply_callback(self):
        # apply source, not hide, and ask to the user if he wants an automatic GRiNS's fixes
        self.__applySource(0, 0)

    # this method is called by the framework when the user try to close the window
    def close_callback(self):
        if self.is_changed():
            parseErrors = self.context.getParseErrors()
            if parseErrors == None:
                # the source contains some datas not applied, and the original source contains mo error
                saveme = windowinterface.GetYesNoCancel("There are unsaved changes in the source view.\nApply these to the document?", self.toplevel.window)
                if saveme == 0:
                    # Which means "YES"
                    self.__applySource(1) # Which will close all windows.
                elif saveme == 1:
                    # Which means "No"
                    self.hide()
                else:
                    # "Cancel"
                    # Pass through to the end of this method.
                    pass    # I know, it's extraneous, but it's here for completion so it's not a hidden option.
            else:
                # the source contains some datas not applied, and the original source contains some errors
                # in this case, if we apply the changes without ask any questions
                self.__applySource(1) # Which will close all windows.
        else:
            # no change
            parseErrors = self.context.getParseErrors()
            if parseErrors == None:
                # no error, so the view can be closed
                self.hide()
            else:
                # there are some, error. So maybe the user want to leave grins fix automaticly the errors
                ret = windowinterface.GetYesNo("The source document still contains some errors.\nDo you wish to accept GRiNS' automatic fixes?", self.toplevel.window)
                if ret == 0:
                    # yes
                    # apply the source, hide the window, and accept automaticly the GRiNS's fixes
                    self.__applySource(1, 1)
                else:
                    # otherwise, we don't allow to close the window, and we re-raise the error
                    self.updateError()

    def kill(self):
        self.destroy()

    def __appendNodeList(self, node, list):
        list.append(node)
        for child in node.GetChildren():
            self.__appendNodeList(child, list)

    def onRetrieveNode(self):
        if self.is_changed():
            # Should not happen
            windowinterface.showmessage("There are unapplied changes.", mtype = 'error')
            return

        parseErrors = self.context.getParseErrors()
        if parseErrors != None:
            # Should not happen
            windowinterface.showmessage("Please fix the parse errors first.", mtype = 'error')
            return

        charIndex = self.getCurrentCharIndex()
        objectListToInspect = []

        # make a list of objects to inspect
        # 1) mmnode
        self.__appendNodeList(self.root, objectListToInspect)
        # 2) viewport/regions
        viewportList = self.context.getviewports()
        for viewport in viewportList:
            self.__appendNodeList(viewport, objectListToInspect)
        # ... XXX to complete the list (regpoint, anchor, ...) for selectable objects

        # find all objects which surround the current pointed char
        objectFoundList = []
        for object in objectListToInspect:
            if hasattr(object, 'char_positions') and object.char_positions:
                begin, end = object.char_positions
                if charIndex >= begin and charIndex < end:
                    objectFoundList.append(object)

        # figure out the most interior object
        objectToSelect = None
        maxInd = -1
        for object in objectFoundList:
            if object.char_positions > maxInd:
                objectToSelect = object
                maxInd = object.char_positions

        # at last select object
        if objectToSelect != None:
            self.editmgr.setglobalfocus([objectToSelect])
        else:
            # if no object, show a warning
            windowinterface.showmessage("Node not found.", mtype = 'error')

    #
    # methods called from the errorsview to update the error
    #

    def onSelectError(self, errorNumber, pop=0):
        self.showError(errorNumber)
        if pop:
            self.pop()
