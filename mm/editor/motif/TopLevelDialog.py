__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *
from flags import *

class TopLevelDialog:
    adornments = {
            'toolbar': [
                    (FLAG_ALL, 'Preview', PLAY),
                    (FLAG_ALL, 'Previewer View', PLAYERVIEW),
                    (FLAG_ALL, 'Structure View', HIERARCHYVIEW),
                    (FLAG_PRO, 'Layout View', LAYOUTVIEW),
                    (FLAG_PRO, 'Hyperlinks', LINKVIEW),
                    (FLAG_BOSTON, 'Custom tests', USERGROUPVIEW),
                    (FLAG_BOSTON, 'Transition', TRANSITIONVIEW),
                    (FLAG_BOSTON, 'Paramgroup', PARAMGROUPVIEW),
                    (FLAG_ALL, 'Properties...', PROPERTIES),
                    (FLAG_ALL, 'Source...', SOURCE),
                    (FLAG_ALL, 'Edit Source...', EDITSOURCE),
                    (FLAG_ALL, 'Save', SAVE),
                    (FLAG_ALL, 'Save as...', SAVE_AS),
                    (FLAG_G2, 'Publish for RealPlayer...', EXPORT_G2),
                    (FLAG_QT, 'Publish for QuickTime...', EXPORT_QT),
                    (FLAG_ALL, 'Restore', RESTORE),
                    (FLAG_ALL, 'Close', CLOSE),
                    (FLAG_ALL, 'Help', HELP),
                    ],
            'toolbarvertical': 1,
            'close': [ CLOSE, ],
            }

    def __init__(self):
        pass

    def show(self):
        if self.window is not None:
            return
        self.adornments['flags'] = curflags()
        self.window = w = windowinterface.newcmwindow(None, None, 0, 0,
                        self.basename, adornments = self.adornments,
                        commandlist = self.commandlist)

    def hide(self):
        if self.window is None:
            return
        self.window.close()
        self.window = None

    def setbuttonstate(self, command, showing):
        self.window.set_toggle(command, showing)

    def setsettingsdict(self, dict):
        pass

    def showsource(self, source = None, optional=0):
##         print 'opt', optional, self.source, 'text', len(source), 'isclosed', self.source and self.source.is_closed()
        if optional and self.source and not self.source.is_showing():
            self.source = None
            return
        if source is None:
            if self.source is not None:
                if not self.source.is_closed():
                    self.source.close()
                self.source = None
            return
        if self.source is not None:
            self.source._children[1].settext(source)
            self.source.show()
            return
        self.source = windowinterface.textwindow(source)

    # set the list of command specific to the system
    def set_commandlist(self):
        pass

    def setcommands(self, commandlist):
        self.window.set_commandlist(commandlist)

    editors = ['XEDITOR', 'WINEDITOR', 'VISUAL', 'EDITOR']
    def do_edit(self, tmp):
        import os
        for e in self.editors:
            editor = os.environ.get(e)
            if editor:
                break
        else:
            # no editor found
            self.edit_finished_callback()
            return
        stat1 = os.stat(tmp)
        os.system('%s %s' % (editor, tmp))
        stat2 = os.stat(tmp)
        from stat import ST_INO, ST_DEV, ST_MTIME, ST_SIZE
        if stat1[ST_INO] == stat2[ST_INO] and \
           stat1[ST_DEV] == stat2[ST_DEV] and \
           stat1[ST_MTIME] == stat2[ST_MTIME] and \
           stat1[ST_SIZE] == stat2[ST_SIZE]:
            # nothing changed
            self.edit_finished_callback()
            return
        self.edit_finished_callback(tmp)
