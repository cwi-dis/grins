"""checkdb - check the database and generate a new htpasswd file"""
import os
import string
import whrandom
import crypt
import sys
import time
import rfc822
import grinsdb
import grpasswd

ADDPASSWDCMD="ssh trawler.cwi.nl /ufs/jack/bin/addgrinspasswd '%s' '%s' '%s'"
DIR="/usr/local/www.cwi.nl/GRiNS/player"

# PASSWD=os.path.join(DIR, ".htpasswd")
PASSWD="/ufs/jack/test"

RESPONSE_MESSAGE=os.path.join(grinsdb.DATABASE, ".mailresponse")
RESPONSE_SENDER="grins-request-admin@oratrix.com"
RESPONSE_URL="http://www.cwi.nl/GRiNS/player/index.html"

SENDMAIL="/usr/lib/sendmail -t"

Error="grinsregister.Error"

def main():
	if len(sys.argv) > 2:
		print "Usage checkdb [newpasswdfile]"
		sys.exit(1)
	dbase = grinsdb.Database()
	allids = dbase.search(None, None)
	emaildict = {}
	badids = []
	for id in allids:
		obj = dbase.open(id)
		if not obj.has_key('email'):
			badids.append(id)
			continue
		email = obj['email']
		if emaildict.has_key(email):
			emaildict[email].append(id)
		else:
			emaildict[email] = [id]
	if badids:
		print 'Bad messages:',
		for id in badids:
			print id,
			obj = dbase.open(id, 'w')
			dbase.remove(obj)
		print
	for email in emaildict.keys():
		if len(emaildict[email]) > 1:
			print 'Multiple:', email,
			for i in emaildict[email]:
				print i,
			print
	if len(sys.argv) > 1:
		fp = open(sys.argv[1], "w")
		genpasswdfile(dbase, fp)

def genpasswdfile(dbase, fp):
	allids = dbase.search(None, None)
	for id in allids:
		obj = dbase.open(id)
		if not obj.has_key('email'):
			print 'Missing email:', id
			continue
		if not obj.has_key('password'):
			print 'Missing password:', id
			continue
		user = obj['email']
		clear = obj['password']
		crypted = crypt_passwd(clear)
		add_passwd(fp, user, crypted)

def crypt_passwd(clear):
	salt = grpasswd.invent_passwd(2)
	return crypt.crypt(clear, salt)

def add_passwd(fp, user, passwd):
	if ':' in user or '\n' in user or ':' in passwd or '\n' in passwd:
		raise Error, "Illegal username/password"
	fp.write('%s:%s\n'%(user, passwd))
	
main()
