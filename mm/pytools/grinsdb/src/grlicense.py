"""grlicense - Set or print the GRiNS license for a customer"""

import maildb
import grinsdb
from graddfield import addfield, getfield, delfield
import sys
import os
import string
try:
	_curdir=os.path.split(__file__)[0]
except:
	_curdir=None
if not _curdir:
	_curdir=sys.path[0]
CMIFLIB=os.path.join(_curdir, "../../../lib")
sys.path.append(CMIFLIB)
import licparser
license = licparser
import getopt
import whrandom
import time
		
Error = license.Error

def gencommerciallicense(version=None):
	if version in (None, 'GSE', 'editor'):
		features = getdefaultfeatures()
	elif version in ('light', 'lite', 'GRL'):
		features = getdefaultlightfeatures()
	else:
		raise Error, ('Unknown license type', version)
	dbase = grinsdb.Database()
	newid = grinsdb.uniqueid()
	date = None
	name = None
	license = codelicense(newid, date, features, name)
	grinsdb.loglicense(license)
	dbase.close()
	return license
	
def genevaluationlicense(version=None):
	if version in (None, 'GSE', 'editor'):
		features = getdefaultfeatures()
	elif version in ('light', 'lite', 'GRL'):
		features = getdefaultlightfeatures()
	else:
		raise Error, ('Unknown license type', version)
	dbase = grinsdb.Database()
	newid = grinsdb.uniqueid()
	date = getdate("+14")
	name = None
	license = codelicense(newid, date, features, name)
	grinsdb.loglicense(license)
	dbase.close()
	return license
	
def main():
	try:
		options, args = getopt.getopt(sys.argv[1:], "lcrn:d:f:u:Eo:")
	except getopt.error:
		usage()
		sys.exit(1)
	list = 0
	create = 0
	remove = 0
	eval = 0
	newid = None
	date = None
	name = None
	features = []
	outfile = None
	for opt, optarg in options:
		if opt == '-l':
			list = 1
		if opt == '-c':
			create = 1
		if opt == '-r':
			remove = 1
		if opt == '-E':
			eval = 1
			create = 1
		if opt == '-n':
			try:
				newid = string.atoi(optarg)
			except string.atoi_error, arg:
				print "Error: -n:", arg
				usage()
				sys.exit(1)
		if opt == '-d':
			try:
				date = getdate(optarg)
			except ValueError, arg:
				print "Error: -d:", arg
				usage()
				sys.exit(1)
		if opt == '-f':
			try:
				features = getfeatures(optarg)
			except ValueError, arg:
				print "Error: -f:", arg
		if opt == '-u':
			name = optarg
		if opt == '-o':
			outfile = optarg
	if not eval and not args:
		usage()
		sys.exit(1)
	if eval and not date:
		print "Error: evaluation licenses need a date"
		usage()
		sys.exit(1)
	if list + create  + remove != 1:
		print "Error: exactly one of -c, -r or -l should be specified"
		usage()
		sys.exit(1)
	if (list or remove) and (newid or date or features or name):
		print "Error: -l and -r exclusive with all other options"
		usage()
		sys.exit(1)
	if (newid or name) and len(args) > 1:
		print "Error: Cannot specify same name or id for multiple licenses"
		usage()
		sys.exit(1)
	dbase = grinsdb.Database()
	if outfile:
		sys.stdout = open(outfile+".NEW", "w")
	if eval:
		if not features:
			features = getdefaultfeatures()
		if not newid:
			newid = grinsdb.uniqueid()
		license = codelicense(newid, date, features, name)
		grinsdb.loglicense(license)
		print "Evaluation-License:", license
		print "Expires: %d/%d/%d"%date
	elif list:
		for email in args:
			license = getfield(dbase, email, 'License')
			if license:
				print 'User: %s'%email
				print 'License: %s'%license
			else:
				print 'User %s has no license'%email
	elif remove:
		for email in args:
			delfield(dbase, email, 'license')
	else:
		if not features:
			features = getdefaultfeatures()
		for email in args:
			if newid:
				thisid = newid
			else:
				thisid = grinsdb.uniqueid()
			license = codelicense(thisid, date, features, name)
			grinsdb.loglicense(license)
			addfield(dbase, email, 'License', license)
	dbase.close()
	if outfile:
		sys.stdout.close()
		try:
			os.rename(outfile, outfile+"~")
		except OSError:
			pass
		os.rename(outfile+".NEW", outfile)

def usage():
	print "Usage: grlicense [options] user"
	print " -l           Print license"
	print " -c           Create license"
	print " -r           Remove license"
	print " -E           Evaluation license, no user required"
	print " -n id        Use this id for new license"
	print " -d yyyymmdd  Use this expiry date (+N for N days in future)"
	print " -f f1,f2,... Enable these features"
	print " -u name      Encode this licenseename"
	print " -o file      Write output to file (with backup)"

def getdefaultfeatures():
	return license.FEATURES["editor"]

def getdefaultlightfeatures():
	return license.FEATURES["light"]

def getfeatures(str):
	strlist = string.split(str, ',')
	features = 0
	for f in strlist:
		try:
			features = features + license.FEATURES[f]
		except IndexError:
			raise ValueError, "Unknown feature: %s"%f
	return features
			
def getdate(str):
	if str[0] == '+':
		# A number of days in the future
		try:
			days = string.atoi(str[1:])
		except string.atoi_error:
			raise ValueError, "Incorrect date offset"
		tv = time.time()
		tv = tv + days*24*60*60
		yyyy, mm, dd = time.localtime(tv)[:3]
		return (yyyy, mm, dd)
	if len(str) != 8:
		raise ValueError, "Incorrect date"
	try:
		yyyy = string.atoi(str[0:4])
		mm = string.atoi(str[4:6])
		dd = string.atoi(str[6:8])
	except string.atoi_error:
		raise ValueError, "Incorrect date"
	return (yyyy, mm, dd)


#
# Coding of licenses. We use a fairly simple scheme: integers are coded
# in groups of 5 bits, right-to-left. Strings are coded in 2 coded chars
# per input char.
#
# Datefields are coded as 3-char year, 2-char month, 2-char day. Any
# year above 3000 is "infinite".
#
# The check is computed by going over the coded string, computing
#    new = old*(MAGIC+ord(char)+index)+(ord(char)+index)
# along the way, and coding the low-order 20 bits of the result.
#
# The final license has the form
#    A-features-date-user-check
# where A can be changed for later algorithms, and user is optional.
#

def _codeint(value, nbytes):
	rv = ''
	for i in range(nbytes):
		next = value & 0x1f
		rv = rv + license._CODEBOOK[next]
		value = value >> 5
	if value:
		raise Error, "Bits remaining in value after coding"
	return rv

def _codestr(value):
	rv = ''
	for ch in value:
		rv = rv + _codeint(ord(ch), 2)
	return rv

def _codedate(date):
	if date is None:
		yyyy = whrandom.randint(3000,9999)
		mm = whrandom.randint(1,12)
		dd = whrandom.randint(1,31)
	else:
		yyyy, mm, dd = date
	return  _codeint(yyyy, 3) + _codeint(mm, 1) + _codeint(dd, 1)

def _codecheck(items):
	value = license._codecheckvalue(items)
	return _codeint(value, 4)

def codelicense(uniqid, date, features, user):
	all = ['A']	# License type
	all.append(_codeint(uniqid, 4))
	all.append(_codedate(date))
	all.append(_codeint(features, 2))
	if user:
		all.append(_codestr(user))
	license = _codecheck(all)
	all.append(license)
	return string.join(all, '-')

if __name__ == '__main__':
	main()
	
