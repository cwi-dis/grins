__version__ = "$Id$"

# Main program for the CMIF player.

import sys
import os

NUM_RECENT_FILES = 10

def usage(msg):
    sys.stdout = sys.stderr
    print msg
    print 'usage: grins file ...'
    print 'file ...   : one or more SMIL or CMIF files or URLs'
    sys.exit(2)

from MainDialog import MainDialog
from usercmd import *

from version import version

import features

# empty document, used to get a working skin
EMPTYDOC = 'data:application/smil,<smil/>'

class Main(MainDialog):
    def __init__(self):
        import windowinterface
        if hasattr(features, 'expiry_date') and features.expiry_date:
            import time
            import version
            tm = time.localtime(time.time())
            yymmdd = tm[:3]
            if yymmdd > features.expiry_date:
                rv = windowinterface.GetOKCancel(
                   "This beta copy of GRiNS has expired.\n\n"
                   "Do you want to check www.oratrix.com for a newer version?")
                if rv == 0:
                    url = 'http://www.oratrix.com/indir/%s/update.html'%version.shortversion
                    windowinterface.htmlwindow(url)
                sys.exit(0)

        self.do_init()

    def do_init(self, license=None):
        # We ignore the license, not needed in the player
        import MMurl, windowinterface
        self._tracing = 0
        self.nocontrol = 0      # For player compatability
        self._closing = 0
        self.tops = []
        self.last_location = ''
        self.commandlist = [
                OPEN(callback = (self.open_callback, ())),
                OPENFILE(callback = (self.openfile_callback, ())),
                EXIT(callback = (self.close_callback, ())),
                ]
        if not hasattr(features, 'trial') or not features.trial:
            self.commandlist.append(CHOOSESKIN(callback = (self.skin_callback, ())))
        import settings
        MainDialog.__init__(self, 'GRiNS')
        if settings.get('skin'):
            self.openURL_callback(EMPTYDOC, askskin = 0)

    def __skin_done(self, filename):
        if filename:
            import settings, MMurl
            url = MMurl.pathname2url(filename)
            settings.set('skin', url)
            settings.save()

    def skin_callback(self):
        import settings
        import windowinterface
        oldskin = settings.get('skin')
        windowinterface.FileDialog('Open skin file', '.', ['text/x-ambulant-skin'], '',
                                   self.__skin_done, None, 1,
                                   parent = windowinterface.getmainwnd())
        newskin = settings.get('skin')
        if newskin and oldskin != newskin:
            if self.tops:
                url = self.tops[0].url
            else:
                url = EMPTYDOC
            self.openURL_callback(url, askskin = 0)

    def openURL_callback(self, url, askskin = 1):
        import windowinterface
        windowinterface.setwaiting()
        from MMExc import MSyntaxError
        import TopLevel
        self.last_location = url
        try:
            top = TopLevel.TopLevel(self, url, askskin = askskin)
        except IOError:
            import windowinterface
            windowinterface.showmessage('Cannot open: %s' % url)
        except MSyntaxError:
            import windowinterface
            windowinterface.showmessage('Parse error in document: %s' % url)
        else:
            while self.tops:
                self.tops[0].close_callback()
            self.tops.append(top)
            top.show()
            top.player.show()
            top.player.play_callback()

    def _update_recent(self, url):
        pass

    def close_callback(self, exitcallback=None):
        for top in self.tops[:]:
            top.destroy()
        import windowinterface
        windowinterface.getmainwnd().destroy()

    def closetop(self, top):
        if self._closing:
            return
        self._closing = 1
        self.tops.remove(top)
        top.hide()
        if len(self.tops) == 0:
            # no TopLevels left: exit
            sys.exit(0)
        self._closing = 0

    def run(self):
        import windowinterface
        windowinterface.mainloop()

def main():
    m = Main()
    m.run()
# Call the main program

main()
