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

PRODUCT_TO_FEATURE = {
	None: ["editor"],
	"editor": ["editor"],
	"GSE": ["editor"],
	"GS1": ["editor"],

	"light": ["light"],
	"lite": ["light"],
	"GRL": ["light"],

	"pro": ["pro"],
	"GRP": ["pro"],
	
	"smil2player": ["smil2player"],
	"embeddedplayer": ["embeddedplayer"],
	"SM2": ["smil2player"],
	"G2P": ["smil2player"],
        "G2PT": ["smil2player"],
	
	"smil2lite": ["smil2lite"],
	"smil2real": ["smil2real"],
	"G2R": ["smil2real"],
	"G2E": ["smil2pro"],
	"smil2pro": ["smil2pro"],

	"ALLPRODUCTS": ["ALLPRODUCTS"],

	"preregistered": ["preregistered"],
	
	"upgradefromsmil1editor": ["upgradefromsmil1editor"],
	"upgradefromsmil2real": ["upgradefromsmil2real"],
	"upgradefromany": ["upgradefromsmil2real", "upgradefromsmil1editor"]

	"G2U": ["upgradefromsmil1editor", "smil2real"],
	"G2V": ["upgradefromsmil1editor", "smil2pro"],
	"G2W": ["upgradefromsmil2real", "smil2pro"],
	}

PLATFORM_TO_PLATFORM = {
	"WIN": "win32",
	"MAC": "mac",
	"SUN": "sunos5",
	"SGI": "irix6",
	None: "ALLPLATFORMS",
	"ALLPLATFORMS": "ALLPLATFORMS",
	}

def gencommerciallicense(version=None, platform=None,
			 user=None, organization=None,
			 preregistered=0):
	features = PRODUCT_TO_FEATURE[version]
	features = features + [PLATFORM_TO_PLATFORM[platform]]
	if preregistered:
		features = features + ["preregistered"]
	features = encodefeatures(features)
	dbase = grinsdb.Database()
	newid = grinsdb.uniqueid()
	date = None
	if user and organization:
		name = user + ',' + organization
	elif user:
		name = user + ','
	elif organization:
		name = organization
	else:
		name = None
	license = codelicense(newid, date, features, name)
	grinsdb.loglicense(license)
	dbase.close()
	return license
	
def genevaluationlicense(version=None, valid=14, platform=None):
	features = PRODUCT_TO_FEATURE[version]
	features = features + [PLATFORM_TO_PLATFORM[platform]]
	features = encodefeatures(features)
	dbase = grinsdb.Database()
	newid = grinsdb.uniqueid()
	date = getdate("+%d"%valid)
	name = None
	license = codelicense(newid, date, features, name)
	grinsdb.loglicense(license)
	dbase.close()
	return license
	
def main():
	try:
		options, args = getopt.getopt(sys.argv[1:], "lcrn:d:f:u:Eo:D:")
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
	decode = None
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
		if opt == '-D':
			decode = optarg
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
	if eval and not date:
		print "Error: evaluation licenses need a date"
		usage()
		sys.exit(1)
	if (not not decode) + list + create  + remove != 1:
		print "Error: exactly one of -D, -c, -r or -l should be specified"
		usage()
		sys.exit(1)
	if decode:
		info = decodelicense(decode)
		print info
		sys.exit(0)
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
			raise 'You must specify features for a commercial license'
		if not args:
			args = [None]
		for email in args:
			if newid:
				thisid = newid
			else:
				thisid = grinsdb.uniqueid()
			license = codelicense(thisid, date, features, name)
			grinsdb.loglicense(license)
			if email:
				addfield(dbase, email, 'License', license)
			else:
				print license
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
	print " -f f1,f2,... Enable these features (default: ALLPRODUCTS, ALLPLATFORMS!)"
	print " -u name      Encode this licenseename"
	print " -o file      Write output to file (with backup)"
	print " -D license   Decode a license and print information"

	print "Features:",
	for k, v in PRODUCT_TO_FEATURE.items():
		if k in v:
			print k,
	print
	print "Platforms:",
	for k, v in PLATFORM_TO_PLATFORM.items():
		print k,
	print

def getdefaultfeatures():
	return encodefeatures(["ALLPRODUCTS", "ALLPLATFORMS"])

def encodefeatures(list):
	rv = 0
	for i in list:
		rv = rv | license.FEATURES[i]
	return rv

def getfeatures(str):
	strlist = string.split(str, ',')
	features = 0
	for f in strlist:
		if PRODUCT_TO_FEATURE.has_key(f):
			fnew = PRODUCT_TO_FEATURE[f]
			if len(fnew) > 1:
				raise 'Canot specify featurelist here: %s'%f
			f = fnew[0]
		elif PLATFORM_TO_PLATFORM.has_key(f):
			f = PLATFORM_TO_PLATFORM[f]
		try:
			features = features + license.FEATURES[f]
		except KeyError:
			raise ValueError, "Unknown feature: %s. Valid: %s"%(f, PRODUCT_TO_FEATURE.keys()+PLATFORM_TO_PLATFORM.keys()+license.FEATURES.keys())
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
	all.append(_codeint(features, 3))
	if user:
		all.append(_codestr(user))
	license = _codecheck(all)
	all.append(license)
	return string.join(all, '-')

def decodelicense(lic):
	status = 'Valid'
	uniqid = ''
	date = (0,0,0)
	features = 0
	user = ''
	fnames = []
	try:
		uniqid, date, features, user = license._decodelicense(lic)
		fnames, dummy, dummy = license._parselicense(lic)
	except license.Error, arg:
		status = 'Invalid: %s'%arg
	fnames = string.join(fnames, ',')
	if date == None or date[0] >= 3000:
		date = 'indefinite'
	else:
		date = "%04.4d/%02.2d/%02.2d"%date
	report="""
License: %s
Status: %s
Unique ID: %s
Expiry Date: %s
Features: %s (0x%x)
Licensee Name: %s
"""%(lic, status, uniqid, date, fnames, features, user)
	return report
		
if __name__ == '__main__':
	main()
	
