"""grpasswd - Set or print the GRiNS password for a customer"""

import maildb
import grinsdb
import sys
import whrandom

def main():
	if len(sys.argv) not in (2,3):
		print "Usage: grpasswd user [passwd]"
		sys.exit(1)
	user = sys.argv[1]
	passwd = None
	if len(sys.argv) > 2:
		passwd = sys.argv[2]
	dbase = grinsdb.Database()
	idlist = dbase.search('email', user)
	if not idlist:
		print 'No such user:', user
		sys.exit(1)
	if len(idlist) > 1:
		print 'Multiple matches:',
		for id in idlist:
			print id,
		sys.exit(1)
	if not passwd:
		record = dbase.open(idlist[0])
		if record.has_key('password'):
			print 'User: %s'%user
			print 'Password: %s'%record['password']
		else:
			print 'User %s has no password'%user
	else:
		record = dbase.open(idlist[0], 'w')
		if record.has_key('password'):
			if record['password'] == passwd:
				print 'Already set for user %s'%user
				dbase.save(record)
				return
			print 'Warning: changing password!'
			print 'User: %s'%user
			print 'Old Password: %s'%record['password']
		addpasswd(record, passwd)
		dbase.save(record)
		if record.has_key('password'):
			print 'User: %s'%user
			print 'Password: %s'%record['password']
		else:
			print 'User %s has no password'%user

def addpasswd(obj, passwd='-'):
	if passwd == '-':
		passwd = invent_passwd()
	obj['password'] = passwd
	

def invent_passwd(length=6):
	"""Invent a password. Not industry-strenght but good enough for us"""
	ok = "abcdefghijkmnopqrstuvwxyz023456789"
	rv = ''
	for i in range(length):
		rv = rv + whrandom.choice(ok)
	return rv

if __name__ == '__main__':
	main()
