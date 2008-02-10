__version__ = "$Id$"

from appcon import *

class UserCmdInterface:
    def __init__(self):
        self._activecmds={'app':{},'document':{},'pview_':{}}
        self._dyncmds = {}

    def set_commandlist(self, commandlist, context):
        self._activecmds[context] = {}
        if commandlist:
            for cmd in      commandlist:
                self._activecmds[context][cmd.__class__] = cmd
##         print 'set_commandlist', commandlist, context

    def setcoords(self,coords, units=UNIT_MM):
        pass
##         print 'setcoords', coords, units

    def set_dynamiclist(self, command, list):
        pass
##         print 'set_dynamiclist', command, list

    def set_toggle(self, cmdcl, onoff):
        pass
##         print 'set_toggle',  cmdcl, onoff

    def setplayerstate(self, state):
        pass
##         print 'setplayerstate', state

    def execute_cmd(self, cmdclass):
        for ctx in ('pview_', 'document', 'app'):
            dict = self._activecmds[ctx]
            if dict:
                cmd = dict.get(cmdclass)
                if cmd is not None and cmd.callback:
                    apply(apply, cmd.callback)
                    return
        print cmdclass, 'not active'

    def get_cmd_instance(self, cmdclass):
        for ctx in ('pview_', 'document', 'app'):
            dict = self._activecmds[ctx]
            if dict:
                cmd = dict.get(cmdclass)
                if cmd is not None and cmd.callback:
                    return cmd
