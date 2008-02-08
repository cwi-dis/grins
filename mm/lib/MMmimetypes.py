__version__ = "$Id$"

import mimetypes
guess_type = mimetypes.guess_type

import grins_mimetypes
mimetypes.types_map.update(grins_mimetypes.mimetypes)
mimetypes.init()


# Platform-specific extensions.
# XXXX This should also be implemented for Windows: we should lookup
# the extension in the registry if we don't know of it.
import sys
if sys.platform in ('mac', 'darwin'):
    import MMurl
    import urlparse
    import MacOS
    import os
    try:
        import ic
        _ic_instance = ic.IC()
    except:
        _ic_instance = None

    # Warn only once per URL last part
    warned_names = {}

    def guess_type(url):
        # On the mac we can have serious conflicts between the
        # extension and the cretor/type of the file. As there is
        # no 100% correct way to solve this we let the extension
        # override the creator/type. This will only lead to unexpected
        # results when a file is given an extension _and_ that extension
        # belongs to files with a different mimetype.
        type, encoding = mimetypes.guess_type(url)
        if type:
            return type, encoding
        if not _ic_instance:
            return type, encoding
        #
        # Next step is to see whether the extension is known to Internet Config
        #
        try:
            descr = _ic_instance.mapfile(url)
        except ic.error:
            descr = None
        else:
            mimetype = descr[8]
            if mimetype:
                if not '/' in mimetype:
                    mimetype = mimetype + '/unknown'
                return mimetype, None
        #
        # Final step, for urls pointing to existing local files, we use
        # the creator/type code and give a warning
        #
        utype, host, path, params, query, fragment = urlparse.urlparse(url)
        if (utype and utype != 'file') or (host and host != 'localhost'):
            return None, None
        import windowinterface
        filename = MMurl.url2pathname(path)
        filename_lastpart = os.path.split(filename)[-1]
        try:
            creator, type = MacOS.GetCreatorAndType(filename)
        except MacOS.Error:
            # File doesn't exist. Give the long talk.
            if not warned_names.has_key(filename_lastpart):
                windowinterface.showmessage('Extension for "%s" not recognized.\nFor use with GRiNS (and for use on the web in general) please give your file the correct extension.'%filename_lastpart, identity='nomimetype')
                warned_names[filename_lastpart] = 1
            return None, None
        try:
            descr = _ic_instance.maptypecreator(type, creator, url)
        except:
            descr = None
        if not descr:
            if not warned_names.has_key(filename_lastpart):
                windowinterface.showmessage('Extension for "%s" not recognized.\nFor use with GRiNS (and for use on the web in general) please give your file the correct extension.'%filename_lastpart, identity='nomimetype')
                warned_names[filename_lastpart] = 1
            return None, None
        import windowinterface
        if not warned_names.has_key(filename_lastpart):
            windowinterface.showmessage('Incorrect extension for "%s"\nThis may cause problems on the web'%filename_lastpart, identity='mimetypemismatch')
            warned_names[filename_lastpart] = 1
        mimetype = descr[8]
        if mimetype:
            if not '/' in mimetype:
                mimetype = mimetype + '/unknown'
        else:
            # it may be an empty string, turn into None
            mimetype = None
        return mimetype, None

_guess_type = guess_type
def guess_type(url):
    import urlparse
    scheme, netloc, url, params, query, fragment = urlparse.urlparse(url)
    if not scheme or scheme == 'file':
        import string
        i = string.find(url, '?')
        if i > 0:
            url = url[:i]
    url = urlparse.urlunparse((scheme, netloc, url, '', '', ''))
    return _guess_type(url)

def _longestfirst(s1, s2):
    ret = len(s2) - len(s1)
    if ret == 0:
        return cmp(s1, s2)
    return ret

def get_extensions(type):
    # Get all extensions mapping to this mimetype
    global inited
    import string
    if not mimetypes.inited:
        mimetypes.init()
    type = string.lower(type)
    if not '/' in type:
        majortype = type
    else:
        majortype = None
    extlist = []
    for ext, stype in mimetypes.types_map.items():
        if type == stype:
            extlist.append(ext)
        elif majortype and string.split(stype, '/')[0] == majortype:
            extlist.append(ext)
    extlist.sort(_longestfirst)
    return extlist

def guess_extension(type):
    extlist = get_extensions(type)
    if extlist:
        return extlist[0]
    return None
