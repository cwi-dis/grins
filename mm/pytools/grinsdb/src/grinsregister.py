"""grinsregister - Add somone to the grins access database and
mail them their password"""
import os
import string
import whrandom
import crypt
import sys
import time
import rfc822
import tempfile
import grinsdb
import grpasswd

# Configurable
HOST="trawler.cwi.nl"
SSHIDENT=os.path.join(grinsdb.DATABASE, ".sshidentity")
SSHOPTS="-i %s -l jack"%SSHIDENT
REMOTECMD="/ufs/jack/bin/addgrinspasswd"
ADDPASSWDCMD= "ssh " + \
	      SSHOPTS + " " + \
	      HOST + " " + \
	      REMOTECMD + " '%s' '%s' '%s'"

DIR="/usr/local/www.cwi.nl/GRiNS/player"
PASSWD=os.path.join(DIR, ".htpasswd")

RESPONSE_MESSAGE=os.path.join(grinsdb.DATABASE, ".mailresponse")
RESPONSE_SENDER="grins-request@oratrix.com"
RESPONSE_URL="http://www.oratrix.com/GRiNS/Download/down-sw1.html"
LICENSE=os.path.join(grinsdb.DATABASE, ".evallicense")

SENDMAIL="/usr/lib/sendmail -t"

Error="grinsregister.Error"

def main():
	status = 0
	if len(sys.argv) <= 1:
		os.umask(02)
		tmpfile = tempfile.mktemp()
		tfp = open(tmpfile, 'w+')
		os.unlink(tmpfile)
		tfp.write(sys.stdin.read())
		tfp.seek(0)
		try:
			register(tfp, "<stdin copied to '%s'>"%tmpfile)
		except Error:
			status = 1
	else:
		for file in sys.argv[1:]:
			fp = open(file)
			try:
				register(fp, file)
			except Error:
				status = 1
			else:
				dir, fn = os.path.split(file)
				tmpfn = os.path.join(dir, ','+fn)
				try:
					os.remove(tmpfn)
				except OSError:
					pass
				os.rename(file, tmpfn)
	sys.exit(status)
	
def register(file, filename):
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
		print "Warning: %s: not added, recent duplicate"%filename
		return
	if prevtime:
		print "Duplicate, not added:", filename
		raise Error

	grpasswd.addpasswd(obj)
	if obj.has_key("want-editor") and obj["want-editor"] == "yes":
		now = time.localtime(time.time())
		elr = time.strftime("%d-%h-%Y", now)
		obj['Eval-License-Req'] = elr
		license = open(LICENSE).read()
	else:
		license = ""

	dbase.save(obj)

	clear = obj['password']
	crypted = crypt_passwd(clear)
	add_passwd(PASSWD, user, crypted)
	mail(user, clear, license)
	print "%s: added (%s)"%(user, filename)

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

def mail(user, passwd, license=""):
	ofp = os.popen(SENDMAIL, 'w')
	ifp = open(RESPONSE_MESSAGE, 'r')
	data = ifp.read()
	dict = {
		"user": user,
		"passwd": passwd,
		"sender": RESPONSE_SENDER,
		"url": RESPONSE_URL,
		"license":license,
		}
	ofp.write(data%dict)
	status = ofp.close()
	if status:
		print "%s: sendmail exit status %d"%(user, status)
		raise Error

main()
