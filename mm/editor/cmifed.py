__version__ = "$Id$"

# Main program for the CMIF editor.

import sys
import os
import features

# The next line enables/disables the CORBA interface to GRiNS

ENABLE_FNORB_SUPPORT = 0
NUM_RECENT_FILES = 10

import getopt

def usage(msg):
    sys.stdout = sys.stderr
    print msg
    print 'usage: cmifed [-q] [-h helpdir] file ...'
    print '-q         : quiet (don\'t print anything to stdout)'
    print '-h helpdir : specify help directory'
    print 'file ...   : one or more CMIF files'
    sys.exit(2)

from MainDialog import MainDialog
from usercmd import *

class Main(MainDialog):
    def __init__(self, opts, files, splash):
        import windowinterface
        import license
        self.splash = splash
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
                    url = self._get_versiondep_url('update.html')
                    windowinterface.htmlwindow(url)
                sys.exit(0)
        self.tmpopts = opts
        self.tmpfiles = files

        self.tmplicensedialog = license.WaitLicense(self.do_init,
                                   features.license_features_needed)
        self.recent_file_list = [] # This is the list of recently opened files.

    def do_init(self, license):
        opts, files = self.tmpopts, self.tmpfiles
        del self.tmpopts
        del self.tmpfiles
##         del self.tmplicensedialog
        import MMurl
        import windowinterface
        if features.lightweight and len(files) > 1:
            windowinterface.showmessage('Cannot open multiple files in this product.')
            files = files[:1]
        self._license = license
##         if not self._license.have('save'):
##             windowinterface.showmessage(
##                 'This is a demo version.\n'+
##                 'You will not be able to save your changes.',
##                 title='CMIFed license')
        self._tracing = 0
        self.tops = []
        self._mm_callbacks = {}
        self.last_location = ''
        self._untitled_counter = 1
        self.template_info = None
        try:
            import mm, posix, fcntl
        except ImportError:
            pass
        else:
            pipe_r, pipe_w = posix.pipe()
            mm.setsyncfd(pipe_w)
            self._mmfd = pipe_r
            windowinterface.select_setcallback(pipe_r,
                                    self._mmcallback,
                                    (posix.read, fcntl.fcntl, fcntl.F_SETFL, posix.O_NDELAY))
        self.commandlist = [
                EXIT(callback = (self.close_callback, ())),
                NEW_DOCUMENT(callback = (self.new_callback, ())),
                OPEN(callback = (self.open_callback, ())),
                OPENFILE(callback = (self.openfile_callback, ())),
                OPEN_RECENT(callback = self.open_recent_callback),      # Dynamic cascade
                PREFERENCES(callback=(self.preferences_callback, ())),
                CHECKVERSION(callback=(self.checkversion_callback, ())),
                ]
        import settings
        if self._license.have('preregistered'):
            settings.set('registered', 'preregistered')
        if not self._license.is_evaluation_license() and \
                        settings.get('registered') != 'preregistered':
            self.commandlist.append(
                    REGISTER(callback=(self.register_callback, ())))
        import Help
        if hasattr(Help, 'hashelp') and Help.hashelp():
            self.commandlist.append(
                    HELP(callback = (self.help_callback, ())))
        if __debug__:
            if settings.get('debug'):
                self.commandlist = self.commandlist + [
                        TRACE(callback = (self.trace_callback, ())),
                        DEBUG(callback = (self.debug_callback, ())),
                        CRASH(callback = (self.crash_callback, ())),
                        ]

        if self.splash is not None:
            self.splash.unsplash()
            self.splash = None

        MainDialog.__init__(self, 'CMIFed', (not not files))

        for file in files:
            self.openURL_callback(MMurl.guessurl(file))
        self._update_recent(None)

        if ENABLE_FNORB_SUPPORT:
            import CORBA.services
            self.corba_services = CORBA.services.services(sys.argv)

        if settings.get('registered') == 'notyet' and \
                        not self._license.is_evaluation_license():
            answer = windowinterface.RegisterDialog()
            astr = ['yes', 'no', 'notyet'][answer]
            settings.set('registered', astr)
            settings.save()
            if astr == 'yes':
                self.register_callback()

    def collect_template_info(self):
        import SMILTreeRead
        import MMmimetypes
        import MMurl
        import settings
        self.templatedir = findfile('Templates')
        names = []
        descriptions = []
        self.template_info = (names, descriptions)
        for dir in settings.get('templatedirs'):
            dir = findfile(dir)
            if not os.path.isdir(dir):
                continue
            files = os.listdir(dir)
            files.sort()
            for file in files:
                pathname = os.path.join(dir, file)
                if not os.path.isfile(pathname):
                    continue
                url = MMurl.pathname2url(pathname)
                if MMmimetypes.guess_type(url)[0] != 'application/x-grins-project':
                    continue
                try:
                    attrs = SMILTreeRead.ReadMetaData(pathname)
                except IOError:
                    windowinterface.showmessage('Error in template: %s'%file)
                    continue
                name = attrs.get('template_name', file)
                description = attrs.get('template_description', '')
                image = attrs.get('template_snapshot')
                if image:
                    image = MMurl.basejoin(url, image)
                    image = MMurl.url2pathname(image)
                names.append(name)
                descriptions.append((description, image, pathname))

    def never_again(self):
        # Called when the user selects the "don't show again" in the initial dialog
        import settings
        settings.set('initial_dialog', 0)
        settings.save()

    def new_callback(self):
        import TopLevel
        import windowinterface

        if not self.canopennewtop():
            return
        if self.template_info is None:
            self.collect_template_info()
        names, descriptions = self.template_info
        if names:
            windowinterface.TemplateDialog(names, descriptions, self._new_ok_callback, parent=self.getparentwindow())
        else:
            windowinterface.showmessage("Missing templates, creating empty document.")
            top = TopLevel.TopLevel(self, self.getnewdocumentname(mimetype="application/x-grins-project"), 1)
            self.new_top(top)

    def help_callback(self, params=None):
        import Help
        Help.showhelpwindow()

    def _new_ok_callback(self, info):
        if not info:
            return
        if len(info) == 3:
            d1, d2, filename = info
            htmltemplate = None
        else:
            d1, d2, filename, htmltemplate = info
        import windowinterface
        windowinterface.setwaiting()
        import TopLevel
        import MMurl
        from MMExc import MSyntaxError, UserCancel
        template_url = MMurl.pathname2url(filename)
        try:
            top = TopLevel.TopLevel(self, self.getnewdocumentname(filename), template_url)
        except IOError:
            import windowinterface
            windowinterface.showmessage('Cannot open: %s' % filename)
        except MSyntaxError, msg:
            message = 'Parse error in document: %s' % filename
            if msg is not None:
                message = message+': %s' % msg
            import windowinterface
            windowinterface.showmessage(message,  mtype='error')
        except (UserCancel, TopLevel.Error):
            pass
        else:
            self.new_top(top)
            if htmltemplate:
                top.context.attributes['project_html_page'] = htmltemplate

    def getnewdocumentname(self, templatename=None, mimetype=None):
        name = 'Untitled%d'%self._untitled_counter
        self._untitled_counter = self._untitled_counter + 1
        if mimetype:
            import MMmimetypes
            ext = MMmimetypes.guess_extension(mimetype)
        else:
            dummy, ext = os.path.splitext(templatename)
        return name + ext

    def canopennewtop(self):
        # Return true if a new top can be opened (only one top in the light version)
        if not features.lightweight:
            return 1
        for top in self.tops:
            top.close()
        if self.tops:
            return 0
        return 1

    def openURL_callback(self, url):
        if not self.canopennewtop():
            return
        import windowinterface
        self.last_location = url
        windowinterface.setwaiting()
        from MMExc import MSyntaxError, UserCancel
        import TopLevel
        for top in self.tops:
            if top.is_document(url):
                windowinterface.showmessage("Already open: %s"%url)
                return
        try:
            top = TopLevel.TopLevel(self, url, 0)
        except IOError:
            import windowinterface
            windowinterface.showmessage('Cannot open: %s' % url)
        except MSyntaxError, msg:
            message = 'Parse error in document: %s' % url
            if msg is not None:
                message = message+': %s' % msg
            import windowinterface
            windowinterface.showmessage(message, mtype='error')
        except (UserCancel, TopLevel.Error):
            pass
        else:
            self.new_top(top)
            self._update_recent(url)

    def open_recent_callback(self, url):
        if not self.canopennewtop():
            return
        self.openURL_callback(url)

    def _update_recent(self, url):
        if url:
            self.add_recent_file(url)
        doclist = self.get_recent_files()
        self.set_recent_list(doclist)

    def get_recent_files(self):
        if not hasattr(self, 'set_recent_list'):
            return
        import settings
        import posixpath
        recent = settings.get('recent_documents')
        doclist = []
        for url in recent:
            base = posixpath.basename(url)
            doclist.append( (base, (url,)))
        return doclist

    def add_recent_file(self, url):
        # Add url to the top of the recent file list.
        assert url
        import settings
        recent = settings.get('recent_documents')
        if url in recent:
            recent.remove(url)
        recent.insert(0, url)
        if len(recent) > NUM_RECENT_FILES:
            recent = recent[:NUM_RECENT_FILES]
        settings.set('recent_documents', recent)
        settings.save()

    def close_callback(self, exitcallback=None):
        import windowinterface
        windowinterface.setwaiting()
        self.do_exit(exitcallback)

    if __debug__:
        def crash_callback(self):
            raise 'Crash requested by user'

        def debug_callback(self):
            import pdb
            pdb.set_trace()

        def trace_callback(self):
            import trace
            if self._tracing:
                trace.unset_trace()
                self._tracing = 0
            else:
                self._tracing = 1
                trace.set_trace()

    def preferences_callback(self):
        import AttrEdit
        AttrEdit.showpreferenceattreditor()

    def checkversion_callback(self):
        import MMurl
        import windowinterface
        url = self._get_versiondep_url('updatecheck.txt')

        try:
            fp = MMurl.urlopen(url)
            data = fp.read()
            fp.close()
        except:
            windowinterface.showmessage('Unable to check for upgrade. You can try again later, or visit www.oratrix.com with your webbrowser.')
            return
        data = data.strip()
        if not data:
            windowinterface.showmessage('You are running the latest version of the software.')
            return
        cancel = windowinterface.GetOKCancel('There appears to be a newer version!\nDo you want to know more?')
        if cancel:
            return
        url = self._add_license_id(self, data)
        windowinterface.htmlwindow(url)

    def _get_versiondep_url(self, filename):
        import version
        return 'http://www.oratrix.com/indir/%s/%s' % (version.shortversion, filename)

    def _add_license_id(self, url, fullkey=0):
        import version
        import settings
        url = '%s?version=%s'%(url, version.shortversion)
        if fullkey:
            url = url + '&key=' + settings.get('license')
        else:
            id = settings.get('license').split('-')[1]
            url = url + '&id=' + id
        return url

    def register_callback(self):
        import windowinterface
        url = self._get_versiondep_url('register.html')
        url = self._add_license_id(url, fullkey=1)
        windowinterface.htmlwindow(url)

    def new_top(self, top):
        top.show()
        top.checkviews()
        self.tops.append(top)

    def do_exit(self, exitcallback=None):
        # XXXX This is pretty expensive (and useless) if AttrEdit hasn't been used...
        import AttrEdit
        AttrEdit.closepreferenceattreditor()
        ok = 1
        for top in self.tops[:]:
            top.close()
        if self.tops:
            return
        if sys.platform == 'mac':
            import MacOS
            MacOS.OutputSeen()
        if exitcallback:
            rtn, arg = exitcallback
            apply(rtn, arg)
        else:
            raise SystemExit, 0

    def run(self):
        import windowinterface
        windowinterface.mainloop()

    def setmmcallback(self, dev, callback):
        if callback:
            self._mm_callbacks[dev] = callback
        elif self._mm_callbacks.has_key(dev):
            del self._mm_callbacks[dev]

    def _mmcallback(self, read, fcntl, F_SETFL, O_NDELAY):
        # set in non-blocking mode
        dummy = fcntl(self._mmfd, F_SETFL, O_NDELAY)
        # read a byte
        devval = read(self._mmfd, 1)
        # set in blocking mode
        dummy = fcntl(self._mmfd, F_SETFL, 0)
        # return if nothing read
        if not devval:
            return
        devval = ord(devval)
        dev, val = devval >> 2, devval & 3
        if self._mm_callbacks.has_key(dev):
            func = self._mm_callbacks[dev]
            func(val)
        else:
            print 'Warning: unknown device in mmcallback'

    def save(self):
        # this is a debug method.  it can be used after a
        # crash to save the documents being edited.
        for top in self.tops:
            nf = top.new_file
            top.new_file = 0
            ok = top.save_callback()
            top.new_file = nf

    def cansave(self):
        return 1

    def wanttosave(self):
##         import license
##         import windowinterface
##         try:
##             features = self._license.need('save')
##         except license.Error, arg:
##             print "No license:", arg
##             return 0
        if self._license.is_evaluation_license():
            return -1
        return 1

def main():
    try:
        opts, files = getopt.getopt(sys.argv[1:], 'qh:')
    except getopt.error, msg:
        usage(msg)

    if sys.argv[0] and sys.argv[0][0] == '-':
        sys.argv[0] = 'cmifed'
    try:
        import splash
    except ImportError:
        splash = None
    else:
        from version import version
        splash.splash(version = 'GRiNS ' + version)

    import settings
    kbd_int = KeyboardInterrupt
    if ('-q', '') in opts and sys.platform not in ('mac', 'win32'):
        # no sense doing this on Mac or Windows
        sys.stdout = open('/dev/null', 'w')
    else:
        if __debug__:
            if settings.get('debug'):
                try:
                    import signal, pdb
                except ImportError:
                    pass
                else:
                    signal.signal(signal.SIGINT,
                                  lambda s, f, pdb=pdb: pdb.set_trace())
                    kbd_int = 'dummy value to prevent interrupts from being caught'

    #
##     import Help
##     if hasattr(Help, 'sethelpprogram'):
##         import settings
##         if settings.get('lightweight'):
##             Help.sethelpprogram('light')
##         else:
##             Help.sethelpprogram('editor')
    for opt, arg in opts:
        if opt == '-h':
            import Help
            Help.sethelpdir(arg)

    m = Main(opts, files, splash)

    try:
        try:
            m.run()
        except kbd_int:
            print 'Interrupt.'
            m.close_callback()
        except SystemExit, sts:
            if type(sts) is type(m):
                if sts.code:
                    print 'Exit %d' % sts.code
            elif sts:
                print 'Exit', sts
            sys.last_traceback = None
            sys.exc_traceback = None
            sys.exit(sts)
        except:
            sys.stdout = sys.stderr
            if hasattr(sys, 'exc_info'):
                exc_type, exc_value, exc_traceback = sys.exc_info()
            else:
                exc_type, exc_value, exc_traceback = sys.exc_type, sys.exc_value, sys.exc_traceback
            import traceback, pdb
            print
            print '\t-------------------------------------------------'
            print '\t| Fatal error - Please mail this output to      |'
            print '\t| grins-support@oratrix.com with a description  |'
            print '\t| of the circumstances.                         |'
            print '\t-------------------------------------------------'
            print '\tVersion:', version
            print
            traceback.print_exception(exc_type, exc_value, None)
            traceback.print_tb(exc_traceback)
            print
            pdb.post_mortem(exc_traceback)
    finally:
        import windowinterface
        windowinterface.close()


# A copy of cmif.findfile().  It is copied here rather than imported
# because the result is needed to extend the Python search path to
# find the cmif module!

# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
# *********  If you change this, also change ../lib/cmif.py   ***********
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

cmifpath = None

def findfile(name):
    global cmifpath
    if os.path.isabs(name):
        return name
    if cmifpath is None:
        if os.environ.has_key('CMIFPATH'):
            var = os.environ['CMIFPATH']
            cmifpath = var.split(':')
        elif os.environ.has_key('CMIF'):
            cmifpath = [os.environ['CMIF']]
        else:
            import sys
            cmifpath = [os.path.dirname(sys.executable)]
            try:
                link = os.readlink(sys.executable)
            except (os.error, AttributeError):
                pass
            else:
                cmifpath.append(os.path.dirname(os.path.join(os.path.dirname(sys.executable), link)))
    for dir in cmifpath:
        fullname = os.path.join(dir, name)
        if os.path.exists(fullname):
            return fullname
    return name

main()
