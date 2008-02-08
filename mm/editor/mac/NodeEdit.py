__version__ = "$Id$"

import windowinterface
import os

channeleditors = {}

def _inventname(ch):            # Invent file name from channel name
    import os
    for i in range(1,99):
        fn = '%s-%d.txt'%(ch, i)
        if not os.path.exists(fn):
            return fn
    return fn

def _do_convert(node, fn):      # Convert imm node to ext
    em = node.GetContext().geteditmgr()
    if not em.transaction():
        return
    values = node.GetValues()
    f = open(fn, 'w')
    for i in values:
        f.write(i+'\n')
    f.close()
    em.setnodevalues(node,[])
    em.setnodetype(node,'ext')
    em.setnodeattr(node,'file',fn)
    em.commit()

class _Convert:
    def __init__(self, node):
        import ChannelMime, string
        self.node = node
        chtype = node.GetChannelType()
        types = ChannelMime.ChannelMime.get(chtype)
        if types:
            types = ['/%s files' % string.capitalize(chtype)] + types
        else:
            types = '*'
        windowinterface.FileDialog(
                'This is an internal node. Convert to external?',
                os.curdir, types, _inventname(node.GetChannelName()),
                self.ok, None)

    def ok(self, file):
        import os
        if os.path.exists(file):
            windowinterface.showmessage(
                    'File already exists. Overwrite?',
                    mtype = 'question', title = 'Overwrite?',
                    callback = (self.convert, (file,)))
            return 1        # don't remove dialog
        self.convert(file)

    def convert(self, file):
        _do_convert(self.node, file)
        showeditor(self.node)

## def _merge(f, filename):    # Merge editors file into data structures
##     import string
##     while 1:
##         l = f.readline()
##         if not l:
##             break
##         l = l[:-1]
##         fields = string.splitfields(l,':')
##         # Skip blank lines and comments
##         if fields == [''] or fields[0][:1] == '#': continue
##         if len(fields) <> 3:
##             print 'Bad line in', `filename` + ':', l
##             continue
##         if not channeleditors.has_key(fields[0]):
##             channeleditors[fields[0]] = {fields[1]:fields[2]}
##         elif not channeleditors[fields[0]].has_key(fields[1]):
##             channeleditors[fields[0]][fields[1]] = fields[2]

## def _do_edit(cmd, filename):
##     import os
##     cmd = 'file=%s; %s &' % (filename, cmd)
##     void = os.system(cmd)

## def _showmenu(menu, filename):    # Show (modal) editor choice dialog
##     keys = menu.keys()
##     keys.sort()
##     list = []
##     for key in keys:
##         list.append((key, (_do_edit, (menu[key], filename))))
##     list.append(None)
##     list.append(('Cancel', None))
##     w = windowinterface.Dialog(list, title = 'Choose',
##                    prompt = 'Choose an editor:', grab = 1,
##                    vertical = 0)

## # InitEditors - Initialize the module.
## def InitEditors():
##     # XXX Should add the directory where the .cmif file resides...
##     # XXX (toplevel.dirname)
##     import cmif, os
##     dirs = [os.curdir, os.environ['HOME'], cmif.findfile('editor')]
##     for dirname in dirs:
##         filename = os.path.join(dirname, '.cmif_editors')
##         try:
##             f = open(filename, 'r')
##         except IOError:
##             continue
##         _merge(f, filename)
##         f.close()

def _do_mac_edit(filename):
    import findertools, macfs, aetools
    try:
        rv = findertools.launch(filename)
    except (macfs.error, aetools.Error), arg:
        windowinterface.showmessage("Failed to open file: %s"%str(arg),
                        mtype='warning')

# showeditor - Show the editor (or selector) for a given node
def showeditor(node, url=None):
##     if len(channeleditors) == 0:
##         InitEditors()
    if not url:
        if node.GetType() == 'imm':
            dummy = _Convert(node)
            return
        if node.GetType() <> 'ext':
            windowinterface.showmessage(
                    'Only external nodes can be edited.',
                    mtype = 'error')
            return
        import MMAttrdefs
        url = MMAttrdefs.getattr(node,'file')
    url = node.context.findurl(url)
    import MMurl, urlparse
    utype, host, path, params, query, fragment = urlparse.urlparse(url)
    if (utype and utype != 'file') or (host and host != 'localhost'):
        windowinterface.showmessage(
                'Can only edit local files.',
                mtype = 'warning')
        return
    filename = MMurl.url2pathname(path)
##     chtype = node.GetChannelType()
##     import os
##     if chtype == 'html' and not channeleditors.has_key('html'):
##         chtype = 'text'
##     if not channeleditors.has_key(chtype):
##         windowinterface.showmessage(
##             'NodeEdit.showeditor: no editors for chtype ' + chtype,
##             mtype = 'warning')
##         return
##     editor = channeleditors[chtype]
##     if type(editor) is type(''):
##         _do_edit(editor, filename)
##     else:
##         cmd = _showmenu(editor, filename)
    _do_mac_edit(filename)

## # Simple test program. Only tests editor file parsing.
## def test():
##     InitEditors()
##     print channeleditors
