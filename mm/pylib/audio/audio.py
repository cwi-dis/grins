import whatsound, string

Error = 'audio.Error'

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
	filetype = whatsound.whathdr(filename)
	if not filetype:
		raise Error, 'Unknown audio file type (bad magic number)'
	if not _filedict.has_key(filetype[0]):
		raise Error, 'No support for audio file type: '+filetype[0]
	return _filedict[filetype[0]].reader(filename)
