"""lostkey - Lookup someone in the database and mail them their password"""
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

RESPONSE_OK=os.path.join(grinsdb.DATABASE, ".mail-license")
RESPONSE_NOTOK=os.path.join(grinsdb.DATABASE, ".mail-no-license")
LICENSE=os.path.join(grinsdb.DATABASE, ".evallicense")
REGISTER_URL="http://www.oratrix.com/cgi-bin/warm?register.warm"

RESPONSE_SENDER="grins-request@oratrix.com"

SENDMAIL="/usr/lib/sendmail -t"

Error="grinsregister.Error"

def main():
	os.umask(02)
	status = 0
	if len(sys.argv) <= 1:
		try:
			evallicense(sys.stdin, "<stdin>")
		except Error:
			status = 1
	else:
		for file in sys.argv[1:]:
			fp = open(file)
			try:
				evallicense(fp, file)
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
	
def evallicense(file, filename):
	license = open(LICENSE).read()
	dbase = grinsdb.Database()
	msg = rfc822.Message(file)
	fullname, email = msg.getaddr('from')
	if msg.has_key('x-generated-message'):
		return
	list = dbase.search('email', email)
	if not list:
		mailnotok(email)
	else:
		obj = dbase.open(list[0], 'w')
		obj['Want-editor'] = 'yes'
		if obj.has_key('Eval-License-Req'):
			elr = obj['Eval-License-Req'] + ', '
		else:
			elr = ''
		now = time.localtime(time.time())
		elr = elr + time.strftime("%d-%h-%Y", now)
		obj['Eval-License-Req'] = elr
		dbase.save(obj)
		mailok(email, license)
	while file.read(10000):
		pass

def mailok(user, license):
	dict = {
		"user": user,
		"license": license,
		"sender": RESPONSE_SENDER,
		}
	mail(RESPONSE_OK, dict)
	
def mailnotok(user):
	dict = {
		"user": user,
		"sender": RESPONSE_SENDER,
		"url": REGISTER_URL,
		}
	mail(RESPONSE_NOTOK, dict)
	
def mail(msg, dict):
	ifp = open(msg)
	ofp = os.popen(SENDMAIL, 'w')
	data = ifp.read()
	ofp.write(data%dict)
	status = ofp.close()
	if status:
		print "%s: sendmail exit status %d"%(user, status)
		raise Error

main()
