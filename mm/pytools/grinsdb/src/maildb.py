# A database that sotres records in MH mail messages
import rfc822
import os
import string
import re
import sys
import time
import stat
import anydbm

Error = 'maildb.Error'

class MdbObject:
	"""A database object stored in an rfc822 message"""
	
	def __init__(self, id, rfcmessage, rw='r'):
		self._id = id
		self._data = rfcmessage
		self._changed = 0
		self._rw = rw

	def is_changed(self):
		return self._changed

	def is_locked(self):
		return self._rw == 'w'

	def getid(self):
		return self._id

	def saveto(self, fp):
		fp.write(str(self._data))
		fp.write('\n') # XXXX
		self._data.rewindbody()
		fp.write(self._data.fp.read())
		self._rw = 'r'
		self._changed = 0
		self._id = None
		
	# Dictionary interface
	def __len__(self):
		return len(self._data)

	def __getitem__(self, name):
		return self._data[name]

	def __setitem__(self, name, value):
		if self._rw != 'w':
			raise Error, 'Cannot modify record'
		self._changed = 1
		self._data[name] = value

	def __delitem__(self, name):
		if self._rw != 'w':
			raise Error, 'Cannot modify record'
		self._changed = 1
		del self._data[name]

	def has_key(self, name):
		return self._data.has_key(name)

	def keys(self):
		return self._data.keys()

	def values(self):
		return self._data.values()

	def items(self):
		return self._data.items()

class DmdbObject(MdbObject):
	"""A database object stored in rfc822 form as the body of another
	rfc822 message"""
	
	def __init__(self, id, rfcmessage, rw='r'):
		self._headers = rfcmessage
		dummy = self._headers.fp.readline()
		if dummy != '\n':
			self._headers.rewindbody()
		data = rfc822.Message(rfcmessage.fp)
		MdbObject.__init__(self, id, data, rw)

	def saveto(self, fp):
		x = str(self._headers)
		if not x:
			x = 'From: noone@nowhere\n'
		fp.write(x)
		fp.write('\n') # XXXX
		MdbObject.saveto(self, fp)

# Filter functions.
PATTERN=re.compile('^[0-9][0-9]*$')
def _filefilter(filename):
	base, file = os.path.split(filename)
	return PATTERN.match(file)

def _msgfilter(rfc822message):
	return 1

# An empty file
class EmptyFile:
	def read(self, *args):
		return ''

	def tell(self):
		return 0

	def readline(self, *args):
		return ''

	def readlines(self, *args):
		return []

	def seek(self, *args):
		pass

def numcmp(str1, str2):
	num1 = string.atoi(num1)
	num2 = string.atoi(num2)
	if num1 < num2:
		return -1
	if num1 > num2:
		return 1
	return 0
		
class MdbDatabase:
	def __init__(self, dirname, objfactory, filefilter=_filefilter):
		self._dirname = dirname
		self._filefilter = filefilter
		self._objfactory = objfactory

	def allids(self):
		filenames = os.listdir(self._dirname)
		return filter(self._filefilter, filenames)

	def id2filename(self, id, type=None):
		rv =  id
		if type == 'BAK':
			rv = rv+'~'
		elif type == 'TMP':
			rv = rv + '.TMP.%d'%os.getpid()
		elif type == 'DEL':
			rv = ','+rv
		elif type:
			rv = rv + '.' + type
		return os.path.join(self._dirname, rv)

	def lock(self, id, new=0):
		if new:
			filename = self.id2filename(id, 'TMP')
			open(filename, 'w').close()
		else:
			filename = self.id2filename(id)
		lockname = self.id2filename(id, 'LCK')
		while 1:
			try:
				os.link(filename, lockname)
			except (OSError, IOError):
				try:
					mtime = os.stat(lockname)[stat.ST_MTIME]
				except (OSError, IOError):
					# Gone in the mean time
					continue
				if mtime < time.time()-20:
					sys.stderr.write("Breaking lock: %s\n"
							 %lockname)
					# More than 2 minutes old
					try:
						os.unlink(lockname)
					except (OSError, IOError):
						pass
				else:
					sys.stderr.write("Wait on lock: %s\n"
							 %lockname)
					time.sleep(2)
			else:
				break
		if new:
			os.unlink(filename)
		

	def unlock(self, id, newfilename=None):
		lockname = self.id2filename(id, 'LCK')
		if newfilename:
			filename = self.id2filename(id)
			backupname = self.id2filename(id, 'BAK')
			
			os.rename(newfilename, filename)
			os.rename(lockname, backupname)
		else:
			os.unlink(lockname)

	def getnewlockedid(self):
		allids = self.allids()
		if allids:
			lastid = allids[-1]
		else:
			lastid = '0'
		while 1:
			lastid = str(string.atoi(lastid)+1)
			try:
				self.lock(lastid, new=1)
			except Error:
				continue
			return lastid

	def open(self, id, rw='r'):
		filename = self.id2filename(id)
		if rw == 'w':
			self.lock(id)
		fp = open(filename)
		msg = rfc822.Message(fp)
		return self._objfactory(id, msg, rw)

	def new(self, msg=None):
		if msg == None:
			msg = rfc822.Message(EmptyFile())
		return self._objfactory(None, msg, 'w')

	def save(self, obj):
		if not obj.is_locked():
			return
		if not obj.is_changed():
			id = obj.getid()
			if id:
				self.unlock(id)
			return
		id = obj.getid()
		if not id:
			id = self.getnewlockedid()
		self._dosave(id, obj)

	def _dosave(self, id, obj):
		tempname = self.id2filename(id, 'NEW')
		fp = open(tempname, "w")
		obj.saveto(fp)
		self.unlock(id, tempname)

	def remove(self, obj):
		if not obj.is_locked():
			return
		id = obj.getid()
		if not id:
			return
		filename = self.id2filename(id)
		delname = self.id2filename(id, 'DEL')
		os.rename(filename, delname)
		self.unlock(id)

	def search(self, field, value):
		allids = self.allids()
		if not field:
			return allids
		matchids = []
		for id in allids:
			obj = self.open(id)
			if obj.has_key(field) and obj[field] == value:
				matchids.append(id)
		return matchids

class Index:
	def __init__(self, filename, mode='r', keylist=[]):
		try:
			self._db = anydbm.open(filename, mode)
		except anydbm.error:
			self._db = None
			self._keylist = []
			return
		if 'c' in mode or 'n' in mode:
			self._keylist = keylist
			self._db['.KEYLIST'] = string.join(keylist, ',')
		else:
			self._keylist = string.split(self._db['.KEYLIST'], ',')

	def add(self, key, value, id):
		if not key in self._keylist:
			raise Error, "Key not in keylist: %s"%key
		keyname = '%s=%s'%(key, value)
		if self._db.has_key(keyname):
			new = self._db[keyname] + ',' + id
		else:
			new = id
		self._db[keyname] = new

	def get(self, key, value):
		if not key in self._keylist:
			raise Error, "Key not in keylist: %s"%key
		keyname = '%s=%s'%(key, value)
		if self._db.has_key(keyname):
			return string.split(self._db[keyname], ',')
		return []

	def has_key(self, key):
		return key in self._keylist

	def keys(self):
		return self._keylist[:]

	def update(self, id, obj):
		for key in self._keylist:
			if obj.has_key(key):
				self.add(key, obj[key], id)


class IndexedMdbDatabase(MdbDatabase):
	def __init__(self, dirname, *args, **kwargs):
		apply(MdbDatabase.__init__, (self, dirname)+args, kwargs)
		indexname = os.path.join(dirname, '.index')
		self.__index = Index(indexname, 'w')

	def search(self, field, value):
		if self.__index.has_key(field):
			return self.__index.get(field, value)
		return MdbDatabase.search(self, field, value)

	def _dosave(self, id, obj):
		self.__index.update(id, obj)
		MdbDatabase._dosave(self, id, obj)
		
def _test():
	dbase = MdbDatabase('.', DmdbObject)
	if len(sys.argv) == 1:
		allids = dbase.search(None, None)
		print "Total records: %d"%len(allids)
		return
	if sys.argv[1] == '-w':
		write = 1
		del sys.argv[1]
	else:
		write = 0
	fieldname = sys.argv[1]
	fieldvalue = sys.argv[2]
	allids = dbase.search(None, None)
	ids = dbase.search(fieldname, fieldvalue)
	print "Matching: %d out of %d"%(len(ids), len(allids))
	for id in ids:
		if write:
			obj = dbase.open(id, 'w')
		else:
			obj = dbase.open(id)
		print id, '\t', obj["email"]
		if write:
			obj['Matched'] = 'yes'
			dbase.save(obj)

if __name__ == "__main__":
	_test()
