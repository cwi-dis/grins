"""GRiNS registration database. This module set location and such,
and modifies the maildb classes to maintain a log of who changed
a record last"""

import maildb
import os
import time
import string

if os.environ.has_key('GRINS_DATABASE'):
    DATABASE=os.environ['GRINS_DATABASE']
else:
    DATABASE="/ufs/mm/clients"
UNIQUEDIR=os.path.join(DATABASE, ".uniqdir")

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

def Database(dir=DATABASE, indexed=1):
    if indexed:
        return maildb.IndexedMdbDatabase(dir, GrinsDmdbObject)
    else:
        return maildb.MdbDatabase(dir, GrinsDmdbObject)

def Index(dir=DATABASE, keys=[]):
    indexname = os.path.join(dir, '.index')
    return maildb.Index(indexname, 'nf', keys)

def uniqueid():
    """This function assumses everything is correct: the id file
    exists, contains an integer and isn't locked"""
    fname = os.path.join(UNIQUEDIR, ".uniqueid")
    lname = fname + ".LCK"
    os.link(fname, lname)
    oldid = open(fname).read()
    newid = string.atoi(oldid)+1
    open(fname, 'w').write('%d\n'%newid)
    os.unlink(lname)
    return newid

def loglicense(license):
    fname = os.path.join(DATABASE, ".licenselog")
    str = "License: %s\n"%license
    str = str + "Generated-Date: %s\n"%time.ctime(time.time())
    str = str + "Generated-By: %s\n"%USER
    str = str + "\n"
    fp = open(fname, "a")
    fp.write(str)
    fp.close()
