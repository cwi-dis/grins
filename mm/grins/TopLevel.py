__version__ = "$Id$"

import os, sys, posixpath
import windowinterface
import MMAttrdefs, MMurl
from urlparse import urlparse, urlunparse
from MMExc import *
from Hlinks import *
from usercmd import *
import settings
import systemtestnames

from TopLevelDialog import TopLevelDialog

class TopLevel(TopLevelDialog):
    def __init__(self, main, url, askskin = 1):
        self.window = None
        self.__immediate = 0
        self.__intimer = 0
        self.select_fdlist = []
        self.select_dict = {}
        self._last_timer_id = None
        self.main = main
        self.url = url
        utype, host, path, params, query, fragment = urlparse(url)
        dir, base = posixpath.split(path)
        if (not utype or utype == 'file') and \
           (not host or host == 'localhost'):
            # local file
            self.dirname = dir
        else:
            # remote file
            self.dirname = ''
##         if base[-5:] == '.cmif':
##             self.basename = base[:-5]
        if base[-4:] == '.smi':
            self.basename = base[:-4]
        elif base[-5:] == '.smil':
            self.basename = base[:-5]
        else:
            self.basename = base
        url = urlunparse((utype, host, path, params, query, None))
        self.filename = url
        self.source = None

        if askskin:
            self.read_it_with_skin()
        else:
            self.read_it()
        self.__checkParseErrors()

        self.makeplayer()
        self.commandlist = [
                CLOSE(callback = (self.close_callback, ())),
                RELOAD(callback = (self.reload_callback, ())),
                USERGROUPS(callback = self.usergroup_callback),
                ]
        import Help
        if hasattr(Help, 'hashelp') and Help.hashelp():
            self.commandlist.append(
                    HELP(callback = (self.help_callback, ())))
        if hasattr(self.root, 'source') and \
           hasattr(windowinterface, 'textwindow'):
            self.commandlist.append(
                    SOURCEVIEW(callback = (self.source_callback, ())))

        settings.register(self)

    # detect the errors/fatal errors
    # if it's a fatal error, re-raise the error
    def __checkParseErrors(self):
        parseErrors = self.root.GetContext().getParseErrors()
        if parseErrors != None:
            if parseErrors.getType() == 'fatal':
                raise MSyntaxError

    def __repr__(self):
        return '<TopLevel instance, url=' + `self.filename` + '>'

    def commit(self, type):
        if self.player is not None:
            self.player.stop()
        self.update_toolbarpulldowns()

    def transaction(self, type):
        return 1

    def show(self):
        TopLevelDialog.show(self)
        if hasattr(self.root, 'source') and \
           hasattr(windowinterface, 'textwindow'):
            if settings.get('showsource'):
                self.source_callback()
        self.setusergroups()

    def destroy(self):
        settings.unregister(self)
        if self in self.main.tops:
            self.main.tops.remove(self)
        self.destroyplayer()
        self.hide()
        self.root.Destroy()

    def timer_callback(self, curtime):
        self.__intimer = 1
##         self.setwaiting()
        self._last_timer_id = None
        self.player.timer_callback(curtime)
        while self.__immediate:
            self.__immediate = 0
            self.player.timer_callback(curtime)
        self.__intimer = 0

    def set_timer(self, delay, arg):
        if self._last_timer_id is not None:
            windowinterface.canceltimer(self._last_timer_id)
            self._last_timer_id = None
        self.__immediate = 0
        if delay >= 0:
            if delay <= 0.01 and self.__intimer:
                self.__immediate = 1
            else:
                self._last_timer_id = windowinterface.settimer(
                        delay, (self.timer_callback, (arg,)))

    #
    # View manipulation.
    #
    def makeplayer(self):
        import Player
        self.player = Player.Player(self)

    def destroyplayer(self):
        self.player.destroy()
        self.player = None

    #
    # Callbacks.
    #
    def source_callback(self):
        self.showsource(self.root.source)
##         self.source.set_mother(self)

#       def open_okcallback(self, filename):
#               if os.path.isabs(filename):
#                       cwd = os.getcwd()
#                       if os.path.isdir(filename):
#                               dir, file = filename, os.curdir
#                       else:
#                               dir, file = os.path.split(filename)
#                       # XXXX maybe should check that dir gets shorter!
#                       while len(dir) > len(cwd):
#                               dir, f = os.path.split(dir)
#                               file = os.path.join(f, file)
#                       if dir == cwd:
#                               filename = file
#               try:
#                       top = TopLevel(self.main, MMurl.pathname2url(filename))
#               except:
#                       msg = sys.exc_value
#                       if type(msg) is type(self):
#                               if hasattr(msg, 'strerror'):
#                                       msg = msg.strerror
#                               else:
#                                       msg = msg.args[0]
#                       windowinterface.showmessage('Open operation failed.\n'+
#                                                   'File: '+filename+'\n'+
#                                                   'Error: '+`msg`)
#                       return
#               top.show()
#               top.player.show()
#               top.player.playsubtree(top.root)

    def progressCallback(self, pValue):
        self.progress.set(self.progressMessage, None, None, pValue*100, 100)

    def getsettingsdict(self):
        # Returns the initializer dictionary used
        # to create the toolbar pulldown menus for
        # preview playback preferences

        alltests = self.root.GetAllSystemTests()
        dict = {}
        for testname in alltests:
            exttestname = systemtestnames.int2extattr(testname)
            val = settings.get(testname)
            values = systemtestnames.getallexternal(testname)
            init = systemtestnames.int2extvalue(testname, val)
            dict[exttestname] = (values, (self.systemtestcb, testname), init)
        # Add the "synchronous playback" button
        offon = ['off', 'on']
        cur = offon[settings.get('default_sync_behavior_locked')]
        dict['Synchronous playback'] = (offon, self.syncmodecb, cur)
        return dict

    def update_toolbarpulldowns(self):
        self.setsettingsdict(self.getsettingsdict())

    def syncmodecb(self, arg):
        settings.set('default_sync_behavior_locked', arg == 'on')

    def systemtestcb(self, attrname, extvalue):
        attrvalue = systemtestnames.ext2intvalue(attrname, extvalue)
        if settings.get(attrname) != attrvalue:
            settings.set(attrname, attrvalue)
            self.root.ResetPlayability()
        return 1                # indicate success

    def read_it_with_skin(self):
        if settings.get('askskin'):
            # default profile is SMIL 2.0 Language Profile
            settings.switch_profile(settings.SMIL_20_MODULES)
            windowinterface.FileDialog('Open Components File', '.', ['text/x-grins-skin'], '',
                                       self.__skin_done, self.__skin_done, 1,
                                       parent = windowinterface.getmainwnd())
        else:
            self.read_it()

    def __skin_done(self, filename = None):
        if filename:
            url = MMurl.pathname2url(filename)
        else:
            url = ''
        settings.set('skin', url, dontsave = 1)
        self.read_it()

    def read_it(self):
##         import time
        self.changed = 0
##         print 'parsing', self.filename, '...'
##         t0 = time.time()
        import urlcache
        mtype = urlcache.mimetype(self.filename)
        if mtype not in ('application/x-grins-project', 'application/smil', 'application/smil+xml', 'application/x-grins-binary-project') and (not hasattr(windowinterface, 'is_embedded') or not windowinterface.is_embedded()):
            ans = windowinterface.GetYesNoCancel('MIME type not application/smil or application/x-grins-project.\nOpen as SMIL document anyway?')
            if ans == 0:    # yes
                mtype = 'application/smil'
            elif ans == 2:  # cancel
                raise IOError('user request')
        if mtype in ('application/x-grins-project', 'application/smil', 'application/smil+xml'):
            # init progress dialog
            if mtype in ('application/smil', 'application/smil+xml'):
                self.progress = windowinterface.ProgressDialog("Loading")
                self.progressMessage = "Loading SMIL document..."
            else:
                self.progress = windowinterface.ProgressDialog("Loading")
                self.progressMessage = "Loading GRiNS document..."

            try:
                import SMILTreeRead
                self.root = SMILTreeRead.ReadFile(self.filename, self.printfunc, \
                                                                        progressCallback=(self.progressCallback, 0))

            except (UserCancel, IOError):
                # the progress dialog will desapear
                self.progress = None
                # re-raise
                raise sys.exc_type

            # just update that the loading is finished
            self.progressCallback(1.0)
            # the progress dialog will disappear
            if sys.platform == 'wince':
                self.progress.close()
            self.progress = None

        elif mtype == 'application/x-grins-binary-project':
            self.progress = windowinterface.ProgressDialog("Loading")
            self.progressMessage = "Loading GRiNS document..."
            import QuickRead
            self.root = QuickRead.ReadFile(self.filename, progressCallback = (self.progressCallback, 0.5))
            self.progressCallback(1.0)
            if sys.platform == 'wince':
                self.progress.close()
            self.progress = None
##         elif mtype == 'application/x-grins-cmif':
##             import MMRead
##             self.root = MMRead.ReadFile(self.filename)
        else:
            from MediaRead import MediaRead
            self.root = MediaRead(self.filename, mtype, self.printfunc)
##         t1 = time.time()
##         print 'done in', round(t1-t0, 3), 'sec.'
        self.context = self.root.GetContext()
        if sys.platform == 'wince':
            errors = self.context.getParseErrors()
            if errors is not None:
                if errors.getType() == 'fatal':
                    msg = 'Fatal error'
                else:
                    msg = 'Error'
                logfile = r'\My Documents\GRiNS Error Log.txt'
                f = open(logfile, 'w')
                f.write(errors.getFormatedErrorsMessage())
                f.close()
                windowinterface.showmessage('%s logged in %s' % (msg, logfile))

    def printfunc(self, msg):
        if sys.platform != 'wince':
            windowinterface.showmessage('%s\n\n(while reading %s)' % (msg, self.filename))

    def reload_callback(self):
        self.setwaiting()
        self.reload()

    def reload(self):
        # create a new instance
        # important: we have to create the new instance before to delete the old one
        # Thus, if the operation fails we can easily back to the original
        settings.unregister(self)
        try:
            top = TopLevel(self.main, self.url)
        except IOError:
            windowinterface.showmessage('Cannot open: %s' % self.url)
            return
        except MSyntaxError:
            windowinterface.showmessage('Parse error in document: %s' % self.url)
            return

        # show the main frame
        top.show()

        # update the recent list.
        self.main._update_recent(None)

        # at list
        top.player.show()

        # at least, we can close the old instance, before at there was no error
        self.close()

    def close_callback(self):
        self.setwaiting()
        if self.source is not None:
            self.source.close()
        self.source = None
        self.close()

    def close(self):
        self.destroy()

    def usergroup_callback(self, name):
        self.setwaiting()
        title, u_state, override, uid = self.context.usergroups[name]
        if not em.transaction():
            return
        if u_state == 'RENDERED':
            u_state = 'NOT_RENDERED'
        else:
            u_state = 'RENDERED'
        self.context.usergroups[name] = title, u_state, override, uid
        self.setusergroups()

    def setusergroups(self):
        menu = []
        ugroups = self.context.usergroups.keys()
        ugroups.sort()
        showhidden = settings.get('showhidden')
        for name in ugroups:
            title, u_state, override, uid = self.context.usergroups[name]
            if not showhidden and override != 'visible':
                continue
            if not title:
                title = name
            menu.append((title, (name,), 't', u_state == 'RENDERED'))
        self.setusergroupsmenu(menu)

    def help_callback(self, params=None):
        import Help
        Help.showhelpwindow()

    def setwaiting(self):
        windowinterface.setwaiting()

    def prefschanged(self):
        self.root.ResetPlayability()

    #
    # Global hyperjump interface
    #
    def jumptoexternal(self, srcanchor, anchor, atype, stype=A_SRC_PLAY, dtype=A_DEST_PLAY):
        # XXXX Should check that document isn't active already,
        # XXXX and, if so, should jump that instance of the
        # XXXX document.
        if type(anchor) is type(''):
            if self.context.state is not None:
                anchor = self.context.state.interpolate(anchor)
            url, aid = MMurl.splittag(anchor)
            url = MMurl.basejoin(self.filename, url)
            # Check whether it's a control anchor
            proto, command = MMurl.splittype(url)
            if proto == 'grins':
                return self.commandurl(command)
        else:
            url = self.filename
            for aid, uid in self.root.SMILidmap.items():
                if uid == anchor.GetUID():
                    break
            else:
                # XXX can't find the SMIL name, guess...
                aid = MMAttrdefs.getattr(anchor, 'name')

        # by default, the document target will be handled by GRiNS
        # note: this varib allow to manage correctly the sourcePlaystate attribute
        # as well, even if the target document is not handled by GRiNS
        grinsTarget = 1

        for top in self.main.tops:
            if top is not self and top.is_document(url):
                break
        else:
            try:
                # if the destination document is not a smil/grins document,
                # it's handle by an external application
                import urlcache
                mtype = urlcache.mimetype(url)
                utype, url2 = MMurl.splittype(url)
                if mtype in ('application/smil',
                             'application/smil+xml',
                             'application/x-grins-project',
##                          'application/x-grins-cmif',
                             ):
                    # in this case, the document is handle by grins
                    top = TopLevel(self.main, url)
                else:
                    grinsTarget = 0
                    windowinterface.shell_execute(url)
            except:
                msg = sys.exc_value
                if type(msg) is type(self):
                    if hasattr(msg, 'strerror'):
                        msg = msg.strerror
                    else:
                        msg = msg.args[0]
                windowinterface.showmessage('Cannot open: '+url+'\n\n'+`msg`)
                return 0

        if grinsTarget:
            top.show()
            # update the recent list.
            if self.main != None:
                self.main._update_recent(None)

            node = top.root
            if hasattr(node, 'SMILidmap') and node.SMILidmap.has_key(aid):
                uid = node.SMILidmap[aid]
                node = node.context.mapuid(uid)
            if dtype == A_DEST_PLAY:
                top.player.show()
                top.player.playfromanchor(node)
            elif dtype == A_DEST_PAUSE:
                top.player.show()
                top.player.playfromanchor(node)
                top.player.pause(1)
            else:
                print 'jump to external: invalid destination state'

        if atype == TYPE_JUMP:
            if grinsTarget:
                self.close()
            else:
                # The hide method doesn't work fine.
                # So, for now stop only the player, instead to hide the window
                self.player.stop()
        elif atype == TYPE_FORK:
            if stype == A_SRC_PLAY:
                pass
            elif stype == A_SRC_PAUSE:
                self.player.pause(1)
            elif stype == A_SRC_STOP:
                self.player.stop()
            else:
                print 'jump to external: invalid source state'

        return 1

    def is_document(self, url):
        return self.filename == url

    def commandurl(self, command):
        # XXXX Or should we schedule it?
        return self._docommandurl(command)

    def _docommandurl(self, command):
        if command == 'pause()':
            if not self.waspaused:
                self.player.pause(1)
            return 1
        if command == 'stop()':
            self.player.stop()
            return 1
        if command == 'close()':
            self.close_callback()
            return 1
        if command == 'open()':
            # self.player.stop() ??
            # self.close_callback() ??
            self.main.openfile_callback()
            return 1
        if command == 'exit()':
            self.main.close_callback()
            return 1
        if command == 'tab()':
            self.player.tab()
            return 1
        if command == 'activate()':
            self.player.activate()
            return 1
        if command == 'skin()':
            self.main.skin_callback()
            return 1
        return 0
