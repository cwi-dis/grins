"""GRiNS registration database. This module set location and such,
and modifies the maildb classes to maintain a log of who changed
a record last"""

import maildb
import os
import time

DATABASE="/ufs/mm/clients"

try:
        USER=os.environ['USER']
except KeyError:
        try:
                USER=os.environ['LOGNAME']
        except KeyError:
                USER='unknown'

class GrinsDmdbObject(maildb.DmdbObject):
	"""Like DmdbObject, but keep track of last modification"""
	def saveto(self, fp):
		self['Last-Modified-Date'] = `int(time.time())`
		self['Last-Modified-User'] = USER
		maildb.DmdbObject.saveto(self, fp)

def Database(dir=DATABASE):
	return maildb.MdbDatabase(dir, GrinsDmdbObject)
