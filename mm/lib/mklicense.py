# License handling code, creation
import string
import sys
import license

Error = license.Error

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
		import whrandom
		yyyy = whrandom.randint(3000,9999)
		mm = whrandom.randint(1,12)
		dd = whrandom.randint(1,31)
	else:
		yyyy, mm, dd = date
	return  _codeint(yyyy, 3) + _codeint(mm, 1) + _codeint(dd, 1)

def _codecheck(items):
	value = license._codecheckvalue(items)
	return _codeint(value, 4)

def _codelicense(uniqid, date, features, user):
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
	print 'Unique id (numeric): ',
	uniqid = input()
	print 'Year (YYYY, zero for indefinite): ',
	yyyy = input()
	if yyyy:
		print 'Month: ',
		mm = input()
		print 'Day: ',
		dd = input()
		date = (yyyy, mm, dd)
	else:
		date = None
	print 'Licensed user (or empty line): ',
	user = raw_input()
	features = 0
	while 1:
		print 'Known features:',
		for i in license.FEATURES.keys():
			print i,
		print
		print 'Feature (or empty line): ',
		fname = raw_input()
		if not fname: break
		features = features+license.FEATURES[fname]
	print 'License:', _codelicense(uniqid, date, features, user)
	
	
