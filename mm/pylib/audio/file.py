__version__ = "$Id$"

import what, string
import audio

# This dummy function is there to make freeze import the right modules
def _dummy_freeze_func():
    import audio.aifc
    import audio.au
    import audio.hcom
    import audio.voc
    import audio.wav
    import audio.svx8
    import audio.sndt
    import audio.sndr

class _FileDict:
    __fmtdict = {
            'aiff': 'aifc',
            'aifc': 'aifc',
            'au': 'au',
            'hcom': 'hcom',
            'voc': 'voc',
            'wav': 'wav',
            '8svx': 'svx8',
            'sndt': 'sndt',
            'sndr': 'sndr',
            }
    has_key = __fmtdict.has_key
    keys = __fmtdict.keys

    def __init__(self):
        self.__cache = {}

    def __getitem__(self, key):
        try:
            return self.__cache[key]
        except KeyError:
            pass
        module = self.__fmtdict[key]
        try:
            exec 'import %s' % module
        except ImportError:
            raise audio.Error, 'No support for audio file type: '+key
        module = eval(module)
        self.__cache[key] = module
        return module
_filedict = _FileDict()

def reader(file, filetype = None):
    if type(file) == type(''):
        file = open(file, 'rb')
    if filetype is None:
        filetype = what.what(file)
    if not filetype:
        file.close()
        raise audio.Error, 'Unknown audio file type (bad magic number)'
    if not _filedict.has_key(filetype):
        file.close()
        raise audio.Error, 'No support for audio file type: '+filetype[0]
    return _filedict[filetype].reader(file)
