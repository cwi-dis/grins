__version__ = "$Id$"

import sys
import pprint
import time
import os

class Trace:
    def __init__(self):
        self.dispatch = {
                'call': self.trace_dispatch_call,
                'return': self.trace_dispatch_return,
                'exception': self.trace_dispatch_exception,
                }
        self.dispatch['c_call'] = self.dispatch['call']
        self.dispatch['c_return'] = self.dispatch['return']
        self.dispatch['c_exception'] = self.dispatch['exception']
        self.modules = None     # restrict to these modules
        self.curframe = None
        self.depth = 0
        self.__printargs = 1
        self.outputfile = open("trace.txt", 'w') # This is never actually closed.
        sys.debugfile = self.outputfile # so other modules can use it.
        print "Sending trace output to trace.txt in working directory."

    def run(self, cmd, globals = None, locals = None):
        if globals is None:
            import __main__
            globals = __main__.__dict__
        if locals is None:
            locals = globals
        sys.setprofile(self.trace_dispatch)
        try:
            exec cmd in globals, locals
        finally:
            sys.setprofile(None)

    def runcall(self, func, *args):
        sys.setprofile(self.trace_dispatch)
        try:
            apply(func, args)
        finally:
            sys.setprofile(None)

    def trace_dispatch(self, frame, event, arg, split = os.path.split, splitext = os.path.splitext):
        curframe = self.curframe
        if curframe is not frame:
            if frame.f_back is curframe:
                self.depth = self.depth + 1
            elif curframe is not None and curframe.f_back is frame:
                self.depth = self.depth - 1
##             elif curframe is not None and curframe.f_back is frame.f_back:
##                 pass
        self.curframe = frame
        if self.modules is not None:
            if not self.modules.has_key(splitext(split(frame.f_code.co_filename)[1])[0]):
                if event == 'return':
                    self.curframe = frame.f_back
                    self.depth = self.depth - 1
                return
        self.dispatch[event](frame, arg)

    def trace_dispatch_call(self, frame, arg, time = time.time):
        pframe = frame.f_back
        code = frame.f_code
        funcname = code.co_name
        if not funcname:
            funcname = '<lambda>'
        filename = code.co_filename
        lineno = frame.f_lineno
        if lineno == -1:
            code = code.co_code
            if code[0] == '\177': # SET_LINENO
                lineno = ord(code[1]) | ord(code[2]) << 8
        if self.__printargs:
            args = self.__args(frame)
        else:
            args = ''
        if pframe is not None:
            plineno = ' (%d)' % pframe.f_lineno
        else:
            plineno = ''
        #print '%s> %s:%d %s(%s)%s' % (' '*self.depth,os.path.split(filename)[1],lineno,funcname,args,plineno)
        self.outputfile.write('%s> %s:%d %s(%s)%s\n' % (' '*self.depth,os.path.split(filename)[1],lineno,funcname,args,plineno))
        self.outputfile.flush() # Incase the program crashes.

        frame.f_locals['__start_time'] = time()

    def trace_dispatch_return(self, frame, arg, time = time.time):
        t = frame.f_locals.get('__start_time', '')
        if t != '':
            t = ' [%.4f]' % (time() - t)
        code = frame.f_code
        funcname = code.co_name
        if not funcname:
            funcname = '<lambda>'
        filename = code.co_filename
        #print '%s< %s:%d %s%s' % (' '*self.depth,filename,frame.f_lineno,funcname,t)
        self.outputfile.write('%s< %s:%d %s%s\n' % (' '*self.depth,filename,frame.f_lineno,funcname,t))
        self.outputfile.flush()
        self.curframe = frame.f_back
        self.depth = self.depth - 1

    def trace_dispatch_exception(self, frame, arg, time = time.time):
        t = frame.f_locals.get('__start_time', '')
        if t != '':
            t = ' [%.4f]' % (time() - t)
        code = frame.f_code
        funcname = code.co_name
        if not funcname:
            funcname = '<lambda>'
        filename = code.co_filename
        #print '%sE %s:%d %s%s' % (' '*self.depth,filename,frame.f_lineno,funcname,t)
        self.outputfile.write('%sE %s:%d %s%s\n' % (' '*self.depth,filename,frame.f_lineno,funcname,t))
        self.outputfile.flush()

    def set_trace(self, *modules):
        try:
            raise Exception
        except:
            frame = sys.exc_traceback.tb_frame
        if modules:
            self.modules = {}
            for m in modules:
                self.modules[m] = 1
        else:
            self.modules = None
        while frame.f_code.co_name != 'set_trace':
            frame = frame.f_back
        d = 0
        self.curframe = frame
        while frame:
            d = d + 1
            frame = frame.f_back
        self.depth = d
        sys.setprofile(self.trace_dispatch)

    def __args(self, frame, repr = pprint.saferepr, range = range):
        code = frame.f_code
        dict = frame.f_locals
        isinit = dict.has_key
        n = code.co_argcount
        flags = code.co_flags
        if flags & 4:
            n = n + 1
        if flags & 8:
            n = n + 1
        str = ''
        sep = ''
        varnames = code.co_varnames
        for i in range(n):
            name = varnames[i]
            if isinit(name):
                try:
                    val = repr(dict[name])
                except:
                    val = '*** not repr-able ***'
            else:
                val = '*** undefined ***'
            str = str + sep + name + '=' + val
            sep = ','
        return str

try:
    import windowinterface
    TraceDialog = windowinterface.TraceDialog
except:
    TraceClass = Trace
else:
    import os
    prunemodules = ['xmllib.py', 're.py']

    class DialogTrace(Trace):
        # A trace variant that shows whatever is traced in a dialog
        def __init__(self):
            Trace.__init__(self)
            self.dialog = TraceDialog()
            self.pruneframe = None
##             self.__printargs = 0

        def trace_dispatch_call(self, frame, arg, time = time.time):
            if self.pruneframe:
                return
            pframe = frame.f_back
            code = frame.f_code
            funcname = code.co_name
            if not funcname:
                funcname = '<lambda>'
            filename = code.co_filename
            lineno = frame.f_lineno
            if lineno == -1:
                code = code.co_code
                if code[0] == '\177': # SET_LINENO
                    lineno = ord(code[1]) | ord(code[2]) << 8
##             if self.__printargs:
##                 args = self.__args(frame)
##             else:
##                 args = ''
##             if pframe is not None:
                plineno = ' (from %d)' % pframe.f_lineno
            else:
                plineno = ''
            filename = os.path.split(filename)[-1]
            if not self.pruneframe and filename in prunemodules:
                self.pruneframe = frame
            msg = '> %s:%d %s %s'%(filename, lineno, funcname, plineno)
            self.dialog.setitem(self.depth, msg, clear=1)
            # XXXX self.dialog.draw
##             frame.f_locals['__start_time'] = time()

        def trace_dispatch_return(self, frame, arg, time = time.time):
##             t = frame.f_locals.get('__start_time', '')
##             if t != '':
##                 t = ' [%.4f]' % (time() - t)
            if self.pruneframe == frame:
                self.pruneframe = None
            if not self.pruneframe:
                code = frame.f_code
                funcname = code.co_name
                if not funcname:
                    funcname = '<lambda>'
                filename = code.co_filename
                filename = os.path.split(filename)[-1]
                msg = '< %s:%d %s'%(filename, frame.f_lineno, funcname)
                self.dialog.setitem(self.depth, msg)
                # XXXX self.dialog.draw
            self.curframe = frame.f_back
            self.depth = self.depth - 1

        def trace_dispatch_exception(self, frame, arg, time = time.time):
##             t = frame.f_locals.get('__start_time', '')
##             if t != '':
##                 t = ' [%.4f]' % (time() - t)
            if self.pruneframe and self.pruneframe != frame:
                return
            code = frame.f_code
            funcname = code.co_name
            if not funcname:
                funcname = '<lambda>'
            filename = code.co_filename
            filename = os.path.split(filename)[-1]
            msg = '< %s:%d %s'%(filename, frame.f_lineno, funcname)
            self.dialog.setitem(self.depth, msg)
            # XXXX self.dialog.draw
    TraceClass = DialogTrace

def run(cmd, globals = None, locals = None):
    TraceClass().run(cmd, globals, locals)

def runcall(*func_args):
    apply(TraceClass().runcall, funcargs)

def set_trace(*modules):
    apply(TraceClass().set_trace, modules)

def unset_trace():
    sys.setprofile(None)
