"""grinsregister - Add somone to the grins access database and
mail them their password"""
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

PASSWD=os.path.join(DIR, ".htpasswd")

RESPONSE_MESSAGE=os.path.join(grinsdb.DATABASE, ".mailresponse")
RESPONSE_SENDER="grins-request@oratrix.com"
RESPONSE_URL="http://www.cwi.nl/GRiNS/player/index.html"

SENDMAIL="/usr/lib/sendmail -t"

Error="grinsregister.Error"

def main():
	status = 0
	if len(sys.argv) <= 1:
		try:
			register(sys.stdin)
		except Error:
			status = 1
	else:
		for file in sys.argv[1:]:
			fp = open(file)
			try:
				register(fp)
			except Error:
				status = 1
	sys.exit(status)
	
def register(file):
	dbase = grinsdb.Database()
	msg = rfc822.Message(file)
	obj = dbase.new(msg)

	if not obj.has_key('email'):
		print "Message is not a registration form"
		raise Error
	
	user = obj['email']
	if ':' in user or ' ' in user or not '@' in user:
		print "Invalid email:", user
		raise Error
	prevtime = find_duplicate(dbase, obj)
	if prevtime and prevtime > time.time() - 3*24*3600:
		print "Warning: not added, recent duplicate"
		return
	if prevtime:
		print "Duplicate, not added"
		raise Error

	grpasswd.addpasswd(obj)
	dbase.save(obj)

	clear = obj['password']
	crypted = crypt_passwd(clear)
	add_passwd(PASSWD, user, crypted)
	mail(user, clear)
	print "%s: added"%user

def find_duplicate(dbase, obj):
	user = obj['email']
	list = dbase.search('email', user)
	if not list:
		return 0
	if len(list) > 1:
		print "Multiple duplicates!"
		return -1
	oldobj = dbase.open(list[0])
	for k, v in obj.items():
		if not oldobj.has_key(k) or oldobj[k] != v:
			print "Different duplicate!"
			return -1
	print 'Possible duplicate:', list[0]
	return string.atoi(oldobj['Last-Modified-Date'])

def crypt_passwd(clear):
	salt = grpasswd.invent_passwd(2)
	return crypt.crypt(clear, salt)

def add_passwd(filename, user, passwd):
	fp = os.popen(ADDPASSWDCMD%(filename, user, passwd))
	sys.stdout.write(fp.read())
	sts = fp.close()
	if sts:
		print "ADDPASSWD: Exit status", sts
		raise Error

def mail(user, passwd):
	ofp = os.popen(SENDMAIL, 'w')
	ifp = open(RESPONSE_MESSAGE, 'r')
	data = ifp.read()
	dict = {
		"user": user,
		"passwd": passwd,
		"sender": RESPONSE_SENDER,
		"url": RESPONSE_URL,
		}
	ofp.write(data%dict)
	status = ofp.close()
	if status:
		print "%s: sendmail exit status %d"%(user, status)
		raise Error

main()
