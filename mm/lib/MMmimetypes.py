import mimetypes
guess_type = mimetypes.guess_type
guess_extension = mimetypes.guess_extension
get_extensions = mimetypes.get_extensions

import grins_mimetypes
mimetypes.types_map.update(grins_mimetypes.mimetypes)

# Platform-specific extensions.
# XXXX This should also be implemented for Windows: we should lookup
# the extension in the registry if we don't know of it.
import sys
if sys.platform == 'mac':
	try:
		import ic
		_ic_instance = ic.IC()
	except:
		_ic_instance = None
		
	def guess_type(url):
		# On the mac we can have serious conflicts between the
		# extension and the cretor/type of the file. As there is
		# no 100% correct way to solve this we let the extension
		# override the creator/type. This will only lead to unexpected
		# results when a file is given an extension _and_ that extension
		# belongs to files with a different mimetype.
		type = mimetypes.guess_type(url)
		if type or not _ic_instance: return type
		try:
			descr = _ic_instance.mapfile(url)
		except ic.error:
			descr = None
		else:
			return descr[8]
		pass # XXXX If file is local get creator/type
		pass # descr = _ic_instance.maptypecreator(type, creator, url)
		if not descr:
			return None
		import windowinterface
		windowinterface.showmessage('Incorrect extension for %s\nThis may cause problems on the web'%url, identity='mimetypemismatch')
		return descr[8]	# The mimetype
