
import win32con
import win32api

class RegKey:
	def __init__(self, key, strSubKey, accessMask = win32con.KEY_READ):
		try:
			self._key = win32api.RegOpenKeyEx(key, strSubKey, 0, accessMask)
		except:
			self._key = None

	def __del__(self):
		if self._key:
			win32api.RegCloseKey(self._key)
	
	def getStrEntry(self, strEntry=''):
		try:
			valobj, type = win32api.RegQueryValueEx(self._key, strEntry)
		except:
			return None
		if type == win32con.REG_SZ or type == win32con.REG_EXPAND_SZ:
			strret = valobj
		else:
			strret = None
		return strret

def setKeyValue(strkey, valname, strval, rootkey = win32con.HKEY_CURRENT_USER):
	try:
		key = win32api.RegOpenKeyEx(rootkey, strkey, 0, win32con.KEY_ALL_ACCESS)
	except win32api.error, arg:
		print arg
		return
	try:
		win32api.RegSetValueEx(key, valname, 0, win32con.REG_SZ, strval)
	except win32api.error, arg:
		print arg
	win32api.RegCloseKey(key)

def getKeyValue(strkey, valname, rootkey = win32con.HKEY_CURRENT_USER):
	retval = None
	try:
		key = win32api.RegOpenKeyEx(rootkey, strkey, 0, win32con.KEY_READ)
	except win32api.error, arg:
		print arg
	else:
		try:
			valobj, type = win32api.RegQueryValueEx(key, valname)
		except win32api.error, arg:
			print arg
		else:
			if type == win32con.REG_SZ or type == win32con.REG_EXPAND_SZ:
				retval = valobj
		win32api.RegCloseKey(key)
	return retval

def createKey(strkey, rootkey = win32con.HKEY_CURRENT_USER):
	try:
		return win32api.RegCreateKey(rootkey, strkey)
	except win32api.error, arg:
		print arg
	else:
		win32api.RegCloseKey(key)
	
# if the file ext exists in the registry db and has an entry 'Content Type'
# then this function returns content type registry value as a string 
# else returns None
def getContentType(ext):
	regKey = RegKey(win32con.HKEY_CLASSES_ROOT,ext)
	if regKey._key:
		contenttype = regKey.getStrEntry('Content Type')
	else:
		contenttype = None
	return contenttype


# on windows for some extensions we have
# only the file type registered not the content
# file_types_map purpose is to fill this gap
# But maybe in such cases would be better
# to use mimetypes.py or search for something even better
file_types_map = {
	'jpegfile': 'image/jpeg',
	'pngfile': 'image/png',
	'giffile': 'image/gif',
	}

def getType(ext):
	regKey = RegKey(win32con.HKEY_CLASSES_ROOT,ext)
	if regKey._key:
		contenttype = regKey.getStrEntry('Content Type')
		filetype = regKey.getStrEntry('')
		if not contenttype and filetype and file_types_map.has_key(filetype):
			contenttype = file_types_map[filetype]
	else:
		contenttype = None
		filetype = None
	return contenttype, filetype


# verb can be: 'open', 'edit', 'print', etc
def getShellCmd(ext, verb='open'):
	regKey = RegKey(win32con.HKEY_CLASSES_ROOT,ext)
	if regKey._key:
		filetype = regKey.getStrEntry()
		fileRegKey = RegKey(win32con.HKEY_CLASSES_ROOT,filetype)
		if fileRegKey._key:
			strSubKey = 'shell\\%s\\command' % verb
			cmdkey = RegKey(fileRegKey._key,strSubKey)
			cmd = cmdkey.getStrEntry()
		else:
			cmd = None	
	else:
		cmd = None
	return cmd


def getShellApp(ext, verb='open'):
	cmd = getShellCmd(ext, verb)
	if cmd:
		cmdl = cmd.split('"')
		if len(cmdl)>1:
			app = cmdl[1]
		else:
			app = cmd.split(' ')[0]
	else:
		app = None
	return app


if __name__ == '__main__':
	print getType('.smi')	
	print getType('.smil')	
	print getType('.asx')
		
	print getType('.bmp')	
	print getType('.gif')	
	print getType('.png')
	print getType('.jpg')
	print getType('.jpeg')

	print getType('.au')	
	print getType('.aiff')
	print getType('.au')	
	print getType('.wav')
	print getType('.avi')
	print getType('.wma')

	print getType('.mov')
	print getType('.mpg')
	print getType('.asf')
	print getType('.wmv')

	print getShellCmd('.smi')
	print getShellApp('.smi')

	createKey(r'Software\Oratrix\toolbars')
	setKeyValue(r'Software\Oratrix\toolbars', 'entry1', '1')
	print getKeyValue(r'Software\Oratrix\toolbars', 'entry1')