__version__ = "$Id$"

import audiowhat, string
from audio import Error

# This dummy function is there to make freeze import the right modules
def _dummy_freeze_func():
	import audioaifc
	import audioau
	import audiohcom
	import audiovoc
	import audiowav
	import audio8svx
	import audiosndt
	import audiosndr
	
class _FileDict:
	__fmtdict = {
		'aiff': 'audioaifc',
		'aifc': 'audioaifc',
		'au': 'audioau',
		'hcom': 'audiohcom',
		'voc': 'audiovoc',
		'wav': 'audiowav',
		'8svx': 'audio8svx',
		'sndt': 'audiosndt',
		'sndr': 'audiosndr',
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
			raise Error, 'No support for audio file type: '+key
		module = eval(module)
		self.__cache[key] = module
		return module
_filedict = _FileDict()

def reader(filename):
	file = open(filename, 'rb')
	filetype = audiowhat.what(file)
	if not filetype:
		file.close()
		raise Error, 'Unknown audio file type (bad magic number)'
	if not _filedict.has_key(filetype):
		file.close()
		raise Error, 'No support for audio file type: '+filetype[0]
	return _filedict[filetype].reader(file)
