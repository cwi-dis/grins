__version__ = "$Id$"

# HTMLWrite - Write out layout information in HTML for embedded G2 player


from MMExc import *             # Exceptions
import MMAttrdefs
import Hlinks
import string
import os
import MMurl
import re
from cmif import findfile
import windowinterface
from fmtfloat import round
from nameencode import nameencode

# CMIF channel types that have a visible representation
visible_channel_types={
        'text':1,
        'image':1,
        'video': 1,
        'html':1,
        'RealPix':1,
        'RealText':1,
        'RealVideo':1,
}

# This string is written at the start of a SMIL file.
EVALcomment = '<!-- Created with an evaluation copy of GRiNS -->\n'

nonascii = re.compile('[\200-\377]')

isidre = re.compile('^[a-zA-Z_][-A-Za-z0-9._]*$')


class Error(Exception):
    pass

def WriteFile(root, filename, smilurl, oldfilename='', evallicense = 0, exporttype = 'REAL'):
    if exporttype == 'REAL':
        __WriteFileG2(root, filename, smilurl, oldfilename, evallicense)
    elif exporttype == 'QuickTime':
        __WriteFileQT(root, filename, smilurl, oldfilename, evallicense)
    else:
        windowinterface.showmessage('Unsupported export type in this product: %s'%exporttype)

def __WriteFileG2(root, filename, smilurl, oldfilename='', evallicense = 0):
    if not smilurl:
        return
    # XXXX If oldfilename set we should use that as a template
    templatedir = findfile('Templates')
    templatedir = MMurl.pathname2url(templatedir)
    #
    # This is a bit of a hack. G2 appears to want its URLs without
    # %-style quoting.
    #
    smilurl = MMurl.unquote(smilurl)
    fp = open(filename, 'w')
    ramfile = ramfilename(filename)

    # specific to g2
    try:
        open(ramfile, 'w').write(smilurl+'\n')
    except IOError, arg:
        windowinterface.showmessage('I/O Error writing %s: %s'%(ramfile, arg), mtype = 'error')
        return

    if os.name == 'mac':
        import macfs
        import macostools
        fss = macfs.FSSpec(ramfile)
        fss.SetCreatorType('PNst', 'PNRA')
        macostools.touched(fss)
    ramurl = MMurl.pathname2url(ramfile)
    try:
        writer = HTMLWriter(root, fp, filename, ramurl, oldfilename, evallicense, templatedir, 'REAL')
        writer.write()
        fp.close()
    except Error, msg:
        windowinterface.showmessage(msg, mtype = 'error')
        return
    if os.name == 'mac':
        fss = macfs.FSSpec(filename)
        fss.SetCreatorType('MOSS', 'TEXT')
        macostools.touched(fss)

def __WriteFileQT(root, filename, smilurl, oldfilename='', evallicense = 0):
    # XXXX If oldfilename set we should use that as a template
    templatedir = findfile('Templates')
    templatedir = MMurl.pathname2url(templatedir)
    #
    # This is a bit of a hack. G2 appears to want its URLs without
    # %-style quoting.
    #
    fp = open(filename, 'w')

    try:
        writer = HTMLWriter(root, fp, filename, smilurl, oldfilename, evallicense, templatedir, 'QuickTime')
        writer.write()
        fp.close()
    except Error, msg:
        windowinterface.showmessage(msg, mtype = 'error')
        return


import FtpWriter
def WriteFTP(root, filename, smilurl, ftpparams, oldfilename='', evallicense = 0, exporttype = None):
    if not smilurl:
        return
    host, user, passwd, dir = ftpparams
    import settings
    templatedir = settings.get('templatedir_url')
    #
    # First create and upload the RAM file
    #
    smilurl = MMurl.unquote(smilurl)
    ramfile = ramfilename(filename)
    try:
        ftp = FtpWriter.FtpWriter(host, ramfile, user=user, passwd=passwd, dir=dir, ascii=1)
        ftp.write(smilurl+'\n')
        ftp.close()
    except FtpWriter.all_errors, msg:
        windowinterface.showmessage('Webserver upload failed:\n%s'%(msg,), mtype = 'error')
        return
    #
    # Now create and upload the webpage
    #
    ramurl = MMurl.pathname2url(ramfile)
    try:
        ftp = FtpWriter.FtpWriter(host, filename, user=user, passwd=passwd, dir=dir, ascii=1)
        try:
            writer = HTMLWriter(root, ftp, filename, ramurl, oldfilename, evallicense, templatedir, exporttype)
            writer.write()
            ftp.close()
        except Error, msg:
            windowinterface.showmessage(msg, mtype = 'error')
            return
    except FtpWriter.all_errors, msg:
        windowinterface.showmessage('Webserver upload failed:\n%s'%(msg,), mtype = 'error')
        return

def ramfilename(htmlfilename):
    if htmlfilename[-4:] == '.htm':
        ramfilename = htmlfilename[:-4] + '.ram'
    elif htmlfilename[-5:] == '.html':
        ramfilename = htmlfilename[:-5] + '.ram'
    else:
        ramfilename = htmlfilename + '.ram'
    return ramfilename

class HTMLWriter:
    def __init__(self, node, fp, filename, ramurl, oldfilename='', evallicense = 0, templatedir_url='', exporttype = None):
        self.evallicense = evallicense
        self.ramurl = ramurl
        self.templatedir_url = templatedir_url

        self.root = node
        self.fp = fp
        self.__title = node.GetContext().gettitle()

        self.ids_used = {}

        self.ch2name = {}
        self.top_levels = []
        self.calcViewportName(node)

        if exporttype == 'REAL':
            self.objectgenerator = self.outobjectG2
        elif exporttype == 'QuickTime':
            self.objectgenerator = self.outobjectQT
        else:
            raise 'unknown export type'

    def outtag(self, tag, attrs = None):
        if attrs is None:
            attrs = []
        out = '<' + tag
        for attr, val in attrs:
            out = out + ' %s=%s' % (attr, nameencode(val))
        out = out + '>\n'
        return out

    def write(self):
        import version
        ctxa = self.root.GetContext().attributes
        #
        # Step one - Read the template data. This is an html file
        # with %(name)s constructs that will be filled in later
        #
        if not ctxa.has_key('project_html_page'):
            raise Error, 'Webpage generation skipped: No HTML template selected.'
        template_name = ctxa['project_html_page']
        templatedir = findfile('Templates')
        templatefile = os.path.join(templatedir, template_name)
        if not os.path.exists(templatefile):
            raise Error, 'HTML template file does not exist'
        try:
            template_data = open(templatefile).read()
        except IOError:
            raise Error, 'HTML template %s: I/O error'%template_name

        #
        # Step two - Construct the dictionary for the %(name)s values
        #
        outdict = {}

        outdict['title'] = nameencode(self.__title)[1:-1]
        outdict['generator'] = '<meta name="generator" content="GRiNS %s">'%version.version
        outdict['generatorname'] = 'GRiNS %s'%version.version
        if self.evallicense:
            outdict['generator'] = outdict['generator'] + '\n' + EVALcomment
            outdict['generatorname'] = outdict['generatorname'] + ' (evaluation copy)'
        outdict['ramurl'] = self.ramurl
        outdict['unquotedramurl'] = MMurl.unquote(self.ramurl)
        outdict['templatedir'] = self.templatedir_url
        outdict['author'] = nameencode(ctxa.get('author', ''))[1:-1]
        outdict['copyright'] = nameencode(ctxa.get('copyright', ''))[1:-1]

        playername = 'clip_1'

        out = '<!-- START-GRINS-GENERATED-CODE singleregion -->\n'

        if self.top_levels:
            import features
            if len(self.top_levels) > 1 and (features.MULTIPLE_TOPLAYOUT not in features.feature_set or \
                       (template_data is not None and template_data.find('singleregion') >=0)):
                raise Error, "Multiple toplevel windows"
            w, h = self.top_channel_size(self.top_levels[0])
            if not w or not h:
                raise Error, "Zero-sized presentation window"

            out = out + '<div>\n'

            # we have to take account of slider's width and height in dimension calculation
            out = out + self.objectgenerator(w+20, h+20, [
                    ('controls', 'ImageWindow'),
                    ('console', playername),
                    ('autostart', 'false'),
                    ('src', MMurl.unquote(self.ramurl))])

            out = out + '</div>\n'

        out = out + '<!-- END-GRINS-GENERATED-CODE singleregion -->\n'
        outdict['singleregion'] = out

        #
        # Step three - generate the output
        #
        try:
            output = template_data % outdict
        except:
            raise Error, "Error in HTML template %s"%templatefile
        #
        # Step four - Write it
        #
        self.fp.write(output)

    def outobjectG2(self, width, height, arglist):
        out = self.outtag('object', [
                ('classid', 'clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA'),
                ('width', `width`),
                ('height', `height`)])
        for arg, val in arglist:
            out = out + self.outtag('param', [('name', arg), ('value', val)])
        # Trick: if the browser understands the object tag but not the embed
        # tag (inside it) it will quietly skip it.
        arglist = arglist[:]
        arglist.append(('width', `width`))
        arglist.append(('height', `height`))
        arglist.append(('type', 'audio/x-pn-realaudio-plugin'))
        arglist.append(('nojava', 'true'))
        out = out + self.outtag('embed', arglist)
        out = out + '</object>\n'
        return out

    def outobjectQT(self, width, height, arglist):
        arglist = arglist[:]
        arglist.append(('width', `width`))
        arglist.append(('height', `height`))
        arglist.append(('type', 'video/quicktime'))
        arglist.append(('nojava', 'true'))
        out = self.outtag('embed', arglist)
        return out

    def calcViewportName(self, node):
        # Calculate unique names for channels; first pass
        context = node.GetContext()
        self.top_levels = context.getviewports()
        for viewport in self.top_levels:
            if not self.__title:
                self.__title = viewport.name

    def top_channel_size(self, ch):
        w = ch.GetAttrDef('width', None)
        h = ch.GetAttrDef('height', None)
        if type(w) is type(h) is type(0):
            return w, h
        # if not pixels, return nothing
        return None, None

namechars = string.letters + string.digits + '_-.'

def identify(name):
    # Turn a CMIF name into an identifier
    rv = []
    for ch in name:
        if ch in namechars:
            rv.append(ch)
        else:
            if rv and rv[-1] != '-':
                rv.append('-')
    # the first character must not be a digit
    if rv and rv[0] in string.digits:
        rv.insert(0, '_')
    return string.join(rv, '')
